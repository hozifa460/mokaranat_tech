"""
Tests for SpecEngine and FpsCalculator Services.
"""

import pytest
from core.domain.models import HardwareSpec
from core.services.spec_engine import SpecEngine
from core.services.fps_calculator import FpsCalculator


@pytest.fixture
def sample_gpus():
    gpu_a = HardwareSpec(
        id="gpu-a",
        slug="gpu-a",
        name="GPU Alpha",
        category="gpu",
        brand="NVIDIA",
        release_year=2024,
        launch_msrp_usd=600.0,
        architecture="Ada",
        process_node_nm=4.0,
        tdp_w=200,
        raw_specs={"vram_gb": 12, "boost_clock_mhz": 2500, "bus_width_bit": 192},
        benchmark_index=85.0,
        gaming_scores={"raster_1080p": 90.0, "raster_1440p": 85.0, "raster_4k": 70.0},
        ray_tracing_score=85.0,
        efficiency_score=90.0,
        features=["DLSS"]
    )
    gpu_b = HardwareSpec(
        id="gpu-b",
        slug="gpu-b",
        name="GPU Beta",
        category="gpu",
        brand="AMD",
        release_year=2023,
        launch_msrp_usd=500.0,
        architecture="RDNA 3",
        process_node_nm=5.0,
        tdp_w=250,
        raw_specs={"vram_gb": 16, "boost_clock_mhz": 2400, "bus_width_bit": 256},
        benchmark_index=80.0,
        gaming_scores={"raster_1080p": 85.0, "raster_1440p": 80.0, "raster_4k": 65.0},
        ray_tracing_score=65.0,
        efficiency_score=75.0,
        features=["FSR"]
    )
    return gpu_a, gpu_b


def test_spec_engine_higher_and_lower_is_better(sample_gpus):
    gpu_a, gpu_b = sample_gpus
    diffs = SpecEngine.compare_specs(gpu_a, gpu_b)

    diff_map = {d.key: d for d in diffs}

    # Benchmark index: higher is better -> GPU A wins
    assert diff_map["benchmark_index"].winner == "a"

    # Price: lower is better ($500 vs $600) -> GPU B wins
    assert diff_map["launch_msrp_usd"].winner == "b"

    # TDP: lower is better (200W vs 250W) -> GPU A wins
    assert diff_map["tdp_w"].winner == "a"

    # VRAM: higher is better (16GB vs 12GB) -> GPU B wins
    assert diff_map["vram_gb"].winner == "b"


def test_fps_calculator(sample_gpus):
    gpu_a, gpu_b = sample_gpus
    fps_items = FpsCalculator.calculate_fps_matrix(gpu_a, gpu_b)

    assert len(fps_items) > 0
    first = fps_items[0]
    assert first.game_title in ["Cyberpunk 2077", "Black Myth: Wukong", "Counter-Strike 2"]
    assert first.fps_a > 0
    assert first.fps_b > 0
    assert first.winner in ("a", "b", "tie")


def test_spec_engine_cpu_excludes_ray_tracing():
    cpu_a = HardwareSpec(
        id="cpu-1",
        slug="cpu-1",
        name="CPU Alpha",
        category="cpu",
        brand="AMD",
        release_year=2024,
        launch_msrp_usd=400.0,
        architecture="Zen 5",
        process_node_nm=4.0,
        tdp_w=120,
        raw_specs={"total_cores": 8, "threads": 16, "l3_cache_mb": 64},
        benchmark_index=90.0
    )
    cpu_b = HardwareSpec(
        id="cpu-2",
        slug="cpu-2",
        name="CPU Beta",
        category="cpu",
        brand="Intel",
        release_year=2024,
        launch_msrp_usd=380.0,
        architecture="Raptor",
        process_node_nm=7.0,
        tdp_w=200,
        raw_specs={"total_cores": 16, "threads": 24, "l3_cache_mb": 30},
        benchmark_index=89.0
    )

    diffs = SpecEngine.compare_specs(cpu_a, cpu_b)
    diff_keys = [d.key for d in diffs]

    assert "ray_tracing_score" not in diff_keys, "CPUs must not contain Ray Tracing metric in comparisons!"
    assert "total_cores" in diff_keys
    assert "threads" in diff_keys
    assert "l3_cache_mb" in diff_keys


