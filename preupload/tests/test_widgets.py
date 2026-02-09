from django.test import TestCase

from preupload.widgets import PreuploadFileWidget


class PreuploadFileWidgetTestCase(TestCase):
    def test_value_from_datadict_returns_token(self):
        widget = PreuploadFileWidget()
        value = widget.value_from_datadict(
            data={"myfile_token": "signed-token"},
            files={},
            name="myfile",
        )
        self.assertEqual(value, "signed-token")

    def test_value_from_datadict_missing_returns_empty(self):
        widget = PreuploadFileWidget()
        value = widget.value_from_datadict(
            data={},
            files={},
            name="myfile",
        )
        self.assertEqual(value, "")

    def test_value_omitted_from_data_when_token_present(self):
        widget = PreuploadFileWidget()
        omitted = widget.value_omitted_from_data(
            data={"myfile_token": "x"},
            files={},
            name="myfile",
        )
        self.assertFalse(omitted)

    def test_value_omitted_from_data_when_file_present(self):
        widget = PreuploadFileWidget()
        omitted = widget.value_omitted_from_data(
            data={},
            files={"myfile": object()},
            name="myfile",
        )
        self.assertFalse(omitted)

    def test_value_omitted_from_data_when_neither_present(self):
        widget = PreuploadFileWidget()
        omitted = widget.value_omitted_from_data(
            data={},
            files={},
            name="myfile",
        )
        self.assertTrue(omitted)
