from app.core.exceptions import InvalidInputError
from app.integrations.aws.constants import (
    AWS_SERVICE_CODES,
    EC2_OS_PRICING_ATTRIBUTES,
    S3_STORAGE_CLASS_TO_VOLUME_TYPE,
    get_location_for_region,
)
from app.services.contracts import EC2PricingContext, LambdaPricingContext, S3PricingContext


class AwsPricingFilterBuilder:
    @staticmethod
    def _term_match(field: str, value: str) -> dict[str, str]:
        return {"Type": "TERM_MATCH", "Field": field, "Value": value}

    def build_ec2_filters(self, context: EC2PricingContext) -> tuple[str, list[dict[str, str]]]:
        os_attributes = EC2_OS_PRICING_ATTRIBUTES[context.operating_system]
        filters = [
            self._term_match("instanceType", context.instance_type),
            self._term_match("location", get_location_for_region(context.region)),
            self._term_match("operatingSystem", os_attributes["pricing_operating_system"]),
            self._term_match("tenancy", "Shared"),
            self._term_match("capacitystatus", "Used"),
            self._term_match("preInstalledSw", "NA"),
        ]
        return AWS_SERVICE_CODES["EC2"], filters

    def build_s3_filters(self, context: S3PricingContext) -> tuple[str, list[dict[str, str]]]:
        try:
            volume_type = S3_STORAGE_CLASS_TO_VOLUME_TYPE[context.storage_class]
        except KeyError as exc:
            raise InvalidInputError(
                f"Unsupported S3 storage class: {context.storage_class}"
            ) from exc

        filters = [
            self._term_match("location", get_location_for_region(context.region)),
            self._term_match("volumeType", volume_type),
        ]
        return AWS_SERVICE_CODES["S3"], filters

    def build_lambda_filters(
        self,
        context: LambdaPricingContext,
    ) -> tuple[str, list[dict[str, str]]]:
        filters = [self._term_match("location", get_location_for_region(context.region))]
        return AWS_SERVICE_CODES["Lambda"], filters

    def get_spot_product_description(self, operating_system: str) -> str:
        try:
            return EC2_OS_PRICING_ATTRIBUTES[operating_system]["spot_product_description"]
        except KeyError as exc:
            raise InvalidInputError(
                f"Unsupported EC2 operating system: {operating_system}"
            ) from exc

