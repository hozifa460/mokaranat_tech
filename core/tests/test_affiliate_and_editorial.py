"""
Tests for AffiliateEngine, AiEditorialService, and HardwareRepository.
"""

import tempfile
from pathlib import Path
import pytest
from core.domain.models import HardwareSpec
from core.services.affiliate_engine import AffiliateEngine, ForbiddenStoreError
from core.services.ai_editorial import AiEditorialService, EditorialRuleEngine
from core.services.fps_calculator import FpsCalculator
from core.repository.database import initialize_schema
from core.repository.hardware_repo import HardwareRepository


def test_affiliate_engine_stores():
    spec = HardwareSpec(
        id="test-card",
        slug="test-card",
        name="Test Graphic Card",
        category="gpu",
        brand="NVIDIA",
        release_year=2024,
        launch_msrp_usd=500.0,
        architecture="Arch",
        process_node_nm=4.0,
        tdp_w=200,
        benchmark_index=80.0
    )

    offers = AffiliateEngine.generate_offers_for_item(spec)
    assert len(offers) == 4
    store_keys = [o.store_key for o in offers]
    assert "noon" in store_keys
    assert "newegg" in store_keys
    assert "aliexpress" in store_keys
    assert "jumia" in store_keys

    # Assert NO Amazon anywhere
    for offer in offers:
        assert "amazon" not in offer.store_key.lower()
        assert "amazon" not in offer.affiliate_url.lower()


def test_affiliate_engine_forbids_amazon_url():
    with pytest.raises(ForbiddenStoreError):
        AffiliateEngine.sanitize_and_validate_url("https://www.amazon.com/dp/B00000?tag=mypartner")


def test_ai_editorial_heuristic_generation():
    service = AiEditorialService(api_key="")
    spec_a = HardwareSpec(
        id="card-1",
        slug="card-1",
        name="Card One",
        category="gpu",
        brand="NVIDIA",
        release_year=2024,
        launch_msrp_usd=599.0,
        architecture="Ada",
        process_node_nm=4.0,
        tdp_w=200,
        raw_specs={"vram_gb": 12},
        benchmark_index=88.0,
        ray_tracing_score=85.0,
        efficiency_score=90.0
    )
    spec_b = HardwareSpec(
        id="card-2",
        slug="card-2",
        name="Card Two",
        category="gpu",
        brand="AMD",
        release_year=2023,
        launch_msrp_usd=499.0,
        architecture="RDNA 3",
        process_node_nm=5.0,
        tdp_w=250,
        raw_specs={"vram_gb": 16},
        benchmark_index=80.0,
        ray_tracing_score=65.0,
        efficiency_score=75.0
    )

    verdict = service.generate_verdict(spec_a, spec_b)
    assert verdict.overall_winner == "a"
    assert "Card One" in verdict.winner_name
    assert len(verdict.pros_a) > 0
    assert len(verdict.cons_b) > 0
    assert len(verdict.quick_verdict_ar) > 20


def test_hardware_repository_crud():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = Path(tmpdir) / "test_hardware.db"
        initialize_schema(test_db)
        repo = HardwareRepository(db_path=test_db)

        spec = HardwareSpec(
            id="test-cpu",
            slug="test-cpu",
            name="Test CPU 9000",
            category="cpu",
            brand="AMD",
            release_year=2024,
            launch_msrp_usd=350.0,
            architecture="Zen 5",
            process_node_nm=4.0,
            tdp_w=105,
            raw_specs={"total_cores": 12, "threads": 24},
            benchmark_index=88.5,
            gaming_scores={"gaming_overall": 90.0},
            ray_tracing_score=80.0,
            efficiency_score=92.0,
            features=["3D Cache"]
        )

        repo.upsert_hardware_spec(spec)
        fetched = repo.get_hardware_by_id("test-cpu")
        assert fetched is not None
        assert fetched.name == "Test CPU 9000"
        assert fetched.benchmark_index == 88.5

        listed = repo.list_by_category("cpu")
        assert len(listed) == 1
        assert listed[0].id == "test-cpu"


def test_ai_editorial_laptop_cons_avoid_desktop_terms():
    service = AiEditorialService(api_key="")
    lap_a = HardwareSpec(
        id="lap-a",
        slug="lap-a",
        name="Laptop Alpha",
        category="laptop",
        brand="ASUS",
        release_year=2024,
        launch_msrp_usd=1800.0,
        architecture="Intel Ultra",
        process_node_nm=4.0,
        tdp_w=100,
        raw_specs={"weight_kg": 1.9, "battery_wh": 90, "display": "16-inch OLED"},
        benchmark_index=85.0
    )
    lap_b = HardwareSpec(
        id="lap-b",
        slug="lap-b",
        name="Laptop Beta",
        category="laptop",
        brand="Lenovo",
        release_year=2024,
        launch_msrp_usd=2000.0,
        architecture="Intel 14th",
        process_node_nm=4.0,
        tdp_w=175,
        raw_specs={"weight_kg": 2.6, "battery_wh": 99, "display": "16-inch IPS"},
        benchmark_index=90.0
    )

    verdict = service.generate_verdict(lap_a, lap_b)

    all_cons = " ".join(verdict.cons_a + verdict.cons_b)
    # Must NOT mention desktop PSU or PC case!
    assert "مزود طاقة" not in all_cons
    assert "الصندوق" not in all_cons
    # Should mention laptop-relevant terms
    assert any("محمول" in text or "الهواء" in text or "وزن" in text or "ألعاب" in text for text in (verdict.cons_a + verdict.cons_b))


def test_comparison_exporter_rejects_cross_category():
    from core.services.exporter import ComparisonExporter

    exporter = ComparisonExporter()
    gpu = HardwareSpec(
        id="gpu-test",
        slug="gpu-test",
        name="GPU Test",
        category="gpu",
        brand="NVIDIA",
        release_year=2024,
        launch_msrp_usd=600.0,
        architecture="Ada",
        process_node_nm=4.0,
        tdp_w=200,
        benchmark_index=85.0
    )
    cpu = HardwareSpec(
        id="cpu-test",
        slug="cpu-test",
        name="CPU Test",
        category="cpu",
        brand="AMD",
        release_year=2024,
        launch_msrp_usd=400.0,
        architecture="Zen 5",
        process_node_nm=4.0,
        tdp_w=105,
        benchmark_index=90.0
    )

    with pytest.raises(ValueError) as exc:
        exporter.build_comparison(gpu, cpu)
    assert "Cannot compare items from different categories" in str(exc.value)


def test_gemini_verdict_json_regex_resilience():
    from unittest.mock import MagicMock

    service = AiEditorialService(api_key="mock_key")
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = """
Here is your technical analysis in Arabic:
```json
{
  "overall_winner": "a",
  "winner_name": "Test GPU Alpha",
  "score_a": 85.0,
  "score_b": 80.0,
  "quick_verdict_ar": "تفوق تقني واضح في الأداء الحسابي",
  "gaming_analysis_ar": "أداء ألعاب متفوق على دقة 1440p",
  "productivity_analysis_ar": "إنتاجية عالية في الرندرة",
  "value_and_budget_ar": "قيمة استثمارية ممتازة",
  "pros_a": ["ميزة 1", "ميزة 2"],
  "cons_a": ["عيب 1"],
  "pros_b": ["ميزة 1"],
  "cons_b": ["عيب 1"],
  "who_should_buy_a": "المصممون واللاعبون",
  "who_should_buy_b": "المستخدم الاقتصادي"
}
```
Hope this comparison helps your readers!
"""
    mock_client.models.generate_content.return_value = mock_response
    service._client = mock_client

    gpu_a = HardwareSpec(
        id="gpu-1", slug="gpu-1", name="Test GPU Alpha", category="gpu", brand="NVIDIA",
        release_year=2024, launch_msrp_usd=500.0, architecture="Ada", process_node_nm=4.0,
        tdp_w=200, benchmark_index=85.0
    )
    gpu_b = HardwareSpec(
        id="gpu-2", slug="gpu-2", name="Test GPU Beta", category="gpu", brand="AMD",
        release_year=2024, launch_msrp_usd=450.0, architecture="RDNA 3", process_node_nm=5.0,
        tdp_w=220, benchmark_index=80.0
    )

    verdict = service._call_gemini_verdict(gpu_a, gpu_b)
    assert verdict is not None
    assert verdict.overall_winner == "a"
    assert verdict.winner_name == "Test GPU Alpha"


def test_ai_editorial_identical_price_no_zero_percent_glitch():
    service = AiEditorialService(api_key="")
    spec_a = HardwareSpec(
        id="rtx-4080-super", slug="rtx-4080-super", name="NVIDIA GeForce RTX 4080 Super",
        category="gpu", brand="NVIDIA", release_year=2024, launch_msrp_usd=999.0,
        architecture="Ada Lovelace", process_node_nm=4.0, tdp_w=320,
        raw_specs={"vram_gb": 16, "bus_width_bit": 256}, benchmark_index=92.0,
        ray_tracing_score=93.0, efficiency_score=88.0
    )
    spec_b = HardwareSpec(
        id="rx-7900-xtx", slug="rx-7900-xtx", name="AMD Radeon RX 7900 XTX",
        category="gpu", brand="AMD", release_year=2022, launch_msrp_usd=999.0,
        architecture="RDNA 3", process_node_nm=5.0, tdp_w=355,
        raw_specs={"vram_gb": 24, "bus_width_bit": 384}, benchmark_index=93.5,
        ray_tracing_score=75.0, efficiency_score=75.0
    )

    verdict = service.generate_verdict(spec_a, spec_b)

    # Must explicitly state that the price is equal and never output 0.0%
    assert "السعر متطابق" in verdict.value_and_budget_ar
    assert "أقل بنسبة 0.0%" not in verdict.value_and_budget_ar


