from app.config import Settings
from app.models import AssessmentResponse, ICPRequest
from app.scoring import build_scorer
from app.vainu_client import VainuClient


class GrowthAgentService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.vainu = VainuClient(settings)
        self.scorer = build_scorer(settings)

    async def qualify(self, icp: ICPRequest) -> AssessmentResponse:
        source, companies = await self.vainu.find_candidates(icp)
        assessments = [self.scorer.assess(company, icp) for company in companies]
        assessments.sort(key=lambda item: item.score, reverse=True)
        return AssessmentResponse(
            icp=icp,
            source=source,
            scorer="bedrock" if self.settings.scorer_mode.lower() == "bedrock" else "rules",
            assessments=assessments,
        )
