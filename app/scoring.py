from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod

import boto3

from app.config import Settings
from app.models import Company, CompanyAssessment, ICPRequest


class Scorer(ABC):
    @abstractmethod
    def assess(self, company: Company, icp: ICPRequest) -> CompanyAssessment:
        raise NotImplementedError


class RuleBasedScorer(Scorer):
    """Deterministic fallback used for local development and named regression tests."""

    def assess(self, company: Company, icp: ICPRequest) -> CompanyAssessment:
        score = 50
        reasons: list[str] = []
        risks: list[str] = []
        evidence: list[str] = []

        if company.employees is not None:
            evidence.append(f"Employees: {company.employees}")
            score += self._range_points(
                company.employees,
                icp.min_employees,
                icp.max_employees,
                18,
                reasons,
                "employee count",
            )
        else:
            risks.append("Employee count is unavailable")

        if company.revenue is not None:
            evidence.append(f"Revenue: {company.revenue:,.0f}")
            score += self._range_points(
                company.revenue,
                icp.min_revenue,
                icp.max_revenue,
                18,
                reasons,
                "revenue",
            )
        else:
            risks.append("Revenue is unavailable")

        if company.industries:
            industry_text = " ".join(company.industries).lower()
            description_tokens = {
                token
                for token in re.findall(r"[a-zA-Z]{4,}", icp.description.lower())
                if token not in STOPWORDS
            }
            overlap = [token for token in description_tokens if token in industry_text]
            evidence.append("Industries: " + ", ".join(company.industries))
            if overlap:
                score += min(14, 4 + len(overlap) * 3)
                reasons.append("Industry description overlaps with the stated ICP")
        else:
            risks.append("Industry data is unavailable")

        if company.domain:
            evidence.append(f"Domain: {company.domain}")

        score = max(0, min(100, score))
        fit = "strong" if score >= 75 else "medium" if score >= 55 else "weak"
        if not reasons:
            reasons.append("Available structured data provides a partial match to the ICP")

        return CompanyAssessment(
            company=company,
            score=score,
            fit=fit,
            reasons=reasons[:5],
            risks_or_unknowns=risks[:5],
            evidence=evidence[:6],
        )

    @staticmethod
    def _range_points(value, minimum, maximum, points, reasons, label):
        if minimum is None and maximum is None:
            return 0
        in_range = (minimum is None or value >= minimum) and (
            maximum is None or value <= maximum
        )
        if in_range:
            reasons.append(f"{label.capitalize()} is inside the requested range")
            return points
        reasons.append(f"{label.capitalize()} is outside the requested range")
        return -points


class BedrockScorer(Scorer):
    """LLM scorer with strict JSON validation through Pydantic."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = boto3.client("bedrock-runtime", region_name=settings.aws_region)

    def assess(self, company: Company, icp: ICPRequest) -> CompanyAssessment:
        prompt = f"""
You are an evidence-first B2B account qualification agent.
Assess the company against the ICP. Use ONLY the company facts provided below.
Do not invent facts. Missing data must be called out as an unknown.

ICP:
{icp.description}

Structured constraints:
- employee range: {icp.min_employees} to {icp.max_employees}
- revenue range: {icp.min_revenue} to {icp.max_revenue}
- industry code: {icp.industry_code}

Company:
{company.model_dump(exclude={"raw"})}

Return ONLY valid JSON with this exact shape:
{{
  "score": 0,
  "fit": "strong|medium|weak",
  "reasons": ["..."],
  "risks_or_unknowns": ["..."],
  "evidence": ["..."]
}}
Score must be an integer from 0 to 100. Every reason must be traceable to provided facts.
""".strip()

        response = self.client.converse(
            modelId=self.settings.bedrock_model_id,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"temperature": 0, "maxTokens": 700},
        )
        text = response["output"]["message"]["content"][0]["text"]
        payload = self._extract_json(text)
        return CompanyAssessment(company=company, **payload)

    @staticmethod
    def _extract_json(text: str) -> dict:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("Model response did not contain a JSON object")
        return json.loads(cleaned[start : end + 1])


def build_scorer(settings: Settings) -> Scorer:
    if settings.scorer_mode.lower() == "bedrock":
        return BedrockScorer(settings)
    return RuleBasedScorer()


STOPWORDS = {
    "with", "that", "this", "from", "into", "your", "their", "they", "them",
    "have", "company", "companies", "business", "looking", "ideal", "customer",
    "customers", "nordic", "swedish", "european",
}