def test_spec_engine_laptop_specs():
    laptop_a = HardwareSpec(
        id="lap-1",
        slug="lap-1",
        name="Laptop Air",
        category="laptop",
        brand="ASUS",
        release_year=2024,
        launch_msrp_usd=1500.0,
        architecture="Intel Ultra",
        process_node_nm=4.0,
        tdp_w=80,
        raw_specs={"weight_kg": 1.5, "battery_wh": 75},
        benchmark_index=80.0
    )
    laptop_b = HardwareSpec(
        id="lap-2",
        slug="lap-2",
        name="Laptop Pro",
        category="laptop",
        brand="Lenovo",
        release_year=2024,
        launch_msrp_usd=1800.0,
        architecture="Intel 14th",
        process_node_nm=4.0,
        tdp_w=140,
        raw_specs={"weight_kg": 2.4, "battery_wh": 99},
        benchmark_index=88.0
    )

    diffs = SpecEngine.compare_specs(laptop_a, laptop_b)
    diff_map = {d.key: d for d in diffs}

    assert "weight_kg" in diff_map
    assert diff_map["weight_kg"].winner == "a"  # 1.5kg < 2.4kg (lighter is better)
    assert "battery_wh" in diff_map
    assert diff_map["battery_wh"].winner == "b"  # 99Wh > 75Wh (bigger is better)


def test_fps_calculator_rt_heavy_differentiation(sample_gpus):
    gpu_a, gpu_b = sample_gpus
    # GPU A has higher ray tracing (85 vs 65)
    fps_items = FpsCalculator.calculate_fps_matrix(gpu_a, gpu_b)
    cp_items = [item for item in fps_items if item.game_title == "Cyberpunk 2077"]

    assert len(cp_items) == 3
    # GPU A should win in Cyberpunk RT-heavy at 1080p and 1440p
    cp_1080p = next(i for i in cp_items if i.resolution == "1080p")
    assert cp_1080p.winner == "a"
    assert cp_1080p.fps_a > cp_1080p.fps_b


def test_spec_engine_identical_prices():
    gpu_1 = HardwareSpec(
        id="gpu-1", slug="gpu-1", name="Card A", category="gpu", brand="NVIDIA",
        release_year=2024, launch_msrp_usd=999.0, architecture="Ada", process_node_nm=4.0,
        tdp_w=300, benchmark_index=90.0
    )
    gpu_2 = HardwareSpec(
        id="gpu-2", slug="gpu-2", name="Card B", category="gpu", brand="AMD",
        release_year=2024, launch_msrp_usd=999.0, architecture="RDNA 3", process_node_nm=5.0,
        tdp_w=300, benchmark_index=85.0
    )

    diffs = SpecEngine.compare_specs(gpu_1, gpu_2)
    diff_map = {d.key: d for d in diffs}

    assert diff_map["launch_msrp_usd"].winner == "tie"
    assert diff_map["launch_msrp_usd"].diff_percentage == 0.0
    assert diff_map["launch_msrp_usd"].advantage_summary_ar == "السعر متطابق"


