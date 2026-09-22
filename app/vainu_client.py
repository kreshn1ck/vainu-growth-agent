from __future__ import annotations

from typing import Any

import httpx

from app.config import Settings
from app.mock_data import MOCK_COMPANIES
from app.models import Company, ICPRequest


FIELDS = [
    "business_id",
    "name",
    "domain",
    "financial_data.revenue",
    "financial_data.employee_count",
    "official_industries",
]


class VainuClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def find_candidates(self, icp: ICPRequest) -> tuple[str, list[Company]]:
        if self.settings.use_mock_vainu:
            return "mock", self._normalize_many(MOCK_COMPANIES)[: icp.limit]

        if not self.settings.vainu_refresh_token:
            raise RuntimeError(
                "VAINU_REFRESH_TOKEN is required when USE_MOCK_VAINU=false. "
                "Request a Vainu API trial token and store it in .env."
            )

        access_token = await self._get_access_token()
        payload = {
            "database": icp.database,
            "query": self._build_query(icp),
            "fields": FIELDS,
            "limit": icp.limit,
        }
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(
            timeout=self.settings.request_timeout_seconds
        ) as client:
            response = await client.post(
                f"{self.settings.vainu_base_url}/organizations/",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        return "vainu", self._normalize_many(data.get("results", []))

    async def _get_access_token(self) -> str:
        async with httpx.AsyncClient(
            timeout=self.settings.request_timeout_seconds
        ) as client:
            response = await client.post(
                self.settings.vainu_token_url,
                json={"refresh": self.settings.vainu_refresh_token},
            )
            response.raise_for_status()
            data = response.json()
        return data["access"]

    @staticmethod
    def _build_query(icp: ICPRequest) -> dict[str, Any]:
        clauses: list[dict[str, Any]] = []

        if icp.industry_code:
            clauses.append({"?EQ": {"official_industries.code": [icp.industry_code]}})

        if icp.min_revenue is not None or icp.max_revenue is not None:
            clauses.append(
                {"?RANGE": {"financial_data.revenue": [icp.min_revenue, icp.max_revenue]}}
            )

        if icp.min_employees is not None or icp.max_employees is not None:
            clauses.append(
                {
                    "?RANGE": {
                        "financial_data.employee_count": [
                            icp.min_employees,
                            icp.max_employees,
                        ]
                    }
                }
            )

        if not clauses:
            return {"?GTE": {"financial_data.employee_count": 0}}
        if len(clauses) == 1:
            return clauses[0]
        return {"?ALL": clauses}

    @classmethod
    def _normalize_many(cls, rows: list[dict[str, Any]]) -> list[Company]:
        return [cls._normalize_company(row) for row in rows]

    @staticmethod
    def _normalize_company(row: dict[str, Any]) -> Company:
        financial = row.get("financial_data") or {}
        industries_raw = row.get("official_industries") or []
        industries: list[str] = []

        for item in industries_raw:
            if isinstance(item, dict):
                label = item.get("description") or item.get("name") or item.get("code")
                if label:
                    industries.append(str(label))
            elif item:
                industries.append(str(item))

        employees = financial.get("employee_count")
        if employees is None:
            employees_block = financial.get("employees") or {}
            if isinstance(employees_block, dict):
                employees = employees_block.get("absolute_count")

        return Company(
            business_id=row.get("business_id"),
            name=row.get("name") or row.get("company_name") or "Unknown company",
            domain=row.get("domain") or row.get("website"),
            revenue=financial.get("revenue"),
            employees=employees,
            industries=industries,
            raw=row,
        )
