from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import Select, desc, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.workflow.base_workflow import BaseWorkflowRunner
from app.models.workflow.catalog_seed_run import CatalogSeedRun
from app.models.workflow.stock_catalog import StockCatalog
from app.providers.fmp_client import FmpClient, FmpClientError

TARGET_CATALOG_SIZE = 500
PROFILE_COVERAGE_THRESHOLD = 0.90
DEFAULT_PROFILE_CONCURRENCY = 10
STALE_RUN_TIMEOUT_SECONDS = 60 * 15


@dataclass(frozen=True)
class SelectedSymbol:
    symbol: str
    market_cap: int
    selection_rank: int


class CatalogSeedService(BaseWorkflowRunner):
    def __init__(
        self,
        *,
        fmp_client: FmpClient,
        session_factory: async_sessionmaker[AsyncSession],
        profile_concurrency: int = DEFAULT_PROFILE_CONCURRENCY,
    ) -> None:
        self._fmp = fmp_client
        self._session_factory = session_factory
        self._profile_concurrency = profile_concurrency
        self._tasks: set[asyncio.Task[None]] = set()

    async def start_top500_us_seed(self) -> str:
        async with self._session_factory() as db:
            await self._recover_stale_runs(db)
            existing_running = await db.execute(
                select(CatalogSeedRun)
                .where(CatalogSeedRun.status == "running")
                .order_by(desc(CatalogSeedRun.started_at))
                .limit(1)
            )
            running = existing_running.scalar_one_or_none()
            if running is not None:
                return running.id

            run_id = str(uuid4())
            db.add(
                CatalogSeedRun(
                    id=run_id,
                    scope="top500_us_market_cap",
                    status="running",
                    endpoint_strategy="hybrid_best_available",
                    request_params={
                        "country": "US",
                        "isActivelyTrading": True,
                        "isEtf": False,
                        "isFund": False,
                        "limit": 5000,
                    },
                    expected_count=TARGET_CATALOG_SIZE,
                    worker_id="seed-service-local",
                    heartbeat_at=datetime.now(UTC),
                )
            )
            await db.commit()

        task = asyncio.create_task(self._execute_seed(run_id))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return run_id

    async def _recover_stale_runs(self, db: AsyncSession) -> None:
        threshold = datetime.now(UTC).timestamp() - STALE_RUN_TIMEOUT_SECONDS
        result = await db.execute(select(CatalogSeedRun).where(CatalogSeedRun.status == "running"))
        stale_runs: list[CatalogSeedRun] = []
        for run in result.scalars().all():
            heartbeat = run.heartbeat_at or run.updated_at
            if heartbeat is None:
                continue
            if heartbeat.timestamp() < threshold:
                stale_runs.append(run)
        for run in stale_runs:
            run.status = "failed"
            run.error_code = "stale_run_recovered"
            run.error_message = "Recovered stale running seed run"
            run.finished_at = datetime.now(UTC)
        if stale_runs:
            await db.commit()

    async def list_runs(self, *, limit: int = 20) -> list[CatalogSeedRun]:
        async with self._session_factory() as db:
            stmt: Select[tuple[CatalogSeedRun]] = (
                select(CatalogSeedRun).order_by(desc(CatalogSeedRun.started_at)).limit(limit)
            )
            result = await db.execute(stmt)
            return list(result.scalars().all())

    async def get_run(self, run_id: str) -> CatalogSeedRun | None:
        async with self._session_factory() as db:
            result = await db.execute(select(CatalogSeedRun).where(CatalogSeedRun.id == run_id))
            return result.scalar_one_or_none()

    async def _execute_seed(self, run_id: str) -> None:
        try:
            await self._heartbeat(run_id)
            directory_result = await self._fmp.fetch_stock_directory()
            screener_result = await self._fmp.fetch_company_screener(
                country="US",
                is_actively_trading=True,
                is_etf=False,
                is_fund=False,
                limit=5000,
            )
            selected = self._select_top500(
                directory_rows=directory_result.data,
                screener_rows=screener_result.data,
            )
            if len(selected) != TARGET_CATALOG_SIZE:
                raise FmpClientError(
                    "insufficient_universe",
                    f"selected {len(selected)} symbols, expected {TARGET_CATALOG_SIZE}",
                )

            profiles, profile_endpoint = await self._fetch_profiles(selected)
            await self._heartbeat(run_id)
            profile_coverage = len(profiles) / TARGET_CATALOG_SIZE
            if profile_coverage < PROFILE_COVERAGE_THRESHOLD:
                raise FmpClientError(
                    "profile_coverage_below_threshold",
                    f"profile coverage {profile_coverage:.2f} below {PROFILE_COVERAGE_THRESHOLD:.2f}",
                )

            inserted_count, updated_count = await self._upsert_catalog(
                run_id=run_id,
                selected=selected,
                profiles_by_symbol=profiles,
            )
            await self._heartbeat(run_id)
            await self._mark_run_succeeded(
                run_id=run_id,
                selected_count=len(selected),
                inserted_count=inserted_count,
                updated_count=updated_count,
                profile_coverage=profile_coverage,
                endpoint_usage={
                    "directory": directory_result.endpoint,
                    "screener": screener_result.endpoint,
                    "profile": profile_endpoint,
                },
            )
        except FmpClientError as exc:
            await self._mark_run_failed(run_id=run_id, error_code=exc.code, error_message=str(exc))
        except Exception as exc:  # pragma: no cover - safety net for background task
            await self._mark_run_failed(run_id=run_id, error_code="unhandled_error", error_message=str(exc))

    def _select_top500(
        self,
        *,
        directory_rows: list[dict[str, Any]],
        screener_rows: list[dict[str, Any]],
    ) -> list[SelectedSymbol]:
        directory_symbols = {
            self._normalize_symbol(row.get("symbol")): row
            for row in directory_rows
            if self._is_directory_candidate(row)
        }

        screened_candidates: list[tuple[str, int]] = []
        for row in screener_rows:
            symbol = self._normalize_symbol(row.get("symbol"))
            if not symbol or symbol not in directory_symbols:
                continue
            market_cap = self._as_positive_int(row.get("marketCap"))
            if market_cap is None:
                continue
            screened_candidates.append((symbol, market_cap))

        dedup: dict[str, int] = {}
        for symbol, market_cap in screened_candidates:
            current = dedup.get(symbol, 0)
            if market_cap > current:
                dedup[symbol] = market_cap

        ordered = sorted(dedup.items(), key=lambda item: (-item[1], item[0]))
        top = ordered[:TARGET_CATALOG_SIZE]
        return [
            SelectedSymbol(
                symbol=symbol,
                market_cap=market_cap,
                selection_rank=index + 1,
            )
            for index, (symbol, market_cap) in enumerate(top)
        ]

    async def _fetch_profiles(
        self,
        selected: list[SelectedSymbol],
    ) -> tuple[dict[str, dict[str, Any]], str]:
        semaphore = asyncio.Semaphore(self._profile_concurrency)
        profiles: dict[str, dict[str, Any]] = {}
        endpoint_usage: dict[str, int] = {}

        async def _pull(item: SelectedSymbol) -> None:
            async with semaphore:
                try:
                    result = await self._fmp.fetch_profile_by_symbol(item.symbol)
                except FmpClientError:
                    return
                endpoint_usage[result.endpoint] = endpoint_usage.get(result.endpoint, 0) + 1
                if not result.data:
                    return
                profile = result.data[0]
                if not isinstance(profile, dict):
                    return
                profiles[item.symbol] = profile

        await asyncio.gather(*[_pull(item) for item in selected])
        endpoint = max(endpoint_usage, key=endpoint_usage.get) if endpoint_usage else "unknown"
        return profiles, endpoint

    async def _upsert_catalog(
        self,
        *,
        run_id: str,
        selected: list[SelectedSymbol],
        profiles_by_symbol: dict[str, dict[str, Any]],
    ) -> tuple[int, int]:
        async with self._session_factory() as db:
            symbols = [item.symbol for item in selected]
            existing_result = await db.execute(
                select(StockCatalog.symbol).where(StockCatalog.symbol.in_(symbols))
            )
            existing_symbols = set(existing_result.scalars().all())
            inserted_count = len(symbols) - len(existing_symbols)
            updated_count = len(existing_symbols)

            rows_to_upsert: list[dict[str, Any]] = []
            for item in selected:
                profile = profiles_by_symbol.get(item.symbol, {})
                name_display = (
                    self._pick_text(profile, ("companyName", "name")) or item.symbol
                )
                values = {
                    "symbol": item.symbol,
                    "name_display": name_display,
                    "name_normalized": self._normalize_name(name_display),
                    "exchange": self._pick_text(profile, ("exchange", "exchangeShortName")),
                    "exchange_short_name": self._pick_text(
                        profile, ("exchangeShortName", "exchange")
                    ),
                    "country": self._pick_text(profile, ("country",)),
                    "sector": self._pick_text(profile, ("sector",)),
                    "industry": self._pick_text(profile, ("industry",)),
                    "market_cap": self._as_positive_int(profile.get("mktCap"))
                    or self._as_positive_int(profile.get("marketCap"))
                    or item.market_cap,
                    "is_active": self._as_bool(profile.get("isActivelyTrading"), default=True),
                    "selection_rank": item.selection_rank,
                    "selection_method": "market_cap_desc_symbol_asc",
                    "source": "fmp",
                    "source_updated_at": datetime.now(UTC),
                    "seed_run_id": run_id,
                }
                rows_to_upsert.append(values)

            stmt = insert(StockCatalog).values(rows_to_upsert)
            update_map = {
                "name_display": stmt.excluded.name_display,
                "name_normalized": stmt.excluded.name_normalized,
                "exchange": stmt.excluded.exchange,
                "exchange_short_name": stmt.excluded.exchange_short_name,
                "country": stmt.excluded.country,
                "sector": stmt.excluded.sector,
                "industry": stmt.excluded.industry,
                "market_cap": stmt.excluded.market_cap,
                "is_active": stmt.excluded.is_active,
                "selection_rank": stmt.excluded.selection_rank,
                "selection_method": stmt.excluded.selection_method,
                "source": stmt.excluded.source,
                "source_updated_at": stmt.excluded.source_updated_at,
                "seed_run_id": stmt.excluded.seed_run_id,
                "updated_at": func.now(),
            }
            stmt = stmt.on_conflict_do_update(
                index_elements=[StockCatalog.symbol],
                set_=update_map,
            )
            await db.execute(stmt)

            await db.execute(
                StockCatalog.__table__.update()
                .where(
                    StockCatalog.source == "fmp",
                    StockCatalog.symbol.notin_(symbols),
                )
                .values(
                    is_active=False,
                    selection_rank=None,
                    updated_at=func.now(),
                )
            )

            await db.commit()
        return inserted_count, updated_count

    async def _mark_run_succeeded(
        self,
        *,
        run_id: str,
        selected_count: int,
        inserted_count: int,
        updated_count: int,
        profile_coverage: float,
        endpoint_usage: dict[str, str],
    ) -> None:
        async with self._session_factory() as db:
            result = await db.execute(select(CatalogSeedRun).where(CatalogSeedRun.id == run_id))
            run = result.scalar_one_or_none()
            if run is None:
                return
            run.status = "succeeded"
            run.selected_count = selected_count
            run.inserted_count = inserted_count
            run.updated_count = updated_count
            run.profile_coverage = profile_coverage
            run.endpoint_usage = endpoint_usage
            run.error_code = None
            run.error_message = None
            run.heartbeat_at = datetime.now(UTC)
            run.finished_at = datetime.now(UTC)
            await db.commit()

    async def _mark_run_failed(self, *, run_id: str, error_code: str, error_message: str) -> None:
        async with self._session_factory() as db:
            result = await db.execute(select(CatalogSeedRun).where(CatalogSeedRun.id == run_id))
            run = result.scalar_one_or_none()
            if run is None:
                return
            run.status = "failed"
            run.error_code = error_code
            run.error_message = error_message[:500]
            run.heartbeat_at = datetime.now(UTC)
            run.finished_at = datetime.now(UTC)
            await db.commit()

    async def _heartbeat(self, run_id: str) -> None:
        async with self._session_factory() as db:
            result = await db.execute(select(CatalogSeedRun).where(CatalogSeedRun.id == run_id))
            run = result.scalar_one_or_none()
            if run is None:
                return
            run.heartbeat_at = datetime.now(UTC)
            run.attempt_count = (run.attempt_count or 0) + 1
            await db.commit()

    @staticmethod
    def _is_directory_candidate(row: dict[str, Any]) -> bool:
        symbol = CatalogSeedService._normalize_symbol(row.get("symbol"))
        if not symbol:
            return False

        country = (row.get("country") or "").strip().upper()
        if country and country != "US":
            return False

        security_type = (row.get("type") or "").strip().lower()
        if security_type and security_type not in {"stock", "commonstock", "common stock"}:
            return False

        is_actively_trading = row.get("isActivelyTrading")
        if isinstance(is_actively_trading, bool) and not is_actively_trading:
            return False

        return True

    @staticmethod
    def _normalize_symbol(raw: Any) -> str:
        if raw is None:
            return ""
        return str(raw).strip().upper()

    @staticmethod
    def _normalize_name(raw: str) -> str:
        lowered = raw.strip().lower()
        collapsed = re.sub(r"[^a-z0-9]+", " ", lowered)
        return re.sub(r"\s+", " ", collapsed).strip()

    @staticmethod
    def _as_positive_int(raw: Any) -> int | None:
        if raw is None or raw == "":
            return None
        try:
            value = int(float(raw))
        except (TypeError, ValueError):
            return None
        return value if value > 0 else None

    @staticmethod
    def _pick_text(row: dict[str, Any], keys: tuple[str, ...]) -> str | None:
        for key in keys:
            value = row.get(key)
            if value is None:
                continue
            text = str(value).strip()
            if text:
                return text
        return None

    @staticmethod
    def _as_bool(raw: Any, *, default: bool) -> bool:
        if isinstance(raw, bool):
            return raw
        if isinstance(raw, str):
            lowered = raw.strip().lower()
            if lowered in {"true", "1", "yes"}:
                return True
            if lowered in {"false", "0", "no"}:
                return False
        return default


__all__ = ["CatalogSeedService"]