def test_ai_editorial_amd_vs_nvidia_vram_and_rt_accuracy():
    service = AiEditorialService(api_key="")
    spec_nvidia = HardwareSpec(
        id="rtx-4080-super", slug="rtx-4080-super", name="NVIDIA GeForce RTX 4080 Super",
        category="gpu", brand="NVIDIA", release_year=2024, launch_msrp_usd=999.0,
        architecture="Ada Lovelace", process_node_nm=4.0, tdp_w=320,
        raw_specs={"vram_gb": 16, "bus_width_bit": 256}, benchmark_index=92.0,
        ray_tracing_score=93.0, efficiency_score=88.0
    )
    spec_amd = HardwareSpec(
        id="rx-7900-xtx", slug="rx-7900-xtx", name="AMD Radeon RX 7900 XTX",
        category="gpu", brand="AMD", release_year=2022, launch_msrp_usd=999.0,
        architecture="RDNA 3", process_node_nm=5.0, tdp_w=355,
        raw_specs={"vram_gb": 24, "bus_width_bit": 384}, benchmark_index=93.5,
        ray_tracing_score=75.0, efficiency_score=75.0
    )

    verdict = service.generate_verdict(spec_nvidia, spec_amd)

    # 1. AMD pros (item b) must recognize 24GB VRAM
    amd_pros_text = " ".join(verdict.pros_b)
    assert "24GB" in amd_pros_text or "VRAM" in amd_pros_text

    # 2. Ray Tracing must NOT be listed as a pro for AMD against NVIDIA
    assert "تتبع الأشعة" not in amd_pros_text

    # 3. Ray Tracing weakness should be recognized in AMD cons
    amd_cons_text = " ".join(verdict.cons_b)
    assert "تتبع الأشعة" in amd_cons_text or "CUDA" in amd_cons_text

    # 4. NVIDIA pros (item a) must highlight DLSS 3.5 / Frame Generation and CUDA / OptiX / NVENC
    nv_pros_text = " ".join(verdict.pros_a)
    assert "DLSS 3.5" in nv_pros_text or "Frame Generation" in nv_pros_text
    assert "CUDA" in nv_pros_text or "NVENC" in nv_pros_text


def test_ai_editorial_no_awkward_float_formatting():
    service = AiEditorialService(api_key="")
    spec_a = HardwareSpec(
        id="gpu-a", slug="gpu-a", name="Card Alpha", category="gpu", brand="NVIDIA",
        release_year=2024, launch_msrp_usd=600.0, architecture="Ada", process_node_nm=4.0,
        tdp_w=200, raw_specs={"vram_gb": 12}, benchmark_index=88.0,
        ray_tracing_score=85.0, efficiency_score=90.0
    )
    spec_b = HardwareSpec(
        id="gpu-b", slug="gpu-b", name="Card Beta", category="gpu", brand="AMD",
        release_year=2024, launch_msrp_usd=500.0, architecture="RDNA 3", process_node_nm=5.0,
        tdp_w=250, raw_specs={"vram_gb": 16}, benchmark_index=80.0,
        ray_tracing_score=75.0, efficiency_score=75.0
    )

    verdict = service.generate_verdict(spec_a, spec_b)

    all_editorial_text = " ".join([
        verdict.quick_verdict_ar,
        verdict.gaming_analysis_ar,
        verdict.productivity_analysis_ar,
        verdict.value_and_budget_ar,
        *verdict.pros_a,
        *verdict.cons_a,
        *verdict.pros_b,
        *verdict.cons_b
    ])

    # Awkward ".0/100" float formatting must be avoided
    assert ".0/100" not in all_editorial_text
    assert "75.0/100" not in all_editorial_text
    assert "88.0/100" not in all_editorial_text
    assert "85.0/100" not in all_editorial_text
    # Process node must be 4nm or 5nm, not 4.0nm
    assert "4.0nm" not in all_editorial_text
    assert "5.0nm" not in all_editorial_text


def test_ai_editorial_amd_vs_amd_vram_and_no_ray_tracing():
    service = AiEditorialService(api_key="")
    spec_a = HardwareSpec(
        id="rx-7800-xt", slug="rx-7800-xt", name="AMD Radeon RX 7800 XT",
        category="gpu", brand="AMD", release_year=2023, launch_msrp_usd=499.0,
        architecture="RDNA 3", process_node_nm=5.0, tdp_w=263,
        raw_specs={"vram_gb": 16, "bus_width_bit": 256}, benchmark_index=81.0,
        ray_tracing_score=67.0, efficiency_score=80.0
    )
    spec_b = HardwareSpec(
        id="rx-7900-xtx", slug="rx-7900-xtx", name="AMD Radeon RX 7900 XTX",
        category="gpu", brand="AMD", release_year=2022, launch_msrp_usd=999.0,
        architecture="RDNA 3", process_node_nm=5.0, tdp_w=355,
        raw_specs={"vram_gb": 24, "bus_width_bit": 384}, benchmark_index=93.5,
        ray_tracing_score=75.0, efficiency_score=75.0
    )

    verdict = service.generate_verdict(spec_a, spec_b)

    # 1. Neither AMD card should have Ray Tracing listed as a pro
    pros_a_text = " ".join(verdict.pros_a)
    pros_b_text = " ".join(verdict.pros_b)
    assert "تتبع الأشعة" not in pros_a_text
    assert "تتبع الأشعة" not in pros_b_text

    # 2. RX 7900 XTX (item b) must highlight 24GB VRAM in pros and gaming analysis
    assert "24GB" in pros_b_text or "24GB" in verdict.gaming_analysis_ar
    assert "16GB" in pros_a_text or "16GB" in verdict.gaming_analysis_ar


def test_ai_editorial_cpu_identical_price_no_gpu_terms():
    service = AiEditorialService(api_key="")
    spec_a = HardwareSpec(
        id="cpu-a", slug="cpu-a", name="AMD Ryzen 7 7700X", category="cpu", brand="AMD",
        release_year=2022, launch_msrp_usd=399.0, architecture="Zen 4", process_node_nm=5.0,
        tdp_w=105, raw_specs={"total_cores": 8, "threads": 16, "l3_cache_mb": 32},
        benchmark_index=88.0, ray_tracing_score=50.0, efficiency_score=85.0
    )
    spec_b = HardwareSpec(
        id="cpu-b", slug="cpu-b", name="Intel Core i7-13700K", category="cpu", brand="Intel",
        release_year=2022, launch_msrp_usd=399.0, architecture="Raptor Lake", process_node_nm=7.0,
        tdp_w=253, raw_specs={"total_cores": 16, "threads": 24, "l3_cache_mb": 30},
        benchmark_index=89.0, ray_tracing_score=50.0, efficiency_score=70.0
    )

    verdict = service.generate_verdict(spec_a, spec_b)

    # Must state identical price with CPU terminology (المعالجين), NOT GPU terms (VRAM / Ray Tracing)
    assert "السعر متطابق" in verdict.value_and_budget_ar
    assert "المعالجين" in verdict.value_and_budget_ar
    assert "VRAM" not in verdict.value_and_budget_ar
    assert "تتبع الأشعة" not in verdict.value_and_budget_ar


def test_ai_editorial_cpu_no_ray_tracing():
    service = AiEditorialService(api_key="")
    spec_a = HardwareSpec(
        id="ryzen-7-7800x3d", slug="ryzen-7-7800x3d", name="AMD Ryzen 7 7800X3D", category="cpu", brand="AMD",
        release_year=2023, launch_msrp_usd=449.0, architecture="Zen 4", process_node_nm=5.0,
        tdp_w=120, raw_specs={"total_cores": 8, "threads": 16, "l3_cache_mb": 96},
        benchmark_index=91.0, ray_tracing_score=85.0, efficiency_score=96.0
    )
    spec_b = HardwareSpec(
        id="i7-14700k", slug="i7-14700k", name="Intel Core i7-14700K", category="cpu", brand="Intel",
        release_year=2023, launch_msrp_usd=409.0, architecture="Raptor Lake Refresh", process_node_nm=7.0,
        tdp_w=253, raw_specs={"total_cores": 20, "threads": 28, "l3_cache_mb": 33},
        benchmark_index=92.5, ray_tracing_score=85.0, efficiency_score=68.0
    )

    verdict = service.generate_verdict(spec_a, spec_b)
    all_text = " ".join([
        verdict.quick_verdict_ar,
        verdict.gaming_analysis_ar,
        verdict.productivity_analysis_ar,
        verdict.value_and_budget_ar,
        *verdict.pros_a,
        *verdict.cons_a,
        *verdict.pros_b,
        *verdict.cons_b
    ])

    assert "تتبع الأشعة" not in all_text
    assert "Ray Tracing" not in all_text


