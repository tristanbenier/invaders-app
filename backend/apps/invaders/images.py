import uuid
import warnings
from io import BytesIO

from django.core.files.base import ContentFile
from django.utils.deconstruct import deconstructible
from PIL import Image, ImageOps

# Images are square: the app crops them before upload, the server enforces it.
MAX_SIZE = 1200
JPEG_QUALITY = 85
# Largest accepted source image: enough for 48 MP phone photos, refuses decompression bombs
# (a small file that would expand to gigabytes of memory once decoded).
MAX_PIXELS = 60_000_000


class InvalidImage(Exception):
    pass


@deconstructible
class UploadTo:
    """Random file name in the given folder (images are always stored as JPEG)."""

    def __init__(self, folder):
        self.folder = folder

    def __call__(self, instance, filename):
        return f"{self.folder}/{uuid.uuid4().hex}.jpg"

    def __eq__(self, other):
        return isinstance(other, UploadTo) and other.folder == self.folder


def normalize_image(uploaded, square=True):
    """Apply EXIF rotation, fit in MAX_SIZE and re-encode as JPEG.

    square=True center-crops to a square (app uploads); False keeps the original
    proportions (bulk import of existing photos).
    """
    with warnings.catch_warnings():
        # Pillow only warns between MAX_IMAGE_PIXELS and twice that: treat it as an error.
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        try:
            return _normalize(uploaded, square)
        except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
            raise InvalidImage("Cette image est trop grande.") from exc
        except OSError as exc:
            raise InvalidImage("Cette image est illisible ou corrompue.") from exc


def _to_rgb(image):
    """JPEG has no transparency: transparent areas become white rather than black."""
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        image = image.convert("RGBA")
        background = Image.new("RGB", image.size, "white")
        background.paste(image, mask=image.getchannel("A"))
        return background
    return image.convert("RGB")


def _normalize(uploaded, square):
    with Image.open(uploaded) as image:
        if image.width * image.height > MAX_PIXELS:
            raise InvalidImage("Cette image est trop grande.")
        # JPEG only: decode at a reduced scale when possible, much faster and lighter.
        image.draft("RGB", (MAX_SIZE * 2, MAX_SIZE * 2))
        image = _to_rgb(ImageOps.exif_transpose(image))
        if square:
            size = min(*image.size, MAX_SIZE)
            image = ImageOps.fit(image, (size, size), method=Image.Resampling.LANCZOS)
        else:
            image.thumbnail((MAX_SIZE, MAX_SIZE), Image.Resampling.LANCZOS)
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return ContentFile(buffer.getvalue(), name="image.jpg")
