"""
Unit & Integration Tests for Phase 21: Production Launch & Search Engine Readiness.
Validates:
1. Existence and integrity of statutory pages: privacy, terms, about, contact.
2. Strict ZERO Amazon compliance across all statutory pages and site metadata.
3. Proper configuration of @astrojs/sitemap and robots.txt.
4. Comprehensive OpenGraph and Twitter Card social metadata in BaseLayout.
5. Footer links to statutory pages.
6. Attribution and data sources (TechPowerUp, Intel ARK, AMD, Jarrod's Tech).
7. Approved affiliate partners (Noon, Newegg, AliExpress, Jumia).
"""

from pathlib import Path
import re
import pytest

WEB_DIR = Path("D:/tech_comparisons/web")
PAGES_DIR = WEB_DIR / "src" / "pages"
COMPONENTS_DIR = WEB_DIR / "src" / "components"
LAYOUTS_DIR = WEB_DIR / "src" / "layouts"
PUBLIC_DIR = WEB_DIR / "public"


def test_statutory_pages_exist():
    """Verify that all four required statutory pages exist."""
    required_pages = ["privacy.astro", "terms.astro", "about.astro", "contact.astro"]
    for page in required_pages:
        page_path = PAGES_DIR / page
        assert page_path.exists(), f"Statutory page '{page}' is missing!"
        content = page_path.read_text(encoding="utf-8")
        assert len(content.strip()) > 500, f"Statutory page '{page}' is too thin or empty!"


def test_strict_zero_amazon_compliance_on_new_pages():
    """Strictly assert ZERO Amazon mentions across all new statutory pages, components, and configs."""
    files_to_audit = [
        PAGES_DIR / "privacy.astro",
        PAGES_DIR / "terms.astro",
        PAGES_DIR / "about.astro",
        PAGES_DIR / "contact.astro",
        COMPONENTS_DIR / "Footer.astro",
        LAYOUTS_DIR / "BaseLayout.astro",
        WEB_DIR / "astro.config.mjs",
        PUBLIC_DIR / "robots.txt",
    ]
    forbidden_terms = ["amazon", "amzn", "أمازون"]

    for file_path in files_to_audit:
        assert file_path.exists(), f"File {file_path} not found"
        content = file_path.read_text(encoding="utf-8").lower()
        for term in forbidden_terms:
            assert term not in content, (
                f"VIOLATION: Forbidden term '{term}' detected in file '{file_path.name}'!"
            )


def test_astro_config_sitemap_and_site_url():
    """Verify that astro.config.mjs configures @astrojs/sitemap and correct site URL."""
    config_path = WEB_DIR / "astro.config.mjs"
    assert config_path.exists()
    content = config_path.read_text(encoding="utf-8")

    assert "import sitemap from '@astrojs/sitemap';" in content or 'import sitemap from "@astrojs/sitemap";' in content
    assert "sitemap(" in content
    assert "https://mokaranat-tech.pages.dev" in content


def test_robots_txt_validity():
    """Verify that robots.txt allows all crawlers and points to sitemap-index.xml."""
    robots_path = PUBLIC_DIR / "robots.txt"
    assert robots_path.exists()
    content = robots_path.read_text(encoding="utf-8")

    assert "User-agent: *" in content
    assert "Allow: /" in content
    assert "Sitemap: https://mokaranat-tech.pages.dev/sitemap-index.xml" in content


def test_footer_statutory_links():
    """Verify that Footer.astro includes prominent links to /about, /privacy, /terms, /contact."""
    footer_path = COMPONENTS_DIR / "Footer.astro"
    assert footer_path.exists()
    content = footer_path.read_text(encoding="utf-8")

    assert 'href="/about"' in content, "Missing /about link in Footer"
    assert 'href="/privacy"' in content, "Missing /privacy link in Footer"
    assert 'href="/terms"' in content, "Missing /terms link in Footer"
    assert 'href="/contact"' in content, "Missing /contact link in Footer"


def test_baselayout_opengraph_and_twitter_cards():
    """Verify that BaseLayout.astro contains complete OpenGraph and Twitter Card tags."""
    layout_path = LAYOUTS_DIR / "BaseLayout.astro"
    assert layout_path.exists()
    content = layout_path.read_text(encoding="utf-8")

    assert 'property="og:type"' in content
    assert 'property="og:title"' in content
    assert 'property="og:description"' in content
    assert 'property="og:url"' in content
    assert 'property="og:image"' in content
    assert 'name="twitter:card"' in content
    assert 'name="twitter:title"' in content
    assert 'name="twitter:description"' in content
    assert 'name="twitter:image"' in content
    assert 'rel="canonical"' in content
    assert 'rel="sitemap"' in content


def test_og_image_assets_exist():
    """Verify that social preview images (og-image.png and og-image.svg) exist and are valid."""
    og_png = PUBLIC_DIR / "og-image.png"
    og_svg = PUBLIC_DIR / "og-image.svg"
    assert og_svg.exists(), "og-image.svg is missing in web/public/"
    assert og_png.exists(), "og-image.png is missing in web/public/"
    assert og_png.stat().st_size > 1000, "og-image.png is too small or corrupt"


def test_about_page_eeat_sources():
    """Verify that about.astro establishes E-E-A-T credibility citing all authoritative hardware sources."""
    about_path = PAGES_DIR / "about.astro"
    assert about_path.exists()
    content = about_path.read_text(encoding="utf-8")

    assert "TechPowerUp" in content
    assert "Intel ARK" in content
    assert "AMD" in content
    assert "Jarrod's Tech" in content or "Jarrod" in content
    assert "Deterministic" in content or "حتمي" in content
    assert "3.0%" in content


def test_privacy_and_terms_affiliate_partners():
    """Verify that privacy.astro and terms.astro disclose the approved partner stores."""
    privacy_path = PAGES_DIR / "privacy.astro"
    terms_path = PAGES_DIR / "terms.astro"

    for path in [privacy_path, terms_path]:
        content = path.read_text(encoding="utf-8")
        assert "نون" in content or "Noon" in content
        assert "نيو إيج" in content or "Newegg" in content
        assert "علي إكسبريس" in content or "AliExpress" in content
        assert "جوميا" in content or "Jumia" in content


def test_contact_page_channels_and_form():
    """Verify that contact.astro provides correction channels, inquiries, and advertising options."""
    contact_path = PAGES_DIR / "contact.astro"
    assert contact_path.exists()
    content = contact_path.read_text(encoding="utf-8")

    assert "editorial@mokaranat-tech.com" in content
    assert "contact@mokaranat-tech.com" in content
    assert "ads@mokaranat-tech.com" in content
    assert 'id="contact-form"' in content
    assert 'name="name"' in content
    assert 'name="email"' in content
    assert 'name="message"' in content