def test_ai_editorial_nvenc_single_vs_dual():
    service = AiEditorialService(api_key="")
    spec_4060_ti = HardwareSpec(
        id="rtx-4060-ti", slug="rtx-4060-ti", name="NVIDIA GeForce RTX 4060 Ti",
        category="gpu", brand="NVIDIA", release_year=2023, launch_msrp_usd=399.0,
        architecture="Ada Lovelace", process_node_nm=4.0, tdp_w=160,
        raw_specs={"cuda_cores": 4352, "vram_gb": 8, "bus_width_bit": 128, "nvenc_encoders": 1},
        benchmark_index=68.0, gaming_scores={"raster_1080p": 78.0, "raster_1440p": 65.0, "raster_4k": 45.0},
        ray_tracing_score=72.0, efficiency_score=92.0,
        features=["DLSS 3 Frame Generation", "Ultra Low 160W TDP", "NVENC AV1"]
    )
    spec_7700_xt = HardwareSpec(
        id="rx-7700-xt", slug="rx-7700-xt", name="AMD Radeon RX 7700 XT",
        category="gpu", brand="AMD", release_year=2023, launch_msrp_usd=449.0,
        architecture="RDNA 3", process_node_nm=5.0, tdp_w=245,
        raw_specs={"stream_processors": 3456, "vram_gb": 12, "bus_width_bit": 192},
        benchmark_index=74.0, gaming_scores={"raster_1080p": 82.0, "raster_1440p": 74.0, "raster_4k": 55.0},
        ray_tracing_score=60.0, efficiency_score=76.0,
        features=["12GB VRAM", "FSR 3", "DisplayPort 2.1"]
    )
    spec_4080_super = HardwareSpec(
        id="rtx-4080-super", slug="rtx-4080-super", name="NVIDIA GeForce RTX 4080 Super",
        category="gpu", brand="NVIDIA", release_year=2024, launch_msrp_usd=999.0,
        architecture="Ada Lovelace", process_node_nm=4.0, tdp_w=320,
        raw_specs={"cuda_cores": 10240, "vram_gb": 16, "bus_width_bit": 256, "nvenc_encoders": 2},
        benchmark_index=92.0, gaming_scores={"raster_1080p": 95.0, "raster_1440p": 93.0, "raster_4k": 88.0},
        ray_tracing_score=93.0, efficiency_score=88.0,
        features=["DLSS 3.5 Frame Generation", "AV1 Dual NVENC", "Reflex"]
    )

    # 1. Domain model property check
    assert spec_4060_ti.has_dual_nvenc is False
    assert spec_4080_super.has_dual_nvenc is True

    # 2. Editorial output for RTX 4060 Ti must NOT contain "NVENC المزدوج"
    verdict_midrange = service.generate_verdict(spec_4060_ti, spec_7700_xt)
    pros_4060 = " ".join(verdict_midrange.pros_a)
    assert "NVENC المزدوج" not in pros_4060
    assert "مشفر NVENC المزدوج" not in verdict_midrange.productivity_analysis_ar
    assert "مشفر NVENC" in verdict_midrange.productivity_analysis_ar or "NVENC" in pros_4060

    # 3. Editorial output for RTX 4080 Super MUST contain "NVENC المزدوج"
    verdict_flagship = service.generate_verdict(spec_4080_super, spec_7700_xt)
    pros_4080 = " ".join(verdict_flagship.pros_a)
    assert "NVENC المزدوج" in pros_4080 or "مشفر NVENC المزدوج" in verdict_flagship.productivity_analysis_ar

    # 4. Fallback test when raw_specs lacks explicit nvenc_encoders
    spec_4070_no_nvenc = HardwareSpec(
        id="rtx-4070", slug="rtx-4070", name="NVIDIA GeForce RTX 4070",
        category="gpu", brand="NVIDIA", release_year=2023, launch_msrp_usd=549.0,
        architecture="Ada Lovelace", process_node_nm=4.0, tdp_w=200,
        raw_specs={"cuda_cores": 5888, "vram_gb": 12},
        benchmark_index=78.0
    )
    spec_4070_ti_no_nvenc = HardwareSpec(
        id="rtx-4070-ti", slug="rtx-4070-ti", name="NVIDIA GeForce RTX 4070 Ti",
        category="gpu", brand="NVIDIA", release_year=2023, launch_msrp_usd=799.0,
        architecture="Ada Lovelace", process_node_nm=4.0, tdp_w=285,
        raw_specs={"cuda_cores": 7680, "vram_gb": 12},
        benchmark_index=88.0
    )
    assert spec_4070_no_nvenc.has_dual_nvenc is False
    assert spec_4070_ti_no_nvenc.has_dual_nvenc is True


def test_ai_editorial_rtx4060ti_vs_rx7700xt_winner_alignment_and_no_hyperbole():
    service = AiEditorialService(api_key="")
    spec_4060_ti = HardwareSpec(
        id="rtx-4060-ti", slug="rtx-4060-ti", name="NVIDIA GeForce RTX 4060 Ti",
        category="gpu", brand="NVIDIA", release_year=2023, launch_msrp_usd=399.0,
        architecture="Ada Lovelace", process_node_nm=4.0, tdp_w=160,
        raw_specs={"cuda_cores": 4352, "vram_gb": 8, "bus_width_bit": 128, "nvenc_encoders": 1},
        benchmark_index=68.0, gaming_scores={"raster_1080p": 78.0, "raster_1440p": 65.0, "raster_4k": 45.0},
        ray_tracing_score=72.0, efficiency_score=92.0,
        features=["DLSS 3 Frame Generation", "Ultra Low 160W TDP", "NVENC AV1"]
    )
    spec_7700_xt = HardwareSpec(
        id="rx-7700-xt", slug="rx-7700-xt", name="AMD Radeon RX 7700 XT",
        category="gpu", brand="AMD", release_year=2023, launch_msrp_usd=449.0,
        architecture="RDNA 3", process_node_nm=5.0, tdp_w=245,
        raw_specs={"stream_processors": 3456, "vram_gb": 12, "bus_width_bit": 192},
        benchmark_index=74.0, gaming_scores={"raster_1080p": 82.0, "raster_1440p": 74.0, "raster_4k": 55.0},
        ray_tracing_score=60.0, efficiency_score=76.0,
        features=["12GB VRAM", "FSR 3", "DisplayPort 2.1"]
    )

    verdict = service.generate_verdict(spec_4060_ti, spec_7700_xt)

    # 1. Winner alignment: RX 7700 XT leads in raw rasterization / gaming performance
    assert "يحسم AMD Radeon RX 7700 XT الصدارة في الأداء الرسومي الخام" in verdict.gaming_analysis_ar
    assert "تتبع الأشعة" in verdict.gaming_analysis_ar
    assert "DLSS" in verdict.gaming_analysis_ar

    # 2. No hyperbole: 12GB is NOT "هائلة" and no "4K Ultra بلا اختناق" on midrange
    assert "VRAM هائلة" not in verdict.gaming_analysis_ar
    assert "هائلة تبلغ 12GB" not in verdict.gaming_analysis_ar
    assert "بدقة 4K وقوام Ultra بدون اختناق الذاكرة" not in verdict.gaming_analysis_ar
    # Stated as balanced 1440p/1080p
    assert "1440p" in verdict.gaming_analysis_ar

    # 3. Value analysis: No contradictory claim calling an 8GB 128-bit card a "smarter medium-term investment"
    assert "استثماراً أذكى على المدى المتوسط" not in verdict.value_and_budget_ar
    assert "استثماراً أكثر استدامة" in verdict.value_and_budget_ar or "أكثر استدامة" in verdict.value_and_budget_ar
    assert "12GB" in verdict.value_and_budget_ar

    # 4. Neutralized buyer recommendations: No subjective "أعلى استقرار"
    assert "أعلى استقرار" not in verdict.who_should_buy_a
    assert "أعلى استقرار" not in verdict.who_should_buy_b
    assert "CUDA" in verdict.who_should_buy_a
    assert "DLSS" in verdict.who_should_buy_a
    assert "VRAM" in verdict.who_should_buy_b or "ذاكرة" in verdict.who_should_buy_b


def test_rule_engine_quick_verdict_precision_no_frame_times():
    spec_a = HardwareSpec(
        id="gpu-a", slug="gpu-a", name="Card Alpha", category="gpu", brand="NVIDIA",
        release_year=2024, launch_msrp_usd=600.0, architecture="Ada", process_node_nm=4.0,
        tdp_w=200, raw_specs={"vram_gb": 12}, benchmark_index=85.0
    )
    spec_b = HardwareSpec(
        id="gpu-b", slug="gpu-b", name="Card Beta", category="gpu", brand="AMD",
        release_year=2024, launch_msrp_usd=500.0, architecture="RDNA 3", process_node_nm=5.0,
        tdp_w=220, raw_specs={"vram_gb": 16}, benchmark_index=75.0
    )

    # Test winner A
    verdict_a = EditorialRuleEngine.generate_verdict(spec_a, spec_b)
    assert verdict_a.overall_winner == "a"
    assert "أزمنة إطارات" not in verdict_a.quick_verdict_ar
    assert "13.3%" in verdict_a.quick_verdict_ar or "13%" in verdict_a.quick_verdict_ar

    # Test winner B
    verdict_b = EditorialRuleEngine.generate_verdict(spec_b, spec_a)
    assert verdict_b.overall_winner == "b"
    assert "أزمنة إطارات" not in verdict_b.quick_verdict_ar
    assert "13.3%" in verdict_b.quick_verdict_ar or "13%" in verdict_b.quick_verdict_ar


def test_rule_engine_price_delta_math_and_cost_per_frame_tie():
    spec_4060_ti = HardwareSpec(
        id="rtx-4060-ti", slug="rtx-4060-ti", name="NVIDIA GeForce RTX 4060 Ti",
        category="gpu", brand="NVIDIA", release_year=2023, launch_msrp_usd=399.0,
        architecture="Ada Lovelace", process_node_nm=4.0, tdp_w=160,
        raw_specs={"cuda_cores": 4352, "vram_gb": 8, "bus_width_bit": 128, "nvenc_encoders": 1},
        benchmark_index=68.0, gaming_scores={"raster_1080p": 78.0, "raster_1440p": 65.0, "raster_4k": 45.0},
        ray_tracing_score=72.0, efficiency_score=92.0,
        features=["DLSS 3 Frame Generation", "Ultra Low 160W TDP", "NVENC AV1"]
    )
    spec_7700_xt = HardwareSpec(
        id="rx-7700-xt", slug="rx-7700-xt", name="AMD Radeon RX 7700 XT",
        category="gpu", brand="AMD", release_year=2023, launch_msrp_usd=449.0,
        architecture="RDNA 3", process_node_nm=5.0, tdp_w=245,
        raw_specs={"stream_processors": 3456, "vram_gb": 12, "bus_width_bit": 192},
        benchmark_index=74.0, gaming_scores={"raster_1080p": 82.0, "raster_1440p": 74.0, "raster_4k": 55.0},
        ray_tracing_score=60.0, efficiency_score=76.0,
        features=["12GB VRAM", "FSR 3", "DisplayPort 2.1"]
    )

    verdict = EditorialRuleEngine.generate_verdict(spec_4060_ti, spec_7700_xt)

    # 1. Price delta calculation: (449 - 399) / 399 = 12.5% (NOT 11.1%)
    assert "12.5%" in verdict.value_and_budget_ar
    assert "11.1%" not in verdict.value_and_budget_ar

    # 2. Average 1440p FPS lead (~8.8%) vs 12.5% price increase
    assert "~8.8%" in verdict.value_and_budget_ar

    # 3. Cost-per-frame is virtually identical (tie in pure value) with market price revision note
    assert "القيمة مقابل السعر" in verdict.value_and_budget_ar or "Cost per Frame" in verdict.value_and_budget_ar
    assert "متطابقة عملياً" in verdict.value_and_budget_ar or "تعادل في القيمة الصافية" in verdict.value_and_budget_ar
    assert "لا يوجد فوز مطلق" in verdict.value_and_budget_ar
    assert "تعديل السعر الرسمي" in verdict.value_and_budget_ar or "$419" in verdict.value_and_budget_ar


