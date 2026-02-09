"""Preupload endpoint: accept POST file, store it, return signed token."""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .conf import preupload_config
from .models import Preupload
from .storage import storage
from . import tokens


@require_http_methods(["POST"])
def preupload(request):
    """POST one file; validate size, store, create Preupload, return token."""
    file = next(iter(request.FILES.values()), None) if request.FILES else None
    if not file:
        return JsonResponse({"error": "No file uploaded"}, status=400)
    if file.size > preupload_config["MAX_UPLOAD_SIZE"]:
        return JsonResponse(
            {
                "error": "File too large",
                "max_size": preupload_config["MAX_UPLOAD_SIZE"],
            },
            status=413,
        )
    try:
        storage_ref = storage.save(file, name=file.name)
    except Exception:
        return JsonResponse({"error": "Storage failed"}, status=500)
    original_filename = file.name or "upload"
    preupload = Preupload(storage_ref=storage_ref, original_filename=original_filename)
    preupload.save()
    preupload.token = tokens.generate_token(preupload)
    preupload.save(update_fields=["token"])
    return JsonResponse(
        {"token": preupload.token, "original_filename": original_filename}
    )
