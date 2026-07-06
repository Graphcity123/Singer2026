from django.conf import settings


def image_base(request):
    """Expose IMAGE_BASE_URL as `image_base` in all templates."""
    return {"image_base": settings.IMAGE_BASE_URL}