def test_spec_engine_statistical_margin_3_percent():
    # 93.5 vs 92.0 has a 1.63% difference (< 3.0% margin of error) -> must be a tie
    gpu_1 = HardwareSpec(
        id="gpu-1", slug="gpu-1", name="Card A", category="gpu", brand="NVIDIA",
        release_year=2024, launch_msrp_usd=999.0, architecture="Ada", process_node_nm=4.0,
        tdp_w=300, benchmark_index=92.0
    )
    gpu_2 = HardwareSpec(
        id="gpu-2", slug="gpu-2", name="Card B", category="gpu", brand="AMD",
        release_year=2024, launch_msrp_usd=999.0, architecture="RDNA 3", process_node_nm=5.0,
        tdp_w=300, benchmark_index=93.5
    )

    diffs = SpecEngine.compare_specs(gpu_1, gpu_2)
    diff_map = {d.key: d for d in diffs}

    assert diff_map["benchmark_index"].winner == "tie"
    assert "أقل من 3%" in diff_map["benchmark_index"].advantage_summary_ar


def test_spec_engine_cross_architecture_no_flawed_winner():
    # Comparing Ada (2550 MHz) vs RDNA 3 (2500 MHz) cannot award a raw winner due to IPC differences
    gpu_1 = HardwareSpec(
        id="gpu-1", slug="gpu-1", name="Card Ada", category="gpu", brand="NVIDIA",
        release_year=2024, launch_msrp_usd=999.0, architecture="Ada Lovelace", process_node_nm=4.0,
        tdp_w=300, raw_specs={"boost_clock_mhz": 2550}, benchmark_index=90.0
    )
    gpu_2 = HardwareSpec(
        id="gpu-2", slug="gpu-2", name="Card RDNA", category="gpu", brand="AMD",
        release_year=2024, launch_msrp_usd=999.0, architecture="RDNA 3", process_node_nm=5.0,
        tdp_w=300, raw_specs={"boost_clock_mhz": 2500}, benchmark_index=90.0
    )

    diffs = SpecEngine.compare_specs(gpu_1, gpu_2)
    diff_map = {d.key: d for d in diffs}

    # Boost clock: cross-architecture must be tie without winner badge
    assert diff_map["boost_clock_mhz"].winner == "tie"
    assert "IPC" in diff_map["boost_clock_mhz"].advantage_summary_ar

    # Process node: cross-architecture must be tie without flawed percentage
    assert diff_map["process_node_nm"].winner == "tie"
    assert diff_map["process_node_nm"].diff_percentage == 0.0


def test_fps_calculator_within_statistical_margin():
    # Test that FPS difference under 3% results in a tie
    gpu_a = HardwareSpec(
        id="gpu-a", slug="gpu-a", name="Card A", category="gpu", brand="NVIDIA",
        release_year=2024, launch_msrp_usd=600.0, architecture="Ada", process_node_nm=4.0,
        tdp_w=200, benchmark_index=85.0,
        gaming_scores={"raster_1080p": 85.0, "raster_1440p": 85.0, "raster_4k": 85.0},
        ray_tracing_score=85.0
    )
    # GPU B is 1% lower in score -> under 3% margin
    gpu_b = HardwareSpec(
        id="gpu-b", slug="gpu-b", name="Card B", category="gpu", brand="NVIDIA",
        release_year=2024, launch_msrp_usd=600.0, architecture="Ada", process_node_nm=4.0,
        tdp_w=200, benchmark_index=84.2,
        gaming_scores={"raster_1080p": 84.2, "raster_1440p": 84.2, "raster_4k": 84.2},
        ray_tracing_score=84.2
    )

    fps_items = FpsCalculator.calculate_fps_matrix(gpu_a, gpu_b)
    assert len(fps_items) > 0
    # Any game where fps difference is < 3% should be tied
    for item in fps_items:
        if item.diff_pct < 3.0:
            assert item.winner == "tie"
        assert item.resolution in ("1080p", "1440p", "4K")
        assert "4Kg" not in item.resolution


