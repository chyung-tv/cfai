from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock_catalog import StockCatalog
from app.workflow.base_node import BaseNode


class ResolveQueryNode(BaseNode):
    name = "resolve_query"

    async def run(self, context: dict) -> dict:
        symbol = str(context.get("symbol", "")).strip().upper()
        if not symbol:
            raise ValueError("symbol is required")

        db = context.get("db")
        if not isinstance(db, AsyncSession):
            raise RuntimeError("workflow db session is missing")

        result = await db.execute(
            select(StockCatalog).where(
                StockCatalog.symbol == symbol,
                StockCatalog.is_active.is_(True),
            )
        )
        catalog_row = result.scalar_one_or_none()
        if catalog_row is None:
            raise ValueError(f"symbol '{symbol}' was not found in catalog")

        context["symbol"] = catalog_row.symbol
        context["catalog_id"] = catalog_row.id
        context["catalog_name_display"] = catalog_row.name_display
        context["catalog_name_normalized"] = catalog_row.name_normalized

        return {
            "symbol": catalog_row.symbol,
            "catalogId": catalog_row.id,
            "nameDisplay": catalog_row.name_display,
        }
