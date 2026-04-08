from __future__ import annotations

from decimal import Decimal

import pandas as pd

from app.engines.estimation.calculators import CostEstimationEngine
from app.integrations.aws.gateway import AwsPricingGateway
from app.modeling.schemas import (
    CompareRequest,
    EC2EstimateRequest,
    EstimateRequest,
    LambdaEstimateRequest,
    S3EstimateRequest,
)
from app.services.contracts import EC2PricingContext, EstimateOutcome, LambdaPricingContext, S3PricingContext


class CloudEstimationService:
    def __init__(
        self,
        pricing_gateway: AwsPricingGateway,
        estimation_engine: CostEstimationEngine,
    ) -> None:
        self._pricing_gateway = pricing_gateway
        self._estimation_engine = estimation_engine

    def estimate(self, payload: EstimateRequest) -> dict[str, object]:
        outcome = self._estimate_payload(payload)
        return self._serialize_estimate(outcome)

    def compare(self, payload: CompareRequest) -> dict[str, object]:
        results = []
        for index, comparison in enumerate(payload.comparisons):
            estimate_payload = self._build_compare_estimate_request(payload, comparison)
            outcome = self._estimate_payload(estimate_payload)
            results.append({"comparison_index": index, **self._serialize_compare_result(outcome)})

        frame = pd.DataFrame(
            [
                {
                    "comparison_index": item["comparison_index"],
                    "total_cost": item["total_cost"],
                }
                for item in results
            ]
        )
        ranked_indices = frame.sort_values(by="total_cost", ascending=True)["comparison_index"].tolist()
        ranked_results = [
            next(item for item in results if item["comparison_index"] == comparison_index)
            for comparison_index in ranked_indices
        ]

        return {
            "results": [
                {key: value for key, value in item.items() if key != "comparison_index"}
                for item in ranked_results
            ],
            "best_option": {
                key: value
                for key, value in ranked_results[0].items()
                if key != "comparison_index"
            },
        }

    def _build_compare_estimate_request(self, payload: CompareRequest, comparison):
        common_fields = {"region": comparison.region, "duration_hours": payload.duration_hours}
        if payload.service == "EC2":
            return EC2EstimateRequest(service="EC2", configuration=comparison.configuration, **common_fields)
        if payload.service == "S3":
            return S3EstimateRequest(service="S3", configuration=comparison.configuration, **common_fields)
        return LambdaEstimateRequest(service="Lambda", configuration=comparison.configuration, **common_fields)

    def _estimate_payload(self, payload: EstimateRequest) -> EstimateOutcome:
        duration_hours = Decimal(str(payload.duration_hours))
        if payload.service == "EC2":
            context = EC2PricingContext(
                region=payload.region,
                instance_type=payload.configuration.instance_type,
                operating_system=payload.configuration.operating_system,
                pricing_model=payload.configuration.pricing_model,
            )
            price = self._pricing_gateway.fetch_ec2_price(context)
            return self._estimation_engine.estimate_ec2(
                price=price,
                duration_hours=duration_hours,
                metadata={
                    "service": "EC2",
                    "region": payload.region,
                    "pricing_model": payload.configuration.pricing_model,
                    "pricing_source": price.source,
                    "filters": {
                        "instance_type": payload.configuration.instance_type,
                        "operating_system": payload.configuration.operating_system,
                    },
                    "assumptions": (
                        ["Reserved pricing defaults to 1-year standard no-upfront when applicable."]
                        if payload.configuration.pricing_model == "Reserved"
                        else []
                    ),
                },
            )

        if payload.service == "S3":
            context = S3PricingContext(
                region=payload.region,
                storage_class=payload.configuration.storage_class,
            )
            price = self._pricing_gateway.fetch_s3_price(context)
            return self._estimation_engine.estimate_s3(
                price=price,
                storage_gb=Decimal(str(payload.configuration.storage_gb)),
                duration_hours=duration_hours,
                metadata={
                    "service": "S3",
                    "region": payload.region,
                    "pricing_source": price.source,
                    "filters": {"storage_class": payload.configuration.storage_class},
                    "assumptions": ["S3 monthly storage pricing is prorated over 730 hours."],
                },
            )

        context = LambdaPricingContext(region=payload.region)
        price_bundle = self._pricing_gateway.fetch_lambda_prices(context)
        return self._estimation_engine.estimate_lambda(
            price_bundle=price_bundle,
            request_count=Decimal(str(payload.configuration.request_count)),
            execution_duration_ms=Decimal(str(payload.configuration.execution_duration_ms)),
            memory_size_mb=Decimal(str(payload.configuration.memory_size_mb)),
            metadata={
                "service": "Lambda",
                "region": payload.region,
                "pricing_source": {
                    "requests": price_bundle.request_price.source,
                    "compute": price_bundle.compute_price.source,
                },
                "filters": {"memory_size_mb": payload.configuration.memory_size_mb},
                "assumptions": ["Lambda pricing combines request charges and GB-second compute."],
            },
        )

    def _serialize_estimate(self, outcome: EstimateOutcome) -> dict[str, object]:
        return {
            "total_cost": float(outcome.total_cost),
            "currency": outcome.currency,
            "breakdown": [
                {
                    "label": line.label,
                    "quantity": float(line.quantity),
                    "unit": line.unit,
                    "rate": float(line.rate),
                    "amount": float(line.amount),
                    "description": line.description,
                }
                for line in outcome.breakdown
            ],
            "metadata": dict(outcome.metadata),
        }

    def _serialize_compare_result(self, outcome: EstimateOutcome) -> dict[str, object]:
        estimate = self._serialize_estimate(outcome)
        return {
            "region": outcome.region,
            "service": outcome.service,
            **estimate,
        }
