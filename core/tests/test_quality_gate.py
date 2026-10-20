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
    assert len(files) == 80, f"Expected exactly 80 comparison JSON files, found: {len(files)}"
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
            has_eff_pro = any(k in pros_text for k in ["كفاءة استهلاك طاقة ممتازة", "كفاءة طاقة متفوقة", "استهلاك طاقة منضبط", "كفاءة طاقة ممتازة"])
            has_eff_con = any(k in cons_text for k in ["استهلاك طاقة مرتفع", "سحب طاقة مرتفع", "يتطلب مزود طاقة", "متطلبات تبريد مرتفعة", "استهلاك طاقة أعلى"])
            assert not (has_eff_pro and has_eff_con), (
                f"{slug} {label}: Contradiction! Praised efficiency in pros but criticized power in cons: {pros_text} vs {cons_text}"
            )

            # Weight contradiction: never praise heavy weight in pros while criticizing weight in cons
            has_heavy_weight_pro = any(k in pros_text for k in ["مع وزن (2.5 كجم)", "مع وزن (2.6 كجم)", "مع وزن (2.7 كجم)", "مع وزن (2.8 كجم)"])
            assert not has_heavy_weight_pro, (
                f"{slug} {label}: Heavy weight falsely praised in pros: {pros_text}"
            )


def test_quality_gate_rule4_realistic_power_claims():
    """Rule 4: No GPU >= 260W or CPU >= 150W described as 'منضبط' or 'فقط' in power context."""
    for fpath in _get_comparison_files():
        doc = _load_comparison(fpath)
        slug = doc["slug"]
        verdict = doc["verdict"]

        all_editorial_texts = [
            verdict.get("summary_ar", ""),
            verdict.get("gaming_analysis_ar", ""),
            verdict.get("productivity_analysis_ar", ""),
            verdict.get("value_and_budget_ar", ""),
            verdict.get("who_should_buy_a", ""),
            verdict.get("who_should_buy_b", ""),
            " ".join(verdict.get("pros_a", [])),
            " ".join(verdict.get("pros_b", [])),
            " ".join(verdict.get("cons_a", [])),
            " ".join(verdict.get("cons_b", []))
        ]
        full_text = " ".join(all_editorial_texts)

        for item, pros, who in [
            (doc["item_a"], verdict["pros_a"], verdict["who_should_buy_a"]),
            (doc["item_b"], verdict["pros_b"], verdict["who_should_buy_b"])
        ]:
            cat = item["category"]
            tdp = item["tdp_w"]
            combined_text = " ".join(pros) + " " + who

            if cat == "gpu" and tdp >= 260:
                assert "منضبط" not in combined_text, f"{slug}: High TDP GPU ({tdp}W) described as 'منضبط': {combined_text}"
                assert f"{tdp}W فقط" not in full_text, f"{slug}: High TDP GPU ({tdp}W) described with '{tdp}W فقط': {full_text}"
                assert f"بسحب {tdp}W فقط" not in full_text, f"{slug}: High TDP GPU ({tdp}W) described with 'بسحب {tdp}W فقط': {full_text}"

            if cat == "cpu" and tdp >= 150:
                assert "منضبط" not in combined_text, f"{slug}: High TDP CPU ({tdp}W) described as 'منضبط': {combined_text}"
                assert f"{tdp}W فقط" not in full_text, f"{slug}: High TDP CPU ({tdp}W) described with '{tdp}W فقط': {full_text}"
                assert f"بسحب {tdp}W فقط" not in full_text, f"{slug}: High TDP CPU ({tdp}W) described with 'بسحب {tdp}W فقط': {full_text}"

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
                        game_name = b_item.get("game_title", "unknown")
                        assert b_item.get("platform_note_ar") is not None, f"{slug}: Missing platform_note_ar on benchmark {game_name}"