def test_spec_engine_cpu_boost_clock_cross_architecture():
    # Cross architecture CPUs (Zen 4 vs Raptor Lake)
    cpu_a = HardwareSpec(
        id="cpu-1", slug="cpu-1", name="AMD Ryzen 7 7800X3D", category="cpu", brand="AMD",
        release_year=2023, launch_msrp_usd=449.0, architecture="Zen 4 (3D V-Cache)",
        process_node_nm=5.0, tdp_w=120, benchmark_index=91.0,
        raw_specs={"total_cores": 8, "threads": 16, "boost_clock_ghz": 5.0, "l3_cache_mb": 96}
    )
    cpu_b = HardwareSpec(
        id="cpu-2", slug="cpu-2", name="Intel Core i7-14700K", category="cpu", brand="Intel",
        release_year=2023, launch_msrp_usd=409.0, architecture="Raptor Lake Refresh",
        process_node_nm=7.0, tdp_w=253, benchmark_index=92.5,
        raw_specs={"total_cores": 20, "threads": 28, "boost_clock_ghz": 5.6, "l3_cache_mb": 33}
    )

    diffs = SpecEngine.compare_specs(cpu_a, cpu_b)
    diff_map = {d.key: d for d in diffs}

    assert "boost_clock_ghz" in diff_map
    assert diff_map["boost_clock_ghz"].winner == "tie"
    assert diff_map["boost_clock_ghz"].diff_percentage == 0.0
    assert "IPC" in diff_map["boost_clock_ghz"].advantage_summary_ar

    # Within same architecture, boost clock should compare normally
    cpu_c = HardwareSpec(
        id="cpu-3", slug="cpu-3", name="AMD Ryzen 9 7900X", category="cpu", brand="AMD",
        release_year=2023, launch_msrp_usd=549.0, architecture="Zen 4 (3D V-Cache)",
        process_node_nm=5.0, tdp_w=170, benchmark_index=94.0,
        raw_specs={"total_cores": 12, "threads": 24, "boost_clock_ghz": 5.4, "l3_cache_mb": 64}
    )
    diffs_same = SpecEngine.compare_specs(cpu_a, cpu_c)
    diff_map_same = {d.key: d for d in diffs_same}
    assert diff_map_same["boost_clock_ghz"].winner == "b"
    assert diff_map_same["boost_clock_ghz"].diff_percentage > 0.0


def test_spec_engine_gpu_vram_summary_tier_aware_no_4k_hyperbole():
    # Midrange test: RTX 4060 Ti 8GB vs RX 7700 XT 12GB
    gpu_4060ti = HardwareSpec(
        id="rtx-4060-ti", slug="rtx-4060-ti", name="NVIDIA GeForce RTX 4060 Ti",
        category="gpu", brand="NVIDIA", release_year=2023, launch_msrp_usd=399.0,
        architecture="Ada Lovelace", process_node_nm=4.0, tdp_w=160,
        raw_specs={"vram_gb": 8, "bus_width_bit": 128},
        benchmark_index=68.0, gaming_scores={"raster_1080p": 78.0, "raster_1440p": 65.0, "raster_4k": 45.0}
    )
    gpu_7700xt = HardwareSpec(
        id="rx-7700-xt", slug="rx-7700-xt", name="AMD Radeon RX 7700 XT",
        category="gpu", brand="AMD", release_year=2023, launch_msrp_usd=449.0,
        architecture="RDNA 3", process_node_nm=5.0, tdp_w=245,
        raw_specs={"vram_gb": 12, "bus_width_bit": 192},
        benchmark_index=74.0, gaming_scores={"raster_1080p": 82.0, "raster_1440p": 74.0, "raster_4k": 55.0}
    )
    diffs_mid = SpecEngine.compare_specs(gpu_4060ti, gpu_7700xt)
    diff_mid_map = {d.key: d for d in diffs_mid}
    assert "vram_gb" in diff_mid_map
    assert diff_mid_map["vram_gb"].winner == "b"
    # Midrange must NOT claim 4K
    assert "4K" not in diff_mid_map["vram_gb"].advantage_summary_ar
    assert "1440p" in diff_mid_map["vram_gb"].advantage_summary_ar

    # Flagship test: RTX 4080 Super 16GB vs RX 7900 XTX 24GB
    gpu_4080s = HardwareSpec(
        id="rtx-4080-super", slug="rtx-4080-super", name="NVIDIA GeForce RTX 4080 Super",
        category="gpu", brand="NVIDIA", release_year=2024, launch_msrp_usd=999.0,
        architecture="Ada Lovelace", process_node_nm=4.0, tdp_w=320,
        raw_specs={"vram_gb": 16, "bus_width_bit": 256},
        benchmark_index=92.0
    )
    gpu_7900xtx = HardwareSpec(
        id="rx-7900-xtx", slug="rx-7900-xtx", name="AMD Radeon RX 7900 XTX",
        category="gpu", brand="AMD", release_year=2022, launch_msrp_usd=999.0,
        architecture="RDNA 3", process_node_nm=5.0, tdp_w=355,
        raw_specs={"vram_gb": 24, "bus_width_bit": 384},
        benchmark_index=93.5
    )
    diffs_flag = SpecEngine.compare_specs(gpu_4080s, gpu_7900xtx)
    diff_flag_map = {d.key: d for d in diffs_flag}
    assert diff_flag_map["vram_gb"].winner == "b"
    # Flagship with 24GB accurately cites 4K
    assert "4K" in diff_flag_map["vram_gb"].advantage_summary_ar


