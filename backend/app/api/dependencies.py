from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.firebase import FirebaseTokenVerifier
from app.auth.models import UserContext
from app.core.config import Settings, get_settings
from app.core.exceptions import AuthenticationError
from app.engines.estimation.calculators import CostEstimationEngine
from app.engines.recommendation.rules import RecommendationEngine
from app.integrations.aws.gateway import AwsPricingGateway
from app.services.estimation_service import CloudEstimationService
from app.services.recommendation_service import CloudRecommendationService

bearer_scheme = HTTPBearer(auto_error=False)


def get_token_verifier(
    settings: Settings = Depends(get_settings),
) -> FirebaseTokenVerifier:
    return FirebaseTokenVerifier(settings)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    verifier: FirebaseTokenVerifier = Depends(get_token_verifier),
) -> UserContext:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationError(
            code="UNAUTHORIZED",
            message="Invalid or missing authentication token",
        )
    return verifier.verify_token(credentials.credentials)


def get_pricing_gateway(
    settings: Settings = Depends(get_settings),
) -> AwsPricingGateway:
    return AwsPricingGateway(settings)


def get_estimation_engine() -> CostEstimationEngine:
    return CostEstimationEngine()


def get_recommendation_engine() -> RecommendationEngine:
    return RecommendationEngine()


def get_estimation_service(
    pricing_gateway: AwsPricingGateway = Depends(get_pricing_gateway),
    estimation_engine: CostEstimationEngine = Depends(get_estimation_engine),
) -> CloudEstimationService:
    return CloudEstimationService(
        pricing_gateway=pricing_gateway,
        estimation_engine=estimation_engine,
    )


def get_recommendation_service(
    settings: Settings = Depends(get_settings),
    pricing_gateway: AwsPricingGateway = Depends(get_pricing_gateway),
    estimation_engine: CostEstimationEngine = Depends(get_estimation_engine),
    recommendation_engine: RecommendationEngine = Depends(get_recommendation_engine),
) -> CloudRecommendationService:
    return CloudRecommendationService(
        settings=settings,
        pricing_gateway=pricing_gateway,
        estimation_engine=estimation_engine,
        recommendation_engine=recommendation_engine,
    )

