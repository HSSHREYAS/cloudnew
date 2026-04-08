def success_response(data: object) -> dict[str, object]:
    return {
        "status": "success",
        "data": data,
    }


def error_response(
    code: str,
    message: str,
    details: object | None = None,
) -> dict[str, object]:
    error: dict[str, object] = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return {
        "status": "error",
        "error": error,
    }

