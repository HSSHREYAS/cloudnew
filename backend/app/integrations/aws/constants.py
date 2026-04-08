from app.core.exceptions import InvalidInputError

AWS_SERVICE_CODES = {
    "EC2": "AmazonEC2",
    "S3": "AmazonS3",
    "Lambda": "AWSLambda",
}

REGION_TO_LOCATION = {
    "us-east-1": "US East (N. Virginia)",
    "us-east-2": "US East (Ohio)",
    "us-west-1": "US West (N. California)",
    "us-west-2": "US West (Oregon)",
    "af-south-1": "Africa (Cape Town)",
    "ap-east-1": "Asia Pacific (Hong Kong)",
    "ap-south-1": "Asia Pacific (Mumbai)",
    "ap-south-2": "Asia Pacific (Hyderabad)",
    "ap-southeast-1": "Asia Pacific (Singapore)",
    "ap-southeast-2": "Asia Pacific (Sydney)",
    "ap-southeast-3": "Asia Pacific (Jakarta)",
    "ap-southeast-4": "Asia Pacific (Melbourne)",
    "ap-northeast-1": "Asia Pacific (Tokyo)",
    "ap-northeast-2": "Asia Pacific (Seoul)",
    "ap-northeast-3": "Asia Pacific (Osaka)",
    "ca-central-1": "Canada (Central)",
    "ca-west-1": "Canada West (Calgary)",
    "eu-central-1": "EU (Frankfurt)",
    "eu-central-2": "Europe (Zurich)",
    "eu-west-1": "EU (Ireland)",
    "eu-west-2": "EU (London)",
    "eu-west-3": "EU (Paris)",
    "eu-north-1": "EU (Stockholm)",
    "eu-south-1": "Europe (Milan)",
    "eu-south-2": "Europe (Spain)",
    "il-central-1": "Israel (Tel Aviv)",
    "me-south-1": "Middle East (Bahrain)",
    "me-central-1": "Middle East (UAE)",
    "sa-east-1": "South America (Sao Paulo)",
}

EC2_OS_PRICING_ATTRIBUTES = {
    "Linux": {
        "pricing_operating_system": "Linux",
        "spot_product_description": "Linux/UNIX",
    },
    "Windows": {
        "pricing_operating_system": "Windows",
        "spot_product_description": "Windows",
    },
}

S3_STORAGE_CLASS_TO_VOLUME_TYPE = {
    "Standard": "Standard",
    "StandardIA": "Standard - Infrequent Access",
    "IntelligentTiering": "Intelligent-Tiering",
    "OneZoneIA": "One Zone - Infrequent Access",
}


def get_location_for_region(region: str) -> str:
    try:
        return REGION_TO_LOCATION[region]
    except KeyError as exc:
        raise InvalidInputError(f"Unsupported AWS region: {region}") from exc