def test_quality_gate_rule7_equal_tdp_differential_neutrality():
    """Rule 7: Equal TDP spec diff never claims 'السحب الأعلى مقابل السحب المنضبط'."""
    for fpath in _get_comparison_files():
        doc = _load_comparison(fpath)
        slug = doc["slug"]
        diffs = doc.get("spec_differences", [])

        for diff in diffs:
            if diff.get("key") == "tdp_w" and diff.get("value_a") == diff.get("value_b"):
                desc = diff.get("advantage_summary_ar", "")
                assert "السحب الأعلى مقابل السحب المنضبط" not in desc, (
                    f"{slug}: Equal TDP differential has biased phrasing: {desc}"
                )
                assert "أقصى طاقة رسومية كاملة" in desc or "استهلاك متماثل" in desc or "سحب طاقة متماثل" in desc, (
                    f"{slug}: Equal TDP differential missing neutral equality phrasing: {desc}"
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

    # 4090 editorial gaming analysis must not claim raster parity
    gaming_analysis = doc_4090["verdict"]["gaming_analysis_ar"]
    assert "أداءً متقارباً في المعالجة الرسومية التقليدية" not in gaming_analysis, (
        f"RTX 4090 vs 7900 XTX claims false raster parity: {gaming_analysis}"
    )

    # 4080 Super vs 7900 XTX: index difference < 3%
    fpath_4080s = os.path.join(COMPARISONS_DIR, "rtx-4080-super-vs-rx-7900-xtx.json")
    assert os.path.exists(fpath_4080s)
    doc_4080s = _load_comparison(fpath_4080s)
    idx_a = doc_4080s["item_a"]["benchmark_index"]
    idx_b = doc_4080s["item_b"]["benchmark_index"]
    delta_pct = (abs(idx_a - idx_b) / min(idx_a, idx_b)) * 100
    assert delta_pct < 3.0, f"RTX 4080 Super vs RX 7900 XTX delta is {delta_pct:.2f}%, expected < 3%"


def test_quality_gate_rx7900xt_revised_msrp_mentioned():
    """Verifies that RX 7900 XT's official revised MSRP ($749) is explicitly stated in value analysis."""
    fpath = os.path.join(COMPARISONS_DIR, "rtx-4070-ti-super-vs-rx-7900-xt.json")
    assert os.path.exists(fpath)
    doc = _load_comparison(fpath)
    value_ar = doc["verdict"]["value_and_budget_ar"]
    assert "749" in value_ar, f"RX 7900 XT revised MSRP ($749) missing from value analysis: {value_ar}"
    assert "خفّضت" in value_ar or "تخفيض" in value_ar or "رسمياً" in value_ar, (
        f"Official markdown note missing from value analysis: {value_ar}"
    )


def test_quality_gate_laptop_personas_accuracy():
    """Verifies laptop buyer personas: Legion Pro 7i is high-end value/vapor chamber, not budget MIL-STD-810H."""
    # Razer Blade 16 vs Legion Pro 7i
    fpath_blade_legion = os.path.join(COMPARISONS_DIR, "razer-blade-16-2024-vs-legion-pro-7i.json")
    assert os.path.exists(fpath_blade_legion)
    doc_blade_legion = _load_comparison(fpath_blade_legion)
    who_legion = doc_blade_legion["verdict"]["who_should_buy_b"]
    assert "MIL-STD-810H" not in who_legion, f"Legion Pro 7i falsely described with MIL-STD-810H: {who_legion}"
    assert "4080" in who_legion or "غرف البخار" in who_legion or "1,600" in who_legion, (
        f"Legion Pro 7i missing high-end value persona: {who_legion}"
    )

    # TUF A15 vs Zephyrus G16: TUF has MIL-STD-810H
    fpath_tuf = os.path.join(COMPARISONS_DIR, "asus-tuf-gaming-a15-vs-rog-zephyrus-g16.json")
    assert os.path.exists(fpath_tuf)
    doc_tuf = _load_comparison(fpath_tuf)
    who_tuf = doc_tuf["verdict"]["who_should_buy_a"]
    assert "MIL-STD-810H" in who_tuf, f"TUF A15 missing MIL-STD-810H durability persona: {who_tuf}"


def test_quality_gate_nvidia_pros_cons_rt_superiority_and_performance_con():
    """Rule 1: Intra-Brand NVIDIA vs NVIDIA Pros/Cons.
    - Only claim 'تفوق في تتبع الأشعة' if card.ray_tracing_score > opp.ray_tracing_score.
    - Otherwise, use neutral 'دعم كامل لتقنيات DLSS 3 (توليد الإطارات) و DLSS 3.5 (إعادة بناء الأشعة) مع تتبع أشعة بمؤشر X/100'.
    - If card.benchmark_index < opp.benchmark_index - 3.0, append performance con 'أداء رسومي إجمالي أقل مقارنة بـ'.
    """
    for fpath in _get_comparison_files():
        doc = _load_comparison(fpath)
        slug = doc["slug"]
        verdict = doc["verdict"]

        for item, opp, pros, cons in [
            (doc["item_a"], doc["item_b"], verdict["pros_a"], verdict["cons_a"]),
            (doc["item_b"], doc["item_a"], verdict["pros_b"], verdict["cons_b"])
        ]:
            if item.get("category") == "gpu" and item.get("brand", "").upper() == "NVIDIA":
                rt_self = item.get("ray_tracing_score") or 0
                rt_opp = opp.get("ray_tracing_score") or 0
                pros_text = " ".join(pros)
                cons_text = " ".join(cons)

                if rt_self <= rt_opp:
                    assert "تفوق في تتبع الأشعة" not in pros_text, (
                        f"{slug}: NVIDIA card {item['name']} (RT={rt_self}) falsely claimed RT superiority over {opp['name']} (RT={rt_opp}) in pros: {pros_text}"
                    )
                    assert "دعم كامل لتقنيات DLSS 3 (توليد الإطارات) و DLSS 3.5 (إعادة بناء الأشعة) مع تتبع أشعة بمؤشر" in pros_text, (
                        f"{slug}: NVIDIA card {item['name']} missing neutral RT pro: {pros_text}"
                    )
                else:
                    assert "تفوق في تتبع الأشعة بمؤشر" in pros_text, (
                        f"{slug}: Winning NVIDIA card {item['name']} missing RT superiority pro: {pros_text}"
                    )

                if item.get("benchmark_index", 0) < opp.get("benchmark_index", 0) - 3.0:
                    assert any("أداء رسومي إجمالي أقل مقارنة بـ" in con for con in cons), (
                        f"{slug}: Weaker NVIDIA card {item['name']} missing performance deficit con against {opp['name']}: {cons_text}"
                    )


def test_quality_gate_gpu_resolution_grounding_by_benchmark_index():
    """Rule 2: Resolution Grounding in GPU Comparisons.
    - No GPU with benchmark_index < 65 described as smooth 1440p card in gaming_analysis_ar or who_should_buy.
    - Target resolution for index < 65 is 'دقة 1080p'.
    - In rtx-4060-ti-vs-rtx-4060: who_should_buy_a targets 'دقة 1080p و 1440p' (not 'الدقات المرتفعة').
    - In AMD vs AMD comparisons with RX 7600 XT: RX 7600 XT targets 'دقة 1080p' in who_should_buy and narrative.
    """
    for fpath in _get_comparison_files():
        doc = _load_comparison(fpath)
        slug = doc["slug"]
        verdict = doc["verdict"]
        gaming_analysis = verdict.get("gaming_analysis_ar", "")

        for item, who in [
            (doc["item_a"], verdict["who_should_buy_a"]),
            (doc["item_b"], verdict["who_should_buy_b"])
        ]:
            if item.get("category") == "gpu":
                bi = item.get("benchmark_index", 0)
                if bi < 65:
                    assert "توازناً ممتازاً على دقة 1440p" not in gaming_analysis, (
                        f"{slug}: Sub-65 GPU {item['name']} described with 'توازناً ممتازاً على دقة 1440p': {gaming_analysis}"
                    )
                    assert "لتشغيل ألعاب دقة 1440p بسلاسة" not in who, (
                        f"{slug}: Sub-65 GPU {item['name']} described with 'لتشغيل ألعاب دقة 1440p بسلاسة': {who}"
                    )
                    assert "1440p" not in who, (
                        f"{slug}: Sub-65 GPU {item['name']} falsely targets 1440p in who_should_buy: {who}"
                    )
                    assert "الدقات المرتفعة" not in who, (
                        f"{slug}: Sub-65 GPU {item['name']} falsely targets 'الدقات المرتفعة' in who_should_buy: {who}"
                    )

    # Specific check: rtx-4060-ti-vs-rtx-4060
    fpath_4060ti_4060 = os.path.join(COMPARISONS_DIR, "rtx-4060-ti-vs-rtx-4060.json")
    if os.path.exists(fpath_4060ti_4060):
        doc = _load_comparison(fpath_4060ti_4060)
        who_a = doc["verdict"]["who_should_buy_a"]
        who_b = doc["verdict"]["who_should_buy_b"]
        assert "الدقات المرتفعة" not in who_a, f"4060 Ti falsely claims 'الدقات المرتفعة': {who_a}"
        assert "دقة 1080p و 1440p" in who_a, f"4060 Ti missing 'دقة 1080p و 1440p': {who_a}"
        assert "دقة 1080p" in who_b, f"4060 missing 'دقة 1080p': {who_b}"

    # Specific check: rx-7800-xt-vs-rx-7600-xt
    fpath_7800_7600 = os.path.join(COMPARISONS_DIR, "rx-7800-xt-vs-rx-7600-xt.json")
    if os.path.exists(fpath_7800_7600):
        doc = _load_comparison(fpath_7800_7600)
        who_b = doc["verdict"]["who_should_buy_b"]
        gaming = doc["verdict"]["gaming_analysis_ar"]
        assert "دقة 1080p" in who_b, f"RX 7600 XT missing 'دقة 1080p' in who_should_buy: {who_b}"
        assert "توازناً ممتازاً على دقة 1080p" in gaming, f"RX 7600 XT missing 'توازناً ممتازاً على دقة 1080p': {gaming}"


def test_quality_gate_dual_x3d_cpu_gaming_narrative():
    """Rule 3: Dual-X3D CPU Gaming Analysis.
    - In ryzen-9-7950x3d-vs-ryzen-7-7800x3d, single_ccd (7800X3D) and dual_ccd (7950X3D) are accurately contrasted.
    - 7800X3D holds slight edge in pure gaming 1% low FPS consistency thanks to Single-CCD design.
    - 7950X3D combines 3D V-Cache with 16-core heavy multitasking/streaming superiority.
    - Must NOT claim 7950X3D has an edge in 1% low FPS.
    """
    fpath_x3d = os.path.join(COMPARISONS_DIR, "ryzen-9-7950x3d-vs-ryzen-7-7800x3d.json")
    assert os.path.exists(fpath_x3d), f"File {fpath_x3d} does not exist"
    doc = _load_comparison(fpath_x3d)
    gaming = doc["verdict"]["gaming_analysis_ar"]

    assert "معمارية الشريحة الواحدة Single CCD دون أي تأخير بين الشرائح" in gaming, (
        f"Missing Single-CCD explanation in gaming analysis: {gaming}"
    )
    assert "استقرار معدلات الإطارات الدنيا (1% low FPS)" in gaming, (
        f"Missing 1% low FPS consistency mention: {gaming}"
    )
    assert "3D V-Cache" in gaming, f"Missing 3D V-Cache mention: {gaming}"
    assert "أسبقية طفيفة لـ AMD Ryzen 9 7950X3D في استقرار 1% low FPS" not in gaming, (
        f"7950X3D falsely credited with 1% low FPS edge: {gaming}"
    )
    assert "AMD Ryzen 7 7800X3D" in gaming, f"Missing 7800X3D in gaming analysis: {gaming}"
    assert "تعدد المهام والبث المباشر" in gaming or "صناعة المحتوى" in gaming, (
        f"Missing multitasking/streaming description for 7950X3D: {gaming}"
    )
