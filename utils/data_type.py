from pydantic import BaseModel

class ImageOutput(BaseModel):
    image: str = ""
    extra_image: dict = {}
