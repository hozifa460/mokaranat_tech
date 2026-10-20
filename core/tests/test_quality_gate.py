"""
Quality Gate & Automated Audit Test Suite.
Phase 19: Contextual Rule Engine & Self-Auditing Quality Gate.

Asserts 7 core editorial & hardware quality rules across all generated comparison JSON files:
1. All scores (benchmark, gaming, efficiency, performance) bounded in [0, 100].
2. SequenceMatcher similarity between buyer recommendations <= 0.75.
3. No attribute praised in pros while criticized in cons on the same device.
4. Realistic power claims: no GPU >= 260W or CPU >= 150W praised as "منضبط" or "فقط".
5. No GPU with benchmark index < 75 described as dedicated for 4K gaming.
6. Platform realism: macOS devices never beat Windows gaming laptops with discrete RTX in average FPS.
7. Equal TDP spec diff never claims "السحب الأعلى مقابل السحب المنضبط".
"""

import glob
import json
import os
from difflib import SequenceMatcher
from typing import List, Dict, Any
import pytest

from core.config import DATA_DIR

COMPARISONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "web", "src", "data", "comparisons")


def _get_comparison_files() -> List[str]:
    files = glob.glob(os.path.join(COMPARISONS_DIR, "*.json"))
    assert len(files) >= 15, f"Expected at least 15 comparison JSON files, found: {len(files)}"
    return files


