from app.models import Company, ICPRequest
from app.scoring import RuleBasedScorer


def test_strong_structured_match_scores_above_mismatch():
    icp = ICPRequest(
        description="B2B software and IT services companies",
        min_revenue=5_000_000,
        max_revenue=50_000_000,
        min_employees=30,
        max_employees=200,
    )
    scorer = RuleBasedScorer()
    match = Company(
        name="GoodFit",
        revenue=15_000_000,
        employees=80,
        industries=["Software and IT services"],
    )
    mismatch = Company(
        name="PoorFit",
        revenue=120_000_000,
        employees=900,
        industries=["Retail trade"],
    )

    assert scorer.assess(match, icp).score > scorer.assess(mismatch, icp).score


def test_missing_data_is_reported_as_unknown():
    icp = ICPRequest(description="Software companies with clear firmographic evidence")
    result = RuleBasedScorer().assess(Company(name="SparseCo"), icp)
    assert result.risks_or_unknowns
