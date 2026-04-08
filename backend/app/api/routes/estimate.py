from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_estimation_service
from app.auth.models import UserContext
from app.core.responses import success_response
from app.modeling.schemas import EstimateRequest
from app.services.estimation_service import CloudEstimationService

router = APIRouter()


@router.post("/estimate")
def estimate_cost(
    payload: EstimateRequest,
    _: UserContext = Depends(get_current_user),
    service: CloudEstimationService = Depends(get_estimation_service),
) -> dict[str, object]:
    return success_response(service.estimate(payload))

