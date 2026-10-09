from PIL import Image
from PIL import ImageFilter


def upgrade_image_quality(image: Image.Image, scale: int = 2) -> Image.Image:
    """Upscale an image and soften resampling artefacts around its edges.

    Upscaling cannot recreate details that are absent from the source image,
    but Lanczos resampling combined with a restrained unsharp mask improves
    the appearance of rotated, low-resolution photos.
    """
    if scale < 1:
        raise ValueError("scale must be greater than or equal to 1")

    if scale == 1:
        return image.copy()

    upscaled = image.resize(
        (image.width * scale, image.height * scale),
        resample=Image.Resampling.LANCZOS,
    )
    return upscaled.filter(
        ImageFilter.UnsharpMask(radius=1.0, percent=110, threshold=3)
    )
    