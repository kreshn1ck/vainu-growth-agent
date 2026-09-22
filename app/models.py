from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class ICPRequest(BaseModel):
    description: str = Field(
        ...,
        min_length=10,
        description="Natural-language ideal customer profile used for semantic assessment.",
    )
    database: Literal["FI", "SE", "NO", "DK", "NL"] = "SE"
    industry_code: str | None = None
    min_revenue: float | None = Field(default=None, ge=0)
    max_revenue: float | None = Field(default=None, ge=0)
    min_employees: int | None = Field(default=None, ge=0)
    max_employees: int | None = Field(default=None, ge=0)
    limit: int = Field(default=10, ge=1, le=20)

    @model_validator(mode="after")
    def validate_ranges(self):
        if self.min_revenue is not None and self.max_revenue is not None:
            if self.min_revenue > self.max_revenue:
                raise ValueError("min_revenue cannot be greater than max_revenue")
        if self.min_employees is not None and self.max_employees is not None:
            if self.min_employees > self.max_employees:
                raise ValueError("min_employees cannot be greater than max_employees")
        return self


class Company(BaseModel):
    business_id: str | None = None
    name: str
    domain: str | None = None
    revenue: float | None = None
    employees: int | None = None
    industries: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict, exclude=True)


class CompanyAssessment(BaseModel):
    company: Company
    score: int = Field(ge=0, le=100)
    fit: Literal["strong", "medium", "weak"]
    reasons: list[str] = Field(min_length=1, max_length=5)
    risks_or_unknowns: list[str] = Field(default_factory=list, max_length=5)
    evidence: list[str] = Field(default_factory=list, max_length=6)


class AssessmentResponse(BaseModel):
    icp: ICPRequest
    source: Literal["vainu", "mock"]
    scorer: Literal["rules", "bedrock"]
    assessments: list[CompanyAssessment]
