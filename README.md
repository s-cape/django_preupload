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

Requires Python 3.8+ and Django 3.2+. Add `preupload` to `INSTALLED_APPS` and include the app URLs:

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

Use `PreuploadFormMixin` (no request needed):

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

Include `{{ form.media }}` in your form template so the preupload script loads. The file is only provided via the token on submit (not re-uploaded with the form).

### Model fields

For models, use `PreuploadFileModelField` or `PreuploadImageModelField` instead of `FileField` / `ImageField`. The ModelForm then gets preupload behaviour without needing the mixin (form field is `PreuploadFileField` or `PreuploadImageField` with `_preupload_name` set).

```python
from django.db import models
from preupload.model_fields import PreuploadFileModelField, PreuploadImageModelField

class Document(models.Model):
    title = models.CharField(max_length=100)
    file = PreuploadFileModelField(upload_to="docs/")
    thumb = PreuploadImageModelField(upload_to="thumbs/", blank=True)
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

### Customizing the “please wait” message

To replace the default “please wait” alert (e.g. with a modal or toast), define `window.preuploadWarn` **before** the preupload script runs. Callback receives `{ form, widgets }`.

```html
<script>
  window.preuploadWarn = function (ctx) {
    // ctx.form, ctx.widgets
    myToast("Please wait for the upload to finish.");
  };
</script>
{{ form.media }}
```

## Development and tests

Use a virtual environment; do not install globally:

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]" "Django>=3.2"
.venv/bin/python -m django test preupload.tests --settings=preupload.tests.settings
```

### CI and releasing

- **Tests:** On push/PR to `main`, [`.github/workflows/test.yml`](.github/workflows/test.yml) runs the test suite and Black across Python 3.8/3.10/3.12 and Django 3.2/4.2/5.0. A separate **integration** job runs one Playwright test (form page, file select, token set via JS). To run the integration test locally: `pip install playwright`, `playwright install chromium`, then `python -m django test preupload.tests.test_integration --settings=preupload.tests.settings --tag=integration`.
- **Test PyPI:** To publish on tag push, add a [Test PyPI](https://test.pypi.org) API token as repo secret `TWINE_PASSWORD`, then push a version tag (e.g. `git tag -a v0.1.0 -m "Release 0.1.0"` and `git push origin v0.1.0`). [`.github/workflows/publish.yml`](.github/workflows/publish.yml) builds and uploads to Test PyPI. Bump `version` in `pyproject.toml` before tagging. For production PyPI, change the workflow to use `twine upload` (no `--repository testpypi`) and use a PyPI token.

## Settings (optional)

Optional configuration via a `PREUPLOAD` dict in `settings.py`:

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

- **Tokens:** Signed with Django’s `Signer` (uses `SECRET_KEY`). Resolution validates signature and expiry (created_at + TTL). Possession of the token is sufficient to resolve; no storage paths are exposed in responses.
- **CSRF:** The preupload endpoint is protected by Django’s `CsrfViewMiddleware`; the JS sends the CSRF token (from the form or cookie).
- **Upload path:** Stored files use a UUID-only path; no user-supplied name or extension is used, so path traversal is not possible.
- **Size:** Uploads are rejected above `MAX_UPLOAD_SIZE` before any file is written.
- **Server errors:** The preupload view returns a generic “Storage failed” message on 500; exception details are not sent to the client.

**Deployer considerations:**

- **Authorization:** The preupload view does not require login. If only authenticated users should upload, wrap the preupload URL (e.g. `@login_required` or URL middleware).
- **Rate limiting:** There is no built-in rate limiting. Consider limiting requests to the preupload path (e.g. django-ratelimit or reverse proxy) to avoid storage abuse.
- **Content validation:** File type or content is not validated at upload. Add validation in your form’s `clean()` or in a custom view if you need allowlists (e.g. images only).
- **SECRET_KEY:** Rotating `SECRET_KEY` invalidates all existing preupload tokens; users will need to re-upload.

## License

BSD-3-Clause
