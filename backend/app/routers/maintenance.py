from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.workflows.maintenance.seed_service import CatalogSeedService


def create_maintenance_router(seed_service: CatalogSeedService) -> APIRouter:
    router = APIRouter(prefix="/api/v1/admin/maintenance", tags=["maintenance"])

    async def _trigger_seed() -> dict[str, str]:
        run_id = await seed_service.start_top_us_market_cap_seed()
        return {"status": "processing", "runId": run_id}

    @router.post("/catalog/seed/top-us-market-cap")
    async def trigger_top_us_market_cap_seed() -> dict[str, str]:
        return await _trigger_seed()

    @router.get("/catalog/seed-runs/{run_id}")
    async def get_seed_run(
        run_id: str,
    ) -> dict[str, Any]:
        run = await seed_service.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="seed run not found")
        return {
            "id": run.id,
            "scope": run.scope,
            "status": run.status,
            "endpointStrategy": run.endpoint_strategy,
            "requestParams": run.request_params,
            "endpointUsage": run.endpoint_usage,
            "expectedCount": run.expected_count,
            "selectedCount": run.selected_count,
            "insertedCount": run.inserted_count,
            "updatedCount": run.updated_count,
            "profileCoverage": run.profile_coverage,
            "errorCode": run.error_code,
            "errorMessage": run.error_message,
            "workerId": run.worker_id,
            "heartbeatAt": run.heartbeat_at.isoformat() if run.heartbeat_at else None,
            "attemptCount": run.attempt_count,
            "startedAt": run.started_at.isoformat(),
            "finishedAt": run.finished_at.isoformat() if run.finished_at else None,
            "createdAt": run.created_at.isoformat(),
            "updatedAt": run.updated_at.isoformat(),
        }

    @router.get("/catalog/seed-runs")
    async def list_seed_runs() -> dict[str, list[dict[str, Any]]]:
        rows = await seed_service.list_runs()
        return {
            "runs": [
                {
                    "id": run.id,
                    "scope": run.scope,
                    "status": run.status,
                    "expectedCount": run.expected_count,
                    "selectedCount": run.selected_count,
                    "insertedCount": run.inserted_count,
                    "updatedCount": run.updated_count,
                    "profileCoverage": run.profile_coverage,
                    "errorCode": run.error_code,
                    "workerId": run.worker_id,
                    "heartbeatAt": run.heartbeat_at.isoformat() if run.heartbeat_at else None,
                    "startedAt": run.started_at.isoformat(),
                    "finishedAt": run.finished_at.isoformat() if run.finished_at else None,
                }
                for run in rows
            ]
        }

    @router.get("/catalog/stocks")
    async def list_catalog_stocks(
        query: str | None = Query(default=None, max_length=100),
        is_active: bool | None = Query(default=None),
        limit: int = Query(default=100, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
    ) -> dict[str, Any]:
        rows, total = await seed_service.list_catalog_stocks(
            query=query,
            is_active=is_active,
            limit=limit,
            offset=offset,
        )
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "stocks": [
                {
                    "symbol": row.symbol,
                    "nameDisplay": row.name_display,
                    "sector": row.sector,
                    "marketCap": row.market_cap,
                    "isActive": row.is_active,
                    "selectionRank": row.selection_rank,
                    "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
                }
                for row in rows
            ],
        }

    return router
