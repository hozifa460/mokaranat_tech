"""
Comparison Document Exporter and Schema.org Generator.
Clean Architecture - Layer: Services
Produces complete comparison objects, builds Schema.org JSON-LD, and exports to Astro SSG directory.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

from core.config import WEB_DATA_DIR, WEB_SUMMARY_JSON, SITE_META
from core.domain.models import (
    HardwareSpec,
    ComparisonDocument,
    ComparisonVerdict
)
from core.services.spec_engine import SpecEngine
from core.services.fps_calculator import FpsCalculator
from core.services.affiliate_engine import AffiliateEngine
from core.services.ai_editorial import AiEditorialService, _format_num


class ComparisonExporter:
    """Orchestrates comparison generation, schema creation, and Astro JSON export."""

    def __init__(self, editorial_service: AiEditorialService = None):
        self.editorial_service = editorial_service or AiEditorialService()

    def build_comparison(self, item_a: HardwareSpec, item_b: HardwareSpec) -> ComparisonDocument:
        """Constructs a full comparison document between two items."""
        if item_a.category != item_b.category:
            raise ValueError(
                f"Cannot compare items from different categories: '{item_a.category}' ({item_a.name}) vs '{item_b.category}' ({item_b.name})"
            )

        slug = f"{item_a.slug}-vs-{item_b.slug}"
        category = item_a.category

        title_ar = f"مقارنة {item_a.name} ضد {item_b.name} | المواصفات والأداء والأسعار"
        meta_title_ar = f"{item_a.name} ضد {item_b.name}: أيهما يستحق الشراء؟ | مقارنات تك"
        meta_desc_ar = (
            f"مقارنة شاملة وتفصيلية بين {item_a.name} و {item_b.name}. "
            f"شاهد الفروقات في المواصفات، مقارنة معمارية وتحليلات الأداء المتوقعة في الألعاب، كفاءة استهلاك الطاقة، "
            f"وحكم الشراء النهائي مع أفضل الأسعار من نون، نيو إيج، وجوميا."
        )

        spec_diffs = SpecEngine.compare_specs(item_a, item_b)
        fps_benchmarks = FpsCalculator.calculate_fps_matrix(item_a, item_b)
        verdict = self.editorial_service.generate_verdict(item_a, item_b, fps_matrix=fps_benchmarks)

        affiliate_a = AffiliateEngine.generate_offers_for_item(item_a)
        affiliate_b = AffiliateEngine.generate_offers_for_item(item_b)

        created_now = datetime.now(timezone.utc).isoformat()

        # Build Rich Schema.org JSON-LD (Product & Review)
        schema_json_ld = self._build_schema_json_ld(
            slug=slug,
            title=title_ar,
            desc=meta_desc_ar,
            item_a=item_a,
            item_b=item_b,
            verdict=verdict,
            date_published=created_now
        )

        return ComparisonDocument(
            slug=slug,
            category=category,
            title_ar=title_ar,
            meta_title_ar=meta_title_ar,
            meta_description_ar=meta_desc_ar,
            item_a=item_a,
            item_b=item_b,
            spec_differences=spec_diffs,
            performance_score_a=item_a.benchmark_index,
            performance_score_b=item_b.benchmark_index,
            fps_benchmarks=fps_benchmarks,
            verdict=verdict,
            affiliate_links_a=affiliate_a,
            affiliate_links_b=affiliate_b,
            schema_json_ld=schema_json_ld,
            created_at=created_now
        )

    def export_to_astro(self, doc: ComparisonDocument, output_dir: Path = WEB_DATA_DIR) -> Path:
        """Writes the comparison JSON file for Astro SSG."""
        output_dir.mkdir(parents=True, exist_ok=True)
        file_path = output_dir / f"{doc.slug}.json"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(doc.model_dump_json(indent=2))

        return file_path

    def update_index_manifest(self, docs: List[ComparisonDocument], manifest_path: Path = WEB_SUMMARY_JSON) -> Path:
        """Generates an index manifest listing all available comparisons for navigation and sitemap."""
        manifest_path.parent.mkdir(parents=True, exist_ok=True)

        summary_list = []
        for d in docs:
            summary_list.append({
                "slug": d.slug,
                "category": d.category,
                "title_ar": d.title_ar,
                "item_a_id": d.item_a.id,
                "item_b_id": d.item_b.id,
                "item_a_name": d.item_a.name,
                "item_b_name": d.item_b.name,
                "item_a_brand": d.item_a.brand,
                "item_b_brand": d.item_b.brand,
                "winner_name": d.verdict.winner_name,
                "score_a": d.performance_score_a,
                "score_b": d.performance_score_b,
                "created_at": d.created_at
            })

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(summary_list, f, ensure_ascii=False, indent=2)

        return manifest_path

    @staticmethod
    def _build_schema_json_ld(
        slug: str,
        title: str,
        desc: str,
        item_a: HardwareSpec,
        item_b: HardwareSpec,
        verdict: ComparisonVerdict,
        date_published: str
    ) -> Dict[str, Any]:
        canonical_url = f"{SITE_META['site_url']}/compare/{slug}"

        return {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "Product",
                    "@id": f"{canonical_url}#productA",
                    "name": item_a.name,
                    "category": item_a.category.upper(),
                    "brand": {"@type": "Brand", "name": item_a.brand},
                    "offers": {
                        "@type": "AggregateOffer",
                        "priceCurrency": "USD",
                        "lowPrice": _format_num(item_a.launch_msrp_usd),
                        "offerCount": "4"
                    }
                },
                {
                    "@type": "Product",
                    "@id": f"{canonical_url}#productB",
                    "name": item_b.name,
                    "category": item_b.category.upper(),
                    "brand": {"@type": "Brand", "name": item_b.brand},
                    "offers": {
                        "@type": "AggregateOffer",
                        "priceCurrency": "USD",
                        "lowPrice": _format_num(item_b.launch_msrp_usd),
                        "offerCount": "4"
                    }
                },
                {
                    "@type": "Review",
                    "@id": f"{canonical_url}#review",
                    "url": canonical_url,
                    "name": title,
                    "description": desc,
                    "datePublished": date_published,
                    "inLanguage": "ar",
                    "author": {
                        "@type": "Organization",
                        "name": SITE_META["default_author"],
                        "url": SITE_META["site_url"]
                    },
                    "publisher": {
                        "@type": "Organization",
                        "name": SITE_META["site_name_ar"],
                        "url": SITE_META["site_url"]
                    },
                    "itemReviewed": {
                        "@type": "Product",
                        "name": f"{item_a.name} vs {item_b.name}"
                    },
                    "reviewRating": {
                        "@type": "Rating",
                        "ratingValue": max(1.0, min(5.0, round((max(item_a.benchmark_index, item_b.benchmark_index) / 20.0), 1))),
                        "bestRating": "5",
                        "worstRating": "1"
                    },
                    "reviewBody": verdict.quick_verdict_ar
                }
            ]
        }
