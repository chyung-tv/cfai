from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from statistics import median
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.workflow.base_node import BaseNode
from app.models.workflow.fmp_symbol_snapshot import FmpSymbolSnapshot
from app.providers.fmp_client import FmpClient, FmpClientError
from app.workflows.analysis.context import WorkflowContext


@dataclass(frozen=True)
class ReverseDcfBaseline:
    baseline_mode: str
    as_of_date: str | None
    revenue: float
    ebit: float
    depreciation_amortization: float
    capex_outflow: float
    change_working_capital: float
    tax_rate: float


@dataclass(frozen=True)
class MarketInputs:
    price: float
    shares_outstanding: float
    market_cap: float
    net_debt: float
    total_debt: float
    cash_equivalents: float


class ReverseDcfNode(BaseNode):
    name = "reverse_dcf"
    timeout_seconds = 60.0
    _ASSUMPTION_SET_ID = "reverse_dcf_v1_fcff_10y"
    _DISCOUNT_RATES = (0.06, 0.07, 0.08, 0.09, 0.10)
    _TERMINAL_GROWTH_RATES = (0.02, 0.025, 0.03)
    _PROJECTION_YEARS = 10
    _SNAPSHOT_TTL = timedelta(hours=24)

    def __init__(self, fmp_client: FmpClient) -> None:
        self._fmp_client = fmp_client

    async def run(self, context: WorkflowContext) -> dict:
        symbol = str(context.get("symbol", "")).strip().upper()
        if not symbol:
            raise ValueError("symbol is required")

        result = context.get("result")
        if not isinstance(result, dict):
            result = {"id": context.get("workflow_id"), "symbol": symbol}

        try:
            (
                quote_call,
                profile_call,
                quarter_income_call,
                quarter_cash_flow_call,
                quarter_balance_call,
            ) = await asyncio.gather(
                self._fetch_dataset_cached(
                    context=context,
                    symbol=symbol,
                    dataset_type="quote",
                    period=None,
                    fetcher=lambda: self._fmp_client.fetch_quote(symbol),
                ),
                self._fetch_dataset_cached(
                    context=context,
                    symbol=symbol,
                    dataset_type="profile",
                    period=None,
                    fetcher=lambda: self._fmp_client.fetch_profile_by_symbol(symbol),
                ),
                self._fetch_dataset_cached(
                    context=context,
                    symbol=symbol,
                    dataset_type="income_statement",
                    period="quarter",
                    fetcher=lambda: self._fmp_client.fetch_income_statement(
                        symbol,
                        period="quarter",
                        limit=4,
                    ),
                ),
                self._fetch_dataset_cached(
                    context=context,
                    symbol=symbol,
                    dataset_type="cash_flow_statement",
                    period="quarter",
                    fetcher=lambda: self._fmp_client.fetch_cash_flow_statement(
                        symbol,
                        period="quarter",
                        limit=4,
                    ),
                ),
                self._fetch_dataset_cached(
                    context=context,
                    symbol=symbol,
                    dataset_type="balance_sheet_statement",
                    period="quarter",
                    fetcher=lambda: self._fmp_client.fetch_balance_sheet_statement(
                        symbol,
                        period="quarter",
                        limit=1,
                    ),
                ),
            )
        except FmpClientError as exc:
            raise RuntimeError(f"reverse_dcf_fmp_{exc.code}: {exc}") from exc

        annual_income_call: list[dict[str, Any]] = []
        annual_cash_flow_call: list[dict[str, Any]] = []
        annual_balance_call: list[dict[str, Any]] = []
        if len(quarter_income_call) < 4 or len(quarter_cash_flow_call) < 4 or len(quarter_balance_call) < 1:
            try:
                annual_income_call, annual_cash_flow_call, annual_balance_call = await asyncio.gather(
                    self._fetch_dataset_cached(
                        context=context,
                        symbol=symbol,
                        dataset_type="income_statement",
                        period="annual",
                        fetcher=lambda: self._fmp_client.fetch_income_statement(symbol, limit=1),
                    ),
                    self._fetch_dataset_cached(
                        context=context,
                        symbol=symbol,
                        dataset_type="cash_flow_statement",
                        period="annual",
                        fetcher=lambda: self._fmp_client.fetch_cash_flow_statement(symbol, limit=1),
                    ),
                    self._fetch_dataset_cached(
                        context=context,
                        symbol=symbol,
                        dataset_type="balance_sheet_statement",
                        period="annual",
                        fetcher=lambda: self._fmp_client.fetch_balance_sheet_statement(symbol, limit=1),
                    ),
                )
            except FmpClientError as exc:
                raise RuntimeError(f"reverse_dcf_fmp_{exc.code}: {exc}") from exc

        quote = quote_call[0] if quote_call else {}
        profile = profile_call[0] if profile_call else {}
        market = self._extract_market_inputs(
            quote=quote,
            profile=profile,
            balance_rows=quarter_balance_call or annual_balance_call,
        )

        warnings: list[str] = []
        baseline, baseline_warnings = self._build_baseline(
            quarter_income_rows=quarter_income_call,
            quarter_cash_flow_rows=quarter_cash_flow_call,
            annual_income_rows=annual_income_call,
            annual_cash_flow_rows=annual_cash_flow_call,
        )
        warnings.extend(baseline_warnings)

        target_enterprise_value = market.market_cap + market.net_debt
        if target_enterprise_value <= 0:
            raise RuntimeError("reverse_dcf_invalid_target_enterprise_value")

        assumptions = self._build_assumptions(baseline=baseline)
        scenario_grid: list[dict[str, Any]] = []
        solved_cagrs: list[float] = []

        for discount_rate in self._DISCOUNT_RATES:
            for terminal_growth in self._TERMINAL_GROWTH_RATES:
                solved = self._solve_required_revenue_cagr(
                    target_enterprise_value=target_enterprise_value,
                    discount_rate=discount_rate,
                    terminal_growth_rate=terminal_growth,
                    assumptions=assumptions,
                )
                if solved["converged"] and solved["requiredRevenueCagrPct"] is not None:
                    solved_cagrs.append(float(solved["requiredRevenueCagrPct"]))
                scenario_grid.append(
                    {
                        "discountRatePct": round(discount_rate * 100.0, 3),
                        "terminalGrowthPct": round(terminal_growth * 100.0, 3),
                        **solved,
                    }
                )

        summary = {
            "bestCaseRevenueCagrPct": min(solved_cagrs) if solved_cagrs else None,
            "medianRevenueCagrPct": median(solved_cagrs) if solved_cagrs else None,
            "worstCaseRevenueCagrPct": max(solved_cagrs) if solved_cagrs else None,
        }

        reverse_dcf_payload = {
            "schemaVersion": "v1",
            "assumptionSetId": self._ASSUMPTION_SET_ID,
            "projectionYears": self._PROJECTION_YEARS,
            "inputs": {
                "symbol": symbol,
                "asOfDate": baseline.as_of_date,
                "price": market.price,
                "sharesOutstanding": market.shares_outstanding,
                "marketCap": market.market_cap,
                "totalDebt": market.total_debt,
                "cashAndEquivalents": market.cash_equivalents,
                "netDebt": market.net_debt,
                "targetEnterpriseValue": target_enterprise_value,
                "baselineMode": baseline.baseline_mode,
                "baselineRevenue": baseline.revenue,
                "baselineTaxRate": baseline.tax_rate,
            },
            "assumptions": {
                "ebitMargin": assumptions["ebit_margin"],
                "depreciationAmortizationMargin": assumptions["depreciation_amortization_margin"],
                "capexOutflowMargin": assumptions["capex_outflow_margin"],
                "workingCapitalChangeMargin": assumptions["working_capital_change_margin"],
                "discountRatesPct": [round(v * 100.0, 3) for v in self._DISCOUNT_RATES],
                "terminalGrowthRatesPct": [round(v * 100.0, 3) for v in self._TERMINAL_GROWTH_RATES],
            },
            "scenarioGrid": scenario_grid,
            "summary": summary,
            "solver": {
                "method": "bisection",
                "bounds": {"low": -0.9, "high": 5.0},
                "maxIterations": 120,
                "relativeEvTolerance": 1e-6,
            },
            "quality": {
                "warnings": warnings,
                "missingFields": [],
                "generatedAt": datetime.now(timezone.utc).isoformat(),
            },
        }

        result["reverseDcf"] = reverse_dcf_payload
        context["reverse_dcf"] = reverse_dcf_payload
        context["result"] = result
        return {"result": result, "reverseDcf": reverse_dcf_payload}

    async def _fetch_dataset_cached(
        self,
        *,
        context: WorkflowContext,
        symbol: str,
        dataset_type: str,
        period: str | None,
        fetcher,
    ) -> list[dict[str, Any]]:
        db = context.get("db")
        if not isinstance(db, AsyncSession):
            fetched = await fetcher()
            return fetched.data
        snapshot = await self._load_snapshot(
            db=db,
            symbol=symbol,
            dataset_type=dataset_type,
            period=period,
        )
        now = datetime.now(timezone.utc)
        if snapshot is not None and snapshot.expires_at > now:
            rows = snapshot.payload.get("rows") if isinstance(snapshot.payload, dict) else None
            if isinstance(rows, list):
                return [row for row in rows if isinstance(row, dict)]

        fetched = await fetcher()
        await self._save_snapshot(
            db=db,
            symbol=symbol,
            catalog_id=context.get("catalog_id"),
            dataset_type=dataset_type,
            period=period,
            endpoint=fetched.endpoint,
            rows=fetched.data,
            now=now,
        )
        return fetched.data

    async def _load_snapshot(
        self,
        *,
        db: AsyncSession,
        symbol: str,
        dataset_type: str,
        period: str | None,
    ) -> FmpSymbolSnapshot | None:
        result = await db.execute(
            select(FmpSymbolSnapshot)
            .where(
                FmpSymbolSnapshot.symbol == symbol,
                FmpSymbolSnapshot.dataset_type == dataset_type,
                FmpSymbolSnapshot.period == period,
            )
            .order_by(desc(FmpSymbolSnapshot.fetched_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _save_snapshot(
        self,
        *,
        db: AsyncSession,
        symbol: str,
        catalog_id: int | None,
        dataset_type: str,
        period: str | None,
        endpoint: str,
        rows: list[dict[str, Any]],
        now: datetime,
    ) -> None:
        snapshot = FmpSymbolSnapshot(
            symbol=symbol,
            catalog_id=catalog_id,
            dataset_type=dataset_type,
            period=period,
            endpoint=endpoint,
            payload={"rows": rows},
            fetched_at=now,
            expires_at=now + self._SNAPSHOT_TTL,
        )
        db.add(snapshot)
        await db.flush()

    def _build_baseline(
        self,
        *,
        quarter_income_rows: list[dict[str, Any]],
        quarter_cash_flow_rows: list[dict[str, Any]],
        annual_income_rows: list[dict[str, Any]],
        annual_cash_flow_rows: list[dict[str, Any]],
    ) -> tuple[ReverseDcfBaseline, list[str]]:
        warnings: list[str] = []
        q_income = self._sort_rows_desc(quarter_income_rows)[:4]
        q_cash_flow = self._sort_rows_desc(quarter_cash_flow_rows)[:4]
        if len(q_income) == 4 and len(q_cash_flow) == 4:
            baseline = self._baseline_from_rows(
                baseline_mode="ttm_4q",
                income_rows=q_income,
                cash_flow_rows=q_cash_flow,
            )
            return baseline, warnings

        warnings.append("ttm_4q_unavailable_fallback_to_latest_fy")
        a_income = self._sort_rows_desc(annual_income_rows)[:1]
        a_cash_flow = self._sort_rows_desc(annual_cash_flow_rows)[:1]
        if len(a_income) == 1 and len(a_cash_flow) == 1:
            baseline = self._baseline_from_rows(
                baseline_mode="latest_fy",
                income_rows=a_income,
                cash_flow_rows=a_cash_flow,
            )
            return baseline, warnings

        raise RuntimeError("reverse_dcf_baseline_unavailable")

    def _baseline_from_rows(
        self,
        *,
        baseline_mode: str,
        income_rows: list[dict[str, Any]],
        cash_flow_rows: list[dict[str, Any]],
    ) -> ReverseDcfBaseline:
        revenue = self._sum_field(income_rows, ("revenue",))
        ebit = self._sum_field(income_rows, ("operatingIncome", "ebit"))
        depreciation_amortization = self._sum_field(
            cash_flow_rows,
            ("depreciationAndAmortization", "depreciationAndAmortizationExpense", "depreciation"),
        )
        capex_raw = self._sum_field(cash_flow_rows, ("capitalExpenditure", "capitalExpenditures"))
        capex_outflow = abs(capex_raw)
        change_working_capital = self._sum_field(
            cash_flow_rows,
            ("changeInWorkingCapital", "changeWorkingCapital"),
        )
        income_before_tax = self._sum_field(income_rows, ("incomeBeforeTax", "incomeBeforeTaxExpense"))
        income_tax = self._sum_field(income_rows, ("incomeTaxExpense",))

        if revenue <= 0:
            raise RuntimeError("reverse_dcf_invalid_revenue_baseline")
        if ebit is None:
            raise RuntimeError("reverse_dcf_missing_ebit_baseline")

        tax_rate = 0.21
        if income_before_tax and income_before_tax > 0 and income_tax is not None:
            tax_rate = max(0.0, min(income_tax / income_before_tax, 0.5))

        as_of_date = self._extract_as_of_date(income_rows)
        return ReverseDcfBaseline(
            baseline_mode=baseline_mode,
            as_of_date=as_of_date,
            revenue=revenue,
            ebit=ebit,
            depreciation_amortization=depreciation_amortization,
            capex_outflow=capex_outflow,
            change_working_capital=change_working_capital,
            tax_rate=tax_rate,
        )

    def _extract_market_inputs(
        self,
        *,
        quote: dict[str, Any],
        profile: dict[str, Any],
        balance_rows: list[dict[str, Any]],
    ) -> MarketInputs:
        price = self._pick_float(quote, ("price",))
        shares_outstanding = self._pick_float(
            quote,
            ("sharesOutstanding", "shareOutstanding"),
        )
        if shares_outstanding is None:
            shares_outstanding = self._pick_float(
                profile,
                ("sharesOutstanding", "shareOutstanding"),
            )
        market_cap = self._pick_float(quote, ("marketCap",))
        if market_cap is None:
            market_cap = self._pick_float(profile, ("mktCap", "marketCap"))

        # If shares are missing but price and market cap exist, derive shares.
        if shares_outstanding is None and price is not None and market_cap is not None and price > 0:
            shares_outstanding = market_cap / price

        if market_cap is None and price is not None and shares_outstanding is not None:
            market_cap = price * shares_outstanding

        if price is None or price <= 0:
            raise RuntimeError("reverse_dcf_missing_price")
        if shares_outstanding is None or shares_outstanding <= 0:
            raise RuntimeError("reverse_dcf_missing_shares_outstanding")
        if market_cap is None or market_cap <= 0:
            raise RuntimeError("reverse_dcf_missing_market_cap")

        latest_balance = self._sort_rows_desc(balance_rows)[:1]
        balance = latest_balance[0] if latest_balance else {}
        total_debt = self._pick_float(
            balance,
            ("totalDebt",),
        )
        if total_debt is None:
            total_debt = (self._pick_float(balance, ("shortTermDebt",)) or 0.0) + (
                self._pick_float(balance, ("longTermDebt",)) or 0.0
            )
        cash_equivalents = self._pick_float(
            balance,
            (
                "cashAndShortTermInvestments",
                "cashAndCashEquivalents",
                "cashAndCashEquivalentsAtCarryingValue",
            ),
        )
        if cash_equivalents is None:
            cash_equivalents = (self._pick_float(balance, ("cashAndCashEquivalents",)) or 0.0) + (
                self._pick_float(balance, ("shortTermInvestments",)) or 0.0
            )

        total_debt = total_debt or 0.0
        cash_equivalents = cash_equivalents or 0.0
        net_debt = total_debt - cash_equivalents

        return MarketInputs(
            price=price,
            shares_outstanding=shares_outstanding,
            market_cap=market_cap,
            net_debt=net_debt,
            total_debt=total_debt,
            cash_equivalents=cash_equivalents,
        )

    def _build_assumptions(self, *, baseline: ReverseDcfBaseline) -> dict[str, float]:
        return {
            "ebit_margin": baseline.ebit / baseline.revenue,
            "depreciation_amortization_margin": baseline.depreciation_amortization / baseline.revenue,
            "capex_outflow_margin": baseline.capex_outflow / baseline.revenue,
            "working_capital_change_margin": baseline.change_working_capital / baseline.revenue,
            "tax_rate": baseline.tax_rate,
            "baseline_revenue": baseline.revenue,
        }

    def _solve_required_revenue_cagr(
        self,
        *,
        target_enterprise_value: float,
        discount_rate: float,
        terminal_growth_rate: float,
        assumptions: dict[str, float],
    ) -> dict[str, Any]:
        if terminal_growth_rate >= discount_rate:
            return {
                "requiredRevenueCagrPct": None,
                "converged": False,
                "iterations": 0,
                "residualEnterpriseValue": None,
                "error": "terminal_growth_must_be_less_than_discount_rate",
            }

        low = -0.9
        high = 5.0
        f_low = self._ev_residual(
            growth_rate=low,
            target_enterprise_value=target_enterprise_value,
            discount_rate=discount_rate,
            terminal_growth_rate=terminal_growth_rate,
            assumptions=assumptions,
        )
        f_high = self._ev_residual(
            growth_rate=high,
            target_enterprise_value=target_enterprise_value,
            discount_rate=discount_rate,
            terminal_growth_rate=terminal_growth_rate,
            assumptions=assumptions,
        )

        if f_low * f_high > 0:
            return {
                "requiredRevenueCagrPct": None,
                "converged": False,
                "iterations": 0,
                "residualEnterpriseValue": None,
                "error": "solver_bracket_not_found",
            }

        tolerance = max(1e-6 * target_enterprise_value, 1.0)
        iterations = 0
        last_residual = None
        while iterations < 120:
            iterations += 1
            mid = (low + high) / 2.0
            residual = self._ev_residual(
                growth_rate=mid,
                target_enterprise_value=target_enterprise_value,
                discount_rate=discount_rate,
                terminal_growth_rate=terminal_growth_rate,
                assumptions=assumptions,
            )
            last_residual = residual
            if abs(residual) <= tolerance:
                return {
                    "requiredRevenueCagrPct": round(mid * 100.0, 4),
                    "converged": True,
                    "iterations": iterations,
                    "residualEnterpriseValue": round(residual, 2),
                    "error": None,
                }
            if f_low * residual <= 0:
                high = mid
                f_high = residual
            else:
                low = mid
                f_low = residual

        return {
            "requiredRevenueCagrPct": round(((low + high) / 2.0) * 100.0, 4),
            "converged": False,
            "iterations": iterations,
            "residualEnterpriseValue": round(last_residual, 2) if last_residual is not None else None,
            "error": "solver_max_iterations_exceeded",
        }

    def _ev_residual(
        self,
        *,
        growth_rate: float,
        target_enterprise_value: float,
        discount_rate: float,
        terminal_growth_rate: float,
        assumptions: dict[str, float],
    ) -> float:
        baseline_revenue = assumptions["baseline_revenue"]
        tax_rate = assumptions["tax_rate"]
        ebit_margin = assumptions["ebit_margin"]
        da_margin = assumptions["depreciation_amortization_margin"]
        capex_margin = assumptions["capex_outflow_margin"]
        nwc_margin = assumptions["working_capital_change_margin"]

        pv = 0.0
        revenue_t = baseline_revenue
        fcff_t = 0.0
        for year in range(1, self._PROJECTION_YEARS + 1):
            revenue_t = revenue_t * (1.0 + growth_rate)
            ebit_t = revenue_t * ebit_margin
            nopat_t = ebit_t * (1.0 - tax_rate)
            da_t = revenue_t * da_margin
            capex_t = revenue_t * capex_margin
            nwc_t = revenue_t * nwc_margin
            fcff_t = nopat_t + da_t - capex_t - nwc_t
            pv += fcff_t / ((1.0 + discount_rate) ** year)

        terminal_fcf = fcff_t * (1.0 + terminal_growth_rate)
        terminal_value = terminal_fcf / (discount_rate - terminal_growth_rate)
        pv_terminal = terminal_value / ((1.0 + discount_rate) ** self._PROJECTION_YEARS)
        return (pv + pv_terminal) - target_enterprise_value

    @staticmethod
    def _pick_float(row: dict[str, Any], keys: tuple[str, ...]) -> float | None:
        for key in keys:
            value = row.get(key)
            parsed = ReverseDcfNode._as_float(value)
            if parsed is not None:
                return parsed
        return None

    @staticmethod
    def _sum_field(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> float:
        total = 0.0
        seen = False
        for row in rows:
            value = ReverseDcfNode._pick_float(row, keys)
            if value is None:
                continue
            total += value
            seen = True
        if not seen:
            return 0.0
        return total

    @staticmethod
    def _extract_as_of_date(rows: list[dict[str, Any]]) -> str | None:
        if not rows:
            return None
        latest = rows[0]
        raw_date = latest.get("date")
        if isinstance(raw_date, str) and raw_date.strip():
            return raw_date
        raw_year = latest.get("calendarYear")
        if isinstance(raw_year, str) and raw_year.strip():
            return raw_year
        return None

    @staticmethod
    def _sort_rows_desc(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        def _row_key(row: dict[str, Any]) -> tuple[str, str]:
            date_val = str(row.get("date") or "")
            year_val = str(row.get("calendarYear") or "")
            return (date_val, year_val)

        return sorted(rows, key=_row_key, reverse=True)

    @staticmethod
    def _as_float(value: Any) -> float | None:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            raw = value.strip().replace(",", "")
            if not raw:
                return None
            try:
                return float(raw)
            except ValueError:
                return None
        return None


__all__ = ["ReverseDcfNode"]