def test_rule_engine_deterministic_identical_verdicts():
    spec_a = HardwareSpec(
        id="rtx-4070-super", slug="rtx-4070-super", name="NVIDIA GeForce RTX 4070 Super",
        category="gpu", brand="NVIDIA", release_year=2024, launch_msrp_usd=599.0,
        architecture="Ada Lovelace", process_node_nm=4.0, tdp_w=220,
        raw_specs={"cuda_cores": 7168, "vram_gb": 12, "bus_width_bit": 192, "nvenc_encoders": 1},
        benchmark_index=82.5, gaming_scores={"raster_1080p": 88.0, "raster_1440p": 82.0, "raster_4k": 68.0},
        ray_tracing_score=85.0, efficiency_score=90.0,
        features=["DLSS 3.5 Frame Generation", "AV1 NVENC", "Reflex"]
    )
    spec_b = HardwareSpec(
        id="rx-7800-xt", slug="rx-7800-xt", name="AMD Radeon RX 7800 XT",
        category="gpu", brand="AMD", release_year=2023, launch_msrp_usd=499.0,
        architecture="RDNA 3", process_node_nm=5.0, tdp_w=263,
        raw_specs={"stream_processors": 3840, "vram_gb": 16, "bus_width_bit": 256},
        benchmark_index=81.0, gaming_scores={"raster_1080p": 87.0, "raster_1440p": 83.5, "raster_4k": 71.0},
        ray_tracing_score=67.0, efficiency_score=78.0,
        features=["FSR 3.1", "HYPR-RX", "DisplayPort 2.1"]
    )

    verdict_1 = EditorialRuleEngine.generate_verdict(spec_a, spec_b)
    verdict_2 = EditorialRuleEngine.generate_verdict(spec_a, spec_b)

    assert verdict_1.model_dump() == verdict_2.model_dump()
    assert verdict_1.quick_verdict_ar == verdict_2.quick_verdict_ar
    assert verdict_1.value_and_budget_ar == verdict_2.value_and_budget_ar


def test_rule_engine_reversed_matchup_symmetry_and_positive_fps_lead():
    """Attack edge case: passing pricier card as item_a and cheaper as item_b must produce identical positive math."""
    spec_4060_ti = HardwareSpec(
        id="rtx-4060-ti", slug="rtx-4060-ti", name="NVIDIA GeForce RTX 4060 Ti",
        category="gpu", brand="NVIDIA", release_year=2023, launch_msrp_usd=399.0,
        architecture="Ada Lovelace", process_node_nm=4.0, tdp_w=160,
        raw_specs={"cuda_cores": 4352, "vram_gb": 8, "bus_width_bit": 128, "nvenc_encoders": 1},
        benchmark_index=68.0, gaming_scores={"raster_1080p": 78.0, "raster_1440p": 65.0, "raster_4k": 45.0},
        ray_tracing_score=72.0, efficiency_score=92.0,
        features=["DLSS 3 Frame Generation", "Ultra Low 160W TDP", "NVENC AV1"]
    )
    spec_7700_xt = HardwareSpec(
        id="rx-7700-xt", slug="rx-7700-xt", name="AMD Radeon RX 7700 XT",
        category="gpu", brand="AMD", release_year=2023, launch_msrp_usd=449.0,
        architecture="RDNA 3", process_node_nm=5.0, tdp_w=245,
        raw_specs={"stream_processors": 3456, "vram_gb": 12, "bus_width_bit": 192},
        benchmark_index=74.0, gaming_scores={"raster_1080p": 82.0, "raster_1440p": 74.0, "raster_4k": 55.0},
        ray_tracing_score=60.0, efficiency_score=76.0,
        features=["12GB VRAM", "FSR 3", "DisplayPort 2.1"]
    )

    # Pass reversed: RX 7700 XT first ($449 - pricier), RTX 4060 Ti second ($399 - cheaper)
    verdict_reversed = EditorialRuleEngine.generate_verdict(spec_7700_xt, spec_4060_ti)

    # 1. Math must be strictly positive: FPS lead is ~8.8% (NEVER negative ~-11.2%)
    assert "~8.8%" in verdict_reversed.value_and_budget_ar
    assert "~-" not in verdict_reversed.value_and_budget_ar
    assert "-11.2%" not in verdict_reversed.value_and_budget_ar

    # 2. Price increase of pricier over cheaper base: 12.5%
    assert "12.5%" in verdict_reversed.value_and_budget_ar

    # 3. Cost-per-frame tie and no unconditional win
    assert "متطابقة عملياً" in verdict_reversed.value_and_budget_ar or "تعادل في القيمة الصافية" in verdict_reversed.value_and_budget_ar
    assert "لا يوجد فوز مطلق" in verdict_reversed.value_and_budget_ar
    assert "تعديل السعر الرسمي" in verdict_reversed.value_and_budget_ar or "$419" in verdict_reversed.value_and_budget_ar

    # 4. Zero stray dollar signs
    assert "%)$" not in verdict_reversed.value_and_budget_ar
    assert "$ " not in verdict_reversed.value_and_budget_ar


def test_rule_engine_cpu_statistical_margin_tie_no_flawed_perf_claim():
    """Attack edge case: CPU matchup where cheaper CPU has < 3% perf difference must not falsely claim perf lead."""
    spec_7800x3d = HardwareSpec(
        id="ryzen-7-7800x3d", slug="ryzen-7-7800x3d", name="AMD Ryzen 7 7800X3D", category="cpu", brand="AMD",
        release_year=2023, launch_msrp_usd=449.0, architecture="Zen 4", process_node_nm=5.0,
        tdp_w=120, raw_specs={"total_cores": 8, "threads": 16, "l3_cache_mb": 96},
        benchmark_index=91.0, ray_tracing_score=85.0, efficiency_score=96.0
    )
    spec_14700k = HardwareSpec(
        id="i7-14700k", slug="i7-14700k", name="Intel Core i7-14700K", category="cpu", brand="Intel",
        release_year=2023, launch_msrp_usd=409.0, architecture="Raptor Lake Refresh", process_node_nm=7.0,
        tdp_w=253, raw_specs={"total_cores": 20, "threads": 28, "l3_cache_mb": 33},
        benchmark_index=92.5, ray_tracing_score=85.0, efficiency_score=68.0
    )

    verdict = EditorialRuleEngine.generate_verdict(spec_7800x3d, spec_14700k)

    # 91.0 vs 92.5 is a 1.62% difference (< 3.0% margin of error) -> must be treated as comparable performance
    assert "تقارب الأداء" in verdict.value_and_budget_ar or "تقارب" in verdict.value_and_budget_ar
    assert "مع أسبقية في الأداء، مما يجعله الفائز المباشر" not in verdict.value_and_budget_ar
    assert "9.8%" in verdict.value_and_budget_ar  # (449 - 409) / 409 = 9.8% price increase


def test_rule_engine_quick_verdict_incorporates_actual_fps():
    """Tests that quick_verdict_ar integrates actual FPS calculations for GPU comparisons."""
    spec_4060_ti = HardwareSpec(
        id="rtx-4060-ti", slug="rtx-4060-ti", name="NVIDIA GeForce RTX 4060 Ti",
        category="gpu", brand="NVIDIA", release_year=2023, launch_msrp_usd=399.0,
        architecture="Ada Lovelace", process_node_nm=4.0, tdp_w=160,
        raw_specs={"cuda_cores": 4352, "vram_gb": 8, "bus_width_bit": 128},
        benchmark_index=68.0, gaming_scores={"raster_1080p": 78.0, "raster_1440p": 65.0, "raster_4k": 45.0}
    )
    spec_7700_xt = HardwareSpec(
        id="rx-7700-xt", slug="rx-7700-xt", name="AMD Radeon RX 7700 XT",
        category="gpu", brand="AMD", release_year=2023, launch_msrp_usd=449.0,
        architecture="RDNA 3", process_node_nm=5.0, tdp_w=245,
        raw_specs={"stream_processors": 3456, "vram_gb": 12, "bus_width_bit": 192},
        benchmark_index=74.0, gaming_scores={"raster_1080p": 82.0, "raster_1440p": 74.0, "raster_4k": 55.0}
    )

    verdict = EditorialRuleEngine.generate_verdict(spec_4060_ti, spec_7700_xt)
    assert verdict.overall_winner == "b"
    assert "AMD Radeon RX 7700 XT" in verdict.quick_verdict_ar
    assert "8.8%" in verdict.quick_verdict_ar  # (74 - 68) / 68 = 8.8%
    assert "~8.8%" in verdict.quick_verdict_ar or "معدل الإطارات" in verdict.quick_verdict_ar
    assert "أزمنة إطارات" not in verdict.quick_verdict_ar


