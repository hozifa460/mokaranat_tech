"""
Affiliate URL & Store Offer Generator Service.
Clean Architecture - Layer: Services
Generates multi-store affiliate search/direct links for Noon, Newegg, AliExpress, and Jumia.
STRICT RULE: Absolutely NO Amazon links or references permitted.
"""

import urllib.parse
from typing import List
from core.config import AFFILIATE_STORES, FORBIDDEN_AFFILIATES
from core.domain.models import HardwareSpec, AffiliateOffer


class ForbiddenStoreError(Exception):
    """Raised if an attempt is made to configure or link to Amazon."""
    pass


class AffiliateEngine:
    """Generates verified affiliate store offers for hardware items."""

    @classmethod
    def generate_offers_for_item(cls, item: HardwareSpec) -> List[AffiliateOffer]:
        offers: List[AffiliateOffer] = []

        query = item.name.strip()
        encoded_query = urllib.parse.quote_plus(query)

        for store_key, store_data in AFFILIATE_STORES.items():
            if store_key.lower() in FORBIDDEN_AFFILIATES:
                raise ForbiddenStoreError(f"Store '{store_key}' is strictly forbidden by project rules.")

            direct_url = store_data["search_url"].format(query=encoded_query)

            # Append tracking tag cleanly with proper delimiter
            delimiter = "&" if "?" in direct_url else "?"
            affiliate_url = f"{direct_url}{delimiter}{store_data['tracking_param']}"

            offers.append(AffiliateOffer(
                store_key=store_key,
                store_name_ar=store_data["name_ar"],
                store_name_en=store_data["name_en"],
                product_title=f"شراء {item.name} من متجر {store_data['name_ar']}",
                direct_url=direct_url,
                affiliate_url=affiliate_url,
                badge_color=store_data["badge_color"],
                text_color=store_data["text_color"]
            ))

        return offers

    @classmethod
    def sanitize_and_validate_url(cls, url: str) -> str:
        """Validates that a URL does not contain forbidden affiliate domains (Amazon)."""
        lower_url = url.lower()
        for forbidden in FORBIDDEN_AFFILIATES:
            if forbidden in lower_url:
                raise ForbiddenStoreError(f"Detected forbidden affiliate domain '{forbidden}' in URL: {url}")
        return url
