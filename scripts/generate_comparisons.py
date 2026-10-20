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
    ("rtx-4090", "rx-7900-xtx"),
    ("rtx-4070-ti-super", "rx-7900-xt"),
    ("rtx-4060", "rx-7600-xt"),
    # CPUs
    ("ryzen-7-7800x3d", "i7-14700k"),
    ("ryzen-9-7950x3d", "i9-14900k"),
    ("ryzen-5-7600x", "i5-14600k"),
    # Laptops
    ("rog-zephyrus-g16", "legion-pro-7i"),
    ("razer-blade-16-2024", "legion-pro-7i"),
    ("macbook-pro-16-m3-max", "rog-zephyrus-g16"),
    ("asus-tuf-gaming-a15", "rog-zephyrus-g16")
]


def get_all_matchups(repo: HardwareRepository) -> List[Tuple[str, str]]:
    """Builds the complete all-pairs comparison matrix across all categories,
    preserving the original 15 high-intent matchups at the beginning of the list.
    """
    import itertools

    all_matchups: List[Tuple[str, str]] = list(DEFAULT_MATCHUPS)
    seen_pairs = {tuple(sorted([a, b])) for a, b in DEFAULT_MATCHUPS}

    categories = ["gpu", "cpu", "laptop"]
    all_hardware = repo.list_all_hardware()

    for cat in categories:
        cat_items = [h for h in all_hardware if h.category == cat]
        cat_items.sort(key=lambda x: x.benchmark_index, reverse=True)
        for spec_a, spec_b in itertools.combinations(cat_items, 2):
            pair_key = tuple(sorted([spec_a.id, spec_b.id]))
            if pair_key not in seen_pairs:
                all_matchups.append((spec_a.id, spec_b.id))
                seen_pairs.add(pair_key)

    return all_matchups


def generate_all_comparisons():
    print("[*] Starting Full Matrix Comparison Pipeline...")
    repo = HardwareRepository()
    exporter = ComparisonExporter()

    matchups = get_all_matchups(repo)
    print(f"[*] Prepared {len(matchups)} pairwise matchups across all categories.")

    generated_docs: List[ComparisonDocument] = []

    for idx, (id_a, id_b) in enumerate(matchups, start=1):
        spec_a = repo.get_hardware_by_id(id_a)
        spec_b = repo.get_hardware_by_id(id_b)

        if not spec_a or not spec_b:
            print(f"[!] Warning: One of the items ({id_a}, {id_b}) was not found in SQLite. Skipping.")
            continue

        print(f" [{idx}/{len(matchups)}] Generating: {spec_a.name} VS {spec_b.name}")
        doc = exporter.build_comparison(spec_a, spec_b)

        # 1. Save to SQLite cache
        repo.save_comparison_cache(doc)

        # 2. Export to Astro data directory
        json_file = exporter.export_to_astro(doc)

        generated_docs.append(doc)

    # 3. Update master index manifest
    manifest_file = exporter.update_index_manifest(generated_docs)
    print(f"\n[OK] Updated comparison index manifest at: {manifest_file}")
    print(f"[OK] Successfully built {len(generated_docs)} programmatic comparisons ready for Astro SSG.")


if __name__ == "__main__":
    generate_all_comparisons()
