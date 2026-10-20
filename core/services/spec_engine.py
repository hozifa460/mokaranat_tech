"""
Hardware Specification Comparison Engine.
Clean Architecture - Layer: Services
Compares two hardware specs and produces normalized differential items with winner flags.
"""

from typing import List, Tuple, Any
from core.domain.models import HardwareSpec, SpecDiffItem


def _format_num(val: Any) -> str:
    """Formats numeric values cleanly without awkward trailing .0 (e.g. 75.0 -> 75)."""
    if val is None:
        return "0"
    if isinstance(val, (int, float)):
        if float(val).is_integer():
            return str(int(val))
        return f"{val:.1f}".rstrip("0").rstrip(".")
    return str(val)


class SpecEngine:
    """Engine for analyzing and contrasting technical specifications between two hardware units."""

    @classmethod
    def compare_specs(cls, item_a: HardwareSpec, item_b: HardwareSpec) -> List[SpecDiffItem]:
        diffs: List[SpecDiffItem] = []

        # 1. Benchmark Index
        diffs.append(cls._compare_numeric(
            key="benchmark_index",
            label_ar="مؤشر الأداء العام (Benchmark Index)",
            val_a=item_a.benchmark_index,
            val_b=item_b.benchmark_index,
            unit="/ 100",
            higher_is_better=True,
            summary_pattern="تفوق في الأداء الكلي بنسبة {diff}%"
        ))

        # 2. Launch Price (MSRP USD) - lower is better for user budget
        diffs.append(cls._compare_numeric(
            key="launch_msrp_usd",
            label_ar="سعر الإطلاق الرسمي",
            val_a=item_a.launch_msrp_usd,
            val_b=item_b.launch_msrp_usd,
            unit="$",
            higher_is_better=False,
            summary_pattern="أوفر بالسعر بنسبة {diff}%"
        ))

        # 3. Power Consumption (TDP Watts) - lower is better for desktops, customized for gaming laptops
        is_laptop = item_a.category == "laptop" or item_b.category == "laptop"
        if is_laptop:
            if item_a.tdp_w == item_b.tdp_w:
                diffs.append(SpecDiffItem(
                    key="tdp_w",
                    label_ar="أقصى استهلاك رسومي متاح (GPU TGP / Thermal Budget)",
                    value_a=item_a.tdp_w,
                    value_b=item_b.tdp_w,
                    unit="W",
                    winner="tie",
                    diff_percentage=0.0,
                    advantage_summary_ar=f"كلا الجهازين يوفران أقصى طاقة رسومية كاملة ({item_a.tdp_w}W TGP) لأعلى أداء مستدام"
                ))
            else:
                max_tgp = max(item_a.tdp_w, item_b.tdp_w)
                min_tgp = min(item_a.tdp_w, item_b.tdp_w)
                tdp_diff_pct = round(abs(item_a.tdp_w - item_b.tdp_w) / max_tgp * 100, 1) if max_tgp > 0 else 0.0
                diffs.append(SpecDiffItem(
                    key="tdp_w",
                    label_ar="أقصى استهلاك رسومي متاح (GPU TGP / Thermal Budget)",
                    value_a=item_a.tdp_w,
                    value_b=item_b.tdp_w,
                    unit="W",
                    winner="tie",
                    diff_percentage=tdp_diff_pct,
                    advantage_summary_ar=f"مقياس هندسي: يمنح السحب الأعلى ({max_tgp}W) أداء رسومياً مستداماً وترددات بطاقة أعلى، بينما يتيح السحب المنضبط ({min_tgp}W) هيكلاً فائق النحافة وحرارة أقل"
                ))
        else:
            diffs.append(cls._compare_numeric(
                key="tdp_w",
                label_ar="استهلاك الطاقة المكتبي (TDP)",
                val_a=item_a.tdp_w,
                val_b=item_b.tdp_w,
                unit="W",
                higher_is_better=False,
                summary_pattern="استهلاك طاقة أقل وتوليد حراري أهدأ بفارق {diff}%"
            ))

        # 4. Manufacturing Process Node (nm)
        # Cross-architecture comparison (e.g. monolithic TSMC 4N vs chiplets 5nm/6nm) is misleading
        # due to differing transistor densities and packaging architectures. Treat as informational tie.
        is_cross_architecture = item_a.architecture.strip().lower() != item_b.architecture.strip().lower()
        if item_a.process_node_nm == item_b.process_node_nm:
            diffs.append(SpecDiffItem(
                key="process_node_nm",
                label_ar="دقة التصنيع (Process Node)",
                value_a=item_a.process_node_nm,
                value_b=item_b.process_node_nm,
                unit="nm",
                winner="tie",
                diff_percentage=0.0,
                advantage_summary_ar="دقة تصنيع متطابقة عتادياً"
            ))
        elif is_cross_architecture:
            is_cpu_comparison = item_a.category == "cpu" or item_b.category == "cpu"
            has_intel_cpu = is_cpu_comparison and ("intel" in item_a.brand.lower() or "intel" in item_b.brand.lower())
            if has_intel_cpu:
                proc_summary = "مقياس تقني استرشادي: تعتمد إنتل معيار Intel 7 (10nm Enhanced SuperFin) بكثافة ترانزستورات مكافئة لـ 7nm، وتختلف بنيوياً عن معيار TSMC 5nm في معالجات AMD"
            else:
                proc_summary = "مقياس تقني استرشادي: تختلف هندسة دقة التصنيع وكثافة الترانزستورات والتصميم (رقاقة أحادية Monolithic مقابل رقاقات Chiplets) بين المعماريات المختلفة"

            diffs.append(SpecDiffItem(
                key="process_node_nm",
                label_ar="دقة التصنيع (Process Node)",
                value_a=item_a.process_node_nm,
                value_b=item_b.process_node_nm,
                unit="nm",
                winner="tie",
                diff_percentage=0.0,
                advantage_summary_ar=proc_summary
            ))
        else:
            diffs.append(cls._compare_numeric(
                key="process_node_nm",
                label_ar="دقة التصنيع (Process Node)",
                val_a=item_a.process_node_nm,
                val_b=item_b.process_node_nm,
                unit="nm",
                higher_is_better=False,
                summary_pattern="معمارية تصنيع أحدث وأكثر كفاءة ترانزستورات"
            ))

        # 5. Ray Tracing Performance Score (Applicable to GPUs and Laptops with discrete GPUs)
        if item_a.category in ("gpu", "laptop") and item_b.category in ("gpu", "laptop"):
            if item_a.ray_tracing_score is not None and item_b.ray_tracing_score is not None:
                diffs.append(cls._compare_numeric(
                    key="ray_tracing_score",
                    label_ar="كفاءة تتبع الأشعة (Ray Tracing)",
                    val_a=item_a.ray_tracing_score,
                    val_b=item_b.ray_tracing_score,
                    unit="/ 100",
                    higher_is_better=True,
                    summary_pattern="معالجة متقدمة لتقنيات الإضاءة الواقعية بفارق {diff}%"
                ))

        # 6. Energy Efficiency Score
        diffs.append(cls._compare_numeric(
            key="efficiency_score",
            label_ar="معيار الكفاءة مقابل الواط",
            val_a=item_a.efficiency_score,
            val_b=item_b.efficiency_score,
            unit="/ 100",
            higher_is_better=True,
            summary_pattern="أداء أعلى لكل واط مستهلك"
        ))

        # Category-Specific Specs Comparison (from raw_specs)
        if item_a.category == "gpu" and item_b.category == "gpu":
            diffs.extend(cls._compare_gpu_raw_specs(item_a, item_b))
        elif item_a.category == "cpu" and item_b.category == "cpu":
            diffs.extend(cls._compare_cpu_raw_specs(item_a, item_b))
        elif item_a.category == "laptop" and item_b.category == "laptop":
            diffs.extend(cls._compare_laptop_raw_specs(item_a, item_b))

        return diffs

    @classmethod
    def _compare_numeric(
        cls,
        key: str,
        label_ar: str,
        val_a: float,
        val_b: float,
        unit: str,
        higher_is_better: bool,
        summary_pattern: str
    ) -> SpecDiffItem:
        if val_a == val_b:
            if key == "launch_msrp_usd":
                summary = "السعر متطابق"
            elif key == "tdp_w":
                summary = f"سحب طاقة متماثل تماماً ({_format_num(val_a)}W) لكلا المعالجين/البطاقتين"
            else:
                summary = "متطابق في هذه القيمة"
            return SpecDiffItem(
                key=key,
                label_ar=label_ar,
                value_a=val_a,
                value_b=val_b,
                unit=unit,
                winner="tie",
                diff_percentage=0.0,
                advantage_summary_ar=summary
            )

        if higher_is_better:
            raw_winner = "a" if val_a > val_b else "b"
            base_min = min(val_a, val_b)
            diff_pct = abs(val_a - val_b) / (base_min if base_min > 0 else 1) * 100
        else:
            raw_winner = "a" if val_a < val_b else "b"
            base_max = max(val_a, val_b)
            diff_pct = abs(val_a - val_b) / (base_max if base_max > 0 else 1) * 100

        rounded_diff_pct = round(diff_pct, 1)

        # Statistical margin rule: below 3% is within measurement/silicon error margin -> treat as tie
        if rounded_diff_pct < 3.0:
            if key == "launch_msrp_usd":
                summary = "السعر متطابق تقريباً (فارق هامشي أقل من 3%)"
            else:
                summary = "تعادل / تقارب في الأداء (فارق هامشي أقل من 3%)"
            return SpecDiffItem(
                key=key,
                label_ar=label_ar,
                value_a=val_a,
                value_b=val_b,
                unit=unit,
                winner="tie",
                diff_percentage=rounded_diff_pct,
                advantage_summary_ar=summary
            )

        summary = summary_pattern.format(diff=_format_num(rounded_diff_pct))

        return SpecDiffItem(
            key=key,
            label_ar=label_ar,
            value_a=val_a,
            value_b=val_b,
            unit=unit,
            winner=raw_winner,
            diff_percentage=rounded_diff_pct,
            advantage_summary_ar=summary
        )

    @classmethod
    def _compare_gpu_raw_specs(cls, a: HardwareSpec, b: HardwareSpec) -> List[SpecDiffItem]:
        items = []
        raw_a = a.raw_specs
        raw_b = b.raw_specs

        # VRAM Capacity
        vram_a = raw_a.get("vram_gb", 0)
        vram_b = raw_b.get("vram_gb", 0)
        if vram_a and vram_b:
            max_vram = max(float(vram_a), float(vram_b))
            max_bench = max(a.benchmark_index, b.benchmark_index)
            if max_bench >= 90 or (max_bench >= 85 and max_vram >= 24):
                vram_summary = "سعة VRAM أكبر تمنح أماناً فائقاً في الألعاب بدقة 4K وعمليات الرندرة الضخمة"
            elif max_bench >= 75 and (max_bench >= 80 or max_vram >= 16):
                vram_summary = "سعة VRAM أكبر تمنح أريحية فائقة في ألعاب 1440p و 4K وتطبيقات التصميم"
            else:
                vram_summary = "سعة VRAM أكبر تمنح أريحية ممتازة في الألعاب بدقة 1440p وتفادي اختناق القوام"

            items.append(cls._compare_numeric(
                key="vram_gb",
                label_ar="سعة الذاكرة الرسومية (VRAM)",
                val_a=float(vram_a),
                val_b=float(vram_b),
                unit="GB",
                higher_is_better=True,
                summary_pattern=vram_summary
            ))

        # Memory Bus Width
        bus_a = raw_a.get("bus_width_bit", 0)
        bus_b = raw_b.get("bus_width_bit", 0)
        if bus_a and bus_b:
            items.append(cls._compare_numeric(
                key="bus_width_bit",
                label_ar="عرض ناقل الذاكرة (Memory Bus)",
                val_a=float(bus_a),
                val_b=float(bus_b),
                unit="bit",
                higher_is_better=True,
                summary_pattern="عرض نطاق أوسع لنقل البيانات الرسومية بسلاسة"
            ))

        # Boost Clock
        boost_a = raw_a.get("boost_clock_mhz", 0)
        boost_b = raw_b.get("boost_clock_mhz", 0)
        if boost_a and boost_b:
            if a.architecture.strip().lower() != b.architecture.strip().lower():
                items.append(SpecDiffItem(
                    key="boost_clock_mhz",
                    label_ar="تردد التعزيز (Boost Clock)",
                    value_a=float(boost_a),
                    value_b=float(boost_b),
                    unit="MHz",
                    winner="tie",
                    diff_percentage=0.0,
                    advantage_summary_ar="مقياس استرشادي: تختلف كفاءة التردد وتعليمات الدورة (IPC) باختلاف المعمارية، ولا يقاس الأداء بالتردد الخام وحده"
                ))
            else:
                items.append(cls._compare_numeric(
                    key="boost_clock_mhz",
                    label_ar="تردد التعزيز (Boost Clock)",
                    val_a=float(boost_a),
                    val_b=float(boost_b),
                    unit="MHz",
                    higher_is_better=True,
                    summary_pattern="تردد أعلى لسرعة معالجة الرسوميات الإطارية"
                ))

        # PCIe Interface & Bus Lanes
        pcie_a = a.pcie_interface or raw_a.get("pcie_interface")
        pcie_b = b.pcie_interface or raw_b.get("pcie_interface")
        if pcie_a and pcie_b:
            lanes_a = raw_a.get("pcie_lanes") or (8 if "x8" in str(pcie_a).lower() else 16)
            lanes_b = raw_b.get("pcie_lanes") or (8 if "x8" in str(pcie_b).lower() else 16)
            if lanes_a == lanes_b:
                summary = (
                    f"واجهة توصيل متطابقة بكامل المسارات ({lanes_a} مساراً)"
                    if lanes_a == 16
                    else f"واجهة توصيل متطابقة تقتصر على {lanes_a} مسارات (PCIe 4.0 x{lanes_a}) على كلا البطاقتين"
                )
                items.append(SpecDiffItem(
                    key="pcie_interface",
                    label_ar="واجهة التوصيل العتادية (PCIe Interface)",
                    value_a=str(pcie_a),
                    value_b=str(pcie_b),
                    unit="",
                    winner="tie",
                    diff_percentage=0.0,
                    advantage_summary_ar=summary
                ))
            elif lanes_a > lanes_b:
                items.append(SpecDiffItem(
                    key="pcie_interface",
                    label_ar="واجهة التوصيل العتادية (PCIe Interface)",
                    value_a=str(pcie_a),
                    value_b=str(pcie_b),
                    unit="",
                    winner="a",
                    diff_percentage=round(((lanes_a - lanes_b) / lanes_b) * 100, 1),
                    advantage_summary_ar=f"واجهة كاملة بـ {lanes_a} مساراً تمنع اختناق نقل البيانات وتذبذب الإطارات عند امتلاء الذاكرة"
                ))
            else:
                items.append(SpecDiffItem(
                    key="pcie_interface",
                    label_ar="واجهة التوصيل العتادية (PCIe Interface)",
                    value_a=str(pcie_a),
                    value_b=str(pcie_b),
                    unit="",
                    winner="b",
                    diff_percentage=round(((lanes_b - lanes_a) / lanes_a) * 100, 1),
                    advantage_summary_ar=f"واجهة كاملة بـ {lanes_b} مساراً تمنع اختناق نقل البيانات وتذبذب الإطارات عند امتلاء الذاكرة"
                ))

        return items

    @classmethod
    def _compare_cpu_raw_specs(cls, a: HardwareSpec, b: HardwareSpec) -> List[SpecDiffItem]:
        items = []
        raw_a = a.raw_specs
        raw_b = b.raw_specs

        # Core count
        cores_a = raw_a.get("total_cores", 0)
        cores_b = raw_b.get("total_cores", 0)
        if cores_a and cores_b:
            items.append(cls._compare_numeric(
                key="total_cores",
                label_ar="إجمالي الأنوية (Cores)",
                val_a=float(cores_a),
                val_b=float(cores_b),
                unit="أنوية",
                higher_is_better=True,
                summary_pattern="عدد أنوية أكبر لتعدد المهام والرندرة البرمجية الثقيلة"
            ))

        # Threads
        threads_a = raw_a.get("threads", 0)
        threads_b = raw_b.get("threads", 0)
        if threads_a and threads_b:
            items.append(cls._compare_numeric(
                key="threads",
                label_ar="المسارات المعالجة (Threads)",
                val_a=float(threads_a),
                val_b=float(threads_b),
                unit="مسار",
                higher_is_better=True,
                summary_pattern="توازي معالجة أسرع للبرمجيات الثقيلة"
            ))

        # L3 Cache
        l3_a = raw_a.get("l3_cache_mb", 0)
        l3_b = raw_b.get("l3_cache_mb", 0)
        if l3_a and l3_b:
            items.append(cls._compare_numeric(
                key="l3_cache_mb",
                label_ar="الذاكرة المخبئية المستوى الثالث (L3 Cache)",
                val_a=float(l3_a),
                val_b=float(l3_b),
                unit="MB",
                higher_is_better=True,
                summary_pattern="ذاكرة كاش أضخم لتقليل زمن التأخير وتسريع معدل الإطارات بالألعاب"
            ))

        # Boost Clock (GHz)
        boost_a = raw_a.get("boost_clock_ghz") or (raw_a.get("boost_clock_mhz", 0) / 1000.0 if raw_a.get("boost_clock_mhz") else 0)
        boost_b = raw_b.get("boost_clock_ghz") or (raw_b.get("boost_clock_mhz", 0) / 1000.0 if raw_b.get("boost_clock_mhz") else 0)
        if boost_a and boost_b:
            unit = "GHz"
            is_cross_architecture = a.architecture.strip().lower() != b.architecture.strip().lower()
            if is_cross_architecture:
                items.append(SpecDiffItem(
                    key="boost_clock_ghz",
                    label_ar="تردد التعزيز الأقصى (Boost Clock)",
                    value_a=float(boost_a),
                    value_b=float(boost_b),
                    unit=unit,
                    winner="tie",
                    diff_percentage=0.0,
                    advantage_summary_ar="مقياس استرشادي: تختلف كفاءة التردد وتعليمات الدورة (IPC) باختلاف معمارية المعالج، ولا يقاس الأداء بالتردد الخام وحده"
                ))
            else:
                items.append(cls._compare_numeric(
                    key="boost_clock_ghz",
                    label_ar="تردد التعزيز الأقصى (Boost Clock)",
                    val_a=float(boost_a),
                    val_b=float(boost_b),
                    unit=unit,
                    higher_is_better=True,
                    summary_pattern="تردد أعلى لسرعة تنفيذ التعليمات الفردية بفارق {diff}%"
                ))

        return items

    @classmethod
    def _compare_laptop_raw_specs(cls, a: HardwareSpec, b: HardwareSpec) -> List[SpecDiffItem]:
        items = []
        raw_a = a.raw_specs
        raw_b = b.raw_specs

        weight_a = raw_a.get("weight_kg", 0)
        weight_b = raw_b.get("weight_kg", 0)
        if weight_a and weight_b:
            items.append(cls._compare_numeric(
                key="weight_kg",
                label_ar="وزن الجهاز المحمول",
                val_a=float(weight_a),
                val_b=float(weight_b),
                unit="kg",
                higher_is_better=False,
                summary_pattern="أخف وزناً وسهولة أعلى في التنقل اليومي"
            ))

        battery_a = raw_a.get("battery_wh", 0)
        battery_b = raw_b.get("battery_wh", 0)
        if battery_a and battery_b:
            items.append(cls._compare_numeric(
                key="battery_wh",
                label_ar="سعة البطارية (Watt-hours)",
                val_a=float(battery_a),
                val_b=float(battery_b),
                unit="Wh",
                higher_is_better=True,
                summary_pattern="سعة بطارية أكبر للعمل لفترات أطول خارج المقبس"
            ))

        display_a = raw_a.get("display")
        display_b = raw_b.get("display")
        if display_a and display_b:
            d_a = str(display_a).lower()
            d_b = str(display_b).lower()
            is_oled_a = "oled" in d_a
            is_oled_b = "oled" in d_b
            is_mini_a = "mini-led" in d_a or "retina xdr" in d_a
            is_mini_b = "mini-led" in d_b or "retina xdr" in d_b

            has_500 = "500" in d_a or "500" in d_b or any("500" in str(f).lower() for f in a.features + b.features)
            ips_desc = "بـ 500 nits سطوع عالٍ وثابت دون مخاطر تطبيع (Burn-in)" if has_500 else "بثبات الإضاءة ومعدل تحديث سريع دون مخاطر تطبيع (Burn-in)"

            if is_oled_a and not is_oled_b and not is_mini_b:
                advantage = f"مقارنة شاشات: شاشة OLED تمتاز بتباين لانهائي وسواد حقيقي وزمن استجابة 0.2ms، بينما تمتاز شاشة IPS {ips_desc}"
            elif is_oled_b and not is_oled_a and not is_mini_a:
                advantage = f"مقارنة شاشات: شاشة OLED تمتاز بتباين لانهائي وسواد حقيقي وزمن استجابة 0.2ms، بينما تمتاز شاشة IPS {ips_desc}"
            elif is_mini_a and is_oled_b:
                advantage = "مقارنة شاشات: شاشة Mini-LED تتفوق بسطوع فائق (1000-1600 nits) دون مخاطر تطبيع (Burn-in)، بينما تمتاز شاشة OLED بتباين لانهائي لكل بكسل وزمن استجابة 0.2ms"
            elif is_mini_b and is_oled_a:
                advantage = "مقارنة شاشات: شاشة OLED تمتاز بتباين لانهائي لكل بكسل وزمن استجابة 0.2ms، بينما تتفوق شاشة Mini-LED بسطوع فائق (1000-1600 nits) دون مخاطر تطبيع (Burn-in)"
            elif (is_mini_a and not is_mini_b) or (is_mini_b and not is_mini_a):
                advantage = "مقارنة شاشات: شاشة Mini-LED متقدمة بسطوع سينمائي (1000-1600 nits) ومناطق تعتيم محلي لتباين HDR وسواد عميق مقارنة بشاشات IPS التقليدية"
            elif is_mini_a and is_mini_b:
                advantage = "مقارنة شاشات: تقنية Mini-LED متطورة على كلا الجهازين بسطوع فائق ومناطق تعتيم محلي دقيقة لإنتاج محتوى HDR واللعب الاحترافي"
            else:
                advantage = "مقارنة شاشات: تقنيات عرض متقدمة بمعدلات تحديث سريعة ملائمة للألعاب التنافسية وصناعة المحتوى"

            items.append(SpecDiffItem(
                key="display",
                label_ar="تقنية ومواصفات الشاشة",
                value_a=str(display_a),
                value_b=str(display_b),
                unit="",
                winner="tie",
                diff_percentage=0.0,
                advantage_summary_ar=advantage
            ))

        ram_a = raw_a.get("ram_gb")
        ram_b = raw_b.get("ram_gb")
        if ram_a and ram_b:
            val_a_f = float(ram_a)
            val_b_f = float(ram_b)
            is_apple_a = "apple" in a.brand.lower() or "apple" in a.name.lower()
            is_apple_b = "apple" in b.brand.lower() or "apple" in b.name.lower()
            apple_bw = raw_a.get("unified_memory_bandwidth_gbps", 300) if is_apple_a else raw_b.get("unified_memory_bandwidth_gbps", 300)

            if (is_apple_a and val_a_f > val_b_f) or (is_apple_b and val_b_f > val_a_f):
                ram_summary = f"سعة ذاكرة أكبر مدعومة بذاكرة موحدة (Unified Memory) فائقة السرعة ({apple_bw}GB/s) تمنح معمارية Apple Silicon سرعة تشارك بيانات فورية"
            elif (is_apple_a and val_b_f > val_a_f) or (is_apple_b and val_a_f > val_b_f):
                ram_summary = "سعة ذاكرة عشوائية أكبر لتشغيل ألعاب العصر وتعدد المهام الثقيلة مع إمكانية الترقية المستقبلية"
            elif is_apple_a or is_apple_b:
                ram_summary = f"سعة ذاكرة متكافئة مع تميز معمارية Apple Silicon بنطاق ترددي فائق للذاكرة الموحدة ({apple_bw}GB/s)"
            else:
                ram_summary = "سعة ذاكرة عشوائية أكبر لتشغيل ألعاب العصر وتعدد المهام الثقيلة"

            items.append(cls._compare_numeric(
                key="ram_gb",
                label_ar="سعة الذاكرة العشوائية (RAM)",
                val_a=val_a_f,
                val_b=val_b_f,
                unit="GB",
                higher_is_better=True,
                summary_pattern=ram_summary
            ))

        return items
