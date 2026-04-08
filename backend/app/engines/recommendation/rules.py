from decimal import Decimal

from app.engines.estimation.calculators import quantize_money
from app.services.contracts import Recommendation, RecommendationScenario


class RecommendationEngine:
    def generate(self, scenario: RecommendationScenario) -> list[Recommendation]:
        recommendations: list[Recommendation] = []

        if scenario.reserved_cost is not None and scenario.reserved_cost < scenario.current_cost:
            savings = quantize_money(scenario.current_cost - scenario.reserved_cost)
            recommendations.append(
                Recommendation(
                    type="cost_optimization",
                    suggestion="Use Reserved pricing for steady EC2 workloads",
                    estimated_savings=savings,
                    risk_level="low",
                    explanation=(
                        "Projected savings are based on the default 1-year standard no-upfront "
                        "reserved term for the same instance configuration."
                    ),
                )
            )

        if scenario.spot_cost is not None and scenario.spot_cost < scenario.current_cost:
            savings = quantize_money(scenario.current_cost - scenario.spot_cost)
            recommendations.append(
                Recommendation(
                    type="cost_optimization",
                    suggestion="Consider Spot capacity for interruptible EC2 workloads",
                    estimated_savings=savings,
                    risk_level="high",
                    explanation=(
                        "Spot savings are calculated from recent regional Spot price history and "
                        "assume the workload can tolerate interruptions."
                    ),
                )
            )

        if (
            scenario.cheaper_region is not None
            and scenario.cheaper_region.projected_cost < scenario.current_cost
        ):
            savings = quantize_money(
                scenario.current_cost - scenario.cheaper_region.projected_cost
            )
            recommendations.append(
                Recommendation(
                    type="cost_optimization",
                    suggestion=f"Consider deploying in {scenario.cheaper_region.region}",
                    estimated_savings=savings,
                    risk_level="medium",
                    explanation=scenario.cheaper_region.explanation,
                )
            )

        if (
            scenario.cheaper_storage_class_cost is not None
            and scenario.cheaper_storage_class_cost < scenario.current_cost
        ):
            savings = quantize_money(
                scenario.current_cost - scenario.cheaper_storage_class_cost
            )
            recommendations.append(
                Recommendation(
                    type="cost_optimization",
                    suggestion="Move infrequently accessed S3 data to Standard-IA",
                    estimated_savings=savings,
                    risk_level="medium",
                    explanation=(
                        "Savings assume the same storage volume with the Standard-IA pricing tier. "
                        "Access charges and retrieval patterns should be reviewed before adopting."
                    ),
                )
            )

        if (
            scenario.lambda_rightsized_cost is not None
            and scenario.lambda_rightsized_cost < scenario.current_cost
        ):
            savings = quantize_money(
                scenario.current_cost - scenario.lambda_rightsized_cost
            )
            recommendations.append(
                Recommendation(
                    type="cost_optimization",
                    suggestion="Right-size Lambda memory allocation",
                    estimated_savings=savings,
                    risk_level="medium",
                    explanation=(
                        "The projection keeps request volume and execution time constant while "
                        "reducing allocated memory to a lower operational baseline."
                    ),
                )
            )

        return sorted(
            recommendations,
            key=lambda item: Decimal(item.estimated_savings),
            reverse=True,
        )

