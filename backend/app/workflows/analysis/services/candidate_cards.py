from __future__ import annotations

from typing import Any, Literal

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow.analysis_candidate_card import AnalysisCandidateCard
from app.models.workflow.stock_catalog import StockCatalog
from app.workflows.analysis.projections.store import (
    portfolio_impact_signal_score,
    quality_score_value,
    recent_change_signal_score,
    valuation_signal_score,
)
from app.workflows.analysis.services.scoring import (
    expected_return_range,
    is_fresh_from_timestamps,
)


async def list_candidate_cards(
    db: AsyncSession,
    *,
    sort_by: Literal["blended", "quality", "portfolio_impact", "valuation_recent"],
    quality_weight: float,
    portfolio_impact_weight: float,
    valuation_recent_weight: float,
    limit: int,
) -> dict[str, Any]:
    result = await db.execute(
        select(AnalysisCandidateCard, StockCatalog.name_display, StockCatalog.sector)
        .outerjoin(StockCatalog, StockCatalog.id == AnalysisCandidateCard.catalog_id)
        .order_by(desc(AnalysisCandidateCard.updated_at))
        .limit(500)
    )
    rows = result.all()
    total_weight = quality_weight + portfolio_impact_weight + valuation_recent_weight
    if total_weight <= 0:
        quality_weight = 0.4
        portfolio_impact_weight = 0.3
        valuation_recent_weight = 0.3
        total_weight = 1.0

    def _build_card(row: Any) -> dict[str, Any]:
        card, name_display, sector = row
        quality_component = quality_score_value(card.quality_score)
        valuation_component = valuation_signal_score(card.valuation_signal)
        recent_change_component = recent_change_signal_score(card.recent_change_signal)
        portfolio_impact_component = portfolio_impact_signal_score(card.portfolio_impact_signal)
        valuation_recent_component = round(
            (valuation_component + recent_change_component) / 2.0,
            4,
        )
        blended_score = round(
            (
                (quality_component * quality_weight)
                + (portfolio_impact_component * portfolio_impact_weight)
                + (valuation_recent_component * valuation_recent_weight)
            )
            / total_weight,
            4,
        )
        expected_return = expected_return_range(
            quality=quality_component,
            valuation=valuation_component,
            portfolio_impact=portfolio_impact_component,
        )
        return {
            "symbol": card.symbol,
            "name": name_display,
            "sector": sector,
            "qualityScore": card.quality_score,
            "valuationSignal": card.valuation_signal,
            "recentChangeSignal": card.recent_change_signal,
            "portfolioImpactSignal": card.portfolio_impact_signal,
            "freshnessUpdatedAt": card.freshness_updated_at.isoformat() if card.freshness_updated_at else None,
            "freshnessExpiresAt": card.freshness_expires_at.isoformat() if card.freshness_expires_at else None,
            "isFresh": is_fresh_from_timestamps(
                freshness_updated_at=card.freshness_updated_at,
                freshness_expires_at=card.freshness_expires_at,
            ),
            "scores": {
                "quality": quality_component,
                "valuation": valuation_component,
                "recentChange": recent_change_component,
                "valuationRecent": valuation_recent_component,
                "portfolioImpact": portfolio_impact_component,
                "blended": blended_score,
                "portfolioRisk": round(1.0 - portfolio_impact_component, 4),
            },
            "expectedReturnRange": expected_return,
            "payload": card.card_payload,
        }

    cards = [_build_card(row) for row in rows]

    def _sort_score(card: dict[str, Any]) -> float:
        scores = card.get("scores")
        if not isinstance(scores, dict):
            return 0.0
        if sort_by == "quality":
            return float(scores.get("quality") or 0.0)
        if sort_by == "portfolio_impact":
            return float(scores.get("portfolioImpact") or 0.0)
        if sort_by == "valuation_recent":
            return float(scores.get("valuationRecent") or 0.0)
        return float(scores.get("blended") or 0.0)

    cards.sort(key=lambda item: (-_sort_score(item), item["symbol"]))
    limited_cards = cards[:limit]
    return {
        "sortBy": sort_by,
        "weights": {
            "quality": quality_weight,
            "portfolioImpact": portfolio_impact_weight,
            "valuationRecent": valuation_recent_weight,
        },
        "cards": limited_cards,
    }

