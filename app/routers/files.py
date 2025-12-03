import shutil
import os
import uuid
from fastapi import APIRouter, UploadFile, File, Request, Depends
from app.core.response import base_success, BaseHTTPException, ErrorCodes
from app.core.i18n import get_lang
from app.core.deps import admin_required
from app.db.models.user import User
from app.schemas.file import FileResponse
from app.schemas.base import BaseResponse

router = APIRouter()

UPLOAD_DIR = "app/static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/images", response_model=BaseResponse[FileResponse])
def upload_image(
    file: UploadFile = File(...),
    request: Request = None,
    _: User = Depends(admin_required),
):
    if not file.content_type.startswith("image/"):
        raise BaseHTTPException(400, ErrorCodes.VALIDATION_ERROR, "File must be an image")

    extension = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{extension}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Construct URL
    # Assuming the app is served at root or we can get base_url from request
    base_url = str(request.base_url).rstrip("/")
    image_url = f"{base_url}/static/uploads/{filename}"

    return base_success(
        FileResponse(image_url=image_url),
        lang=get_lang(request),
    )