def test_rule_engine_cpu_argument_reversal_symmetry():
    """Adversarial test: Reversing CPU arguments must maintain factual technical accuracy without order-dependent hallucinations."""
    spec_7800x3d = HardwareSpec(
        id="ryzen-7-7800x3d", slug="ryzen-7-7800x3d", name="AMD Ryzen 7 7800X3D", category="cpu", brand="AMD",
        release_year=2023, launch_msrp_usd=449.0, architecture="Zen 4", process_node_nm=5.0,
        tdp_w=120, raw_specs={"total_cores": 8, "threads": 16, "l3_cache_mb": 96},
        benchmark_index=91.0, ray_tracing_score=85.0, efficiency_score=96.0
    )
    spec_14700k = HardwareSpec(
        id="i7-14700k", slug="i7-14700k", name="Intel Core i7-14700K", category="cpu", brand="Intel",
        release_year=2023, launch_msrp_usd=409.0, architecture="Raptor Lake Refresh", process_node_nm=7.0,
        tdp_w=253, raw_specs={"total_cores": 20, "threads": 28, "l3_cache_mb": 33},
        benchmark_index=92.5, ray_tracing_score=85.0, efficiency_score=68.0
    )

    # Pass reversed: 14700K (20 cores, 253W) first, 7800X3D (8 cores, 96MB L3, 120W) second
    verdict = EditorialRuleEngine.generate_verdict(spec_14700k, spec_7800x3d)

    # 1. Pros of item a (14700K) must reflect 20 cores multi-threaded rendering, NOT false 96MB L3 cache or 120W efficiency
    pros_14700k = " ".join(verdict.pros_a)
    assert "20" in pros_14700k or "نوى" in pros_14700k
    assert "96MB" not in pros_14700k

    # 2. Cons of item a (14700K) must capture high 253W power draw and cooling demands
    cons_14700k = " ".join(verdict.cons_a)
    assert "253W" in cons_14700k or "تبريد" in cons_14700k

    # 3. Pros of item b (7800X3D) must capture 96MB L3 cache and high efficiency
    pros_7800x3d = " ".join(verdict.pros_b)
    assert "96MB" in pros_7800x3d or "كاش" in pros_7800x3d
    assert "كفاءة طاقة" in pros_7800x3d or "96/100" in pros_7800x3d

    # 4. Cons of item b (7800X3D) must NOT accuse 7800X3D of 253W thermal issues
    cons_7800x3d = " ".join(verdict.cons_b)
    assert "253W" not in cons_7800x3d

    # 5. Gaming analysis must properly credit 3D V-Cache / 1% low FPS to 7800X3D
    assert "3D V-Cache" in verdict.gaming_analysis_ar or "AMD Ryzen 7 7800X3D" in verdict.gaming_analysis_ar
    assert "20" in verdict.productivity_analysis_ar  # 20 cores credited in productivity


def test_rule_engine_laptop_argument_reversal_symmetry():
    """Adversarial test: Reversing laptop arguments must not declare biased 'أسبقية للأول' or falsely praise heavy laptops."""
    laptop_zephyrus = HardwareSpec(
        id="rog-zephyrus-g14", slug="rog-zephyrus-g14", name="ASUS ROG Zephyrus G14 (2024)", category="laptop", brand="ASUS",
        release_year=2024, launch_msrp_usd=1999.0, architecture="Zen 4 / Ada", process_node_nm=4.0,
        tdp_w=90, raw_specs={"weight_kg": 1.5, "battery_wh": 73, "display": "14 OLED 120Hz 3K"},
        benchmark_index=84.0, ray_tracing_score=75.0, efficiency_score=94.0
    )
    laptop_legion = HardwareSpec(
        id="legion-pro-5", slug="legion-pro-5", name="Lenovo Legion Pro 5 (2024)", category="laptop", brand="Lenovo",
        release_year=2024, launch_msrp_usd=1599.0, architecture="Raptor Lake / Ada", process_node_nm=5.0,
        tdp_w=140, raw_specs={"weight_kg": 2.5, "battery_wh": 80, "display": "16 IPS 240Hz WQXGA"},
        benchmark_index=86.0, ray_tracing_score=78.0, efficiency_score=78.0
    )

    # Pass reversed: Legion (2.5kg) first, Zephyrus (1.5kg) second
    verdict = EditorialRuleEngine.generate_verdict(laptop_legion, laptop_zephyrus)

    # 1. No biased "أسبقية للأول"
    assert "أسبقية للأول" not in verdict.gaming_analysis_ar

    # 2. Heavy Legion (item a) must NOT be praised for lightweight daily portability
    pros_legion = " ".join(verdict.pros_a)
    assert "يسهل التنقل" not in pros_legion

    # 3. Lightweight Zephyrus (item b) MUST be recognized for lightweight portability
    pros_zephyrus = " ".join(verdict.pros_b)
    assert "خفيف" in pros_zephyrus or "1.5" in pros_zephyrus or "التنقل" in pros_zephyrus

    # 4. Heavy weight must appear in Legion's cons
    cons_legion = " ".join(verdict.cons_a)
    assert "2.5" in cons_legion or "أثقل" in cons_legion


def test_rule_engine_gpu_cost_per_frame_tie_equal_vram():
    """Adversarial test: Two GPUs with equal VRAM where FPS lead matches price increase within 2.5% must trigger cost-per-frame tie."""
    spec_a = HardwareSpec(
        id="gpu-mid-1", slug="gpu-mid-1", name="GPU Value A", category="gpu", brand="NVIDIA",
        release_year=2024, launch_msrp_usd=500.0, architecture="Ada Lovelace", process_node_nm=4.0,
        tdp_w=200, raw_specs={"vram_gb": 16, "bus_width_bit": 256},
        benchmark_index=80.0, gaming_scores={"raster_1080p": 80.0, "raster_1440p": 80.0, "raster_4k": 70.0},
        ray_tracing_score=80.0, efficiency_score=85.0
    )
    spec_b = HardwareSpec(
        id="gpu-mid-2", slug="gpu-mid-2", name="GPU Value B", category="gpu", brand="AMD",
        release_year=2024, launch_msrp_usd=550.0, architecture="RDNA 3", process_node_nm=5.0,
        tdp_w=240, raw_specs={"vram_gb": 16, "bus_width_bit": 256},
        benchmark_index=88.0, gaming_scores={"raster_1080p": 88.0, "raster_1440p": 88.0, "raster_4k": 77.0},
        ray_tracing_score=70.0, efficiency_score=78.0
    )

    verdict = EditorialRuleEngine.generate_verdict(spec_a, spec_b)

    # Price increase: (550 - 500) / 500 = 10.0%. FPS lead: (88 - 80) / 80 = 10.0%. Difference = 0.0% <= 2.5%
    assert "القيمة مقابل السعر" in verdict.value_and_budget_ar
    assert "متطابقة عملياً" in verdict.value_and_budget_ar or "تعادل في القيمة الصافية" in verdict.value_and_budget_ar
    assert "لا يوجد فوز مطلق" in verdict.value_and_budget_ar


def test_fps_calculator_engine_affinity_and_vendor_biases():
    """Verifies engine-aware game FPS modeling across UE5 Lumen RT, Source 2, IW 9.0, and overall lead."""
    from core.services.fps_calculator import FpsCalculator

    spec_4060_ti = HardwareSpec(
        id="rtx-4060-ti", slug="rtx-4060-ti", name="NVIDIA GeForce RTX 4060 Ti",
        category="gpu", brand="NVIDIA", release_year=2023, launch_msrp_usd=399.0,
        architecture="Ada Lovelace", process_node_nm=4.0, tdp_w=160,
        raw_specs={"cuda_cores": 4352, "vram_gb": 8, "bus_width_bit": 128, "pcie_lanes": 8, "pcie_interface": "PCIe 4.0 x8"},
        benchmark_index=68.0, gaming_scores={"raster_1080p": 78.0, "raster_1440p": 65.0, "raster_4k": 45.0},
        ray_tracing_score=72.0, efficiency_score=92.0
    )
    spec_7700_xt = HardwareSpec(
        id="rx-7700-xt", slug="rx-7700-xt", name="AMD Radeon RX 7700 XT",
        category="gpu", brand="AMD", release_year=2023, launch_msrp_usd=449.0,
        architecture="RDNA 3", process_node_nm=5.0, tdp_w=245,
        raw_specs={"stream_processors": 3456, "vram_gb": 12, "bus_width_bit": 192, "pcie_lanes": 16, "pcie_interface": "PCIe 4.0 x16"},
        benchmark_index=74.0, gaming_scores={"raster_1080p": 82.0, "raster_1440p": 74.0, "raster_4k": 55.0},
        ray_tracing_score=60.0, efficiency_score=76.0
    )

    matrix = FpsCalculator.calculate_fps_matrix(spec_4060_ti, spec_7700_xt)
    by_game_1440p = {f"{item.game_title}_{item.resolution}": item for item in matrix}

    # 1. Black Myth: Wukong (UE5 Lumen RT) - realistic 38-44 FPS, 4060 Ti edges out 7700 XT
    wukong_1440p = by_game_1440p["Black Myth: Wukong_1440p"]
    assert 38 <= wukong_1440p.fps_a <= 44
    assert wukong_1440p.fps_a >= wukong_1440p.fps_b  # 4060 Ti edges out 7700 XT in RT/Lumen

    # 2. Counter-Strike 2 (Source 2) - Reflex parity / tight margin (<= 3%)
    cs2_1440p = by_game_1440p["Counter-Strike 2_1440p"]
    assert abs(cs2_1440p.fps_a - cs2_1440p.fps_b) / min(cs2_1440p.fps_a, cs2_1440p.fps_b) <= 0.03
    assert cs2_1440p.fps_a >= cs2_1440p.fps_b  # slight NVIDIA Reflex edge or dead tie

    # 3. Call of Duty: Warzone (IW 9.0) - AMD historical optimization (~25-28% lead)
    warzone_1440p = by_game_1440p["Call of Duty: Warzone_1440p"]
    warzone_lead = (warzone_1440p.fps_b - warzone_1440p.fps_a) / warzone_1440p.fps_a * 100
    assert 24.0 <= warzone_lead <= 30.0

    # 4. Overall 1440p average lead of RX 7700 XT over RTX 4060 Ti is calibrated to ~8.8%
    items_1440p = [item for item in matrix if item.resolution == "1440p"]
    leads = [(item.fps_b - item.fps_a) / item.fps_a * 100 for item in items_1440p]
    avg_lead_1440p = sum(leads) / len(leads)
    assert 8.0 <= avg_lead_1440p <= 9.5


