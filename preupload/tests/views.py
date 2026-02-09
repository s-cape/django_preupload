"""Minimal view for integration test: form with preupload widget."""

from django import forms
from django.shortcuts import render

from preupload.forms import PreuploadFormMixin


class TestForm(PreuploadFormMixin, forms.Form):
    title = forms.CharField(required=True, max_length=100)
    file = forms.FileField(required=True)


def form_page(request):
    if request.method == "POST":
        form = TestForm(request.POST, request.FILES)
        if form.is_valid():
            f = form.cleaned_data["file"]
            return render(
                request,
                "preupload_tests/success.html",
                {"filename": f.name, "size": len(f.read())},
            )
    else:
        form = TestForm()
    return render(request, "preupload_tests/form.html", {"form": form})
