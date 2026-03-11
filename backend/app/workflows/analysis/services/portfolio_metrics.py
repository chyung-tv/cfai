from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow.analysis_candidate_card import AnalysisCandidateCard
from app.models.workflow.stock_catalog import StockCatalog
from app.workflows.analysis.projections.store import (
    portfolio_impact_signal_score,
    quality_score_value,
    valuation_signal_score,
)
from app.workflows.analysis.services.scoring import expected_return_range


def default_portfolio_metrics() -> dict[str, Any]:
    return {
        "portfolioRiskScore": 50,
        "expectedReturnRange": {"lowPct": 0.0, "highPct": 0.0},
        "sectorConcentrationWarning": None,
    }


async def calculate_portfolio_metrics(
    db: AsyncSession,
    *,
    positions: list[tuple[str, float]],
) -> dict[str, Any]:
    total_weight = sum(weight for _, weight in positions)
    if not positions or total_weight <= 0:
        return default_portfolio_metrics()

    symbols = sorted({symbol for symbol, _ in positions})
    result = await db.execute(
        select(AnalysisCandidateCard.symbol, AnalysisCandidateCard, StockCatalog.sector)
        .outerjoin(StockCatalog, StockCatalog.id == AnalysisCandidateCard.catalog_id)
        .where(AnalysisCandidateCard.symbol.in_(symbols))
    )
    rows = result.all()
    card_by_symbol = {row[0]: (row[1], row[2]) for row in rows}

    weighted_risk = 0.0
    weighted_low = 0.0
    weighted_high = 0.0
    sector_weights: dict[str, float] = {}

    for symbol, weight in positions:
        normalized_weight = weight / total_weight
        card_tuple = card_by_symbol.get(symbol)
        if card_tuple is None:
            risk = 0.5
            expected_return = {"lowPct": -1.0, "highPct": 7.0}
            sector = "Unknown"
        else:
            card, sector_value = card_tuple
            quality_component = quality_score_value(card.quality_score)
            valuation_component = valuation_signal_score(card.valuation_signal)
            portfolio_impact_component = portfolio_impact_signal_score(card.portfolio_impact_signal)
            risk = max(0.0, min(1.0, 1.0 - portfolio_impact_component))
            expected_return = expected_return_range(
                quality=quality_component,
                valuation=valuation_component,
                portfolio_impact=portfolio_impact_component,
            )
            sector = sector_value.strip() if isinstance(sector_value, str) and sector_value.strip() else "Unknown"

        weighted_risk += normalized_weight * risk
        weighted_low += normalized_weight * float(expected_return["lowPct"])
        weighted_high += normalized_weight * float(expected_return["highPct"])
        sector_weights[sector] = sector_weights.get(sector, 0.0) + normalized_weight

    top_sector = "Unknown"
    top_weight = 0.0
    for sector, sector_weight in sector_weights.items():
        if sector_weight > top_weight:
            top_sector = sector
            top_weight = sector_weight

    warning = None
    if top_weight >= 0.4:
        warning = f"{top_sector} concentration is high ({round(top_weight * 100)}%)."

    return {
        "portfolioRiskScore": int(round(weighted_risk * 100)),
        "expectedReturnRange": {
            "lowPct": round(weighted_low, 1),
            "highPct": round(weighted_high, 1),
        },
        "sectorConcentrationWarning": warning,
    }

