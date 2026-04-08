from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_recommendation_service
from app.auth.models import UserContext
from app.core.responses import success_response
from app.modeling.schemas import RecommendationsRequest
from app.services.recommendation_service import CloudRecommendationService

router = APIRouter()


@router.post("/recommendations")
def get_recommendations(
    payload: RecommendationsRequest,
    _: UserContext = Depends(get_current_user),
    service: CloudRecommendationService = Depends(get_recommendation_service),
) -> dict[str, object]:
    return success_response(service.generate(payload))

