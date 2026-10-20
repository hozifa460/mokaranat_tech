"""
Phase 20 Test Suite: Full Category All-Pairs Matrix & Interactive Comparison Builder Validation.

Validates:
1. Exact all-pairs matrix sizing: 55 GPUs, 15 CPUs, 10 Laptops = 80 total comparisons.
2. Preservation of the original 15 high-intent matchups at the head of the manifest.
3. Bidirectional slug resolution coverage for all 80 pairs (both A:B and B:A).
4. Manifest metadata completeness (item_a_id, item_b_id, item_a_brand, item_b_brand) for ComparisonBuilder.
5. Within-category consistency (no cross-category comparisons).
6. Zero self-comparisons.
"""

import json
import itertools
from pathlib import Path
from collections import defaultdict
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST_PATH = PROJECT_ROOT / "web" / "src" / "data" / "comparisons_index.json"
COMPARISONS_DIR = PROJECT_ROOT / "web" / "src" / "data" / "comparisons"
SEED_SPECS_PATH = PROJECT_ROOT / "core" / "data" / "seed_specs.json"

EXPECTED_TOP_15_SLUGS = [
    "rtx-4070-super-vs-rx-7800-xt",
    "rtx-4080-super-vs-rx-7900-xtx",
    "rtx-4060-ti-vs-rx-7700-xt",
    "rtx-4070-super-vs-rtx-4080-super",
    "rx-7800-xt-vs-rx-7900-xtx",
    "rtx-4090-vs-rx-7900-xtx",
    "rtx-4070-ti-super-vs-rx-7900-xt",
    "rtx-4060-vs-rx-7600-xt",
    "ryzen-7-7800x3d-vs-i7-14700k",
    "ryzen-9-7950x3d-vs-i9-14900k",
    "ryzen-5-7600x-vs-i5-14600k",
    "rog-zephyrus-g16-vs-legion-pro-7i",
    "razer-blade-16-2024-vs-legion-pro-7i",
    "macbook-pro-16-m3-max-vs-rog-zephyrus-g16",
    "asus-tuf-gaming-a15-vs-rog-zephyrus-g16"
]


def _load_manifest():
    assert MANIFEST_PATH.exists(), f"Manifest file missing: {MANIFEST_PATH}"
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_seed_specs():
    assert SEED_SPECS_PATH.exists(), f"Seed specs file missing: {SEED_SPECS_PATH}"
    with open(SEED_SPECS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_phase20_matrix_category_breakdown():
    """Verifies that the full all-pairs matrix matches combinatorial math exactly:
    - GPUs: 11 choose 2 = 55
    - CPUs: 6 choose 2 = 15
    - Laptops: 5 choose 2 = 10
    Total = 80 comparisons.
    """
    manifest = _load_manifest()
    assert len(manifest) == 80, f"Expected 80 comparisons in manifest, got {len(manifest)}"

    counts = defaultdict(int)
    for entry in manifest:
        counts[entry["category"]] += 1

    assert counts["gpu"] == 55, f"Expected 55 GPU comparisons, got {counts['gpu']}"
    assert counts["cpu"] == 15, f"Expected 15 CPU comparisons, got {counts['cpu']}"
    assert counts["laptop"] == 10, f"Expected 10 Laptop comparisons, got {counts['laptop']}"


def test_phase20_top_15_curated_matchups_preserved_in_order():
    """Verifies that the original 15 high-intent matchups are preserved at the top of the manifest in exact order."""
    manifest = _load_manifest()
    top_15_manifest_slugs = [item["slug"] for item in manifest[:15]]
    assert top_15_manifest_slugs == EXPECTED_TOP_15_SLUGS, (
        f"Top 15 slugs mismatch!\nExpected: {EXPECTED_TOP_15_SLUGS}\nActual: {top_15_manifest_slugs}"
    )


def test_phase20_manifest_builder_metadata_completeness():
    """Verifies that every entry in comparisons_index.json has required fields for ComparisonBuilder.astro."""
    manifest = _load_manifest()
    required_keys = [
        "slug", "category", "title_ar",
        "item_a_id", "item_b_id", "item_a_name", "item_b_name",
        "item_a_brand", "item_b_brand",
        "winner_name", "score_a", "score_b"
    ]

    for idx, entry in enumerate(manifest, start=1):
        slug = entry.get("slug", f"entry_{idx}")
        for k in required_keys:
            assert k in entry and entry[k] is not None and entry[k] != "", (
                f"Manifest entry {slug} missing or empty metadata key: '{k}'"
            )
        assert entry["item_a_id"] != entry["item_b_id"], (
            f"Manifest entry {slug} has identical item IDs: {entry['item_a_id']}"
        )


def test_phase20_bidirectional_slug_resolution():
    """Verifies that every valid pair within a category resolves bidirectionally to a valid slug and file."""
    manifest = _load_manifest()
    pair_to_slug = {}

    for entry in manifest:
        id_a = entry["item_a_id"]
        id_b = entry["item_b_id"]
        slug = entry["slug"]

        pair_to_slug[f"{id_a}:{id_b}"] = slug
        pair_to_slug[f"{id_b}:{id_a}"] = slug

    # Test all pairs from seed specs
    specs = _load_seed_specs()
    cat_items = defaultdict(list)
    for s in specs:
        cat_items[s["category"]].append(s["id"])

    total_tested_permutations = 0
    for cat, ids in cat_items.items():
        for id_a, id_b in itertools.permutations(ids, 2):
            total_tested_permutations += 1
            key = f"{id_a}:{id_b}"
            assert key in pair_to_slug, f"Missing bidirectional slug resolution for permutation: {key}"
            resolved_slug = pair_to_slug[key]

            # Verify target JSON file exists
            json_file = COMPARISONS_DIR / f"{resolved_slug}.json"
            assert json_file.exists(), f"Target comparison file missing for slug '{resolved_slug}' ({key})"

    # 55*2 + 15*2 + 10*2 = 160 permutations tested
    assert total_tested_permutations == 160, f"Expected 160 permutations, tested {total_tested_permutations}"


def test_phase20_comparison_files_match_manifest():
    """Verifies that all 80 JSON files on disk match the manifest slugs exactly with 0 orphans."""
    manifest = _load_manifest()
    manifest_slugs = {item["slug"] for item in manifest}

    disk_files = list(COMPARISONS_DIR.glob("*.json"))
    assert len(disk_files) == 80, f"Expected 80 JSON files on disk, found {len(disk_files)}"

    disk_slugs = {f.stem for f in disk_files}
    assert disk_slugs == manifest_slugs, (
        f"Disk slugs differ from manifest slugs: {disk_slugs.symmetric_difference(manifest_slugs)}"
    )
