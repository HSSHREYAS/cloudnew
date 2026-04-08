from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

from app.core.config import Settings
from app.core.exceptions import PricingApiError
from app.engines.estimation.calculators import CostEstimationEngine, quantize_money
from app.engines.recommendation.rules import RecommendationEngine
from app.integrations.aws.gateway import AwsPricingGateway
from app.modeling.schemas import RecommendationsRequest
from app.services.contracts import (
    EC2PricingContext,
    LambdaPricingContext,
    RecommendationScenario,
    RegionalOption,
    S3PricingContext,
)

DEFAULT_RECOMMENDATION_DURATION_HOURS = Decimal("730")


class CloudRecommendationService:
    def __init__(
        self,
        settings: Settings,
        pricing_gateway: AwsPricingGateway,
        estimation_engine: CostEstimationEngine,
        recommendation_engine: RecommendationEngine,
    ) -> None:
        self._settings = settings
        self._pricing_gateway = pricing_gateway
        self._estimation_engine = estimation_engine
        self._recommendation_engine = recommendation_engine

    def generate(self, payload: RecommendationsRequest) -> dict[str, object]:
        current_cost = Decimal(str(payload.current_cost))
        duration_hours = (
            Decimal(str(payload.duration_hours))
            if payload.duration_hours is not None
            else DEFAULT_RECOMMENDATION_DURATION_HOURS
        )

        scenario = RecommendationScenario(
            service=payload.service,
            region=payload.region,
            current_cost=current_cost,
            duration_hours=duration_hours,
            configuration=payload.configuration.model_dump(),
        )

        if payload.service == "EC2":
            scenario = self._enrich_ec2_scenario(payload, scenario, duration_hours)
        elif payload.service == "S3":
            scenario = self._enrich_s3_scenario(payload, scenario, duration_hours)
        else:
            scenario = self._enrich_lambda_scenario(payload, scenario)

        recommendations = self._recommendation_engine.generate(scenario)
        return {
            "recommendations": [
                {
                    "type": item.type,
                    "suggestion": item.suggestion,
                    "estimated_savings": float(item.estimated_savings),
                    "risk_level": item.risk_level,
                    "explanation": item.explanation,
                }
                for item in recommendations
            ]
        }

    def _enrich_ec2_scenario(
        self,
        payload,
        scenario: RecommendationScenario,
        duration_hours: Decimal,
    ) -> RecommendationScenario:
        reserved_cost = None
        if payload.configuration.pricing_model != "Reserved":
            try:
                reserved_price = self._pricing_gateway.fetch_ec2_price(
                    EC2PricingContext(
                        region=payload.region,
                        instance_type=payload.configuration.instance_type,
                        operating_system=payload.configuration.operating_system,
                        pricing_model="Reserved",
                    )
                )
                reserved_cost = self._estimation_engine.estimate_ec2(
                    price=reserved_price,
                    duration_hours=duration_hours,
                    metadata={},
                ).total_cost
            except PricingApiError:
                reserved_cost = None

        spot_cost = None
        if payload.configuration.pricing_model != "Spot":
            try:
                spot_price = self._pricing_gateway.fetch_ec2_price(
                    EC2PricingContext(
                        region=payload.region,
                        instance_type=payload.configuration.instance_type,
                        operating_system=payload.configuration.operating_system,
                        pricing_model="Spot",
                    )
                )
                spot_cost = self._estimation_engine.estimate_ec2(
                    price=spot_price,
                    duration_hours=duration_hours,
                    metadata={},
                ).total_cost
            except PricingApiError:
                spot_cost = None

        cheaper_region = self._find_cheaper_region_for_ec2(payload, duration_hours, payload.region)
        return replace(
            scenario,
            reserved_cost=reserved_cost,
            spot_cost=spot_cost,
            cheaper_region=cheaper_region,
        )

    def _find_cheaper_region_for_ec2(self, payload, duration_hours: Decimal, current_region: str):
        best_option = None
        for candidate_region in self._settings.candidate_regions:
            if candidate_region == current_region:
                continue
            try:
                candidate_price = self._pricing_gateway.fetch_ec2_price(
                    EC2PricingContext(
                        region=candidate_region,
                        instance_type=payload.configuration.instance_type,
                        operating_system=payload.configuration.operating_system,
                        pricing_model=payload.configuration.pricing_model,
                    )
                )
                estimate = self._estimation_engine.estimate_ec2(
                    price=candidate_price,
                    duration_hours=duration_hours,
                    metadata={},
                )
            except PricingApiError:
                continue
            option = RegionalOption(
                region=candidate_region,
                projected_cost=estimate.total_cost,
                explanation=(
                    f"{candidate_region} returned a lower projected EC2 cost for the same "
                    f"instance, operating system, and pricing model."
                ),
            )
            if best_option is None or option.projected_cost < best_option.projected_cost:
                best_option = option
        return best_option

    def _enrich_s3_scenario(
        self,
        payload,
        scenario: RecommendationScenario,
        duration_hours: Decimal,
    ) -> RecommendationScenario:
        cheaper_storage_class_cost = None
        if payload.configuration.storage_class == "Standard":
            try:
                candidate_price = self._pricing_gateway.fetch_s3_price(
                    S3PricingContext(region=payload.region, storage_class="StandardIA")
                )
                cheaper_storage_class_cost = self._estimation_engine.estimate_s3(
                    price=candidate_price,
                    storage_gb=Decimal(str(payload.configuration.storage_gb)),
                    duration_hours=duration_hours,
                    metadata={},
                ).total_cost
            except PricingApiError:
                cheaper_storage_class_cost = None

        cheaper_region = self._find_cheaper_region_for_s3(payload, duration_hours, payload.region)
        return replace(
            scenario,
            cheaper_region=cheaper_region,
            cheaper_storage_class_cost=cheaper_storage_class_cost,
        )

    def _find_cheaper_region_for_s3(self, payload, duration_hours: Decimal, current_region: str):
        best_option = None
        for candidate_region in self._settings.candidate_regions:
            if candidate_region == current_region:
                continue
            try:
                candidate_price = self._pricing_gateway.fetch_s3_price(
                    S3PricingContext(
                        region=candidate_region,
                        storage_class=payload.configuration.storage_class,
                    )
                )
                estimate = self._estimation_engine.estimate_s3(
                    price=candidate_price,
                    storage_gb=Decimal(str(payload.configuration.storage_gb)),
                    duration_hours=duration_hours,
                    metadata={},
                )
            except PricingApiError:
                continue
            option = RegionalOption(
                region=candidate_region,
                projected_cost=estimate.total_cost,
                explanation=(
                    f"{candidate_region} returned a lower projected S3 storage price for the "
                    f"same storage class and allocation."
                ),
            )
            if best_option is None or option.projected_cost < best_option.projected_cost:
                best_option = option
        return best_option

    def _enrich_lambda_scenario(
        self,
        payload,
        scenario: RecommendationScenario,
    ) -> RecommendationScenario:
        cheaper_region = self._find_cheaper_region_for_lambda(payload, payload.region)
        rightsized_cost = None
        if payload.configuration.memory_size_mb > 512:
            try:
                current_bundle = self._pricing_gateway.fetch_lambda_prices(
                    LambdaPricingContext(region=payload.region)
                )
                rightsized_memory = max(128, int(payload.configuration.memory_size_mb * 0.8))
                projected = self._estimation_engine.estimate_lambda(
                    price_bundle=current_bundle,
                    request_count=Decimal(str(payload.configuration.request_count)),
                    execution_duration_ms=Decimal(str(payload.configuration.execution_duration_ms)),
                    memory_size_mb=Decimal(str(rightsized_memory)),
                    metadata={},
                )
                rightsized_cost = quantize_money(projected.total_cost)
            except PricingApiError:
                rightsized_cost = None

        return replace(
            scenario,
            cheaper_region=cheaper_region,
            lambda_rightsized_cost=rightsized_cost,
        )

    def _find_cheaper_region_for_lambda(self, payload, current_region: str):
        best_option = None
        for candidate_region in self._settings.candidate_regions:
            if candidate_region == current_region:
                continue
            try:
                candidate_bundle = self._pricing_gateway.fetch_lambda_prices(
                    LambdaPricingContext(region=candidate_region)
                )
                estimate = self._estimation_engine.estimate_lambda(
                    price_bundle=candidate_bundle,
                    request_count=Decimal(str(payload.configuration.request_count)),
                    execution_duration_ms=Decimal(str(payload.configuration.execution_duration_ms)),
                    memory_size_mb=Decimal(str(payload.configuration.memory_size_mb)),
                    metadata={},
                )
            except PricingApiError:
                continue
            option = RegionalOption(
                region=candidate_region,
                projected_cost=estimate.total_cost,
                explanation=(
                    f"{candidate_region} returned a lower projected Lambda request and compute "
                    f"price for the same invocation profile."
                ),
            )
            if best_option is None or option.projected_cost < best_option.projected_cost:
                best_option = option
        return best_option
