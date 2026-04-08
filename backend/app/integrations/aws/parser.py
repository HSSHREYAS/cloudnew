from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from app.core.exceptions import PricingApiError
from app.services.contracts import EC2PricingContext, LambdaPriceBundle, NormalizedPrice


class AwsPriceListParser:
    def _decimal(self, value: str | int | float | Decimal) -> Decimal:
        return Decimal(str(value))

    def _build_normalized_price(
        self,
        *,
        service: str,
        region: str,
        source: str,
        product: dict,
        price_dimension: dict,
        description: str,
        effective_date: str | None = None,
    ) -> NormalizedPrice:
        currency, amount = next(iter(price_dimension["pricePerUnit"].items()))
        return NormalizedPrice(
            service=service,
            region=region,
            currency=currency,
            unit_price=self._decimal(amount),
            unit=price_dimension.get("unit", "Count"),
            source=source,
            description=description,
            attributes=product.get("attributes", {}),
            sku=product.get("sku"),
            usage_type=product.get("attributes", {}).get("usagetype"),
            effective_date=effective_date,
        )

    def _iter_dimensions(self, documents: list[dict], term_name: str):
        for document in documents:
            product = document.get("product", {})
            terms = document.get("terms", {}).get(term_name, {})
            for term in terms.values():
                for dimension in term.get("priceDimensions", {}).values():
                    yield product, term, dimension

    def parse_ec2_catalog_price(
        self,
        documents: list[dict],
        context: EC2PricingContext,
    ) -> NormalizedPrice:
        if context.pricing_model == "OnDemand":
            for product, term, dimension in self._iter_dimensions(documents, "OnDemand"):
                unit = dimension.get("unit", "").lower()
                if unit in {"hrs", "hours", "hour"}:
                    return self._build_normalized_price(
                        service="EC2",
                        region=context.region,
                        source="aws_pricing_api",
                        product=product,
                        price_dimension=dimension,
                        description=dimension.get("description", "EC2 on-demand hourly rate"),
                        effective_date=term.get("effectiveDate"),
                    )
        elif context.pricing_model == "Reserved":
            preferred_terms = []
            fallback_terms = []
            for product, term, dimension in self._iter_dimensions(documents, "Reserved"):
                unit = dimension.get("unit", "").lower()
                if unit not in {"hrs", "hours", "hour"}:
                    continue
                attributes = term.get("termAttributes", {})
                term_record = (product, term, dimension)
                if (
                    attributes.get("LeaseContractLength") == "1yr"
                    and attributes.get("PurchaseOption") == "No Upfront"
                    and attributes.get("OfferingClass", "").lower() == "standard"
                ):
                    preferred_terms.append(term_record)
                fallback_terms.append(term_record)
            selected = preferred_terms[0] if preferred_terms else (fallback_terms[0] if fallback_terms else None)
            if selected:
                product, term, dimension = selected
                return self._build_normalized_price(
                    service="EC2",
                    region=context.region,
                    source="aws_pricing_api",
                    product=product,
                    price_dimension=dimension,
                    description=(
                        "EC2 reserved hourly rate using the default 1-year standard no-upfront term"
                    ),
                    effective_date=term.get("effectiveDate"),
                )

        raise PricingApiError(
            f"Unable to parse {context.pricing_model} EC2 pricing for {context.instance_type}"
        )

    def parse_s3_storage_price(self, documents: list[dict], region: str) -> NormalizedPrice:
        for product, term, dimension in self._iter_dimensions(documents, "OnDemand"):
            unit = dimension.get("unit", "").lower()
            if unit in {"gb-mo", "gb-month", "gb/mo"}:
                return self._build_normalized_price(
                    service="S3",
                    region=region,
                    source="aws_pricing_api",
                    product=product,
                    price_dimension=dimension,
                    description=dimension.get("description", "Amazon S3 storage price per GB-month"),
                    effective_date=term.get("effectiveDate"),
                )
        raise PricingApiError("Unable to parse S3 storage pricing from AWS response")

    def parse_lambda_prices(self, documents: list[dict], region: str) -> LambdaPriceBundle:
        request_price: NormalizedPrice | None = None
        compute_price: NormalizedPrice | None = None

        for product, term, dimension in self._iter_dimensions(documents, "OnDemand"):
            description = dimension.get("description", "").lower()
            unit = dimension.get("unit", "").lower()
            normalized = self._build_normalized_price(
                service="Lambda",
                region=region,
                source="aws_pricing_api",
                product=product,
                price_dimension=dimension,
                description=dimension.get("description", "AWS Lambda pricing dimension"),
                effective_date=term.get("effectiveDate"),
            )
            if request_price is None and unit in {"requests", "request"}:
                request_price = normalized
            elif compute_price is None and ("gb-second" in unit or "gb-second" in description):
                compute_price = normalized

            if request_price and compute_price:
                break

        if request_price is None or compute_price is None:
            raise PricingApiError("Unable to parse Lambda request and compute pricing")
        return LambdaPriceBundle(request_price=request_price, compute_price=compute_price)

    def parse_spot_price_history(
        self,
        history: list[dict],
        region: str,
        instance_type: str,
        operating_system: str,
    ) -> NormalizedPrice:
        latest_by_zone: dict[str, tuple[datetime, Decimal]] = defaultdict(
            lambda: (datetime.min, Decimal("0"))
        )

        for item in history:
            timestamp = item["Timestamp"]
            zone = item["AvailabilityZone"]
            price = self._decimal(item["SpotPrice"])
            previous_timestamp, _ = latest_by_zone[zone]
            if timestamp.replace(tzinfo=None) > previous_timestamp:
                latest_by_zone[zone] = (timestamp.replace(tzinfo=None), price)

        if not latest_by_zone:
            raise PricingApiError("Unable to derive EC2 Spot pricing from AWS history")

        zone_prices = [price for _, price in latest_by_zone.values()]
        average_price = sum(zone_prices) / Decimal(len(zone_prices))
        return NormalizedPrice(
            service="EC2",
            region=region,
            currency="USD",
            unit_price=average_price,
            unit="Hrs",
            source="ec2_spot_price_history",
            description=(
                f"Average latest Spot price across {len(zone_prices)} availability zones "
                f"for {instance_type} on {operating_system}"
            ),
            attributes={"instanceType": instance_type, "operatingSystem": operating_system},
            sku=None,
            usage_type=None,
            effective_date=None,
        )

