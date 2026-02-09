import os
import tempfile

SECRET_KEY = "test-secret"
TEST_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
DEBUG = True
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.admin",
    "django.contrib.staticfiles",
    "preupload",
]
ROOT_URLCONF = "preupload.tests.urls"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [TEST_TEMPLATES_DIR],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
PREUPLOAD = {
    "TTL_MINUTES": 60,
    "MAX_UPLOAD_SIZE": 1024 * 1024,
}
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = tempfile.mkdtemp(prefix="preupload_test_static_")
MEDIA_URL = "/media/"
MEDIA_ROOT = tempfile.mkdtemp(prefix="preupload_test_")
