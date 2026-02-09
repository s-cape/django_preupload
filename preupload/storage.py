"""Preupload storage layer: save/open/delete preuploaded files via Django Storage abstraction."""

import uuid

from django.utils.module_loading import import_string

from .conf import preupload_config

PREFIX = "preupload/"


def get_preupload_storage():
    """Return the configured preupload storage backend."""
    cfg = preupload_config["STORAGE"]
    storage_class = import_string(cfg["BACKEND"])
    opts = cfg.get("OPTIONS") or {}
    return storage_class(**opts)


class PreuploadStorage:
    """Wraps Django Storage for staging files; exposes only storage_ref strings."""

    def __init__(self):
        self._storage = get_preupload_storage()

    def save(self, file, name=None):
        """Save file; return opaque storage_ref."""
        safe_name = (name or getattr(file, "name", None) or "upload")[:200]
        ext = ""
        if "." in safe_name:
            ext = "." + safe_name.rsplit(".", 1)[-1]
        ref = PREFIX + uuid.uuid4().hex + ext
        return self._storage.save(ref, file)

    def open(self, storage_ref):
        """Open preuploaded file by storage_ref; return file-like."""
        return self._storage.open(storage_ref, mode="rb")

    def delete(self, storage_ref):
        """Delete preuploaded file by storage_ref."""
        self._storage.delete(storage_ref)


def save(file, name=None):
    """Save file to preupload storage; return opaque storage_ref."""
    return PreuploadStorage().save(file, name)


def open_file(storage_ref):
    """Open preuploaded file by storage_ref; return file-like."""
    return PreuploadStorage().open(storage_ref)


def delete(storage_ref):
    """Delete preuploaded file by storage_ref."""
    PreuploadStorage().delete(storage_ref)
