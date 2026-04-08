from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from functools import lru_cache

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import Settings
from app.core.exceptions import PricingApiError


class AwsClientFactory:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def _client_config(self) -> Config:
        return Config(
            retries={
                "max_attempts": self._settings.aws_retry_max_attempts,
                "mode": "standard",
            },
            connect_timeout=self._settings.aws_connect_timeout_seconds,
            read_timeout=self._settings.aws_read_timeout_seconds,
        )

    @lru_cache(maxsize=1)
    def pricing_client(self):
        return boto3.client(
            "pricing",
            region_name=self._settings.aws_pricing_region,
            config=self._client_config,
        )

    @lru_cache(maxsize=16)
    def ec2_client(self, region: str):
        return boto3.client("ec2", region_name=region, config=self._client_config)


class PriceListApiClient:
    def __init__(self, settings: Settings, factory: AwsClientFactory) -> None:
        self._settings = settings
        self._factory = factory

    def get_products(self, service_code: str, filters: list[dict[str, str]]) -> list[dict]:
        try:
            client = self._factory.pricing_client()
            next_token: str | None = None
            documents: list[dict] = []
            page_count = 0

            while True:
                page_count += 1
                request_kwargs = {
                    "ServiceCode": service_code,
                    "Filters": filters,
                    "FormatVersion": "aws_v1",
                    "MaxResults": 100,
                }
                if next_token:
                    request_kwargs["NextToken"] = next_token

                response = client.get_products(**request_kwargs)
                documents.extend(json.loads(item) for item in response.get("PriceList", []))
                next_token = response.get("NextToken")

                if not next_token or page_count >= self._settings.aws_max_price_pages:
                    break

            if not documents:
                raise PricingApiError("AWS Pricing API returned no matching products")
            return documents
        except (BotoCoreError, ClientError, ValueError) as exc:
            raise PricingApiError(
                "Failed to fetch catalog pricing from AWS",
                details=str(exc),
            ) from exc


class SpotPriceHistoryClient:
    def __init__(self, settings: Settings, factory: AwsClientFactory) -> None:
        self._settings = settings
        self._factory = factory

    def get_spot_price_history(
        self,
        region: str,
        instance_type: str,
        product_description: str,
    ) -> list[dict]:
        try:
            client = self._factory.ec2_client(region)
            start_time = datetime.now(UTC) - timedelta(hours=self._settings.aws_spot_history_hours)
            next_token: str | None = None
            history: list[dict] = []

            while True:
                request_kwargs = {
                    "InstanceTypes": [instance_type],
                    "ProductDescriptions": [product_description],
                    "StartTime": start_time,
                    "MaxResults": 1000,
                }
                if next_token:
                    request_kwargs["NextToken"] = next_token

                response = client.describe_spot_price_history(**request_kwargs)
                history.extend(response.get("SpotPriceHistory", []))
                next_token = response.get("NextToken")
                if not next_token:
                    break

            if not history:
                raise PricingApiError("AWS EC2 Spot pricing returned no matching history")
            return history
        except (BotoCoreError, ClientError, ValueError) as exc:
            raise PricingApiError(
                "Failed to fetch EC2 Spot pricing from AWS",
                details=str(exc),
            ) from exc

