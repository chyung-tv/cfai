from __future__ import annotations

from pydantic import BaseModel, Field


class KeyPerson(BaseModel):
    name: str
    role: str | None = None
    impact: str | None = None


class ExecutiveSummarySection(BaseModel):
    summary: str
    lifeline: str | None = None
    evidenceRefs: list[str] = Field(default_factory=list)


class ManagementProfileSection(BaseModel):
    leadershipSummary: str | None = None
    keyPeople: list[KeyPerson] = Field(default_factory=list)
    evidenceRefs: list[str] = Field(default_factory=list)


class BusinessQualitySection(BaseModel):
    qualityTier: str
    moat: list[str] = Field(default_factory=list)
    evidenceRefs: list[str] = Field(default_factory=list)


class IndustryProfileSection(BaseModel):
    marketStructure: str | None = None
    position: str | None = None
    positionRationale: str | None = None
    evidenceRefs: list[str] = Field(default_factory=list)


class RecentDevelopmentItem(BaseModel):
    event: str
    timing: str | None = None
    impact: str | None = None
    confidence: str | None = None
    evidenceRefs: list[str] = Field(default_factory=list)


class RecentDevelopmentsSection(BaseModel):
    items: list[RecentDevelopmentItem] = Field(default_factory=list)
    evidenceRefs: list[str] = Field(default_factory=list)


class QualityBlock(BaseModel):
    parserVersion: str
    extractionConfidence: str | None = None
    missingFields: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class StructuredOutputModel(BaseModel):
    schemaVersion: str
    executiveSummary: ExecutiveSummarySection
    managementProfile: ManagementProfileSection
    businessQuality: BusinessQualitySection
    industryProfile: IndustryProfileSection
    recentDevelopments: RecentDevelopmentsSection
    quality: QualityBlock
