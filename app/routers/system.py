from fastapi import APIRouter
from app.core.response import base_success

router = APIRouter()

@router.get("/health")
def health():
    return base_success({"status": "ok"})
