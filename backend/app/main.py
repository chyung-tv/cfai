from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.core.logging import configure_app_logging
from app.db.session import AsyncSessionLocal
from app.agent import AgentRuntime, DisabledPlaceholderTool, SkillRegistry, ToolRegistry
from app.copilot.api import create_copilot_router
from app.copilot.service import CopilotWorkspaceService, MemoryJobRunner, MemoryService, NotificationBroker
from app.providers.gemini.chat_client import GeminiChatClient
from app.tools.documents import CreateDocumentTool, EditDocumentTool

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
copilot_service = CopilotWorkspaceService()
tool_registry = ToolRegistry()
tool_registry.register(
    EditDocumentTool(
        session_factory=AsyncSessionLocal,
        service=copilot_service,
    )
)
tool_registry.register(
    CreateDocumentTool(
        session_factory=AsyncSessionLocal,
        service=copilot_service,
    )
)
tool_registry.register(
    DisabledPlaceholderTool(
        name="run_research",
        description="Execute deeper financial research workflow (planned).",
    )
)
chat_client = GeminiChatClient(
    vertex_api_key=settings.vertex_ai_api_key,
    vertex_project_id=settings.vertex_ai_project_id,
    vertex_location=settings.vertex_ai_location,
    use_vertex_ai=settings.google_genai_use_vertexai,
    model=settings.llm_flash_lite_model,
    enable_live_calls=settings.chat_enable_live_calls,
)
skill_registry = SkillRegistry()
memory_service = MemoryService()
notification_broker = NotificationBroker()
memory_jobs = MemoryJobRunner(
    session_factory=AsyncSessionLocal,
    memory_service=memory_service,
    broker=notification_broker,
)
agent_runtime = AgentRuntime(chat_client=chat_client, tool_registry=tool_registry)
app.include_router(
    create_copilot_router(
        copilot_service,
        agent_runtime,
        skill_registry,
        memory_service,
        memory_jobs,
        notification_broker,
    )
)


@app.on_event("startup")
async def startup_memory_jobs() -> None:
    await memory_jobs.start()


@app.on_event("shutdown")
async def shutdown_memory_jobs() -> None:
    await memory_jobs.stop()


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
