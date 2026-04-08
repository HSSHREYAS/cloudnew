from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from app.services.contracts import BreakdownLine, EstimateOutcome, LambdaPriceBundle, NormalizedPrice

HOURS_PER_MONTH = Decimal("730")
GB_IN_MB = Decimal("1024")
MS_IN_SECOND = Decimal("1000")
MONEY_QUANTUM = Decimal("0.000001")


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


class CostEstimationEngine:
    def estimate_ec2(
        self,
        price: NormalizedPrice,
        duration_hours: Decimal,
        metadata: dict[str, object],
    ) -> EstimateOutcome:
        total_cost = quantize_money(price.unit_price * duration_hours)
        breakdown = [
            BreakdownLine(
                label="Compute runtime",
                quantity=duration_hours,
                unit="Hours",
                rate=price.unit_price,
                amount=total_cost,
                description=price.description,
            )
        ]
        return EstimateOutcome(
            service="EC2",
            region=price.region,
            total_cost=total_cost,
            currency=price.currency,
            breakdown=breakdown,
            metadata=metadata,
        )

    def estimate_s3(
        self,
        price: NormalizedPrice,
        storage_gb: Decimal,
        duration_hours: Decimal,
        metadata: dict[str, object],
    ) -> EstimateOutcome:
        proration = duration_hours / HOURS_PER_MONTH
        effective_quantity = storage_gb * proration
        total_cost = quantize_money(price.unit_price * effective_quantity)
        breakdown = [
            BreakdownLine(
                label="Storage allocation",
                quantity=storage_gb,
                unit="GB",
                rate=price.unit_price,
                amount=total_cost,
                description=f"{price.description} prorated over {duration_hours} hours",
            )
        ]
        return EstimateOutcome(
            service="S3",
            region=price.region,
            total_cost=total_cost,
            currency=price.currency,
            breakdown=breakdown,
            metadata=metadata | {"proration_factor": float(proration)},
        )

    def estimate_lambda(
        self,
        price_bundle: LambdaPriceBundle,
        request_count: Decimal,
        execution_duration_ms: Decimal,
        memory_size_mb: Decimal,
        metadata: dict[str, object],
    ) -> EstimateOutcome:
        request_cost = quantize_money(price_bundle.request_price.unit_price * request_count)
        compute_gb_seconds = (
            request_count
            * (execution_duration_ms / MS_IN_SECOND)
            * (memory_size_mb / GB_IN_MB)
        )
        compute_cost = quantize_money(price_bundle.compute_price.unit_price * compute_gb_seconds)
        total_cost = quantize_money(request_cost + compute_cost)
        breakdown = [
            BreakdownLine(
                label="Invocation requests",
                quantity=request_count,
                unit="Requests",
                rate=price_bundle.request_price.unit_price,
                amount=request_cost,
                description=price_bundle.request_price.description,
            ),
            BreakdownLine(
                label="Function compute",
                quantity=compute_gb_seconds,
                unit="GB-Seconds",
                rate=price_bundle.compute_price.unit_price,
                amount=compute_cost,
                description=price_bundle.compute_price.description,
            ),
        ]
        return EstimateOutcome(
            service="Lambda",
            region=price_bundle.request_price.region,
            total_cost=total_cost,
            currency=price_bundle.request_price.currency,
            breakdown=breakdown,
            metadata=metadata | {"computed_gb_seconds": float(compute_gb_seconds)},
        )

