from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.core.logging import configure_app_logging
from app.db.session import AsyncSessionLocal
from app.providers.advisor_client import AdvisorClient
from app.providers.fmp_client import FmpClient
from app.providers.gemini_deep_research import GeminiDeepResearchClient
from app.routers.maintenance import create_maintenance_router
from app.routers.workflow import create_workflow_router
from app.workflows.analysis.orchestrator import WorkflowOrchestrator
from app.workflows.analysis.sse import SseBroker
from app.workflows.maintenance.seed_service import CatalogSeedService

configure_app_logging(level=settings.app_log_level)

app = FastAPI(title="CFAI Backend", version="0.1.0")
allowed_origins = {
    settings.frontend_url.rstrip("/"),
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://0.0.0.0:3000",
    "http://localhost:3100",
    "http://127.0.0.1:3100",
    "http://0.0.0.0:3100",
}
app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(allowed_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
broker = SseBroker()
fmp_client = FmpClient(
    api_key=settings.fmp_api_key,
    base_url=settings.fmp_base_url,
    timeout_seconds=settings.fmp_timeout_seconds,
)
gemini_client = GeminiDeepResearchClient(
    vertex_api_key=settings.vertex_ai_api_key,
    vertex_project_id=settings.vertex_ai_project_id,
    vertex_location=settings.vertex_ai_location,
    use_vertex_ai=settings.google_genai_use_vertexai,
    app_env=settings.app_env,
    agent=settings.deep_research_agent,
    deep_research_dev_model=settings.deep_research_dev_model,
    deep_research_dev_grounding_enabled=settings.deep_research_dev_grounding_enabled,
    deep_research_use_endpoint_in_production=settings.deep_research_use_endpoint_in_production,
    structured_output_model=settings.structured_output_model,
    poll_interval_seconds=settings.deep_research_poll_interval_seconds,
    max_wait_seconds=settings.deep_research_max_wait_seconds,
    enable_live_calls=settings.deep_research_enable_live_calls,
)
advisor_client = AdvisorClient(gemini_client=gemini_client)
workflow_orchestrator = WorkflowOrchestrator(
    broker,
    gemini_client,
    fmp_client,
    advisor_client,
)
seed_service = CatalogSeedService(
    fmp_client=fmp_client,
    session_factory=AsyncSessionLocal,
    target_catalog_size=settings.maintenance_seed_target_count,
    min_market_cap=settings.maintenance_seed_min_market_cap,
)
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
