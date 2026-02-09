"""Browser integration tests: preupload widget + JS + endpoint."""

import os
import tempfile

from django.test import LiveServerTestCase, tag

from preupload import tokens

# Coerce path to str for Django FSFilesHandler._should_handle (PATH_INFO can be bytes)
from django.test.testcases import FSFilesHandler

_original_should_handle = FSFilesHandler._should_handle


def _should_handle_str(self, path):
    if isinstance(path, bytes):
        path = path.decode("utf-8")
    base_path = self.base_url.path
    if isinstance(base_path, bytes):
        base_path = base_path.decode("utf-8")
    return path.startswith(base_path) and not self.base_url.netloc


FSFilesHandler._should_handle = _should_handle_str


def _skip_if_no_playwright():
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except ImportError:
        return True
    return False


def _launch_browser(playwright):
    """Launch chromium; skip test if browser not installed (e.g. playwright install not run)."""
    try:
        return playwright.chromium.launch()
    except Exception as e:
        if "Executable doesn't exist" in str(e) or "browser" in str(e).lower():
            return None
        raise


@tag("integration")
class PreuploadIntegrationTestCase(LiveServerTestCase):
    """Form page, file select, token, validation, submit block, success, 413."""

    @classmethod
    def setUpClass(cls):
        from django.core import management

        management.call_command("collectstatic", "--noinput", verbosity=0)
        super().setUpClass()

    def _new_page(self, playwright):
        browser = _launch_browser(playwright)
        if browser is None:
            self.skipTest("playwright browsers not installed (run: playwright install chromium)")
        return browser.new_page(), browser

    def test_js_sets_token_after_file_select(self):
        if _skip_if_no_playwright():
            self.skipTest("playwright not installed")

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="wb") as f:
            f.write(b"integration test file")
            path = f.name
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                page, browser = self._new_page(p)
                page.goto(self.live_server_url + "/form/")
                page.set_input_files('input[type="file"]', path)
                page.wait_for_selector(
                    '[data-preupload-state="ready"]',
                    timeout=10000,
                )
                token_value = page.input_value('input[name="file_token"]')
                browser.close()
            self.assertTrue(len(token_value) > 0)
            preupload = tokens.resolve_preupload_token(token_value)
            self.assertIsNotNone(preupload)
            self.assertEqual(preupload.original_filename, os.path.basename(path))
        finally:
            os.unlink(path)

    def test_validation_error_preserves_token(self):
        if _skip_if_no_playwright():
            self.skipTest("playwright not installed")

        from playwright.sync_api import sync_playwright

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="wb") as f:
            f.write(b"validation test file")
            path = f.name
        try:
            with sync_playwright() as p:
                page, browser = self._new_page(p)
                page.goto(self.live_server_url + "/form/")
                page.set_input_files('input[type="file"]', path)
                page.wait_for_selector(
                    '[data-preupload-state="ready"]',
                    timeout=10000,
                )
                token_before = page.input_value('input[name="file_token"]')
                self.assertTrue(len(token_before) > 0)
                page.click('button[type="submit"]')
                page.wait_for_load_state("networkidle")
                token_after = page.input_value('input[name="file_token"]')
                self.assertEqual(token_before, token_after)
                self.assertIn("This field is required", page.content())
                browser.close()
        finally:
            os.unlink(path)

    def test_submit_blocked_while_uploading(self):
        if _skip_if_no_playwright():
            self.skipTest("playwright not installed")

        from playwright.sync_api import sync_playwright

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="wb") as f:
            f.write(b"x" * (1024 * 1024))
            path = f.name
        try:
            with sync_playwright() as p:
                page, browser = self._new_page(p)
                dialog_seen = []
                preupload_resolve = []

                def on_dialog(dialog):
                    dialog_seen.append(dialog.message)
                    dialog.accept()

                page.on("dialog", on_dialog)
                page.goto(self.live_server_url + "/form/")
                page.route(
                    "**/preupload/preupload/",
                    lambda route: preupload_resolve.append(route),
                )
                page.set_input_files('input[type="file"]', path)
                page.wait_for_selector(
                    '[data-preupload-state="uploading"]',
                    timeout=3000,
                )
                page.click('button[type="submit"]')
                self.assertTrue(
                    dialog_seen,
                    "Expected 'please wait' dialog when submitting while upload in progress",
                )
                self.assertIn("wait", dialog_seen[0].lower())
                for route in preupload_resolve:
                    route.continue_()
                page.wait_for_selector(
                    '[data-preupload-state="ready"], [data-preupload-state="error"]',
                    timeout=15000,
                )
                browser.close()
        finally:
            os.unlink(path)

    def test_full_submit_success(self):
        if _skip_if_no_playwright():
            self.skipTest("playwright not installed")

        from playwright.sync_api import sync_playwright

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="wb") as f:
            f.write(b"full success file content")
            path = f.name
        try:
            with sync_playwright() as p:
                page, browser = self._new_page(p)
                page.goto(self.live_server_url + "/form/")
                page.fill('input[name="title"]', "My title")
                page.set_input_files('input[type="file"]', path)
                page.wait_for_selector(
                    '[data-preupload-state="ready"]',
                    timeout=10000,
                )
                page.click('button[type="submit"]')
                page.wait_for_selector("#success-message", timeout=10000)
                content = page.text_content("#success-message")
                browser.close()
            self.assertIn(os.path.basename(path), content)
            self.assertIn("25", content)
        finally:
            os.unlink(path)

    def test_upload_too_large_shows_error(self):
        if _skip_if_no_playwright():
            self.skipTest("playwright not installed")

        from playwright.sync_api import sync_playwright

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="wb") as f:
            f.write(b"x" * (1024 * 1024 + 1))
            path = f.name
        try:
            with sync_playwright() as p:
                page, browser = self._new_page(p)
                page.goto(self.live_server_url + "/form/")
                page.set_input_files('input[type="file"]', path)
                page.wait_for_selector(
                    '[data-preupload-state="error"]',
                    timeout=10000,
                )
                token_value = page.input_value('input[name="file_token"]')
                browser.close()
            self.assertEqual(token_value, "")
        finally:
            os.unlink(path)
