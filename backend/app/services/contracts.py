from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping


@dataclass(frozen=True)
class EC2PricingContext:
    region: str
    instance_type: str
    operating_system: str
    pricing_model: str


@dataclass(frozen=True)
class S3PricingContext:
    region: str
    storage_class: str


@dataclass(frozen=True)
class LambdaPricingContext:
    region: str


@dataclass(frozen=True)
class NormalizedPrice:
    service: str
    region: str
    currency: str
    unit_price: Decimal
    unit: str
    source: str
    description: str
    attributes: Mapping[str, Any]
    sku: str | None
    usage_type: str | None
    effective_date: str | None


@dataclass(frozen=True)
class LambdaPriceBundle:
    request_price: NormalizedPrice
    compute_price: NormalizedPrice


@dataclass(frozen=True)
class BreakdownLine:
    label: str
    quantity: Decimal
    unit: str
    rate: Decimal
    amount: Decimal
    description: str


@dataclass(frozen=True)
class EstimateOutcome:
    service: str
    region: str
    total_cost: Decimal
    currency: str
    breakdown: list[BreakdownLine]
    metadata: Mapping[str, Any]


@dataclass(frozen=True)
class RegionalOption:
    region: str
    projected_cost: Decimal
    explanation: str


@dataclass(frozen=True)
class RecommendationScenario:
    service: str
    region: str
    current_cost: Decimal
    duration_hours: Decimal | None
    configuration: Mapping[str, Any]
    reserved_cost: Decimal | None = None
    spot_cost: Decimal | None = None
    cheaper_region: RegionalOption | None = None
    cheaper_storage_class_cost: Decimal | None = None
    lambda_rightsized_cost: Decimal | None = None


@dataclass(frozen=True)
class Recommendation:
    type: str
    suggestion: str
    estimated_savings: Decimal
    risk_level: str
    explanation: str

