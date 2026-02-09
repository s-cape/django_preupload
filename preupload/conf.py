"""Merge settings.PREUPLOAD with defaults; export preupload_config."""

from django.conf import settings

_DEFAULTS = {
    "STORAGE": None,
    "TTL_MINUTES": 60,
    "MAX_UPLOAD_SIZE": None,
}

_user = getattr(settings, "PREUPLOAD", {})
preupload_config = {**_DEFAULTS, **_user}
if preupload_config.get("MAX_UPLOAD_SIZE") is None:
    preupload_config["MAX_UPLOAD_SIZE"] = getattr(
        settings, "FILE_UPLOAD_MAX_MEMORY_SIZE", 2621440
    )
if preupload_config.get("STORAGE") is None:
    _default = getattr(settings, "STORAGES", {}).get("default")
    preupload_config["STORAGE"] = _default or {
        "BACKEND": getattr(
            settings, "DEFAULT_FILE_STORAGE", "django.core.files.storage.FileSystemStorage"
        ),
        "OPTIONS": {},
    }