def test_ai_editorial_pcie_lane_con_detection_for_8_lane_gpus():
    """Verifies that 8-lane PCIe GPUs have the critical bus bottleneck con exposed in Arabic editorial cons."""
    spec_4060_ti = HardwareSpec(
        id="rtx-4060-ti", slug="rtx-4060-ti", name="NVIDIA GeForce RTX 4060 Ti",
        category="gpu", brand="NVIDIA", release_year=2023, launch_msrp_usd=399.0,
        architecture="Ada Lovelace", process_node_nm=4.0, tdp_w=160,
        raw_specs={"cuda_cores": 4352, "vram_gb": 8, "bus_width_bit": 128, "pcie_lanes": 8, "pcie_interface": "PCIe 4.0 x8"},
        benchmark_index=68.0, gaming_scores={"raster_1080p": 78.0, "raster_1440p": 65.0, "raster_4k": 45.0},
        ray_tracing_score=72.0, efficiency_score=92.0
    )
    spec_7700_xt = HardwareSpec(
        id="rx-7700-xt", slug="rx-7700-xt", name="AMD Radeon RX 7700 XT",
        category="gpu", brand="AMD", release_year=2023, launch_msrp_usd=449.0,
        architecture="RDNA 3", process_node_nm=5.0, tdp_w=245,
        raw_specs={"stream_processors": 3456, "vram_gb": 12, "bus_width_bit": 192, "pcie_lanes": 16, "pcie_interface": "PCIe 4.0 x16"},
        benchmark_index=74.0, gaming_scores={"raster_1080p": 82.0, "raster_1440p": 74.0, "raster_4k": 55.0},
        ray_tracing_score=60.0, efficiency_score=76.0
    )

    verdict = EditorialRuleEngine.generate_verdict(spec_4060_ti, spec_7700_xt)

    # RTX 4060 Ti cons must contain the PCIe 4.0 x8 con
    cons_4060_ti = " ".join(verdict.cons_a)
    assert "8 مسارات" in cons_4060_ti or "PCIe 4.0 x8" in cons_4060_ti
    assert "عنق زجاجة" in cons_4060_ti
    assert "PCIe 3.0" in cons_4060_ti

    # RX 7700 XT (16 lanes) must NOT contain this con
    cons_7700_xt = " ".join(verdict.cons_b)
    assert "8 مسارات" not in cons_7700_xt
    assert "PCIe 4.0 x8" not in cons_7700_xt


def test_ai_editorial_precise_terminology_frame_gen_dlss35_and_av1():
    """Verifies correct separation of DLSS 3 (Frame Gen) vs DLSS 3.5 (Ray Recon), FSR 3.1 Frame Gen, and dual AV1."""
    spec_4060_ti = HardwareSpec(
        id="rtx-4060-ti", slug="rtx-4060-ti", name="NVIDIA GeForce RTX 4060 Ti",
        category="gpu", brand="NVIDIA", release_year=2023, launch_msrp_usd=399.0,
        architecture="Ada Lovelace", process_node_nm=4.0, tdp_w=160,
        raw_specs={"cuda_cores": 4352, "vram_gb": 8, "bus_width_bit": 128, "pcie_lanes": 8, "pcie_interface": "PCIe 4.0 x8"},
        benchmark_index=68.0, gaming_scores={"raster_1080p": 78.0, "raster_1440p": 65.0, "raster_4k": 45.0},
        ray_tracing_score=72.0, efficiency_score=92.0
    )
    spec_7700_xt = HardwareSpec(
        id="rx-7700-xt", slug="rx-7700-xt", name="AMD Radeon RX 7700 XT",
        category="gpu", brand="AMD", release_year=2023, launch_msrp_usd=449.0,
        architecture="RDNA 3", process_node_nm=5.0, tdp_w=245,
        raw_specs={"stream_processors": 3456, "vram_gb": 12, "bus_width_bit": 192, "pcie_lanes": 16, "pcie_interface": "PCIe 4.0 x16"},
        benchmark_index=74.0, gaming_scores={"raster_1080p": 82.0, "raster_1440p": 74.0, "raster_4k": 55.0},
        ray_tracing_score=60.0, efficiency_score=76.0
    )

    verdict = EditorialRuleEngine.generate_verdict(spec_4060_ti, spec_7700_xt)

    # 1. Gaming analysis must distinguish DLSS 3 (Frame Gen) and DLSS 3.5 (Ray Recon)
    assert "DLSS 3 لتوليد الإطارات" in verdict.gaming_analysis_ar or "DLSS 3 (توليد الإطارات)" in verdict.gaming_analysis_ar
    assert "DLSS 3.5 لإعادة بناء الأشعة" in verdict.gaming_analysis_ar or "DLSS 3.5 (إعادة بناء الأشعة)" in verdict.gaming_analysis_ar
    assert "DLSS 3.5 وتوليد الإطارات" not in verdict.gaming_analysis_ar  # Never conflate DLSS 3.5 with Frame Gen

    # 2. AMD FSR 3.1 Frame Gen open-source recognition
    assert "FSR 3.1" in verdict.gaming_analysis_ar
    assert "توليد الإطارات" in verdict.gaming_analysis_ar

    # 3. Productivity AV1 dual architecture acknowledgment
    assert "AV1" in verdict.productivity_analysis_ar
    assert "VCN 4.0" in verdict.productivity_analysis_ar
    assert "CUDA" in verdict.productivity_analysis_ar

    # 4. Pros check
    pros_nv = " ".join(verdict.pros_a)
    assert "DLSS 3 (توليد الإطارات)" in pros_nv
    assert "DLSS 3.5 (إعادة بناء الأشعة)" in pros_nv

    pros_amd = " ".join(verdict.pros_b)
    assert "FSR 3.1" in pros_amd
    assert "توليد الإطارات" in pros_amd


def test_ai_editorial_pricing_nuance_and_market_price_revision():
    """Verifies that value budget analysis reflects AMD's subsequent retail price revision to ~$419/$399."""
    spec_4060_ti = HardwareSpec(
        id="rtx-4060-ti", slug="rtx-4060-ti", name="NVIDIA GeForce RTX 4060 Ti",
        category="gpu", brand="NVIDIA", release_year=2023, launch_msrp_usd=399.0,
        architecture="Ada Lovelace", process_node_nm=4.0, tdp_w=160,
        raw_specs={"cuda_cores": 4352, "vram_gb": 8, "bus_width_bit": 128, "pcie_lanes": 8, "pcie_interface": "PCIe 4.0 x8"},
        benchmark_index=68.0, gaming_scores={"raster_1080p": 78.0, "raster_1440p": 65.0, "raster_4k": 45.0},
        ray_tracing_score=72.0, efficiency_score=92.0
    )
    spec_7700_xt = HardwareSpec(
        id="rx-7700-xt", slug="rx-7700-xt", name="AMD Radeon RX 7700 XT",
        category="gpu", brand="AMD", release_year=2023, launch_msrp_usd=449.0,
        architecture="RDNA 3", process_node_nm=5.0, tdp_w=245,
        raw_specs={"stream_processors": 3456, "vram_gb": 12, "bus_width_bit": 192, "pcie_lanes": 16, "pcie_interface": "PCIe 4.0 x16"},
        benchmark_index=74.0, gaming_scores={"raster_1080p": 82.0, "raster_1440p": 74.0, "raster_4k": 55.0},
        ray_tracing_score=60.0, efficiency_score=76.0
    )

    verdict = EditorialRuleEngine.generate_verdict(spec_4060_ti, spec_7700_xt)

    # Narrative must mention retail price adjustment
    assert "تعديل السعر الرسمي" in verdict.value_and_budget_ar
    assert "$419" in verdict.value_and_budget_ar
    assert "$399" in verdict.value_and_budget_ar
    assert "~8.8%" in verdict.value_and_budget_ar


def test_database_persistence_and_loading_of_pcie_interface(tmp_path):
    """Verifies that SQLite schema and HardwareRepository correctly persist and load pcie_interface."""
    test_db = tmp_path / "test_hardware.db"
    from core.repository.database import initialize_schema
    from core.repository.hardware_repo import HardwareRepository

    initialize_schema(test_db)
    repo = HardwareRepository(test_db)

    spec = HardwareSpec(
        id="rtx-4060-ti-test",
        slug="rtx-4060-ti-test",
        name="NVIDIA GeForce RTX 4060 Ti",
        category="gpu",
        brand="NVIDIA",
        release_year=2023,
        launch_msrp_usd=399.0,
        architecture="Ada Lovelace",
        process_node_nm=4.0,
        tdp_w=160,
        pcie_interface="PCIe 4.0 x8",
        raw_specs={"pcie_lanes": 8},
        benchmark_index=68.0
    )
    repo.upsert_hardware_spec(spec)

    loaded = repo.get_hardware_by_id("rtx-4060-ti-test")
    assert loaded is not None
    assert loaded.pcie_interface == "PCIe 4.0 x8"
    assert loaded.is_8_lane_pcie is True


