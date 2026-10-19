"""
Tests for Domain Models and Validation.
"""

import pytest
from pydantic import ValidationError
from core.domain.models import HardwareSpec, AffiliateOffer, SpecDiffItem


def test_hardware_spec_validation():
    valid_spec = HardwareSpec(
        id="test-gpu",
        slug="test-gpu",
        name="Test GPU 1000",
        category="gpu",
        brand="NVIDIA",
        release_year=2024,
        launch_msrp_usd=499.0,
        architecture="TestArch",
        process_node_nm=4.0,
        tdp_w=200,
        raw_specs={"vram_gb": 12},
        benchmark_index=80.0,
        gaming_scores={"raster_1440p": 80.0},
        ray_tracing_score=75.0,
        efficiency_score=85.0,
        features=["DLSS"]
    )
    assert valid_spec.id == "test-gpu"
    assert valid_spec.launch_msrp_usd == 499.0


def test_hardware_spec_invalid_year():
    with pytest.raises(ValidationError):
        HardwareSpec(
            id="bad-year",
            slug="bad-year",
            name="Bad Year",
            category="gpu",
            brand="NVIDIA",
            release_year=1990,  # Below min 2015
            launch_msrp_usd=200.0,
            architecture="Old",
            process_node_nm=10.0,
            tdp_w=100,
            benchmark_index=50.0
        )


def test_affiliate_offer_rejects_amazon():
    with pytest.raises(ValidationError) as exc_info:
        AffiliateOffer(
            store_key="amazon",
            store_name_ar="أمازون",
            store_name_en="Amazon",
            product_title="Forbidden Item",
            direct_url="https://noon.com/dp/123",
            affiliate_url="https://noon.com/dp/123?tag=aff",
            badge_color="#000",
            text_color="#fff"
        )
    assert "Amazon is strictly forbidden" in str(exc_info.value)


def test_affiliate_offer_rejects_amazon_in_urls():
    # Even if store_key is valid (noon), an Amazon URL must be strictly rejected
    with pytest.raises(ValidationError) as exc_info:
        AffiliateOffer(
            store_key="noon",
            store_name_ar="نون",
            store_name_en="Noon",
            product_title="Sneaky Item",
            direct_url="https://www.amazon.com/dp/B000123",
            affiliate_url="https://www.noon.com/item",
            badge_color="#fee600",
            text_color="#000"
        )
    assert "Amazon URLs are strictly forbidden" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info2:
        AffiliateOffer(
            store_key="newegg",
            store_name_ar="نيو إيج",
            store_name_en="Newegg",
            product_title="Sneaky Shortlink",
            direct_url="https://www.newegg.com/item",
            affiliate_url="https://amzn.to/3xyz",
            badge_color="#f37021",
            text_color="#fff"
        )
    assert "Amazon URLs are strictly forbidden" in str(exc_info2.value)


def test_hardware_spec_invalid_numeric_bounds():
    with pytest.raises(ValidationError):
        HardwareSpec(
            id="bad-tdp",
            slug="bad-tdp",
            name="Bad TDP",
            category="gpu",
            brand="NVIDIA",
            release_year=2024,
            launch_msrp_usd=499.0,
            architecture="Ada",
            process_node_nm=4.0,
            tdp_w=-10,  # Negative TDP
            benchmark_index=80.0
        )

    with pytest.raises(ValidationError):
        HardwareSpec(
            id="bad-nm",
            slug="bad-nm",
            name="Bad Node",
            category="gpu",
            brand="NVIDIA",
            release_year=2024,
            launch_msrp_usd=499.0,
            architecture="Ada",
            process_node_nm=0.0,  # Zero process node
            tdp_w=200,
            benchmark_index=80.0
        )


def test_spec_diff_item_winner_literal():
    item = SpecDiffItem(
        key="test",
        label_ar="اختبار",
        value_a=100,
        value_b=80,
        unit="W",
        winner="a",
        diff_percentage=25.0
    )
    assert item.winner == "a"


def test_hardware_spec_pcie_interface_and_8_lane_property():
    gpu_8_lane = HardwareSpec(
        id="gpu-8", slug="gpu-8", name="GPU 8 Lane", category="gpu", brand="NVIDIA",
        release_year=2023, launch_msrp_usd=399.0, architecture="Ada", process_node_nm=4.0,
        tdp_w=160, benchmark_index=68.0, pcie_interface="PCIe 4.0 x8", raw_specs={"pcie_lanes": 8}
    )
    assert gpu_8_lane.is_8_lane_pcie is True
    assert gpu_8_lane.pcie_interface == "PCIe 4.0 x8"

    gpu_16_lane = HardwareSpec(
        id="gpu-16", slug="gpu-16", name="GPU 16 Lane", category="gpu", brand="AMD",
        release_year=2023, launch_msrp_usd=449.0, architecture="RDNA 3", process_node_nm=5.0,
        tdp_w=245, benchmark_index=74.0, pcie_interface="PCIe 4.0 x16", raw_specs={"pcie_lanes": 16}
    )
    assert gpu_16_lane.is_8_lane_pcie is False

    cpu = HardwareSpec(
        id="cpu-test", slug="cpu-test", name="CPU Test", category="cpu", brand="AMD",
        release_year=2023, launch_msrp_usd=449.0, architecture="Zen 4", process_node_nm=5.0,
        tdp_w=120, benchmark_index=91.0, raw_specs={"pcie_lanes": 8}
    )
    # CPUs must never be flagged as 8-lane GPU bottleneck
    assert cpu.is_8_lane_pcie is False

