"""
Programmatic SEO Comparison Generator Script.
Loads hardware items from SQLite, generates pairwise comparisons with AI editorial analysis,
saves documents to SQLite cache, and exports JSON collections for Astro SSG.
"""

import sys
from pathlib import Path
from typing import List, Tuple

# Reconfigure stdout for Windows console UTF-8 support
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.repository.hardware_repo import HardwareRepository
from core.services.exporter import ComparisonExporter
from core.domain.models import HardwareSpec, ComparisonDocument


# Curated high-intent SEO matchups
DEFAULT_MATCHUPS: List[Tuple[str, str]] = [
    # GPUs
    ("rtx-4070-super", "rx-7800-xt"),
    ("rtx-4080-super", "rx-7900-xtx"),
    ("rtx-4060-ti", "rx-7700-xt"),
    ("rtx-4070-super", "rtx-4080-super"),
    ("rx-7800-xt", "rx-7900-xtx"),
    # CPUs
    ("ryzen-7-7800x3d", "i7-14700k"),
    # Laptops
    ("rog-zephyrus-g16", "legion-pro-7i")
]


def generate_all_comparisons():
    print("[*] Starting Comparison Pipeline...")
    repo = HardwareRepository()
    exporter = ComparisonExporter()

    generated_docs: List[ComparisonDocument] = []

    for id_a, id_b in DEFAULT_MATCHUPS:
        spec_a = repo.get_hardware_by_id(id_a)
        spec_b = repo.get_hardware_by_id(id_b)

        if not spec_a or not spec_b:
            print(f"[!] Warning: One of the items ({id_a}, {id_b}) was not found in SQLite. Skipping.")
            continue

        print(f" -> Generating comparison: {spec_a.name} VS {spec_b.name}")
        doc = exporter.build_comparison(spec_a, spec_b)

        # 1. Save to SQLite cache
        repo.save_comparison_cache(doc)

        # 2. Export to Astro data directory
        json_file = exporter.export_to_astro(doc)
        print(f"    [OK] Exported JSON: {json_file.name}")

        generated_docs.append(doc)

    # 3. Update master index manifest
    manifest_file = exporter.update_index_manifest(generated_docs)
    print(f"\n[OK] Updated comparison index manifest at: {manifest_file}")
    print(f"[OK] Successfully built {len(generated_docs)} programmatic comparisons ready for Astro SSG.")


if __name__ == "__main__":
    generate_all_comparisons()
