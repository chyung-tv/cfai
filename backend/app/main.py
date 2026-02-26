from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI(title="CFAI Backend", version="0.1.0")


class TriggerBody(BaseModel):
    symbol: str


queries: list[dict[str, Any]] = []
analysis_results: dict[str, dict[str, Any]] = {}
stream_events: dict[str, dict[str, Any]] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_mock_analysis(symbol: str, trace_id: str) -> dict[str, Any]:
    return {
        "id": trace_id,
        "symbol": symbol,
        "price": 100.0,
        "score": 0,
        "tier": "Tier 2",
        "moat": "Narrow",
        "valuationStatus": "Fair",
        "thesis": {
            "executiveSummary": f"{symbol} baseline placeholder analysis.",
            "businessProfile": {
                "essence": "Migration placeholder.",
                "moat": "Migration placeholder.",
            },
            "industryProfile": {
                "growthProjections": 0.08,
                "trends": "Migration placeholder.",
                "competition": "Migration placeholder.",
            },
            "porter": {
                "threatOfEntrants": "Medium",
                "bargainingPowerSuppliers": "Medium",
                "bargainingPowerBuyers": "Medium",
                "threatOfSubstitutes": "Medium",
                "competitiveRivalry": "Medium",
            },
            "drivers": {
                "externalTailwinds": "Migration placeholder.",
                "externalHeadwinds": "Migration placeholder.",
                "internalCatalysts": "Migration placeholder.",
                "internalDrags": "Migration placeholder.",
            },
            "managementProfile": {
                "leadership": "Migration placeholder.",
                "compensationAlignment": "Migration placeholder.",
            },
            "recentDevelopments": "Migration placeholder.",
        },
        "dcf": {
            "intrinsicValuePerShare": 100.0,
            "impliedMargin": 0.1,
            "usedDiscountRate": 0.09,
            "sumPvFcf": 0,
            "terminalValue": 0,
            "presentTerminalValue": 0,
            "enterpriseValue": 0,
            "equityValue": 0,
            "projections": [],
            "upsideDownside": 0,
            "sensitivity": {
                "terminalGrowthRates": [0.02, 0.025, 0.03],
                "discountRates": [0.08, 0.09, 0.1],
                "values": [[98, 100, 102], [96, 100, 104], [94, 100, 106]],
            },
            "scenarios": [
                {
                    "discountRate": 0.09,
                    "impliedGrowth": 0.08,
                    "feasibility": "MEDIUM",
                    "gapAnalysis": "Migration placeholder scenario.",
                }
            ],
            "independentPrediction": {
                "predictedCagr": 0.08,
                "confidence": 0.5,
            },
        },
        "financials": {
            "revenue": 0,
            "netIncome": 0,
            "fcf": 0,
            "netDebt": 0,
        },
        "rating": {
            "tier": {"classification": "tier2"},
            "economicMoat": {
                "primaryMoat": "narrow",
                "reason": "Migration placeholder.",
            },
            "marketStructure": {"structure": "competitive"},
            "portfolioFunction": {
                "primaryFunction": "core",
                "riskProfile": "moderate",
            },
            "action": {
                "recommendation": "hold",
                "targetAllocation": 0,
                "reason": "Migration placeholder.",
            },
        },
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/auth/me")
def auth_me() -> dict[str, Any]:
    return {
        "authenticated": False,
        "user": None,
        "canTriggerAnalysis": True,
    }


@app.get("/auth/oauth/google/start")
def auth_oauth_google_start() -> dict[str, str]:
    return {"message": "OAuth start endpoint placeholder for backend authority"}


@app.get("/auth/oauth/google/callback")
def auth_oauth_google_callback() -> dict[str, str]:
    return {"message": "OAuth callback endpoint placeholder for backend authority"}


@app.post("/auth/logout")
def auth_logout() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analysis/trigger")
def trigger_analysis(
    body: TriggerBody,
    force: bool = Query(default=False),
) -> dict[str, str]:
    symbol = body.symbol.strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol is required")

    trace_id = str(uuid4())
    created_at = _now_iso()

    queries.append(
        {
            "id": str(uuid4()),
            "symbol": symbol,
            "status": "processing",
            "traceId": trace_id,
            "createdAt": created_at,
            "analysisResult": None,
        }
    )
    stream_events[trace_id] = {
        "id": trace_id,
        "symbol": symbol,
        "status": "processing",
        "message": "Analysis queued",
        "updatedAt": created_at,
    }

    if force:
        stream_events[trace_id]["message"] = "Force refresh requested"

    analysis_results[symbol] = _build_mock_analysis(symbol, trace_id)
    stream_events[trace_id]["status"] = "completed"
    stream_events[trace_id]["message"] = "Analysis completed"

    for item in queries:
        if item["traceId"] == trace_id:
            item["status"] = "completed"
            item["analysisResult"] = analysis_results[symbol]

    return {"status": "processing", "traceId": trace_id}


@app.get("/analysis/events")
def get_analysis_events(traceId: str | None = None) -> dict[str, Any]:
    if traceId:
        event = stream_events.get(traceId)
        return {"events": [event] if event else []}
    return {"events": list(stream_events.values())}


@app.get("/analysis/latest")
def get_latest_analysis(symbol: str) -> dict[str, Any] | None:
    return analysis_results.get(symbol.strip().upper())


@app.get("/analysis/history")
def get_analysis_history() -> list[dict[str, Any]]:
    return queries


@app.get("/analysis/query/{query_id}/sync")
def sync_query(query_id: str) -> dict[str, Any]:
    for item in queries:
        if item["id"] == query_id:
            if item["status"] == "processing":
                event = stream_events.get(item["traceId"])
                if event and event.get("status") == "completed":
                    item["status"] = "completed"
            return {"status": item["status"], "analysisResultId": None}
    raise HTTPException(status_code=404, detail="query not found")


@app.post("/analysis/query/{query_id}/mark-failed")
def mark_query_failed(query_id: str) -> dict[str, str]:
    for item in queries:
        if item["id"] == query_id:
            item["status"] = "failed"
            return {"status": "failed"}
    raise HTTPException(status_code=404, detail="query not found")
