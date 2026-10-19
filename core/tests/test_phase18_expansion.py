"""
Comprehensive tests for Phase 18:
- Hardware catalog expansion (22 items in seed_specs.json and SQLite).
- Strict ceiling validation (all scores <= 98.0, CPU ray tracing is None).
- Dual NVENC vs Single NVENC detection.
- PCIe lane detection (8-lane PCIe 4.0 x8 on RTX 4060 and RX 7600 XT with accurate con & diff messages).
- Apple Silicon handling (Unified memory, macOS gaming translation, battery performance).
- Mini-LED vs OLED vs IPS laptop display diffs.
- Zero Amazon rule across all exported comparison JSON files.
- Manifest and comparison count validation.
"""

import json
from pathlib import Path
import pytest

from core.domain.models import HardwareSpec
from core.repository.hardware_repo import HardwareRepository
from core.services.spec_engine import SpecEngine
from core.services.ai_editorial import EditorialRuleEngine, _is_dual_nvenc
from core.services.fps_calculator import FpsCalculator


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def test_seed_specs_catalog_completeness():
    """Verify all 22 items are present in seed_specs.json."""
    seed_path = PROJECT_ROOT / "core" / "data" / "seed_specs.json"
    with open(seed_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data) == 22, f"Expected 22 hardware items in catalog, found {len(data)}"
    ids = {item["id"] for item in data}

    expected_new_ids = {
        "rtx-4090",
        "rtx-4070-ti-super",
        "rtx-4060",
        "rx-7900-xt",
        "rx-7600-xt",
        "i9-14900k",
        "ryzen-9-7950x3d",
        "i5-14600k",
        "ryzen-5-7600x",
        "razer-blade-16-2024",
        "macbook-pro-16-m3-max",
        "asus-tuf-gaming-a15"
    }
    for item_id in expected_new_ids:
        assert item_id in ids, f"Expected ID '{item_id}' not found in seed specs"


