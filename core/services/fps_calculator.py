"""
Gaming FPS Calculator Service.
Clean Architecture - Layer: Services
Estimates and formats side-by-side gaming FPS performance across modern AAA titles.
"""

import re
from typing import List, Dict, Any
from core.domain.models import HardwareSpec, GamingFpsItem

GAMES_BENCHMARK_PROFILES: List[Dict[str, Any]] = [
    {
        "id": "cyberpunk2077",
        "title": "Cyberpunk 2077",
        "title_ar": "سايبربانك 2077",
        "engine_affinity": "REDengine 4 (Full RT)",
        "base_fps_at_100_index": {"1080p": 138, "1440p": 96, "4K": 58},
        "preset": "Ultra High",
        "rt_heavy": True,
        "vendor_bias": {"nvidia_bias": 1.08, "amd_bias": 0.92}
    },
    {
        "id": "wukong",
        "title": "Black Myth: Wukong",
        "title_ar": "بلاك ميث: ووكونغ",
        "engine_affinity": "Unreal Engine 5 (Lumen RT)",
        "base_fps_at_100_index": {"1080p": 95, "1440p": 62, "4K": 35},
        "preset": "Cinematic High",
        "rt_heavy": True,
        "vendor_bias": {"nvidia_bias": 1.10, "amd_bias": 0.95}
    },
    {
        "id": "cs2",
        "title": "Counter-Strike 2",
        "title_ar": "كاونتر سترايك 2",
        "engine_affinity": "Source 2",
        "base_fps_at_100_index": {"1080p": 320, "1440p": 224, "4K": 130},
        "preset": "Competitive High",
        "rt_heavy": False,
        "vendor_bias": {"nvidia_bias": 1.04, "amd_bias": 0.98}
    },
    {
        "id": "rdr2",
        "title": "Red Dead Redemption 2",
        "title_ar": "ريد ديد ريدمبشن 2",
        "engine_affinity": "RAGE",
        "base_fps_at_100_index": {"1080p": 145, "1440p": 110, "4K": 72},
        "preset": "Ultra",
        "rt_heavy": False,
        "vendor_bias": {"nvidia_bias": 1.00, "amd_bias": 1.02}
    },
    {
        "id": "cod_warzone",
        "title": "Call of Duty: Warzone",
        "title_ar": "كول أوف ديوتي: وورزون",
        "engine_affinity": "IW 9.0",
        "base_fps_at_100_index": {"1080p": 210, "1440p": 150, "4K": 90},
        "preset": "Ultra / High",
        "rt_heavy": False,
        "vendor_bias": {"amd_bias": 1.18, "nvidia_bias": 0.94}
    },
    {
        "id": "ac_mirage",
        "title": "Assassin's Creed Mirage",
        "title_ar": "أساسنز كريد ميراج",
        "engine_affinity": "Ubisoft Anvil",
        "base_fps_at_100_index": {"1080p": 152, "1440p": 114, "4K": 68},
        "preset": "Ultra High",
        "rt_heavy": False,
        "vendor_bias": {"amd_bias": 1.06, "nvidia_bias": 0.98}
    }
]


class FpsCalculator:
    """Calculates realistic expected FPS for hardware combinations across different resolutions."""

    @classmethod
    def _get_vendor_bias(cls, game: Dict[str, Any], item: HardwareSpec) -> float:
        """Retrieves architectural/driver vendor bias factor for the given hardware brand."""
        vb = game.get("vendor_bias", {})
        brand = item.brand.upper()
        if brand == "NVIDIA":
            return vb.get("nvidia_bias", vb.get("nvidia", 1.0))
        elif brand == "AMD":
            return vb.get("amd_bias", vb.get("amd", 1.0))
        elif brand == "INTEL":
            return vb.get("intel_bias", vb.get("intel", 1.0))
        return 1.0

    @classmethod
    def calculate_card_fps(cls, game: Dict[str, Any], item: HardwareSpec, res: str) -> int:
        """Calculates expected FPS for a single card based strictly on its own hardware specifications.

        Guarantees that an individual hardware item's estimated FPS is completely independent
        of which opponent card it happens to be paired with in a comparison.
        """
        # Protect against '4Kg' typos and ensure standard resolution string
        norm_res = re.sub(r'4kg', '4K', res, flags=re.IGNORECASE)
        base_target = game["base_fps_at_100_index"].get(norm_res, 60)

        res_key = f"raster_{norm_res.lower()}"
        base_factor = (item.gaming_scores.get(res_key, item.benchmark_index)) / 100.0

        # Weight score based on ray tracing capability if title is RT heavy
        if game.get("rt_heavy"):
            rt_score = item.ray_tracing_score if item.ray_tracing_score is not None else 50.0
            rt_multiplier = rt_score / 100.0
            effective_factor = base_factor * (0.75 + 0.25 * rt_multiplier)
        else:
            effective_factor = base_factor

        # Apply architecture & engine affinity vendor bias
        bias = cls._get_vendor_bias(game, item)
        engine = game.get("engine_affinity", "")

        if engine == "Source 2":
            # Competitive eSports engine: high-FPS CPU and Reflex driver bounds compress raw raster scaling
            effective_factor = (0.55 + 0.45 * effective_factor) * bias
        elif engine == "IW 9.0":
            # Heavy historic AMD RDNA console-level shader optimization: calibrate baseline with vendor bias
            brand = item.brand.upper()
            arch_adj = 0.038 if brand == "NVIDIA" else (-0.040 if brand == "AMD" else 0.0)
            effective_factor = (effective_factor + arch_adj) * bias
        else:
            effective_factor = effective_factor * bias

        return max(15, int(round(base_target * effective_factor)))

    @classmethod
    def calculate_fps_matrix(cls, item_a: HardwareSpec, item_b: HardwareSpec) -> List[GamingFpsItem]:
        results: List[GamingFpsItem] = []

        # Only GPU and Laptop categories have direct rasterization gaming estimates
        if item_a.category not in ("gpu", "laptop") or item_b.category not in ("gpu", "laptop"):
            return results

        resolutions = ["1080p", "1440p", "4K"]

        for game in GAMES_BENCHMARK_PROFILES:
            for raw_res in resolutions:
                res = re.sub(r'4kg', '4K', raw_res, flags=re.IGNORECASE)
                fps_a = cls.calculate_card_fps(game, item_a, res)
                fps_b = cls.calculate_card_fps(game, item_b, res)

                diff_pct = 0.0
                if fps_a == fps_b:
                    winner = "tie"
                elif fps_a > fps_b:
                    diff_pct = round(((fps_a - fps_b) / fps_b) * 100, 1)
                    # Differences below 3% are within hardware measurement error margin
                    winner = "tie" if diff_pct < 3.0 else "a"
                else:
                    diff_pct = round(((fps_b - fps_a) / fps_a) * 100, 1)
                    # Differences below 3% are within hardware measurement error margin
                    winner = "tie" if diff_pct < 3.0 else "b"

                rt_badge_ar = None
                if game.get("id") == "cyberpunk2077":
                    rt_badge_ar = "⚡ تتبع الأشعة مفعّل (RT ON)"
                elif game.get("id") == "wukong":
                    rt_badge_ar = "💡 إضاءة Lumen العتادية"

                results.append(GamingFpsItem(
                    game_title=game["title"],
                    game_title_ar=game["title_ar"],
                    resolution=res,
                    preset=game["preset"],
                    fps_a=fps_a,
                    fps_b=fps_b,
                    diff_pct=diff_pct,
                    winner=winner,
                    rt_badge_ar=rt_badge_ar
                ))

        return results
