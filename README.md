# django-preupload

A reusable Django mini-app that preserves uploaded files across failed form validation by preuploading server-side and resolving them via signed tokens on resubmission.

## Features

- **Preupload**: Files are uploaded immediately to temporary storage and referenced by an opaque token.
- **Validation retries**: Users can fix other form errors without re-uploading; the token resolves to the preuploaded file.
- **Standard Django**: Works with `forms.Form` / `ModelForm` and admin; no frontend framework or multi-step wizard required.
- **Modular**: Storage backend, token lifecycle, form/widget, JS controller, and cleanup are separate and configurable.

## Install

```bash
pip install django-preupload
```

Add `preupload` to `INSTALLED_APPS` and include the app URLs:

```python
# settings.py
INSTALLED_APPS = [
    ...
    "preupload",
]

# urls.py
urlpatterns = [
    ...
    path("preupload/", include("preupload.urls")),
]
```

Run migrations:

```bash
python manage.py migrate preupload
```

## Usage

### Forms

Use `PreuploadFormMixin` (no request needed; widget gets preupload URL from reverse(), CSRF from cookie in JS):

```python
from django import forms
from preupload.forms import PreuploadFormMixin

class MyForm(PreuploadFormMixin, forms.Form):
    file = forms.FileField()

# In the view
form = MyForm(request.POST, request.FILES)
if form.is_valid():
    file = form.cleaned_data["file"]
    # Save to your model or final storage; cleanup_preuploads removes expired records
```

### Admin

Use `PreuploadAdminMixin` on your `ModelAdmin`:

```python
from django.contrib import admin
from preupload.admin import PreuploadAdminMixin

@admin.register(MyModel)
class MyModelAdmin(PreuploadAdminMixin, admin.ModelAdmin):
    pass
```

### Cleanup

Remove expired preuploaded files and records:

```bash
python manage.py cleanup_preuploads
```

Run periodically (e.g. cron). Use `--dry-run` to list what would be removed.

## Development and tests

Use a virtual environment; do not install globally:

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]" "Django>=3.2"
.venv/bin/python -m django test preupload.tests --settings=preupload.tests.settings
```

### CI and releasing

- **Tests:** On push/PR to `main`, [`.github/workflows/test.yml`](.github/workflows/test.yml) runs the test suite and Black across Python 3.8/3.10/3.12 and Django 3.2/4.2/5.0.
- **Test PyPI:** To publish on tag push, add a [Test PyPI](https://test.pypi.org) API token as repo secret `TWINE_PASSWORD`, then push a version tag (e.g. `git tag -a v0.1.0 -m "Release 0.1.0"` and `git push origin v0.1.0`). [`.github/workflows/publish.yml`](.github/workflows/publish.yml) builds and uploads to Test PyPI. Bump `version` in `pyproject.toml` before tagging. For production PyPI, change the workflow to use `twine upload` (no `--repository testpypi`) and use a PyPI token.

## Settings (optional)

Configuration uses a single `PREUPLOAD` dict (similar to Django's `DATABASES` / `CACHES`). [preupload/conf.py](preupload/conf.py) defines defaults, merges with `settings.PREUPLOAD`, and exposes `preupload_config`.

In `settings.py`:

```python
PREUPLOAD = {
    "STORAGE": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {"location": "/tmp/preupload"},  # optional
    },
    "TTL_MINUTES": 60,
    "MAX_UPLOAD_SIZE": 10 * 1024 * 1024,  # optional; default = FILE_UPLOAD_MAX_MEMORY_SIZE
}
```

| Key | Default | Description |
|-----|---------|-------------|
| `STORAGE` | `STORAGES["default"]` | Django storage config (BACKEND + OPTIONS); None = default file storage |
| `TTL_MINUTES` | `60` | Preupload expiry (minutes) |
| `MAX_UPLOAD_SIZE` | `FILE_UPLOAD_MAX_MEMORY_SIZE` | Max size in bytes (Django default 2.5 MB) |

## Security

- Tokens are signed (Django `Signer`); resolution validates signature and expiry (created_at + TTL from settings).
- Possession of the token is sufficient to resolve; no raw storage paths are exposed.

## License

BSD-3-Clause
