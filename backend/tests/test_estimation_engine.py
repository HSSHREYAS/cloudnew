from decimal import Decimal

from app.engines.estimation.calculators import CostEstimationEngine
from app.services.contracts import LambdaPriceBundle, NormalizedPrice


def make_price(service: str, unit_price: str, unit: str, region: str = "us-east-1") -> NormalizedPrice:
    return NormalizedPrice(
        service=service,
        region=region,
        currency="USD",
        unit_price=Decimal(unit_price),
        unit=unit,
        source="test",
        description="fixture",
        attributes={},
        sku="fixture",
        usage_type="fixture",
        effective_date=None,
    )


def test_ec2_estimate_is_hourly_rate_times_duration():
    engine = CostEstimationEngine()
    outcome = engine.estimate_ec2(
        price=make_price("EC2", "0.0116", "Hrs"),
        duration_hours=Decimal("100"),
        metadata={},
    )

    assert outcome.total_cost == Decimal("1.160000")


def test_s3_estimate_prorates_gb_month_pricing():
    engine = CostEstimationEngine()
    outcome = engine.estimate_s3(
        price=make_price("S3", "0.023", "GB-Mo"),
        storage_gb=Decimal("500"),
        duration_hours=Decimal("730"),
        metadata={},
    )

    assert outcome.total_cost == Decimal("11.500000")


def test_lambda_estimate_combines_request_and_compute_pricing():
    engine = CostEstimationEngine()
    outcome = engine.estimate_lambda(
        price_bundle=LambdaPriceBundle(
            request_price=make_price("Lambda", "0.0000002", "Requests"),
            compute_price=make_price("Lambda", "0.0000166667", "GB-Seconds"),
        ),
        request_count=Decimal("1000000"),
        execution_duration_ms=Decimal("250"),
        memory_size_mb=Decimal("512"),
        metadata={},
    )

    assert outcome.total_cost == Decimal("2.283338")
