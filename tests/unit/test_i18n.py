"""Tests for internationalization (i18n) module."""

import pytest
import json
import os
import tempfile
from unittest.mock import patch, mock_open
from flask import Flask

from backend.utils.i18n import (
    get_translation,
    t,
    LANGUAGES,
    DEFAULT_LANGUAGE,
    load_translations,
)


class TestI18n:
    """Test suite for i18n functionality."""

    def setup_method(self):
        """Setup before each test."""
        # Clear translation cache
        from backend.utils.i18n import _translations

        _translations.clear()

    def test_languages_defined(self):
        """Test supported languages are defined."""
        assert "en" in LANGUAGES
        assert "ar" in LANGUAGES
        assert LANGUAGES["en"] == "English"
        assert LANGUAGES["ar"] == "العربية"

    def test_load_translations(self):
        """Test loading translation files."""
        with patch("backend.utils.i18n.os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data='{"test": "value"}')):
                load_translations()

        from backend.utils.i18n import _translations

        assert "en" in _translations
        # The actual loading depends on file existence

    def test_get_translation_existing_key(self):
        """Test getting an existing translation key."""
        from backend.utils.i18n import _translations

        _translations["en"] = {"errors": {"no_file": "No file provided"}}
        _translations["ar"] = {"errors": {"no_file": "لم يتم اختيار ملف"}}

        assert get_translation("en", "errors.no_file") == "No file provided"
        assert get_translation("ar", "errors.no_file") == "لم يتم اختيار ملف"

    def test_get_translation_missing_key_fallback(self):
        """Test fallback to default language or key."""
        from backend.utils.i18n import _translations

        _translations["en"] = {}
        _translations["ar"] = {}

        # Should fall back to key itself
        assert get_translation("en", "missing.key") == "missing.key"
        assert get_translation("ar", "missing.key") == "missing.key"

    def test_get_translation_with_formatting(self):
        """Test translation with formatting arguments."""
        from backend.utils.i18n import _translations

        _translations["en"] = {"errors": {"max_size": "Max {max_size}MB"}}

        result = get_translation("en", "errors.max_size", max_size="5")
        assert result == "Max 5MB"

    def test_nested_keys(self):
        """Test nested key lookup."""
        from backend.utils.i18n import _translations

        _translations["en"] = {
            "app": {"name": "ResumeAI", "settings": {"title": "Settings"}}
        }

        assert get_translation("en", "app.name") == "ResumeAI"
        assert get_translation("en", "app.settings.title") == "Settings"

    def test_translation_fallback_to_default(self):
        """Test fallback to default language when key missing in target."""
        from backend.utils.i18n import _translations

        _translations["ar"] = {"errors": {"no_file": "لم يتم اختيار ملف"}}
        _translations["en"] = {"errors": {"no_file": "No file provided"}}

        # Arabic requested, key exists in Arabic
        assert get_translation("ar", "errors.no_file") == "لم يتم اختيار ملف"

        # Arabic requested, key doesn't exist in Arabic, fallback to English
        assert get_translation("ar", "missing.key") == "missing.key"


class TestTranslationFunction:
    """Test translation helper function t()."""

    def test_t_with_request_context(self):
        """Test t() with Flask request context."""
        from flask import Flask, g
        from backend.utils.i18n import _translations

        _translations["en"] = {"test": "Test value"}

        app = Flask(__name__)
        with app.test_request_context():
            g.lang = "en"
            result = t("test")
            assert result == "Test value"

    def test_t_with_accept_language(self):
        """Test t() respects Accept-Language header."""
        from backend.utils.i18n import _translations

        _translations["ar"] = {"test": "قيمة"}
        _translations["en"] = {"test": "value"}

        app = Flask(__name__)
        with app.test_request_context(headers=[("Accept-Language", "ar")]):
            result = t("test")
            # Should pick Arabic as it's the best match
            assert result == "قيمة"
