from pydantic import BaseModel

class FileResponse(BaseModel):
    image_url: str
