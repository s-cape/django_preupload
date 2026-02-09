from django.test import TestCase, RequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from django import forms

from preupload.forms import PreuploadFileField, PreuploadFormMixin
from preupload.models import Preupload
from preupload.storage import storage
from preupload import tokens


class SimpleForm(PreuploadFormMixin, forms.Form):
    file = forms.FileField(required=True)


class OptionalImageForm(PreuploadFormMixin, forms.Form):
    thumb = forms.ImageField(required=False)


class FormsTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_form_with_only_file_in_files_rejected(self):
        """Preupload is required; direct file upload without token is invalid."""
        request = self.factory.post("/", data={}, format="multipart")
        request.FILES["file"] = SimpleUploadedFile("a.txt", b"content", "text/plain")
        form = SimpleForm(request.POST, request.FILES, request=request)
        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    def test_form_with_token_resolves_preuploaded_file(self):
        storage_ref = storage.save(
            __import__("io").BytesIO(b"preuploaded"), name="s.txt"
        )
        preupload = Preupload.objects.create(
            token=None,
            storage_ref=storage_ref,
            original_filename="s.txt",
        )
        preupload.token = tokens.generate_token(preupload)
        preupload.save(update_fields=["token"])

        request = self.factory.post("/", data={"file_token": preupload.token})
        form = SimpleForm(request.POST, request.FILES, request=request)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["file"].name, "s.txt")
        self.assertEqual(form.cleaned_data["file"].read(), b"preuploaded")

    def test_form_submit_with_token_only_no_file_uploaded(self):
        """File is resolved from token only; form submit must not re-upload the file."""
        content = b"from-preupload-only"
        storage_ref = storage.save(__import__("io").BytesIO(content), name="p.txt")
        preupload = Preupload.objects.create(
            token=None,
            storage_ref=storage_ref,
            original_filename="p.txt",
        )
        preupload.token = tokens.generate_token(preupload)
        preupload.save(update_fields=["token"])

        request = self.factory.post("/", data={"file_token": preupload.token})
        self.assertFalse(request.FILES)
        form = SimpleForm(request.POST, request.FILES, request=request)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["file"].read(), content)
        self.assertEqual(form.cleaned_data["file"].name, "p.txt")

    def test_form_invalid_token_raises_validation_error(self):
        request = self.factory.post("/", data={"file_token": "bad-token"})
        form = SimpleForm(request.POST, request.FILES, request=request)
        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    def test_optional_image_clear_checkbox_clears_token(self):
        """Clear checkbox on PreuploadImageWidget clears the field (token ignored)."""
        storage_ref = storage.save(__import__("io").BytesIO(b"image"), name="img.png")
        preupload = Preupload.objects.create(
            token=None,
            storage_ref=storage_ref,
            original_filename="img.png",
        )
        preupload.token = tokens.generate_token(preupload)
        preupload.save(update_fields=["token"])

        request = self.factory.post(
            "/",
            data={"thumb_token": preupload.token, "thumb-clear": "on"},
        )
        form = OptionalImageForm(request.POST, request.FILES, request=request)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertFalse(form.cleaned_data["thumb"])
