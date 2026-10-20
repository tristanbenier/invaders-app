import uuid
from io import BytesIO

from django.core.files.base import ContentFile
from django.utils.deconstruct import deconstructible
from PIL import Image, ImageOps

# Images are square: the app crops them before upload, the server enforces it.
MAX_SIZE = 1200
JPEG_QUALITY = 85


@deconstructible
class UploadTo:
    """Random file name in the given folder (images are always stored as JPEG)."""

    def __init__(self, folder):
        self.folder = folder

    def __call__(self, instance, filename):
        return f"{self.folder}/{uuid.uuid4().hex}.jpg"

    def __eq__(self, other):
        return isinstance(other, UploadTo) and other.folder == self.folder


def normalize_image(uploaded):
    """Apply EXIF rotation, center-crop to a square of at most MAX_SIZE and re-encode as JPEG."""
    with Image.open(uploaded) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        size = min(*image.size, MAX_SIZE)
        image = ImageOps.fit(image, (size, size), method=Image.Resampling.LANCZOS)
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return ContentFile(buffer.getvalue(), name="image.jpg")
