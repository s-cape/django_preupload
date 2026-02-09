from django.test import TestCase, RequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from django import forms

from preupload.forms import PreuploadFileField, PreuploadFormMixin
from preupload.models import Preupload
from preupload.storage import save as storage_save
from preupload import tokens


class SimpleForm(PreuploadFormMixin, forms.Form):
    file = forms.FileField(required=True)


class FormsTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_form_with_new_file(self):
        request = self.factory.post("/", data={}, format="multipart")
        request.FILES["file"] = SimpleUploadedFile("a.txt", b"content", "text/plain")
        form = SimpleForm(request.POST, request.FILES, request=request)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["file"].read(), b"content")

    def test_form_with_token_resolves_preuploaded_file(self):
        storage_ref = storage_save(__import__("io").BytesIO(b"preuploaded"), name="s.txt")
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

    def test_form_invalid_token_raises_validation_error(self):
        request = self.factory.post("/", data={"file_token": "bad-token"})
        form = SimpleForm(request.POST, request.FILES, request=request)
        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)
