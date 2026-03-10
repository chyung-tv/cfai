from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
from typing import Any
from urllib.parse import urlsplit

import httpx
import fmpsdk


class FmpClientError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class FmpCallResult:
    data: list[dict[str, Any]]
    endpoint: str


class FmpClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        timeout_seconds: int = 30,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        parts = urlsplit(self._base_url)
        self._base_origin = f"{parts.scheme}://{parts.netloc}" if parts.scheme and parts.netloc else self._base_url
        self._timeout_seconds = timeout_seconds
        self._max_retries = 3
        self._base_backoff_seconds = 0.5
        self._client: httpx.AsyncClient | None = None

    async def fetch_stock_directory(self) -> FmpCallResult:
        return await self._request_with_fallback(
            candidates=(
                "/stable/stock-list",
                "/api/v3/stock/list",
            ),
            params={},
        )

    async def fetch_company_screener(
        self,
        *,
        country: str,
        is_actively_trading: bool,
        is_etf: bool,
        is_fund: bool,
        limit: int,
    ) -> FmpCallResult:
        params = {
            "country": country,
            "isActivelyTrading": str(is_actively_trading).lower(),
            "isEtf": str(is_etf).lower(),
            "isFund": str(is_fund).lower(),
            "limit": limit,
        }
        try:
            data = await asyncio.to_thread(
                fmpsdk.stock_screener,
                apikey=self._api_key,
                country=country,
                is_actively_trading=is_actively_trading,
                is_etf=is_etf,
                is_fund=is_fund,
                limit=limit,
            )
            normalized = self._normalize_sdk_rows(data, sdk_method="stock_screener")
            if normalized:
                return FmpCallResult(data=normalized, endpoint="fmpsdk.stock_screener")
        except FmpClientError:
            pass

        return await self._request_with_fallback(
            candidates=(
                "/stable/company-screener",
                "/api/v3/stock-screener",
            ),
            params=params,
        )

    async def fetch_profile_by_symbol(self, symbol: str) -> FmpCallResult:
        normalized = symbol.strip().upper()
        try:
            data = await asyncio.to_thread(
                fmpsdk.company_profile,
                apikey=self._api_key,
                symbol=normalized,
            )
            rows = self._normalize_sdk_rows(data, sdk_method="company_profile")
            if rows:
                return FmpCallResult(data=rows, endpoint="fmpsdk.company_profile")
        except FmpClientError:
            pass

        return await self._request_with_fallback(
            candidates=(
                "/stable/profile",
                f"/api/v3/profile/{normalized}",
            ),
            params={"symbol": normalized},
        )

    async def fetch_quote(self, symbol: str) -> FmpCallResult:
        normalized = symbol.strip().upper()
        return await self._request_with_fallback(
            candidates=(
                "/stable/quote",
                f"/api/v3/quote/{normalized}",
            ),
            params={"symbol": normalized},
        )

    async def fetch_income_statement(
        self,
        symbol: str,
        *,
        period: str | None = None,
        limit: int = 8,
    ) -> FmpCallResult:
        return await self._fetch_statement(
            symbol=symbol,
            stable_endpoint="/stable/income-statement",
            v3_prefix="/api/v3/income-statement",
            period=period,
            limit=limit,
        )

    async def fetch_cash_flow_statement(
        self,
        symbol: str,
        *,
        period: str | None = None,
        limit: int = 8,
    ) -> FmpCallResult:
        return await self._fetch_statement(
            symbol=symbol,
            stable_endpoint="/stable/cash-flow-statement",
            v3_prefix="/api/v3/cash-flow-statement",
            period=period,
            limit=limit,
        )

    async def fetch_balance_sheet_statement(
        self,
        symbol: str,
        *,
        period: str | None = None,
        limit: int = 8,
    ) -> FmpCallResult:
        return await self._fetch_statement(
            symbol=symbol,
            stable_endpoint="/stable/balance-sheet-statement",
            v3_prefix="/api/v3/balance-sheet-statement",
            period=period,
            limit=limit,
        )

    async def _fetch_statement(
        self,
        *,
        symbol: str,
        stable_endpoint: str,
        v3_prefix: str,
        period: str | None,
        limit: int,
    ) -> FmpCallResult:
        normalized = symbol.strip().upper()
        params: dict[str, Any] = {
            "symbol": normalized,
            "limit": limit,
        }
        if period:
            params["period"] = period
        return await self._request_with_fallback(
            candidates=(
                stable_endpoint,
                f"{v3_prefix}/{normalized}",
            ),
            params=params,
        )

    async def _request_with_fallback(
        self,
        *,
        candidates: tuple[str, ...],
        params: dict[str, Any],
    ) -> FmpCallResult:
        if not self._api_key:
            raise FmpClientError("missing_api_key", "FMP_API_KEY is not configured")

        errors: list[str] = []
        for endpoint in candidates:
            try:
                data = await self._request_json(endpoint=endpoint, params=params)
                return FmpCallResult(data=data, endpoint=endpoint)
            except FmpClientError as exc:
                errors.append(f"{endpoint}:{exc.code}")
                if exc.code in {"missing_api_key", "unauthorized"}:
                    raise
                continue

        joined = ", ".join(errors) if errors else "unknown_error"
        raise FmpClientError("all_endpoints_failed", f"all endpoint attempts failed ({joined})")

    async def _request_json(self, *, endpoint: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        full_params = {**params, "apikey": self._api_key}
        url = self._build_url(endpoint)
        for attempt in range(1, self._max_retries + 1):
            try:
                response = await self._get_client().get(url, params=full_params)
                if response.status_code == 401:
                    raise FmpClientError("unauthorized", "FMP API key is unauthorized")
                if response.status_code == 402:
                    raise FmpClientError("plan_restricted", "FMP plan does not include this endpoint")
                if response.status_code == 429:
                    wait = self._retry_after_seconds(response) or self._backoff_seconds(attempt)
                    if attempt < self._max_retries:
                        await asyncio.sleep(wait)
                        continue
                    raise FmpClientError("rate_limited", "FMP rate limit exceeded")
                if response.status_code >= 500:
                    if attempt < self._max_retries:
                        await asyncio.sleep(self._backoff_seconds(attempt))
                        continue
                    raise FmpClientError("upstream_error", f"upstream status {response.status_code}")
                if response.status_code >= 400:
                    raise FmpClientError("upstream_error", f"upstream status {response.status_code}")
                try:
                    payload = response.json()
                except json.JSONDecodeError as exc:
                    raise FmpClientError("decode_error", f"non-json response from {endpoint}") from exc
                if isinstance(payload, list):
                    return [row for row in payload if isinstance(row, dict)]
                if isinstance(payload, dict):
                    maybe_rows = payload.get("data")
                    if isinstance(maybe_rows, list):
                        return [row for row in maybe_rows if isinstance(row, dict)]
                raise FmpClientError("schema_error", f"unexpected payload shape from {endpoint}")
            except httpx.TimeoutException as exc:
                if attempt < self._max_retries:
                    await asyncio.sleep(self._backoff_seconds(attempt))
                    continue
                raise FmpClientError("timeout", f"request timed out for {endpoint}") from exc
            except httpx.HTTPError as exc:
                if attempt < self._max_retries:
                    await asyncio.sleep(self._backoff_seconds(attempt))
                    continue
                raise FmpClientError("http_error", f"http client error for {endpoint}") from exc
        raise FmpClientError("upstream_error", f"unreachable request failure for {endpoint}")

    def _build_url(self, endpoint: str) -> str:
        raw_endpoint = endpoint.strip()
        if raw_endpoint.startswith("http://") or raw_endpoint.startswith("https://"):
            return raw_endpoint

        base = self._base_url
        normalized_endpoint = raw_endpoint if raw_endpoint.startswith("/") else f"/{raw_endpoint}"

        # Allow base URL forms like ".../stable/" or ".../api/v3/" without double-prefixing.
        if base.endswith("/stable") and normalized_endpoint.startswith("/stable/"):
            normalized_endpoint = normalized_endpoint[len("/stable") :]
        if base.endswith("/api/v3") and normalized_endpoint.startswith("/api/v3/"):
            normalized_endpoint = normalized_endpoint[len("/api/v3") :]

        # If base is scoped (e.g. ".../stable"), absolute API-family endpoints should use origin.
        if normalized_endpoint.startswith(("/api/v3/", "/api/v4/", "/stable/")):
            return f"{self._base_origin}{normalized_endpoint}"

        return f"{base}{normalized_endpoint}"

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self._timeout_seconds,
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            )
        return self._client

    def _backoff_seconds(self, attempt: int) -> float:
        return self._base_backoff_seconds * (2 ** max(0, attempt - 1))

    @staticmethod
    def _retry_after_seconds(response: httpx.Response) -> float | None:
        value = response.headers.get("Retry-After")
        if value is None:
            return None
        try:
            parsed = float(value)
        except ValueError:
            return None
        return parsed if parsed > 0 else None

    @staticmethod
    def _normalize_sdk_rows(payload: Any, *, sdk_method: str) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [row for row in payload if isinstance(row, dict)]
        if isinstance(payload, dict):
            # fmpsdk returns {"Error Message": "..."} for legacy endpoint failures.
            if "Error Message" in payload:
                raise FmpClientError("sdk_legacy_endpoint", f"{sdk_method} unavailable for current plan")
            data_rows = payload.get("data")
            if isinstance(data_rows, list):
                return [row for row in data_rows if isinstance(row, dict)]
        raise FmpClientError("sdk_schema_error", f"unexpected payload shape from {sdk_method}")
