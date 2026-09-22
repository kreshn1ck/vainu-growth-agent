import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.models import Company, ICPRequest
from app.scoring import RuleBasedScorer


def main() -> int:
    cases = json.loads((ROOT / "evaluation" / "golden_cases.json").read_text())
    scorer = RuleBasedScorer()
    failures = 0

    for case in cases:
        icp = ICPRequest(**case["icp"])
        preferred = scorer.assess(Company(**case["preferred"]), icp)
        other = scorer.assess(Company(**case["other"]), icp)
        passed = preferred.score > other.score
        print(
            f"{'PASS' if passed else 'FAIL'} | {case['name']} | "
            f"{preferred.score} > {other.score}"
        )
        failures += 0 if passed else 1

    return failures


if __name__ == "__main__":
    raise SystemExit(main())
