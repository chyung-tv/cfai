from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.maintenance.seed_service import CatalogSeedService
from app.providers.fmp_client import FmpClient
from app.providers.gemini_deep_research import GeminiDeepResearchClient
from app.routers.auth import router as auth_router
from app.routers.maintenance import create_maintenance_router
from app.routers.workflow import create_workflow_router
from app.workflow.orchestrator import WorkflowOrchestrator
from app.workflow.sse import SseBroker

app = FastAPI(title="CFAI Backend", version="0.1.0")
broker = SseBroker()
workflow_orchestrator = WorkflowOrchestrator(
    broker,
    GeminiDeepResearchClient(
        api_key=settings.google_api_key,
        agent=settings.deep_research_agent,
        structured_output_model=settings.structured_output_model,
        poll_interval_seconds=settings.deep_research_poll_interval_seconds,
        max_wait_seconds=settings.deep_research_max_wait_seconds,
        enable_live_calls=settings.deep_research_enable_live_calls,
    ),
)
seed_service = CatalogSeedService(
    fmp_client=FmpClient(
        api_key=settings.fmp_api_key,
        base_url=settings.fmp_base_url,
        timeout_seconds=settings.fmp_timeout_seconds,
    ),
    session_factory=AsyncSessionLocal,
)
app.include_router(auth_router)
app.include_router(create_workflow_router(workflow_orchestrator, broker))
app.include_router(create_maintenance_router(seed_service))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db")
async def health_db() -> dict[str, str]:
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"database unavailable: {exc}") from exc
