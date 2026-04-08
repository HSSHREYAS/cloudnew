from datetime import UTC, datetime
from decimal import Decimal

from app.integrations.aws.mappers import AwsPricingFilterBuilder
from app.integrations.aws.parser import AwsPriceListParser
from app.services.contracts import EC2PricingContext


def test_ec2_filter_builder_maps_region_and_attributes():
    builder = AwsPricingFilterBuilder()
    service_code, filters = builder.build_ec2_filters(
        EC2PricingContext(
            region="us-east-1",
            instance_type="t3.micro",
            operating_system="Linux",
            pricing_model="OnDemand",
        )
    )

    assert service_code == "AmazonEC2"
    assert {"Type": "TERM_MATCH", "Field": "location", "Value": "US East (N. Virginia)"} in filters
    assert {"Type": "TERM_MATCH", "Field": "instanceType", "Value": "t3.micro"} in filters


def test_parser_selects_reserved_hourly_price_with_expected_term():
    parser = AwsPriceListParser()
    documents = [
        {
            "product": {"sku": "sku-1", "attributes": {"usagetype": "BoxUsage:t3.micro"}},
            "terms": {
                "Reserved": {
                    "term-1": {
                        "effectiveDate": "2026-01-01T00:00:00Z",
                        "termAttributes": {
                            "LeaseContractLength": "1yr",
                            "PurchaseOption": "No Upfront",
                            "OfferingClass": "standard",
                        },
                        "priceDimensions": {
                            "rate-1": {
                                "unit": "Hrs",
                                "description": "Reserved hourly price",
                                "pricePerUnit": {"USD": "0.008"},
                            }
                        },
                    }
                }
            },
        }
    ]

    price = parser.parse_ec2_catalog_price(
        documents,
        EC2PricingContext(
            region="us-east-1",
            instance_type="t3.micro",
            operating_system="Linux",
            pricing_model="Reserved",
        ),
    )

    assert price.unit_price == Decimal("0.008")


def test_parser_averages_latest_spot_price_by_zone():
    parser = AwsPriceListParser()
    history = [
        {
            "Timestamp": datetime(2026, 4, 9, 10, 0, tzinfo=UTC),
            "AvailabilityZone": "us-east-1a",
            "SpotPrice": "0.0042",
        },
        {
            "Timestamp": datetime(2026, 4, 9, 10, 5, tzinfo=UTC),
            "AvailabilityZone": "us-east-1b",
            "SpotPrice": "0.0048",
        },
    ]

    price = parser.parse_spot_price_history(history, "us-east-1", "t3.micro", "Linux")

    assert price.unit_price == Decimal("0.0045")

