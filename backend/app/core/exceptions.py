class AppException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: object | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


class InvalidInputError(AppException):
    def __init__(self, message: str, details: object | None = None) -> None:
        super().__init__(
            code="INVALID_INPUT",
            message=message,
            status_code=422,
            details=details,
        )


class AuthenticationError(AppException):
    def __init__(
        self,
        code: str,
        message: str,
        details: object | None = None,
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            status_code=401,
            details=details,
        )


class PricingApiError(AppException):
    def __init__(self, message: str, details: object | None = None) -> None:
        super().__init__(
            code="PRICING_API_ERROR",
            message=message,
            status_code=502,
            details=details,
        )

