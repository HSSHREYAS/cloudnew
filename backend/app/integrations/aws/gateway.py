from __future__ import annotations

from app.core.config import Settings
from app.integrations.aws.clients import AwsClientFactory, PriceListApiClient, SpotPriceHistoryClient
from app.integrations.aws.mappers import AwsPricingFilterBuilder
from app.integrations.aws.parser import AwsPriceListParser
from app.services.contracts import EC2PricingContext, LambdaPriceBundle, LambdaPricingContext, NormalizedPrice, S3PricingContext


class AwsPricingGateway:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client_factory = AwsClientFactory(settings)
        self._catalog_client = PriceListApiClient(settings, self._client_factory)
        self._spot_client = SpotPriceHistoryClient(settings, self._client_factory)
        self._filter_builder = AwsPricingFilterBuilder()
        self._parser = AwsPriceListParser()

    def fetch_ec2_price(self, context: EC2PricingContext) -> NormalizedPrice:
        if context.pricing_model == "Spot":
            spot_product_description = self._filter_builder.get_spot_product_description(
                context.operating_system
            )
            history = self._spot_client.get_spot_price_history(
                region=context.region,
                instance_type=context.instance_type,
                product_description=spot_product_description,
            )
            return self._parser.parse_spot_price_history(
                history=history,
                region=context.region,
                instance_type=context.instance_type,
                operating_system=context.operating_system,
            )

        service_code, filters = self._filter_builder.build_ec2_filters(context)
        documents = self._catalog_client.get_products(service_code, filters)
        return self._parser.parse_ec2_catalog_price(documents, context)

    def fetch_s3_price(self, context: S3PricingContext) -> NormalizedPrice:
        service_code, filters = self._filter_builder.build_s3_filters(context)
        documents = self._catalog_client.get_products(service_code, filters)
        return self._parser.parse_s3_storage_price(documents, context.region)

    def fetch_lambda_prices(self, context: LambdaPricingContext) -> LambdaPriceBundle:
        service_code, filters = self._filter_builder.build_lambda_filters(context)
        documents = self._catalog_client.get_products(service_code, filters)
        return self._parser.parse_lambda_prices(documents, context.region)

