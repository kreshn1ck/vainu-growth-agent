from fastapi import Depends, FastAPI, HTTPException

from app.config import Settings, get_settings
from app.models import AssessmentResponse, ICPRequest
from app.service import GrowthAgentService

app = FastAPI(
    title="Vainu Growth Agent",
    version="0.1.0",
    description=(
        "Evidence-first ICP qualification: retrieve candidate companies from Vainu, "
        "then assess fit with deterministic rules or an AWS Bedrock LLM."
    ),
)


@app.get("/health")
def health(settings: Settings = Depends(get_settings)):
    return {
        "status": "ok",
        "vainu_source": "mock" if settings.use_mock_vainu else "api",
        "scorer": settings.scorer_mode,
    }


@app.post("/v1/qualify", response_model=AssessmentResponse)
async def qualify(icp: ICPRequest, settings: Settings = Depends(get_settings)):
    try:
        return await GrowthAgentService(settings).qualify(icp)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