def _load_comparison(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_quality_gate_files_exist():
    """Rule 0: Verifies all expected comparison files are present and valid JSON."""
    files = _get_comparison_files()
    assert len(files) == 15
    for fpath in files:
        data = _load_comparison(fpath)
        assert "slug" in data
        assert "item_a" in data
        assert "item_b" in data
        assert "verdict" in data


def test_quality_gate_rule1_scores_bounded_0_to_100():
    """Rule 1: All scores (benchmark_index, gaming_scores, efficiency_score, verdict scores) are in [0, 100]."""
    for fpath in _get_comparison_files():
        doc = _load_comparison(fpath)
        slug = doc["slug"]

        # Document level performance scores
        assert 0.0 <= doc["performance_score_a"] <= 100.0, f"{slug}: performance_score_a out of bounds"
        assert 0.0 <= doc["performance_score_b"] <= 100.0, f"{slug}: performance_score_b out of bounds"

        # Verdict scores
        verdict = doc["verdict"]
        assert 0.0 <= verdict["score_a"] <= 100.0, f"{slug}: verdict score_a out of bounds"
        assert 0.0 <= verdict["score_b"] <= 100.0, f"{slug}: verdict score_b out of bounds"

        # Item level scores
        for label, item in [("item_a", doc["item_a"]), ("item_b", doc["item_b"])]:
            bi = item["benchmark_index"]
            assert 0.0 <= bi <= 100.0, f"{slug} {label}: benchmark_index {bi} not in [0, 100]"

            eff = item.get("efficiency_score", 50.0)
            assert 0.0 <= eff <= 100.0, f"{slug} {label}: efficiency_score {eff} not in [0, 100]"

            for res, score in item.get("gaming_scores", {}).items():
                if score is not None:
                    assert 0.0 <= score <= 100.0, f"{slug} {label}: gaming_score[{res}] {score} not in [0, 100]"

            rt = item.get("ray_tracing_score")
            if rt is not None:
                assert 0.0 <= rt <= 100.0, f"{slug} {label}: ray_tracing_score {rt} not in [0, 100]"


def test_quality_gate_rule2_who_should_buy_differentiation():
    """Rule 2: SequenceMatcher similarity between who_should_buy_a and who_should_buy_b <= 0.75."""
    for fpath in _get_comparison_files():
        doc = _load_comparison(fpath)
        slug = doc["slug"]
        verdict = doc["verdict"]

        who_a = verdict["who_should_buy_a"]
        who_b = verdict["who_should_buy_b"]

        ratio = SequenceMatcher(None, who_a, who_b).ratio()
        assert ratio <= 0.75, f"{slug}: Buyer recommendations too similar (ratio={ratio:.3f} > 0.75)"


def test_quality_gate_rule3_no_contradictory_pros_cons():
    """Rule 3: No attribute praised in pros while criticized in cons on the same device."""
    for fpath in _get_comparison_files():
        doc = _load_comparison(fpath)
        slug = doc["slug"]
        verdict = doc["verdict"]

        for label, pros, cons in [
            ("item_a", verdict["pros_a"], verdict["cons_a"]),
            ("item_b", verdict["pros_b"], verdict["cons_b"])
        ]:
            pros_text = " ".join(pros)
            cons_text = " ".join(cons)

            # Battery contradiction
            has_battery_pro = any(k in pros_text for k in ["بطارية ضخمة", "عمر بطارية استثنائي", "بطارية ممتازة", "بطارية بسعة"])
            has_battery_con = any(k in cons_text for k in ["عمر بطارية قصير", "استنزاف البطارية", "سعة بطارية متواضعة", "بطارية أقل"])
            assert not (has_battery_pro and has_battery_con), (
                f"{slug} {label}: Contradiction! Praised battery in pros but criticized in cons: {pros_text} vs {cons_text}"
            )

            # Energy efficiency contradiction
            has_eff_pro = any(k in pros_text for k in ["كفاءة استهلاك طاقة ممتازة", "كفاءة طاقة متفوقة", "استهلاك طاقة منضبط"])
            has_eff_con = any(k in cons_text for k in ["استهلاك طاقة مرتفع", "سحب طاقة مرتفع", "يتطلب مزود طاقة", "متطلبات تبريد مرتفعة"])
            assert not (has_eff_pro and has_eff_con), (
                f"{slug} {label}: Contradiction! Praised efficiency in pros but criticized power in cons: {pros_text} vs {cons_text}"
            )


def test_quality_gate_rule4_realistic_power_claims():
    """Rule 4: No GPU >= 260W or CPU >= 150W described as 'منضبط' or 'فقط' in pros or who_should_buy."""
    for fpath in _get_comparison_files():
        doc = _load_comparison(fpath)
        slug = doc["slug"]
        verdict = doc["verdict"]

        for item, pros, who in [
            (doc["item_a"], verdict["pros_a"], verdict["who_should_buy_a"]),
            (doc["item_b"], verdict["pros_b"], verdict["who_should_buy_b"])
        ]:
            cat = item["category"]
            tdp = item["tdp_w"]
            combined_text = " ".join(pros) + " " + who

            if cat == "gpu" and tdp >= 260:
                assert "منضبط" not in combined_text, f"{slug}: High TDP GPU ({tdp}W) described as 'منضبط': {combined_text}"
                assert "فقط" not in combined_text, f"{slug}: High TDP GPU ({tdp}W) described with 'فقط': {combined_text}"

            if cat == "cpu" and tdp >= 150:
                assert "منضبط" not in combined_text, f"{slug}: High TDP CPU ({tdp}W) described as 'منضبط': {combined_text}"
                assert "فقط" not in combined_text, f"{slug}: High TDP CPU ({tdp}W) described with 'فقط': {combined_text}"

        # Explicit check for RTX 4090: must have 450W / 12VHPWR con
        if doc["item_a"]["id"] == "rtx-4090":
            cons_4090 = " ".join(verdict["cons_a"])
            assert "450W" in cons_4090 or "12VHPWR" in cons_4090 or "مزود طاقة" in cons_4090
        elif doc["item_b"]["id"] == "rtx-4090":
            cons_4090 = " ".join(verdict["cons_b"])
            assert "450W" in cons_4090 or "12VHPWR" in cons_4090 or "مزود طاقة" in cons_4090


def test_quality_gate_rule5_no_4k_claims_for_sub75_gpus():
    """Rule 5: No GPU with benchmark_index < 75 described as dedicated for 4K in pros."""
    for fpath in _get_comparison_files():
        doc = _load_comparison(fpath)
        slug = doc["slug"]
        verdict = doc["verdict"]

        for item, pros in [
            (doc["item_a"], verdict["pros_a"]),
            (doc["item_b"], verdict["pros_b"])
        ]:
            if item["category"] == "gpu" and item["benchmark_index"] < 75.0:
                pros_text = " ".join(pros)
                assert "دقة 4K" not in pros_text, f"{slug}: GPU {item['name']} (index {item['benchmark_index']}) falsely praises 4K in pros: {pros_text}"
                assert "ألعاب 4K" not in pros_text, f"{slug}: GPU {item['name']} (index {item['benchmark_index']}) falsely praises 4K in pros: {pros_text}"


def test_quality_gate_rule6_platform_realism_macos_vs_windows():
    """Rule 6: No macOS device beats Windows gaming laptop with dedicated RTX in average FPS."""
    for fpath in _get_comparison_files():
        doc = _load_comparison(fpath)
        slug = doc["slug"]
        a = doc["item_a"]
        b = doc["item_b"]

        if a["category"] == "laptop":
            is_a_mac = a["brand"].upper() == "APPLE"
            is_b_mac = b["brand"].upper() == "APPLE"

            if is_a_mac or is_b_mac:
                benchmarks = doc.get("fps_benchmarks", [])
                if benchmarks:
                    avg_a = sum(b_item["fps_a"] for b_item in benchmarks) / len(benchmarks)
                    avg_b = sum(b_item["fps_b"] for b_item in benchmarks) / len(benchmarks)

                    if is_a_mac:
                        assert avg_a < avg_b, f"{slug}: Apple Mac ({avg_a} FPS) must not beat Windows RTX laptop ({avg_b} FPS)"
                    if is_b_mac:
                        assert avg_b < avg_a, f"{slug}: Apple Mac ({avg_b} FPS) must not beat Windows RTX laptop ({avg_a} FPS)"

                    # Verify platform note is present on all benchmarks
                    for b_item in benchmarks:
                        assert b_item.get("platform_note_ar") is not None, f"{slug}: Missing platform_note_ar on benchmark {b_item['game_id']}"


def test_quality_gate_rule7_equal_tdp_differential_neutrality():
    """Rule 7: Equal TDP spec diff never claims 'السحب الأعلى مقابل السحب المنضبط'."""
    for fpath in _get_comparison_files():
        doc = _load_comparison(fpath)
        slug = doc["slug"]
        diffs = doc.get("spec_differences", [])

        for diff in diffs:
            if diff.get("key") == "tdp_w" and diff.get("winner") == "tie":
                desc = diff.get("advantage_description", "")
                assert "السحب الأعلى مقابل السحب المنضبط" not in desc, (
                    f"{slug}: Equal TDP differential has biased phrasing: {desc}"
                )


def test_quality_gate_zero_amazon_links():
    """Zero-Tolerance Security Check: No Amazon links or tokens exist anywhere in comparison documents."""
    for fpath in _get_comparison_files():
        with open(fpath, "r", encoding="utf-8") as f:
            raw_text = f.read().lower()

        assert "amazon." not in raw_text, f"{fpath} contains forbidden 'amazon.'"
        assert "amzn.to" not in raw_text, f"{fpath} contains forbidden 'amzn.to'"


def test_quality_gate_high_end_gpu_calibration():
    """Verifies RTX 4090 vs RX 7900 XTX has >= 6% index lead and >= 20% FPS lead, while 4080S vs 7900 XTX is a tie."""
    fpath_4090 = os.path.join(COMPARISONS_DIR, "rtx-4090-vs-rx-7900-xtx.json")
    assert os.path.exists(fpath_4090)
    doc_4090 = _load_comparison(fpath_4090)

    # 4090 index lead >= 6%
    index_4090 = doc_4090["item_a"]["benchmark_index"]
    index_7900xtx = doc_4090["item_b"]["benchmark_index"]
    index_lead_pct = ((index_4090 - index_7900xtx) / index_7900xtx) * 100
    assert index_lead_pct >= 6.0, f"RTX 4090 index lead is {index_lead_pct:.2f}%, expected >= 6%"

    # 4090 average FPS lead >= 20%
    benchmarks = doc_4090["fps_benchmarks"]
    avg_fps_4090 = sum(b["fps_a"] for b in benchmarks) / len(benchmarks)
    avg_fps_7900 = sum(b["fps_b"] for b in benchmarks) / len(benchmarks)
    fps_lead_pct = ((avg_fps_4090 - avg_fps_7900) / avg_fps_7900) * 100
    assert fps_lead_pct >= 20.0, f"RTX 4090 average FPS lead is {fps_lead_pct:.2f}%, expected >= 20%"

    # 4080 Super vs 7900 XTX: index difference < 3%
    fpath_4080s = os.path.join(COMPARISONS_DIR, "rtx-4080-super-vs-rx-7900-xtx.json")
    assert os.path.exists(fpath_4080s)
    doc_4080s = _load_comparison(fpath_4080s)
    idx_a = doc_4080s["item_a"]["benchmark_index"]
    idx_b = doc_4080s["item_b"]["benchmark_index"]
    delta_pct = (abs(idx_a - idx_b) / min(idx_a, idx_b)) * 100
    assert delta_pct < 3.0, f"RTX 4080 Super vs RX 7900 XTX delta is {delta_pct:.2f}%, expected < 3%"
