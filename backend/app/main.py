from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from app.db.session import AsyncSessionLocal
from app.routers.auth import router as auth_router
from app.routers.workflow import create_workflow_router
from app.workflow.orchestrator import WorkflowOrchestrator
from app.workflow.sse import SseBroker

app = FastAPI(title="CFAI Backend", version="0.1.0")
broker = SseBroker()
workflow_orchestrator = WorkflowOrchestrator(broker)
app.include_router(auth_router)
app.include_router(create_workflow_router(workflow_orchestrator, broker))


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