def test_spec_engine_gpu_pcie_interface_comparison():
    gpu_4060ti = HardwareSpec(
        id="rtx-4060-ti", slug="rtx-4060-ti", name="NVIDIA GeForce RTX 4060 Ti",
        category="gpu", brand="NVIDIA", release_year=2023, launch_msrp_usd=399.0,
        architecture="Ada Lovelace", process_node_nm=4.0, tdp_w=160,
        pcie_interface="PCIe 4.0 x8", raw_specs={"pcie_lanes": 8, "vram_gb": 8},
        benchmark_index=68.0
    )
    gpu_7700xt = HardwareSpec(
        id="rx-7700-xt", slug="rx-7700-xt", name="AMD Radeon RX 7700 XT",
        category="gpu", brand="AMD", release_year=2023, launch_msrp_usd=449.0,
        architecture="RDNA 3", process_node_nm=5.0, tdp_w=245,
        pcie_interface="PCIe 4.0 x16", raw_specs={"pcie_lanes": 16, "vram_gb": 12},
        benchmark_index=74.0
    )

    diffs = SpecEngine.compare_specs(gpu_4060ti, gpu_7700xt)
    diff_map = {d.key: d for d in diffs}

    assert "pcie_interface" in diff_map
    assert diff_map["pcie_interface"].winner == "b"
    assert diff_map["pcie_interface"].value_a == "PCIe 4.0 x8"
    assert diff_map["pcie_interface"].value_b == "PCIe 4.0 x16"
    assert "16 مساراً" in diff_map["pcie_interface"].advantage_summary_ar

    # Equal 16 lanes comparison must be a tie
    gpu_4070s = HardwareSpec(
        id="rtx-4070-super", slug="rtx-4070-super", name="NVIDIA GeForce RTX 4070 Super",
        category="gpu", brand="NVIDIA", release_year=2024, launch_msrp_usd=599.0,
        architecture="Ada Lovelace", process_node_nm=4.0, tdp_w=220,
        pcie_interface="PCIe 4.0 x16", raw_specs={"pcie_lanes": 16, "vram_gb": 12},
        benchmark_index=82.5
    )
    diffs_equal = SpecEngine.compare_specs(gpu_4070s, gpu_7700xt)
    diff_equal_map = {d.key: d for d in diffs_equal}
    assert diff_equal_map["pcie_interface"].winner == "tie"
    assert diff_equal_map["pcie_interface"].diff_percentage == 0.0


