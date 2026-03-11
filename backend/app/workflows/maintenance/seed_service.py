from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import Select, and_, desc, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.workflow.base_workflow import BaseWorkflowRunner
from app.models.workflow.catalog_seed_run import CatalogSeedRun
from app.models.workflow.stock_catalog import StockCatalog
from app.providers.fmp_client import FmpClient, FmpClientError

DEFAULT_SEED_TARGET_COUNT = 100
DEFAULT_MIN_MARKET_CAP = 10_000_000_000
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
        target_catalog_size: int = DEFAULT_SEED_TARGET_COUNT,
        min_market_cap: int = DEFAULT_MIN_MARKET_CAP,
    ) -> None:
        self._fmp = fmp_client
        self._session_factory = session_factory
        self._target_catalog_size = max(1, target_catalog_size)
        self._min_market_cap = max(0, min_market_cap)
        self._tasks: set[asyncio.Task[None]] = set()

    async def start_top_us_market_cap_seed(self) -> str:
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
                    scope="top_us_market_cap",
                    status="running",
                    endpoint_strategy="hybrid_best_available",
                    request_params={
                        "country": "US",
                        "isActivelyTrading": True,
                        "isEtf": False,
                        "isFund": False,
                        "marketCapMoreThan": self._min_market_cap,
                        "limit": 5000,
                    },
                    expected_count=self._target_catalog_size,
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

    async def list_catalog_stocks(
        self,
        *,
        query: str | None = None,
        is_active: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[StockCatalog], int]:
        normalized_limit = max(1, min(limit, 500))
        normalized_offset = max(0, offset)
        filters = []
        if is_active is not None:
            filters.append(StockCatalog.is_active == is_active)
        if query:
            normalized_query = query.strip().upper()
            if normalized_query:
                like_pattern = f"%{normalized_query}%"
                filters.append(
                    or_(
                        StockCatalog.symbol.ilike(like_pattern),
                        StockCatalog.name_display.ilike(like_pattern),
                    )
                )

        async with self._session_factory() as db:
            stmt = select(StockCatalog)
            count_stmt = select(func.count()).select_from(StockCatalog)
            if filters:
                predicate = and_(*filters)
                stmt = stmt.where(predicate)
                count_stmt = count_stmt.where(predicate)
            stmt = (
                stmt.order_by(
                    StockCatalog.is_active.desc(),
                    StockCatalog.selection_rank.is_(None),
                    StockCatalog.selection_rank.asc(),
                    desc(StockCatalog.market_cap),
                    StockCatalog.symbol.asc(),
                )
                .limit(normalized_limit)
                .offset(normalized_offset)
            )
            rows = await db.execute(stmt)
            count_result = await db.execute(count_stmt)
            total = int(count_result.scalar_one() or 0)
            return list(rows.scalars().all()), total

    async def _execute_seed(self, run_id: str) -> None:
        try:
            await self._heartbeat(run_id)
            directory_result = await self._fmp.fetch_stock_directory()
            screener_result = await self._fmp.fetch_company_screener(
                country="US",
                is_actively_trading=True,
                is_etf=False,
                is_fund=False,
                market_cap_more_than=self._min_market_cap,
                limit=5000,
            )
            selected, screener_by_symbol = self._select_top_by_market_cap(
                directory_rows=directory_result.data,
                screener_rows=screener_result.data,
            )
            if len(selected) != self._target_catalog_size:
                raise FmpClientError(
                    "insufficient_universe",
                    f"selected {len(selected)} symbols, expected {self._target_catalog_size}",
                )

            await self._heartbeat(run_id)
            inserted_count, updated_count = await self._upsert_catalog(
                run_id=run_id,
                selected=selected,
                screener_by_symbol=screener_by_symbol,
            )
            await self._heartbeat(run_id)
            await self._mark_run_succeeded(
                run_id=run_id,
                selected_count=len(selected),
                inserted_count=inserted_count,
                updated_count=updated_count,
                profile_coverage=1.0,
                endpoint_usage={
                    "directory": directory_result.endpoint,
                    "screener": screener_result.endpoint,
                },
            )
        except FmpClientError as exc:
            await self._mark_run_failed(run_id=run_id, error_code=exc.code, error_message=str(exc))
        except Exception as exc:  # pragma: no cover - safety net for background task
            await self._mark_run_failed(run_id=run_id, error_code="unhandled_error", error_message=str(exc))

    def _select_top_by_market_cap(
        self,
        *,
        directory_rows: list[dict[str, Any]],
        screener_rows: list[dict[str, Any]],
    ) -> tuple[list[SelectedSymbol], dict[str, dict[str, Any]]]:
        directory_symbols = {
            self._normalize_symbol(row.get("symbol")): row
            for row in directory_rows
            if self._is_directory_candidate(row)
        }

        dedup_market_cap: dict[str, int] = {}
        screener_by_symbol: dict[str, dict[str, Any]] = {}
        for row in screener_rows:
            symbol = self._normalize_symbol(row.get("symbol"))
            if not symbol or symbol not in directory_symbols:
                continue
            market_cap = self._as_positive_int(row.get("marketCap"))
            if market_cap is None:
                continue
            if market_cap < self._min_market_cap:
                continue
            current = dedup_market_cap.get(symbol, 0)
            if market_cap > current:
                dedup_market_cap[symbol] = market_cap
                screener_by_symbol[symbol] = row

        ordered = sorted(dedup_market_cap.items(), key=lambda item: (-item[1], item[0]))
        top = ordered[: self._target_catalog_size]
        selected = [
            SelectedSymbol(
                symbol=symbol,
                market_cap=market_cap,
                selection_rank=index + 1,
            )
            for index, (symbol, market_cap) in enumerate(top)
        ]
        selected_symbols = {item.symbol for item in selected}
        selected_screener_rows = {
            symbol: row for symbol, row in screener_by_symbol.items() if symbol in selected_symbols
        }
        return selected, selected_screener_rows

    async def _upsert_catalog(
        self,
        *,
        run_id: str,
        selected: list[SelectedSymbol],
        screener_by_symbol: dict[str, dict[str, Any]],
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
                screener = screener_by_symbol.get(item.symbol, {})
                name_display = (
                    self._pick_text(screener, ("companyName", "name")) or item.symbol
                )
                values = {
                    "symbol": item.symbol,
                    "name_display": name_display,
                    "name_normalized": self._normalize_name(name_display),
                    "exchange": self._pick_text(screener, ("exchange", "exchangeShortName")),
                    "exchange_short_name": self._pick_text(
                        screener, ("exchangeShortName", "exchange")
                    ),
                    "country": self._pick_text(screener, ("country",)),
                    "sector": self._pick_text(screener, ("sector",)),
                    "industry": self._pick_text(screener, ("industry",)),
                    "market_cap": self._as_positive_int(screener.get("marketCap")) or item.market_cap,
                    "is_active": self._as_bool(screener.get("isActivelyTrading"), default=True),
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
