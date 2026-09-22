from app.models import ICPRequest
from app.vainu_client import VainuClient


def test_builds_all_filter_query():
    icp = ICPRequest(
        description="Nordic software companies with a mid-market profile",
        database="SE",
        industry_code="62",
        min_revenue=5_000_000,
        max_revenue=50_000_000,
        min_employees=20,
        max_employees=250,
    )
    query = VainuClient._build_query(icp)
    assert "?ALL" in query
    assert len(query["?ALL"]) == 3


def test_empty_structured_filters_still_produce_query():
    icp = ICPRequest(description="B2B companies that could benefit from enriched company data")
    query = VainuClient._build_query(icp)
    assert query == {"?GTE": {"financial_data.employee_count": 0}}
