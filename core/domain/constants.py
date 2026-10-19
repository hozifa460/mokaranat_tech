"""
Domain Constants and Enums for Hardware & Comparisons.
Clean Architecture - Layer: Domain
"""

from enum import Enum


class HardwareCategory(str, Enum):
    GPU = "gpu"
    CPU = "cpu"
    LAPTOP = "laptop"


class Brand(str, Enum):
    NVIDIA = "NVIDIA"
    AMD = "AMD"
    INTEL = "Intel"
    APPLE = "Apple"
    ASUS = "ASUS"
    LENOVO = "Lenovo"
    DELL = "Dell"
    HP = "HP"
    MSI = "MSI"
    ACER = "Acer"


class Resolution(str, Enum):
    RES_1080P = "1080p"
    RES_1440P = "1440p"
    RES_4K = "4K"


class GraphicQuality(str, Enum):
    ULTRA = "Ultra"
    HIGH = "High"
    MEDIUM = "Medium"


class BenchmarkType(str, Enum):
    SYNTHETIC = "synthetic_3dmark"
    RASTER_1080P = "raster_1080p"
    RASTER_1440P = "raster_1440p"
    RASTER_4K = "raster_4k"
    RAY_TRACING = "ray_tracing"
    COMPUTE = "compute_tflops"
    EFFICIENCY = "performance_per_watt"
