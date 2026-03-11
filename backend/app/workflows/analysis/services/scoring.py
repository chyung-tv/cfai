from __future__ import annotations

from datetime import UTC, datetime, timedelta

ANALYSIS_FRESHNESS_TTL = timedelta(days=7)


def is_fresh_from_timestamps(
    *,
    freshness_updated_at: datetime | None,
    freshness_expires_at: datetime | None,
) -> bool | None:
    now = datetime.now(UTC)
    if freshness_expires_at is not None:
        return freshness_expires_at >= now
    if freshness_updated_at is not None:
        return freshness_updated_at >= (now - ANALYSIS_FRESHNESS_TTL)
    return None


def expected_return_range(
    quality: float,
    valuation: float,
    portfolio_impact: float,
) -> dict[str, float]:
    # Heuristic v1 range, bounded for stable UX output.
    midpoint = 2.0 + (quality * 12.0) + (valuation * 8.0) - ((1.0 - portfolio_impact) * 4.0)
    low = max(-8.0, midpoint - 5.0)
    high = min(35.0, midpoint + 5.0)
    return {"lowPct": round(low, 1), "highPct": round(high, 1)}

