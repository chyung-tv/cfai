from __future__ import annotations

from pydantic import BaseModel, Field


class ReportMeta(BaseModel):
    title: str
    date: str | None = None
    analyst_classification: str | None = None
    subject: str | None = None
    ticker: str
    sector: str | None = None
    recommendation_text: str | None = None


class ExecutiveSummary(BaseModel):
    summary_text: str
    core_thesis_points: list[str] = Field(default_factory=list)
    final_verdict: str


class SegmentItem(BaseModel):
    name: str
    description: str | None = None
    revenue_share_estimate: str | None = None
    growth_signal: str | None = None


class EconomicMoat(BaseModel):
    rating: str | None = None
    drivers: list[str] = Field(default_factory=list)


class FiveForceItem(BaseModel):
    force: str
    intensity: str | None = None
    rationale: str | None = None


class CompanyProfile(BaseModel):
    business_essence: str | None = None
    value_proposition: str | None = None
    segments: list[SegmentItem] = Field(default_factory=list)
    economic_moat: EconomicMoat = Field(default_factory=EconomicMoat)
    five_forces: list[FiveForceItem] = Field(default_factory=list)
    growth_drivers: list[str] = Field(default_factory=list)
    decline_drivers: list[str] = Field(default_factory=list)
    customer_choice_rationale: str | None = None


class ExecutiveItem(BaseModel):
    name: str
    role: str | None = None
    impact: str | None = None
    compensation_notes: str | None = None


class ManagementProfile(BaseModel):
    executives: list[ExecutiveItem] = Field(default_factory=list)
    incentive_alignment_summary: str | None = None


class IndustryProfile(BaseModel):
    market_structure: str | None = None
    competitive_landscape: str | None = None
    ecosystem_dependencies: list[str] = Field(default_factory=list)
    secular_growth_drivers: list[str] = Field(default_factory=list)
    secular_decline_drivers: list[str] = Field(default_factory=list)
    ten_year_outlook_summary: str | None = None
    market_share_projection_notes: str | None = None


class ProjectionRow(BaseModel):
    period: str
    revenue: str | None = None
    operating_margin: str | None = None
    notes: str | None = None


class ProjectionModel(BaseModel):
    revenue_cagr_10y: str
    operating_margin_path: str | None = None
    projection_table_rows: list[ProjectionRow] = Field(default_factory=list)


class CapitalEfficiencyModel(BaseModel):
    roe_5y: str | None = None
    roic_5y: str | None = None
    roce_5y: str | None = None
    peer_context: str | None = None


class FinancialProfile(BaseModel):
    capital_efficiency: CapitalEfficiencyModel = Field(default_factory=CapitalEfficiencyModel)
    projection: ProjectionModel
    assumptions: list[str] = Field(default_factory=list)


class RecentEvent(BaseModel):
    event: str
    date_or_window: str | None = None
    impact: str | None = None
    confidence: str | None = None


class PriceMove(BaseModel):
    magnitude: str | None = None
    direction: str | None = None
    driver: str | None = None


class RecentDevelopments(BaseModel):
    events_6m: list[RecentEvent] = Field(default_factory=list)
    material_price_moves: list[PriceMove] = Field(default_factory=list)


class LifeLine(BaseModel):
    thrive_factor: str
    break_condition: str | None = None
    failure_impact: str | None = None


class ViewpointCondition(BaseModel):
    viewpoint: str
    suitability: str
    rationale: str | None = None


class VerdictAlternative(BaseModel):
    name: str
    reason: str | None = None


class GeminiVerdict(BaseModel):
    decision: str
    verdict_logic: str | None = None
    viewpoint_conditions: list[ViewpointCondition] = Field(min_length=1)
    alternatives: list[VerdictAlternative] = Field(default_factory=list)


class QualityBlock(BaseModel):
    parser_version: str
    extraction_confidence: str | None = None
    missing_fields: list[str] = Field(default_factory=list)


class StructuredOutputModel(BaseModel):
    report_meta: ReportMeta
    executive_summary: ExecutiveSummary
    company_profile: CompanyProfile
    management_profile: ManagementProfile
    industry_profile: IndustryProfile
    financial_profile: FinancialProfile
    recent_developments: RecentDevelopments
    life_line: LifeLine
    gemini_verdict: GeminiVerdict
    quality: QualityBlock