def test_fps_calculator_card_fps_completely_decoupled_from_opponent():
    """Attack architectural defect: verifies that an individual GPU's FPS never changes based on opponent."""
    spec_4070_s = HardwareSpec(
        id="rtx-4070-super", slug="rtx-4070-super", name="NVIDIA GeForce RTX 4070 Super",
        category="gpu", brand="NVIDIA", release_year=2024, launch_msrp_usd=599.0,
        architecture="Ada Lovelace", process_node_nm=4.0, tdp_w=220,
        raw_specs={"cuda_cores": 7168, "vram_gb": 12, "bus_width_bit": 192, "pcie_lanes": 16},
        benchmark_index=82.5, gaming_scores={"raster_1080p": 88.0, "raster_1440p": 82.0, "raster_4k": 68.0},
        ray_tracing_score=85.0, efficiency_score=90.0
    )
    spec_7800_xt = HardwareSpec(
        id="rx-7800-xt", slug="rx-7800-xt", name="AMD Radeon RX 7800 XT",
        category="gpu", brand="AMD", release_year=2023, launch_msrp_usd=499.0,
        architecture="RDNA 3", process_node_nm=5.0, tdp_w=263,
        raw_specs={"stream_processors": 3840, "vram_gb": 16, "bus_width_bit": 256, "pcie_lanes": 16},
        benchmark_index=81.0, gaming_scores={"raster_1080p": 87.0, "raster_1440p": 83.5, "raster_4k": 71.0},
        ray_tracing_score=67.0, efficiency_score=78.0
    )
    spec_4080_s = HardwareSpec(
        id="rtx-4080-super", slug="rtx-4080-super", name="NVIDIA GeForce RTX 4080 Super",
        category="gpu", brand="NVIDIA", release_year=2024, launch_msrp_usd=999.0,
        architecture="Ada Lovelace", process_node_nm=4.0, tdp_w=320,
        raw_specs={"cuda_cores": 10240, "vram_gb": 16, "bus_width_bit": 256, "pcie_lanes": 16},
        benchmark_index=92.0, gaming_scores={"raster_1080p": 95.0, "raster_1440p": 93.0, "raster_4k": 88.0},
        ray_tracing_score=93.0, efficiency_score=88.0
    )

    # Calculate 4070S paired against 7800 XT
    matrix_1 = FpsCalculator.calculate_fps_matrix(spec_4070_s, spec_7800_xt)
    fps_4070s_m1 = {f"{i.game_title}_{i.resolution}": i.fps_a for i in matrix_1}

    # Calculate 4070S paired against 4080 Super (as item_a)
    matrix_2 = FpsCalculator.calculate_fps_matrix(spec_4070_s, spec_4080_s)
    fps_4070s_m2 = {f"{i.game_title}_{i.resolution}": i.fps_a for i in matrix_2}

    # Calculate 4070S paired against 4080 Super (as item_b)
    matrix_3 = FpsCalculator.calculate_fps_matrix(spec_4080_s, spec_4070_s)
    fps_4070s_m3 = {f"{i.game_title}_{i.resolution}": i.fps_b for i in matrix_3}

    # Every single game at every resolution must produce IDENTICAL FPS for 4070S
    for key in fps_4070s_m1:
        assert fps_4070s_m1[key] == fps_4070s_m2[key] == fps_4070s_m3[key], f"FPS mismatch for 4070S in {key}!"

    # Intra-brand comparison: 4080 Super must be faster than 4070 Super in Call of Duty: Warzone
    wz_item = next(i for i in matrix_2 if i.game_title == "Call of Duty: Warzone" and i.resolution == "1440p")
    assert wz_item.fps_b > wz_item.fps_a
    assert wz_item.fps_b - wz_item.fps_a >= 10  # 4080 Super must maintain clear lead over 4070 Super


def test_ai_editorial_dynamic_retail_price_revision_from_metadata():
    """Verifies that setting revised_msrp_usd in raw_specs triggers the market price revision note."""
    spec_a = HardwareSpec(
        id="card-a", slug="card-a", name="Card Alpha", category="gpu", brand="NVIDIA",
        release_year=2024, launch_msrp_usd=500.0, architecture="Ada", process_node_nm=4.0,
        tdp_w=200, benchmark_index=80.0
    )
    spec_b = HardwareSpec(
        id="card-b", slug="card-b", name="Card Beta", category="gpu", brand="AMD",
        release_year=2024, launch_msrp_usd=550.0, architecture="RDNA 3", process_node_nm=5.0,
        tdp_w=250, benchmark_index=85.0, raw_specs={"revised_msrp_usd": 499.0}
    )

    verdict = EditorialRuleEngine.generate_verdict(spec_a, spec_b)
    assert "تعديل السعر الرسمي" in verdict.value_and_budget_ar


def test_laptop_classification_and_weight_threshold_zephyrus_g16():
    """Verifies that Zephyrus G16 (weight 1.85 kg <= 1.9) is recognized as portable/thin-and-light with OLED."""
    g16 = HardwareSpec(
        id="rog-zephyrus-g16", slug="rog-zephyrus-g16", name="ASUS ROG Zephyrus G16 (2024)",
        category="laptop", brand="ASUS", release_year=2024, launch_msrp_usd=1999.0,
        architecture="Meteor Lake + Ada", process_node_nm=4.0, tdp_w=105,
        raw_specs={"weight_kg": 1.85, "display_tech": "OLED", "battery_wh": 90.0},
        benchmark_index=84.0, features=["OLED 2.5K 240Hz 0.2ms"]
    )
    legion = HardwareSpec(
        id="legion-pro-7i", slug="legion-pro-7i", name="Lenovo Legion Pro 7i (Gen 9)",
        category="laptop", brand="Lenovo", release_year=2024, launch_msrp_usd=2199.0,
        architecture="Intel 14th Gen + RTX 4080", process_node_nm=4.0, tdp_w=175,
        raw_specs={"weight_kg": 2.6, "display_tech": "IPS", "battery_wh": 99.9},
        benchmark_index=91.0, features=["500 nits High-Brightness IPS"]
    )
    verdict = EditorialRuleEngine.generate_verdict(g16, legion)
    # Check who_should_buy_a recognizes portability and OLED
    assert "كثير التنقل" in verdict.who_should_buy_a or "خفة الوزن" in verdict.who_should_buy_a
    assert "1.9 كجم" in verdict.who_should_buy_a or "1.85" in verdict.who_should_buy_a
    assert "OLED" in verdict.who_should_buy_a

    # Check pros and cons for display
    pros_a_text = " ".join(verdict.pros_a)
    cons_a_text = " ".join(verdict.cons_a)
    pros_b_text = " ".join(verdict.pros_b)
    assert "OLED" in pros_a_text and "0.2ms" in pros_a_text
    assert "Burn-in" in cons_a_text or "تطبيع" in cons_a_text
    assert "500 nits" in pros_b_text and "IPS" in pros_b_text


def test_laptop_tdp_custom_label_and_tie_nuance():
    """Verifies that laptop tdp_w is compared as tie with GPU TGP / Thermal Budget nuance."""
    from core.services.spec_engine import SpecEngine
    g16 = HardwareSpec(
        id="rog-zephyrus-g16", slug="rog-zephyrus-g16", name="ASUS ROG Zephyrus G16 (2024)",
        category="laptop", brand="ASUS", release_year=2024, launch_msrp_usd=1999.0,
        architecture="Meteor Lake + Ada", process_node_nm=4.0, tdp_w=105,
        raw_specs={"weight_kg": 1.85, "display_tech": "OLED", "battery_wh": 90.0},
        benchmark_index=84.0
    )
    legion = HardwareSpec(
        id="legion-pro-7i", slug="legion-pro-7i", name="Lenovo Legion Pro 7i (Gen 9)",
        category="laptop", brand="Lenovo", release_year=2024, launch_msrp_usd=2199.0,
        architecture="Intel 14th Gen + RTX 4080", process_node_nm=4.0, tdp_w=175,
        raw_specs={"weight_kg": 2.6, "display_tech": "IPS", "battery_wh": 99.9},
        benchmark_index=91.0
    )
    diffs = SpecEngine.compare_specs(g16, legion)
    tdp_diff = next(d for d in diffs if d.key == "tdp_w")
    assert tdp_diff.winner == "tie"
    assert "GPU TGP / Thermal Budget" in tdp_diff.label_ar
    assert "مقياس هندسي" in tdp_diff.advantage_summary_ar


def test_cpu_cleanliness_ray_tracing_null_and_platform_longevity():
    """Verifies null ray_tracing_score for CPUs and AM5 2027+ / LGA 1700 EOL editorial badges."""
    from core.services.spec_engine import SpecEngine
    cpu_amd = HardwareSpec(
        id="ryzen-7-7800x3d", slug="ryzen-7-7800x3d", name="AMD Ryzen 7 7800X3D",
        category="cpu", brand="AMD", release_year=2023, launch_msrp_usd=449.0,
        architecture="Zen 4 (3D V-Cache)", process_node_nm=5.0, tdp_w=120,
        raw_specs={"total_cores": 8, "threads": 16, "socket": "AM5"},
        benchmark_index=91.0, ray_tracing_score=None,
        features=["96MB 3D V-Cache", "AM5 Platform Lifecycle through 2027+"]
    )
    cpu_intel = HardwareSpec(
        id="i7-14700k", slug="i7-14700k", name="Intel Core i7-14700K",
        category="cpu", brand="Intel", release_year=2023, launch_msrp_usd=409.0,
        architecture="Raptor Lake Refresh (Intel 7 / 10nm Enhanced SuperFin)", process_node_nm=7.0, tdp_w=253,
        raw_specs={"total_cores": 20, "threads": 28, "socket": "LGA 1700 (End of Life)", "process_node": "Intel 7 (10nm Enhanced SuperFin)"},
        benchmark_index=92.5, ray_tracing_score=None,
        features=["Intel 7 (10nm Enhanced SuperFin)"]
    )

    # 1. Spec diffs must NOT include ray_tracing_score for CPUs
    diffs = SpecEngine.compare_specs(cpu_amd, cpu_intel)
    assert not any(d.key == "ray_tracing_score" for d in diffs)

    # 2. Process node must be a tie with Intel 7 vs TSMC 5nm note
    nm_diff = next(d for d in diffs if d.key == "process_node_nm")
    assert nm_diff.winner == "tie"
    assert "Intel 7" in nm_diff.advantage_summary_ar

    # 3. Editorial pros/cons must reflect AM5 2027+ and LGA 1700 EOL
    verdict = EditorialRuleEngine.generate_verdict(cpu_amd, cpu_intel)
    pros_amd = " ".join(verdict.pros_a)
    cons_intel = " ".join(verdict.cons_b)
    assert "2027+" in pros_amd and "AM5" in pros_amd
    assert "LGA 1700" in cons_intel and ("منتهية" in cons_intel or "Dead-end" in cons_intel)


