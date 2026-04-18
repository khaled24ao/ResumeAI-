"""Multi-language support with i18n."""

import json
import os
from typing import Optional, Dict

from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Supported languages
LANGUAGES = {
    'en': 'English',
    'ar': 'العربية'
}

# Default language
DEFAULT_LANGUAGE = 'en'

# Translation cache
_translations: Dict[str, Dict[str, str]] = {}


def load_translations() -> None:
    """Load translation files from disk."""
    translations_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'translations'
    )
    
    for lang_code in LANGUAGES.keys():
        file_path = os.path.join(translations_dir, f'{lang_code}.json')
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    _translations[lang_code] = json.load(f)
                logger.info(f"Loaded translations for {lang_code}")
            except Exception as e:
                logger.error(f"Failed to load {lang_code} translations: {e}")
                _translations[lang_code] = {}
        else:
            logger.warning(f"Translation file not found: {file_path}")


def get_translation(lang: str, key: str, **kwargs) -> str:
    """
    Get translated string for given language and key.
    
    Args:
        lang: Language code (e.g., 'en', 'ar')
        key: Translation key (dot notation for nested)
        **kwargs: Variables to format into translation
    
    Returns:
        Translated string (falls back to key if not found)
    """
    if not _translations:
        load_translations()
    
    # Split key for nested lookup
    keys = key.split('.')
    value = None
    
    # Try specified language
    if lang in _translations:
        value = _translations[lang]
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                value = None
                break
    
    # Fall back to default language
    if value is None and lang != DEFAULT_LANGUAGE and DEFAULT_LANGUAGE in _translations:
        value = _translations[DEFAULT_LANGUAGE]
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                value = None
                break
    
    # Fall back to key itself
    if value is None:
        value = key
    
    # Format with kwargs if any
    if kwargs:
        try:
            value = value.format(**kwargs)
        except:
            pass
    
    return value


def t(key: str, **kwargs) -> str:
    """
    Translate using current request language.
    
    Usage:
        t('errors.file_too_large', max_size='5MB')
    """
    from flask import request, g
    
    # Get language from request context
    lang = getattr(g, 'lang', DEFAULT_LANGUAGE)
    
    # Also check Accept-Language header
    if hasattr(request, 'accept_languages'):
        best = request.accept_languages.best_match(LANGUAGES.keys())
        if best:
            lang = best
    
    return get_translation(lang, key, **kwargs)


# Initialize translations on module load
load_translations()