def test_scores_ceiling_and_cpu_ray_tracing_null():
    """Verify all benchmark scores <= 98.0 and all CPU ray tracing scores are None/null."""
    seed_path = PROJECT_ROOT / "core" / "data" / "seed_specs.json"
    with open(seed_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for item in data:
        spec = HardwareSpec.model_validate(item)
        assert spec.benchmark_index <= 98.0, f"{spec.id} benchmark_index {spec.benchmark_index} exceeds 98.0 ceiling"
        assert spec.efficiency_score <= 98.0, f"{spec.id} efficiency_score {spec.efficiency_score} exceeds 98.0 ceiling"

        for k, v in spec.gaming_scores.items():
            if v is not None:
                assert v <= 98.0, f"{spec.id} gaming score '{k}' value {v} exceeds 98.0 ceiling"

        if spec.category == "cpu":
            assert spec.ray_tracing_score is None, f"CPU {spec.id} has ray_tracing_score {spec.ray_tracing_score}, must be None/null"
        else:
            if spec.ray_tracing_score is not None:
                assert spec.ray_tracing_score <= 98.0, f"{spec.id} ray_tracing_score exceeds 98.0 ceiling"


def test_dual_nvenc_detection():
    """Verify RTX 4090 and RTX 4070 Ti Super detect as Dual NVENC, while RTX 4060 detects as Single NVENC."""
    repo = HardwareRepository()
    rtx4090 = repo.get_hardware_by_id("rtx-4090")
    rtx4070_ti_s = repo.get_hardware_by_id("rtx-4070-ti-super")
    rtx4060 = repo.get_hardware_by_id("rtx-4060")
    rx7900xtx = repo.get_hardware_by_id("rx-7900-xtx")

    assert rtx4090 is not None and _is_dual_nvenc(rtx4090) is True
    assert rtx4070_ti_s is not None and _is_dual_nvenc(rtx4070_ti_s) is True
    assert rtx4060 is not None and _is_dual_nvenc(rtx4060) is False
    assert rx7900xtx is not None and _is_dual_nvenc(rx7900xtx) is False


def test_pcie_8_lane_detection_and_con():
    """Verify RTX 4060 and RX 7600 XT have 8 lanes, and receive accurate PCIe 8-lane cons and diff summaries."""
    repo = HardwareRepository()
    rtx4060 = repo.get_hardware_by_id("rtx-4060")
    rx7600xt = repo.get_hardware_by_id("rx-7600-xt")

    assert rtx4060.raw_specs.get("pcie_lanes") == 8
    assert rx7600xt.raw_specs.get("pcie_lanes") == 8
    assert "x8" in rtx4060.pcie_interface.lower()
    assert "x8" in rx7600xt.pcie_interface.lower()

    # Test spec differences between two 8-lane cards
    diffs = SpecEngine.compare_specs(rtx4060, rx7600xt)
    pcie_diff = next((d for d in diffs if d.key == "pcie_interface"), None)
    assert pcie_diff is not None
    assert pcie_diff.winner == "tie"
    assert "8 مسارات" in pcie_diff.advantage_summary_ar

    # Test editorial verdict cons
    verdict = EditorialRuleEngine.generate_verdict(rtx4060, rx7600xt)
    assert any("PCIe 4.0 x8" in c for c in verdict.cons_a)
    assert any("PCIe 4.0 x8" in c for c in verdict.cons_b)


def test_apple_silicon_laptop_comparison():
    """Verify MacBook Pro 16 (M3 Max) vs ROG Zephyrus G16 produces authentic Apple Silicon handling."""
    repo = HardwareRepository()
    macbook = repo.get_hardware_by_id("macbook-pro-16-m3-max")
    zephyrus = repo.get_hardware_by_id("rog-zephyrus-g16")

    assert macbook is not None and zephyrus is not None

    # Test RAM diff notes Unified Memory bandwidth
    diffs = SpecEngine.compare_specs(macbook, zephyrus)
    ram_diff = next((d for d in diffs if d.key == "ram_gb"), None)
    assert ram_diff is not None
    assert "Unified Memory" in ram_diff.advantage_summary_ar
    assert "300GB/s" in ram_diff.advantage_summary_ar

    # Test editorial verdict
    verdict = EditorialRuleEngine.generate_verdict(macbook, zephyrus)

    # Windows laptop wins gaming analysis
    assert "Windows" in verdict.gaming_analysis_ar
    assert "DirectX" in verdict.gaming_analysis_ar
    assert "DLSS 3" in verdict.gaming_analysis_ar

    # Apple laptop dominates productivity & battery efficiency
    assert "Unified Memory" in verdict.productivity_analysis_ar
    assert "البطارية" in verdict.productivity_analysis_ar
    assert "ProRes" in verdict.productivity_analysis_ar

    # Pros and Cons
    assert any("Liquid Retina XDR" in p for p in verdict.pros_a)
    assert any("Unified Memory" in p for p in verdict.pros_a)
    assert any("macOS" in c for c in verdict.cons_a)
    assert any("ترقية" in c for c in verdict.cons_a)  # Non-upgradable RAM/SSD

    assert any("DirectX 12" in p for p in verdict.pros_b)
    assert any("البطارية" in c for c in verdict.cons_b)


def test_mini_led_vs_oled_vs_ips_display_handling():
    """Verify Mini-LED displays (Liquid Retina XDR, Dual-Mode) compare cleanly against OLED and IPS."""
    repo = HardwareRepository()
    blade16 = repo.get_hardware_by_id("razer-blade-16-2024")
    legion = repo.get_hardware_by_id("legion-pro-7i")
    zephyrus = repo.get_hardware_by_id("rog-zephyrus-g16")

    # Blade 16 (Mini-LED) vs Legion (IPS)
    diffs_blade_legion = SpecEngine.compare_specs(blade16, legion)
    disp_diff = next((d for d in diffs_blade_legion if d.key == "display"), None)
    assert disp_diff is not None
    assert "Mini-LED" in disp_diff.advantage_summary_ar
    assert "IPS" in disp_diff.advantage_summary_ar

    # Blade 16 verdict has Dual-Mode pro
    verdict_blade = EditorialRuleEngine.generate_verdict(blade16, legion)
    assert any("Mini-LED" in p for p in verdict_blade.pros_a)


def test_zero_amazon_rule_across_all_exported_comparisons():
    """Strict verification: No Amazon links or mentions in any exported comparison JSON file."""
    comp_dir = PROJECT_ROOT / "web" / "src" / "data" / "comparisons"
    assert comp_dir.exists(), "Comparisons export directory does not exist"

    json_files = list(comp_dir.glob("*.json"))
    assert len(json_files) == 15, f"Expected 15 exported comparison JSON files, found {len(json_files)}"

    forbidden = ["amazon", "amzn.to", "أمازون"]

    for jf in json_files:
        with open(jf, "r", encoding="utf-8") as f:
            content = f.read()

        for term in forbidden:
            assert term not in content.lower(), f"Strict ZERO Amazon violation: Found '{term}' in {jf.name}"


def test_comparisons_manifest_count():
    """Verify comparisons_index.json contains exactly 15 valid comparison items."""
    manifest_path = PROJECT_ROOT / "web" / "src" / "data" / "comparisons_index.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data) == 15, f"Expected 15 items in comparisons_index.json, found {len(data)}"
    slugs = {item["slug"] for item in data}

    expected_slugs = {
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
    }

    assert slugs == expected_slugs, f"Manifest slugs mismatch: {slugs.symmetric_difference(expected_slugs)}"