def test_intertier_gpu_scaling_and_rt_badges():
    """Verifies calibrated inter-tier scaling (4070S vs 4080S ~30%, 7800XT vs 7900XTX ~38%) and RT badges."""
    import json
    from core.config import SEED_DATA_PATH
    with open(SEED_DATA_PATH, "r", encoding="utf-8") as f:
        data = {item["id"]: HardwareSpec.model_validate(item) for item in json.load(f)}

    # 1. RTX 4070S vs RTX 4080S
    s_4070 = data["rtx-4070-super"]
    s_4080 = data["rtx-4080-super"]
    matrix_4080 = FpsCalculator.calculate_fps_matrix(s_4070, s_4080)
    leads_4080 = [((i.fps_b - i.fps_a) / i.fps_a) * 100 for i in matrix_4080 if i.resolution == "1440p"]
    avg_lead_4080 = sum(leads_4080) / len(leads_4080)
    assert 28.0 <= avg_lead_4080 <= 33.0, f"Expected ~30% lead for 4080S, got {avg_lead_4080:.1f}%"

    verdict_4080 = EditorialRuleEngine.generate_verdict(s_4070, s_4080, matrix_4080)
    assert "~30" in verdict_4080.quick_verdict_ar or "~30" in verdict_4080.value_and_budget_ar

    # 2. RX 7800 XT vs RX 7900 XTX
    s_7800 = data["rx-7800-xt"]
    s_7900 = data["rx-7900-xtx"]
    matrix_7900 = FpsCalculator.calculate_fps_matrix(s_7800, s_7900)
    leads_7900 = [((i.fps_b - i.fps_a) / i.fps_a) * 100 for i in matrix_7900 if i.resolution == "1440p"]
    avg_lead_7900 = sum(leads_7900) / len(leads_7900)
    assert 35.0 <= avg_lead_7900 <= 40.0, f"Expected ~38% lead for 7900XTX, got {avg_lead_7900:.1f}%"

    verdict_7900 = EditorialRuleEngine.generate_verdict(s_7800, s_7900, matrix_7900)
    assert "~37" in verdict_7900.quick_verdict_ar or "~38" in verdict_7900.value_and_budget_ar

    # 3. Ray Tracing disclosures
    cp_item = next(i for i in matrix_4080 if i.game_title == "Cyberpunk 2077")
    wk_item = next(i for i in matrix_4080 if i.game_title == "Black Myth: Wukong")
    cs_item = next(i for i in matrix_4080 if i.game_title == "Counter-Strike 2")
    assert cp_item.rt_badge_ar == "⚡ تتبع الأشعة مفعّل (RT ON)"
    assert wk_item.rt_badge_ar == "💡 إضاءة Lumen العتادية"
    assert cs_item.rt_badge_ar is None

    # 4. RTX 4060 Ti variant name clarity
    s_4060 = data["rtx-4060-ti"]
    assert s_4060.name == "NVIDIA GeForce RTX 4060 Ti (8GB)"


def test_pricing_framing_markup_over_cheaper_msrp():
    """Verifies that editorial value narratives explicitly frame price deltas as markup over cheaper MSRP."""
    s_4070 = HardwareSpec(
        id="card-a", slug="card-a", name="Card Alpha", category="gpu", brand="NVIDIA",
        release_year=2024, launch_msrp_usd=500.0, architecture="Ada", process_node_nm=4.0,
        tdp_w=200, benchmark_index=80.0
    )
    s_4080 = HardwareSpec(
        id="card-b", slug="card-b", name="Card Beta", category="gpu", brand="NVIDIA",
        release_year=2024, launch_msrp_usd=750.0, architecture="Ada", process_node_nm=4.0,
        tdp_w=300, benchmark_index=95.0
    )
    verdict = EditorialRuleEngine.generate_verdict(s_4070, s_4080)
    # Price difference is $250. Over $500 (cheaper), that is 50% markup.
    assert "عن السعر الأقل" in verdict.value_and_budget_ar


def test_laptop_portability_sub_2kg_edge_case():
    """Verifies that laptops weighing between 1.90 and 1.99 kg are classified as portable thin-and-light."""
    slim_195 = HardwareSpec(
        id="laptop-195", slug="laptop-195", name="Thin Gaming 16 (1.95kg)",
        category="laptop", brand="ASUS", release_year=2024, launch_msrp_usd=1800.0,
        architecture="Meteor Lake", process_node_nm=4.0, tdp_w=100,
        raw_specs={"weight_kg": 1.95, "display": "16-inch OLED 240Hz", "battery_wh": 85.0},
        benchmark_index=83.0, features=["OLED Display"]
    )
    heavy_desk = HardwareSpec(
        id="laptop-heavy", slug="laptop-heavy", name="Heavy Beast 17 (2.8kg)",
        category="laptop", brand="Lenovo", release_year=2024, launch_msrp_usd=2500.0,
        architecture="Intel 14th Gen", process_node_nm=4.0, tdp_w=175,
        raw_specs={"weight_kg": 2.8, "display": "17-inch IPS 500nits", "battery_wh": 99.0},
        benchmark_index=92.0
    )
    verdict = EditorialRuleEngine.generate_verdict(slim_195, heavy_desk)
    # 1.95kg laptop must receive portable buyer recommendation
    assert "كثير التنقل" in verdict.who_should_buy_a or "خفة الوزن" in verdict.who_should_buy_a
    assert "اللاعب أو المحترف" in verdict.who_should_buy_b


def test_laptop_heavy_weight_con_deduplication():
    """Verifies that heavy laptops (>= 2.5 kg) do not receive redundant duplicate weight cons."""
    g16 = HardwareSpec(
        id="rog-zephyrus-g16", slug="rog-zephyrus-g16", name="ASUS ROG Zephyrus G16 (2024)",
        category="laptop", brand="ASUS", release_year=2024, launch_msrp_usd=1999.0,
        architecture="Meteor Lake + Ada", process_node_nm=4.0, tdp_w=105,
        raw_specs={"weight_kg": 1.85, "display": "16-inch OLED 2.5K 240Hz 0.2ms", "battery_wh": 90.0},
        benchmark_index=84.0, features=["OLED"]
    )
    legion = HardwareSpec(
        id="legion-pro-7i", slug="legion-pro-7i", name="Lenovo Legion Pro 7i (Gen 9)",
        category="laptop", brand="Lenovo", release_year=2024, launch_msrp_usd=2199.0,
        architecture="Intel 14th Gen + RTX 4080", process_node_nm=4.0, tdp_w=175,
        raw_specs={"weight_kg": 2.6, "display": "16-inch IPS 2.5K 240Hz 500nits", "battery_wh": 99.9},
        benchmark_index=91.0
    )
    verdict = EditorialRuleEngine.generate_verdict(g16, legion)
    # Count how many cons mention weight for Legion
    weight_cons = [c for c in verdict.cons_b if "وزن" in c or "كجم" in c]
    assert len(weight_cons) == 1, f"Expected exactly 1 weight con for heavy laptop, found: {weight_cons}"


def test_laptop_display_spec_diff_and_oled_vs_ips():
    """Verifies that SpecEngine compares laptop display specs and provides OLED vs IPS technical context."""
    from core.services.spec_engine import SpecEngine
    g16 = HardwareSpec(
        id="rog-zephyrus-g16", slug="rog-zephyrus-g16", name="ASUS ROG Zephyrus G16 (2024)",
        category="laptop", brand="ASUS", release_year=2024, launch_msrp_usd=1999.0,
        architecture="Meteor Lake + Ada", process_node_nm=4.0, tdp_w=105,
        raw_specs={"weight_kg": 1.85, "display": "16-inch OLED 2.5K 240Hz 0.2ms", "battery_wh": 90.0},
        benchmark_index=84.0
    )
    legion = HardwareSpec(
        id="legion-pro-7i", slug="legion-pro-7i", name="Lenovo Legion Pro 7i (Gen 9)",
        category="laptop", brand="Lenovo", release_year=2024, launch_msrp_usd=2199.0,
        architecture="Intel 14th Gen + RTX 4080", process_node_nm=4.0, tdp_w=175,
        raw_specs={"weight_kg": 2.6, "display": "16-inch IPS 2.5K 240Hz 500nits Anti-Glare", "battery_wh": 99.9},
        benchmark_index=91.0
    )
    diffs = SpecEngine.compare_specs(g16, legion)
    display_diff = next((d for d in diffs if d.key == "display"), None)
    assert display_diff is not None, "Expected 'display' row in laptop spec differences"
    assert display_diff.winner == "tie"
    assert "OLED" in display_diff.advantage_summary_ar and "IPS" in display_diff.advantage_summary_ar
    assert "0.2ms" in display_diff.advantage_summary_ar and "500 nits" in display_diff.advantage_summary_ar


def test_cpu_intel7_no_raw_7nm_in_pros():
    """Verifies that Intel Core i7-14700K pros do not include misleading raw 'بدقة تصنيع 7nm'."""
    cpu_intel = HardwareSpec(
        id="i7-14700k", slug="i7-14700k", name="Intel Core i7-14700K",
        category="cpu", brand="Intel", release_year=2023, launch_msrp_usd=409.0,
        architecture="Raptor Lake Refresh (Intel 7 / 10nm Enhanced SuperFin)", process_node_nm=7.0, tdp_w=253,
        raw_specs={"total_cores": 20, "threads": 28, "socket": "LGA 1700 (End of Life)"},
        benchmark_index=92.5
    )
    cpu_amd = HardwareSpec(
        id="ryzen-7-7800x3d", slug="ryzen-7-7800x3d", name="AMD Ryzen 7 7800X3D",
        category="cpu", brand="AMD", release_year=2023, launch_msrp_usd=449.0,
        architecture="Zen 4 (3D V-Cache)", process_node_nm=5.0, tdp_w=120,
        raw_specs={"total_cores": 8, "threads": 16, "socket": "AM5"},
        benchmark_index=91.0
    )
    verdict = EditorialRuleEngine.generate_verdict(cpu_amd, cpu_intel)
    pros_intel_text = " ".join(verdict.pros_b)
    assert "بدقة تصنيع 7nm" not in pros_intel_text
    assert "Intel 7" in pros_intel_text


def test_pricing_framing_markup_over_cheaper_msrp_on_cost_per_frame_parity():
    """Verifies that cost-per-frame parity narratives (e.g. 4060 Ti vs 7700 XT) also clarify markup over cheaper MSRP."""
    import json
    from core.config import SEED_DATA_PATH
    with open(SEED_DATA_PATH, "r", encoding="utf-8") as f:
        data = {item["id"]: HardwareSpec.model_validate(item) for item in json.load(f)}

    s_4060 = data["rtx-4060-ti"]
    s_7700 = data["rx-7700-xt"]
    verdict = EditorialRuleEngine.generate_verdict(s_4060, s_7700)
    assert "عن السعر الأقل" in verdict.value_and_budget_ar







