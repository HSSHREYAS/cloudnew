from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, object]:
    return {"status": "ok"}
