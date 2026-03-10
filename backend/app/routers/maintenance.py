from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.workflows.maintenance.seed_service import CatalogSeedService


def create_maintenance_router(seed_service: CatalogSeedService) -> APIRouter:
    router = APIRouter(prefix="/api/v1/admin/maintenance", tags=["maintenance"])

    @router.post("/catalog/seed/top500-us")
    async def trigger_top500_seed() -> dict[str, str]:
        run_id = await seed_service.start_top500_us_seed()
        return {"status": "processing", "runId": run_id}

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

    return router
