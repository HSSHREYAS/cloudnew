from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, PositiveFloat, PositiveInt, field_validator

from app.integrations.aws.constants import REGION_TO_LOCATION


class BaseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EC2Configuration(BaseSchema):
    instance_type: str = Field(min_length=2)
    operating_system: Literal["Linux", "Windows"]
    pricing_model: Literal["OnDemand", "Reserved", "Spot"]


class S3Configuration(BaseSchema):
    storage_gb: PositiveFloat
    storage_class: Literal["Standard", "StandardIA", "IntelligentTiering", "OneZoneIA"]


class LambdaConfiguration(BaseSchema):
    request_count: PositiveInt
    execution_duration_ms: PositiveFloat
    memory_size_mb: PositiveInt

    @field_validator("memory_size_mb")
    @classmethod
    def validate_memory_size(cls, value: int) -> int:
        if value < 128 or value > 10240:
            raise ValueError("memory_size_mb must be between 128 and 10240")
        return value


class EstimateBase(BaseSchema):
    region: str
    duration_hours: PositiveFloat

    @field_validator("region")
    @classmethod
    def validate_region(cls, value: str) -> str:
        if value not in REGION_TO_LOCATION:
            raise ValueError(f"Unsupported AWS region: {value}")
        return value


class EC2EstimateRequest(EstimateBase):
    service: Literal["EC2"]
    configuration: EC2Configuration


class S3EstimateRequest(EstimateBase):
    service: Literal["S3"]
    configuration: S3Configuration


class LambdaEstimateRequest(EstimateBase):
    service: Literal["Lambda"]
    configuration: LambdaConfiguration


EstimateRequest = Annotated[
    EC2EstimateRequest | S3EstimateRequest | LambdaEstimateRequest,
    Field(discriminator="service"),
]


class RecommendationsBase(BaseSchema):
    region: str
    current_cost: PositiveFloat
    duration_hours: PositiveFloat | None = None

    @field_validator("region")
    @classmethod
    def validate_region(cls, value: str) -> str:
        if value not in REGION_TO_LOCATION:
            raise ValueError(f"Unsupported AWS region: {value}")
        return value


class EC2RecommendationsRequest(RecommendationsBase):
    service: Literal["EC2"]
    configuration: EC2Configuration


class S3RecommendationsRequest(RecommendationsBase):
    service: Literal["S3"]
    configuration: S3Configuration


class LambdaRecommendationsRequest(RecommendationsBase):
    service: Literal["Lambda"]
    configuration: LambdaConfiguration


RecommendationsRequest = Annotated[
    EC2RecommendationsRequest | S3RecommendationsRequest | LambdaRecommendationsRequest,
    Field(discriminator="service"),
]


class EC2ComparisonItem(BaseSchema):
    region: str
    configuration: EC2Configuration

    @field_validator("region")
    @classmethod
    def validate_region(cls, value: str) -> str:
        if value not in REGION_TO_LOCATION:
            raise ValueError(f"Unsupported AWS region: {value}")
        return value


class S3ComparisonItem(BaseSchema):
    region: str
    configuration: S3Configuration

    @field_validator("region")
    @classmethod
    def validate_region(cls, value: str) -> str:
        if value not in REGION_TO_LOCATION:
            raise ValueError(f"Unsupported AWS region: {value}")
        return value


class LambdaComparisonItem(BaseSchema):
    region: str
    configuration: LambdaConfiguration

    @field_validator("region")
    @classmethod
    def validate_region(cls, value: str) -> str:
        if value not in REGION_TO_LOCATION:
            raise ValueError(f"Unsupported AWS region: {value}")
        return value


class CompareBase(BaseSchema):
    duration_hours: PositiveFloat


class EC2CompareRequest(CompareBase):
    service: Literal["EC2"]
    comparisons: list[EC2ComparisonItem] = Field(min_length=2)


class S3CompareRequest(CompareBase):
    service: Literal["S3"]
    comparisons: list[S3ComparisonItem] = Field(min_length=2)


class LambdaCompareRequest(CompareBase):
    service: Literal["Lambda"]
    comparisons: list[LambdaComparisonItem] = Field(min_length=2)


CompareRequest = Annotated[
    EC2CompareRequest | S3CompareRequest | LambdaCompareRequest,
    Field(discriminator="service"),
]


class BreakdownItem(BaseSchema):
    label: str
    quantity: float
    unit: str
    rate: float
    amount: float
    description: str


class EstimateResponseData(BaseSchema):
    total_cost: float
    currency: str
    breakdown: list[BreakdownItem]
    metadata: dict[str, Any]


class RecommendationItem(BaseSchema):
    type: str
    suggestion: str
    estimated_savings: float
    risk_level: str
    explanation: str


class RecommendationsResponseData(BaseSchema):
    recommendations: list[RecommendationItem]


class CompareResultItem(EstimateResponseData):
    region: str
    service: str


class CompareResponseData(BaseSchema):
    results: list[CompareResultItem]
    best_option: CompareResultItem

