"""
Domain Models for Tech Comparisons Engine.
Clean Architecture - Layer: Domain Entities & Value Objects
Using Pydantic V2 for strict validation and serialization.
"""

from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field, field_validator


class HardwareSpec(BaseModel):
    id: str = Field(..., description="Unique hardware identifier, e.g. 'rtx-4070'")
    slug: str = Field(..., description="URL-friendly slug, e.g. 'rtx-4070'")
    name: str = Field(..., description="Full official product name, e.g. 'NVIDIA GeForce RTX 4070'")
    category: str = Field(..., description="Category: gpu, cpu, laptop")
    brand: str = Field(..., description="Brand: NVIDIA, AMD, Intel, etc.")
    release_year: int = Field(..., ge=2015, le=2030)
    launch_msrp_usd: float = Field(..., gt=0)
    architecture: str
    process_node_nm: float = Field(..., gt=0)
    tdp_w: int = Field(..., gt=0)
    raw_specs: Dict[str, Any] = Field(default_factory=dict, description="Detailed technical specs (cores, clocks, vram, bus)")
    benchmark_index: float = Field(..., ge=0, le=100, description="Normalized overall performance index (0-100)")
    gaming_scores: Dict[str, float] = Field(default_factory=dict, description="Resolution rasterization indices (1080p, 1440p, 4k)")
    ray_tracing_score: float = Field(default=50.0, ge=0, le=100)
    efficiency_score: float = Field(default=50.0, ge=0, le=100)
    features: List[str] = Field(default_factory=list)
    pcie_interface: Optional[str] = Field(default=None, description="PCIe interface, e.g. 'PCIe 4.0 x8' or 'PCIe 4.0 x16'")

    @property
    def is_8_lane_pcie(self) -> bool:
        """Accurately checks whether this GPU has an 8-lane PCIe interface constraint (e.g. PCIe 4.0 x8 on RTX 4060 / 4060 Ti)."""
        if self.category != "gpu":
            return False
        if self.pcie_interface and "x8" in self.pcie_interface.lower():
            return True
        raw_pcie = str(self.raw_specs.get("pcie_interface", "")).lower()
        if "x8" in raw_pcie:
            return True
        if self.raw_specs.get("pcie_lanes") == 8:
            return True
        return False

    @property
    def has_dual_nvenc(self) -> bool:
        """Accurately checks whether this NVIDIA GPU features Dual NVENC encoders.
        Dual NVENC encoders exist only on RTX 4070 Ti, RTX 4080, and RTX 4090 (AD104 full, AD103, AD102).
        Midrange chips AD106 (RTX 4060 Ti) and AD107 (RTX 4060) feature a single 8th Gen NVENC encoder.
        """
        if self.brand.upper() != "NVIDIA" or self.category != "gpu":
            return False
        val = self.raw_specs.get("nvenc_encoders")
        if val is not None:
            try:
                if int(val) == 2:
                    return True
                if int(val) == 1:
                    return False
            except (ValueError, TypeError):
                pass
        if any("dual nvenc" in f.lower() for f in self.features):
            return True
        name_lower = self.name.lower()
        return any(m in name_lower for m in ["4070 ti", "4080", "4090"])


class SpecDiffItem(BaseModel):
    key: str
    label_ar: str
    value_a: Any
    value_b: Any
    unit: str = ""
    winner: Literal["a", "b", "tie"] = "tie"
    diff_percentage: float = 0.0
    advantage_summary_ar: str = ""


class GamingFpsItem(BaseModel):
    game_title: str
    game_title_ar: str
    resolution: str
    preset: str
    fps_a: int
    fps_b: int
    diff_pct: float
    winner: Literal["a", "b", "tie"]


class AffiliateOffer(BaseModel):
    store_key: str
    store_name_ar: str
    store_name_en: str
    product_title: str
    direct_url: str
    affiliate_url: str
    badge_color: str
    text_color: str

    @field_validator("store_key")
    @classmethod
    def validate_forbidden_stores(cls, v: str) -> str:
        if v.lower() in ("amazon", "amzn"):
            raise ValueError("Amazon is strictly forbidden per project rules.")
        return v

    @field_validator("direct_url", "affiliate_url")
    @classmethod
    def validate_forbidden_urls(cls, v: str) -> str:
        lower_v = v.lower()
        if "amazon." in lower_v or "amzn.to" in lower_v or "amazon" in lower_v or "amzn" in lower_v:
            raise ValueError("Amazon URLs are strictly forbidden per project rules.")
        return v


class ComparisonVerdict(BaseModel):
    overall_winner: Literal["a", "b", "tie"]
    winner_name: str
    score_a: float
    score_b: float
    quick_verdict_ar: str
    gaming_analysis_ar: str
    productivity_analysis_ar: str
    value_and_budget_ar: str
    pros_a: List[str]
    cons_a: List[str]
    pros_b: List[str]
    cons_b: List[str]
    who_should_buy_a: str
    who_should_buy_b: str


class ComparisonDocument(BaseModel):
    slug: str
    category: str
    title_ar: str
    meta_title_ar: str
    meta_description_ar: str
    item_a: HardwareSpec
    item_b: HardwareSpec
    spec_differences: List[SpecDiffItem]
    performance_score_a: float
    performance_score_b: float
    fps_benchmarks: List[GamingFpsItem]
    verdict: ComparisonVerdict
    affiliate_links_a: List[AffiliateOffer]
    affiliate_links_b: List[AffiliateOffer]
    schema_json_ld: Dict[str, Any]
    created_at: str
