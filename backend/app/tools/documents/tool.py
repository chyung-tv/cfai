from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.tools.documents.workflows.apply_patch import apply_document_patch


@dataclass(frozen=True)
class DocumentsToolDescriptor:
    name: str = "edit_document"
    description: str = "Canonical document editing tool boundary."
    enabled: bool = True


class CreateDocumentTool:
    name = "create_document"
    description = "Create a new canonical markdown document."
    enabled = True

    def __init__(self, *, session_factory: async_sessionmaker[AsyncSession], service: Any) -> None:
        self._session_factory = session_factory
        self._service = service

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        title = str(arguments.get("title") or "").strip()
        doc_key = arguments.get("doc_key")
        initial_content = str(arguments.get("initial_content") or "")
        if not title:
            return {"status": "error", "errorCode": "title_required", "message": "title is required"}
        async with self._session_factory() as db:
            doc = await self._service.create_document(
                db,
                title=title,
                doc_key=str(doc_key).strip() if isinstance(doc_key, str) and doc_key.strip() else None,
                initial_content=initial_content,
                author_type="agent",
            )
            head = await self._service.ensure_document_head(db, doc=doc)
            await db.commit()
            return {
                "status": "ok",
                "document": self._service.serialize_document(doc=doc, head=head),
            }


class EditDocumentTool:
    name = "edit_document"
    description = "Edit an existing canonical markdown document."
    enabled = True

    def __init__(self, *, session_factory: async_sessionmaker[AsyncSession], service: Any) -> None:
        self._session_factory = session_factory
        self._service = service

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        doc_key = str(arguments.get("doc_key") or "").strip()
        mode = str(arguments.get("mode") or "replace").strip().lower()
        if not doc_key:
            return {"status": "error", "errorCode": "doc_key_required", "message": "doc_key is required"}

        async with self._session_factory() as db:
            doc = await self._service.get_document(db, doc_key=doc_key)
            if doc is None:
                return {"status": "error", "errorCode": "document_not_found", "message": f"Document not found: {doc_key}"}

            if mode == "patch":
                patch = str(arguments.get("patch") or "")
                if not patch.strip():
                    return {"status": "error", "errorCode": "patch_required", "message": "patch is required for patch mode"}
                next_content = apply_document_patch(doc.content, patch, doc_key=doc.doc_key)
            else:
                next_content = str(arguments.get("content") or "")
                if not next_content.strip():
                    return {"status": "error", "errorCode": "content_required", "message": "content is required for replace mode"}

            updated = await self._service.update_working_document(
                db,
                doc_key=doc.doc_key,
                content=next_content,
                author_type="agent",
                message=f"Agent {mode} edit",
            )
            head = await self._service.ensure_document_head(db, doc=updated)
            await db.commit()
            return {"status": "ok", "document": self._service.serialize_document(doc=updated, head=head)}

