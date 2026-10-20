"""
Configuration and Environment Settings for Tech Comparisons Engine.
Clean Architecture - Layer: Core Configuration
"""

import os
from pathlib import Path
from typing import Dict, Any

# Root Paths
PROJECT_ROOT = Path("D:/tech_comparisons").resolve()
CORE_DIR = PROJECT_ROOT / "core"
DATA_DIR = CORE_DIR / "data"
DATABASE_PATH = DATA_DIR / "hardware.db"
SEED_DATA_PATH = DATA_DIR / "seed_specs.json"

# Web Integration Paths
WEB_DIR = PROJECT_ROOT / "web"
WEB_DATA_DIR = WEB_DIR / "src" / "data" / "comparisons"
WEB_SUMMARY_JSON = WEB_DIR / "src" / "data" / "comparisons_index.json"

# AI Configuration (Gemini API)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# Affiliate Settings (Strictly NO Amazon)
FORBIDDEN_AFFILIATES = {"amazon", "amzn"}

AFFILIATE_STORES: Dict[str, Dict[str, Any]] = {
    "noon": {
        "name_ar": "نون",
        "name_en": "Noon",
        "base_url": "https://www.noon.com",
        "search_url": "https://www.noon.com/search?q={query}",
        "tracking_param": "affiliate_id=TECHCOMP_NOON_AR",
        "badge_color": "#FEE600",
        "text_color": "#1F2937"
    },
    "newegg": {
        "name_ar": "نيو إيج",
        "name_en": "Newegg",
        "base_url": "https://www.newegg.com",
        "search_url": "https://www.newegg.com/p/pl?d={query}",
        "tracking_param": "cm_mmc=aff-techcomp_ar",
        "badge_color": "#F37021",
        "text_color": "#FFFFFF"
    },
    "aliexpress": {
        "name_ar": "علي إكسبريس",
        "name_en": "AliExpress",
        "base_url": "https://www.aliexpress.com",
        "search_url": "https://www.aliexpress.com/wholesale?SearchText={query}",
        "tracking_param": "aff_fcid=TECHCOMP_ALI_AR",
        "badge_color": "#FF4747",
        "text_color": "#FFFFFF"
    },
    "jumia": {
        "name_ar": "جوميا",
        "name_en": "Jumia",
        "base_url": "https://www.jumia.com",
        "search_url": "https://www.jumia.com/catalog/?q={query}",
        "tracking_param": "tag=techcomparisons-jumia",
        "badge_color": "#F68B1E",
        "text_color": "#FFFFFF"
    }
}

# SEO & Meta Defaults
SITE_META = {
    "site_name_ar": "مقارنات تك | الدليل الأقوى لمقارنة العتاد والبطاقات الرسومية",
    "site_url": "https://mokaranat-tech.pages.dev",
    "default_author": "فريق تحرير مقارنات تك",
    "locale": "ar_SA",
    "currency_default": "USD"
}
