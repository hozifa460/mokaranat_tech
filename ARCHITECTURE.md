# ARCHITECTURE BLUEPRINT: Tech Comparisons (مقارنات تك)
**Clean Architecture Specification & System Blueprint**

---

## 1. System High-Level Topology

```
                       ┌────────────────────────────────────────┐
                       │  Hardware Specifications & Seed Data   │
                       │     (core/data/seed_specs.json)        │
                       └───────────────────┬────────────────────┘
                                           │
                                           ▼
                       ┌────────────────────────────────────────┐
                       │        SQLite Database Engine          │
                       │       (core/data/hardware.db)          │
                       │     [hardware_specs, cache_table]      │
                       └───────────────────┬────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        Python Core Pipeline (Clean Architecture)                       │
│                                                                                        │
│   ┌─────────────────────┐   ┌──────────────────────┐   ┌───────────────────────────┐   │
│   │     SpecEngine      │   │    FpsCalculator     │   │      AffiliateEngine      │   │
│   │  (Differentials &   │   │ (Cyberpunk, Wukong,  │   │  (Noon, Newegg, Ali,      │   │
│   │   Winner Badges)    │   │  CS2, RDR2, 1080p/4K)│   │   Jumia - STRICT NO AMZN) │   │
│   └──────────┬──────────┘   └──────────┬───────────┘   └─────────────┬─────────────┘   │
│              │                         │                             │                 │
│              └─────────────────────────┼─────────────────────────────┘                 │
│                                        ▼                                               │
│                         ┌─────────────────────────────┐                                │
│                         │     EditorialRuleEngine     │                                │
│                         │  (100% Deterministic Engine │                                │
│                         │  + Specs & Math Grounding)  │                                │
│                         └──────────────┬──────────────┘                                │
│                                        │                                               │
│                                        ▼                                               │
│                         ┌─────────────────────────────┐                                │
│                         │     ComparisonExporter      │                                │
│                         │ (Schema.org JSON-LD + Meta) │                                │
│                         └──────────────┬──────────────┘                                │
└────────────────────────────────────────┼───────────────────────────────────────────────┘
                                         │
                                         ▼
                       ┌────────────────────────────────────────┐
                       │    Static Content Collections JSON     │
                       │    (web/src/data/comparisons/*.json)   │
                       └───────────────────┬────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        Astro SSG Static Frontend (Cloudflare Pages)                    │
│                                                                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                               BaseLayout.astro                                 │   │
│   │  (RTL 'dir=rtl', Cairo/Tajawal Typography, Meta OpenGraph, SchemaJsonLd Head)   │   │
│   └──────────────────────────────────────┬─────────────────────────────────────────┘   │
│                                          │                                             │
│          ┌───────────────────────────────┼──────────────────────────────┐              │
│          ▼                               ▼                              ▼              │
│    pages/index.astro           pages/category/[category]       pages/compare/[slug]    │
│  - Live Search Filter         - Category Listings (GPU/CPU)   - ComparisonHero         │
│  - Category Quick Cards       - Winner Micro Badges           - PerformanceBars        │
│  - Featured Matchups Grid     - Score Comparisons             - SpecsTable (Winner tag)│
│                                                               - GamingFpsWidget (Tabs) │
│                                                               - EditorialVerdict (AI)  │
│                                                               - AffiliateWidget        │
│                                                               - AdSlot (AdSense)       │
│                                                               - InternalLinksGrid      │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Layer-by-Layer Responsibilities

### Layer 1: Domain Entities (`core/domain/`)
- **`models.py`:**
  - `HardwareSpec`: Strongly typed data model representing a physical GPU, CPU, or Laptop. Includes hardened `@property def has_dual_nvenc` with category validation (`self.category == "gpu"`) and robust type casting on `raw_specs["nvenc_encoders"]`, distinguishing dual NVENC flagship silicon (RTX 4070 Ti, RTX 4080, RTX 4090) from single-encoder midrange silicon (RTX 4060, RTX 4060 Ti, RTX 4070).
  - `SpecDiffItem`: Comparison row entity with differential calculations, unit, and winner flag (`a`, `b`, `tie`).
  - `GamingFpsItem`: Game title, preset, resolution, frame rate numbers, and winner badge.
  - `AffiliateOffer`: Branded store offer entity with strict field validator that throws an exception if Amazon is used.
  - `ComparisonVerdict`: AI-generated or heuristic Arabic technical review, pros/cons, and target buyers.
  - `ComparisonDocument`: Aggregate root containing all comparison properties, Schema.org graph, and timestamps.
- **`constants.py`:**
  - Enums for `HardwareCategory` (`gpu`, `cpu`, `laptop`), `Brand`, `Resolution`, `BenchmarkType`.

### Layer 2: Repository & Data Access (`core/repository/`)
- **`database.py`:**
  - Manages SQLite connection lifecycle.
  - Enables SQLite `WAL` mode and `PRAGMA foreign_keys = ON;`.
  - Maintains `hardware_specs` table (including `pcie_interface TEXT` with automated non-destructive PRAGMA migration) and `comparisons_cache` table.
- **`hardware_repo.py`:**
  - Decoupled repository implementing CRUD operations.
  - Encapsulates all SQL statements so business services never touch raw SQL.
  - Persists and loads hardware specifications including `pcie_interface` with backward-compatible fallbacks.

### Layer 3: Business Services (`core/services/`)
- **`spec_engine.py`:**
  - Encapsulates technical comparison rules and statistical significance thresholds.
  - Handles directionality:
    - *Higher is better:* Benchmark index, VRAM, Clock speeds, Memory Bus, Cache, Efficiency, PCIe lanes/interface.
    - *Lower is better:* TDP (power draw), Process node (nm), MSRP launch price, Weight (laptops).
  - **PCIe Interface Diffing:** Evaluates PCIe interface and lane allocations (e.g. PCIe 4.0 x16 vs PCIe 4.0 x8), highlighting bandwidth differences and flagging potential stuttering bottlenecks on PCIe 3.0 motherboards.
  - **Statistical Margin Rule (< 3.0%):** Any performance or specification difference under 3.0% is classified as `winner = "tie"` (`تعادل / تقارب في الأداء`), preventing artificial trophy inflation across both Python engines and Astro UI components (`PerformanceBars.astro`).
  - **Tier-Aware VRAM Advantage Phrasing:** Dynamically evaluates GPU tier (`_get_gpu_tier`) in `_compare_gpu_raw_specs()`: for midrange GPUs (e.g. RX 7700 XT vs RTX 4060 Ti), 12GB VRAM advantage is described as providing comfortable 1440p texture headroom and preventing stutter (`أريحية ممتازة في الألعاب بدقة 1440p وتفادي اختناق القوام`), while flagship GPUs describe 16GB+ as providing 4K Ultra headroom, eliminating marketing hyperbole.
  - **Laptop Dynamic TGP & Display Nomenclature:** Evaluates laptop power draw as `أقصى استهلاك رسومي متاح (GPU TGP / Thermal Budget)` with dynamic wattage interpolation as an informational tie. Compares laptop display panels in `_compare_laptop_raw_specs()`, presenting OLED (infinite contrast, 0.2ms response, true blacks) vs high-brightness IPS (500 nits, burn-in immunity) context.
  - **Cross-Architecture Normalization:** When comparing chips across different architectures (e.g. NVIDIA Ada Lovelace vs AMD RDNA 3, or AMD Zen 4 vs Intel Raptor Lake), raw clock speeds (GPU MHz, CPU Boost GHz) and process nodes (nm) are treated as informational ties (`winner = "tie"`) due to differing IPC, cache architectures, and transistor density metrics (e.g. Intel 7 vs TSMC 5nm). Identical process nodes (e.g. 4nm vs 4nm) are explicitly identified as hardware-identical.
  - **Identical Price Handling:** Catches `val_a == val_b` to output `السعر متطابق` cleanly without zero-percent discrepancies.
  - Generates clear, non-robotic Arabic advantage descriptions.
- **`fps_calculator.py`:**
  - Independent, decoupled performance modeling via `calculate_card_fps(game, item, res)`: Each card's FPS is strictly determined by its own silicon specs, resolution penalty, engine affinity, and vendor bias, guaranteeing zero opponent cross-talk and linear intra-brand scaling.
  - Calibrated against extensive benchmark matrices for top games (Cyberpunk 2077, Black Myth: Wukong, CS2, RDR2, Warzone, AC Mirage).
  - Takes engine affinities (Source 2, IW 9.0, UE5 Lumen RT) and ray-tracing weight into account for realistic gaming predictions.
  - Injects `rt_badge_ar` for RT-intensive titles (`⚡ تتبع الأشعة مفعّل (RT ON)` for Cyberpunk 2077 and generic `rt_heavy` profiles, `💡 إضاءة Lumen العتادية` for Black Myth: Wukong).
  - Multi-tier GPU scaling calibration: RTX 4080 Super achieves ~30% lead over RTX 4070 Super at 1440p, and RX 7900 XTX achieves ~37.4% lead over RX 7800 XT at 1440p / 4K.
  - Applies 3.0% statistical margin for gaming FPS differentials.
  - Normalizes resolution labels strictly to `4K` (guarding against `4Kg` typos).
- **`affiliate_engine.py`:**
  - Builds tracked search queries for approved stores:
    - Noon (`affiliate_id=TECHCOMP_NOON_AR`)
    - Newegg (`cm_mmc=aff-techcomp_ar`)
    - AliExpress (`aff_fcid=TECHCOMP_ALI_AR`)
    - Jumia (`tag=techcomparisons-jumia`)
  - Validates all generated URLs against `FORBIDDEN_AFFILIATES` (strictly NO Amazon).
- **`ai_editorial.py`:**
  - **`EditorialRuleEngine` (100% Deterministic Rule Engine):** Generates objective, mathematically verified Arabic editorial verdicts directly from SQLite hardware specifications and calculated FPS matrices. Eliminates runtime dependence on external LLM APIs, preventing rate-limiting, network failures, non-deterministic phrasing, or hallucinated claims.
  - **Quick Verdict Precision:** Scrubbed unsupported claims of "أزمنة إطارات أفضل" (frame times). Base verdict purely on verified benchmark index calculations and actual FPS calculation matrices. Symmetrically incorporates both benchmark index lead and 1440p average FPS lead (+12.7%) for GPU winners.
  - **Symmetric Mathematical Value & Budget Accuracy:** Calculates price increases strictly relative to the cheaper base: `(Pricier - Cheaper) / Cheaper`. Explicitly frames markup over cheaper MSRP across all narratives (`يرتفع سعر منافسه بنسبة ... عن السعر الأقل`), distinguishing it from MSRP table discount percentages.
  - **Laptop Portability Threshold & Con De-duplication:** Categorizes laptops `< 2.0` kg as portable thin-and-light with OLED benefits, and de-duplicates heavy laptop weight cons to ensure exactly 1 descriptive weight assessment for machines >= 2.5 kg.
  - **CPU Cleanliness & Longevity:** Omits raw 7nm from Intel 7 Core i7-14700K pros; attributes AM5 socket longevity through 2027+ for Ryzen 7000 and LGA 1700 EOL dead-end socket for Intel 14th Gen.
  - **Universal 3.0% Statistical Margin Enforcement:** Enforces the `< 3.0%` margin rule across GPU, CPU, and laptop value and budget analyses (`_build_value_budget_gpu`, `_build_cpu_narrative`, `_build_laptop_narrative`). Matchups with performance differences < 3.0% (e.g. Ryzen 7 7800X3D at 91.0 vs Core i7-14700K at 92.5, diff 1.62%) are accurately recognized as practically tied in performance (`مع تقارب الأداء`), reporting economic upfront savings without false claims of performance dominance.
  - **Clean float formatting via `_format_num()`:** Eliminates awkward `.0` representations.
  - **Global `gpu_tier` Scoping:** Computes `gpu_tier = _get_gpu_tier(a, b)` at the top level of the GPU branch, guaranteeing availability across all brand pairings (NVIDIA vs AMD, AMD vs AMD, NVIDIA vs NVIDIA) and preventing `UnboundLocalError`.
  - **Dynamic Editorial Winner Alignment:** When a card leads in raw rasterization benchmarks (e.g. RX 7700 XT over RTX 4060 Ti), `gaming_analysis_ar` objectively leads with the actual raster/gaming winner, framing NVIDIA's advantage specifically around Ray Tracing and DLSS/Frame Generation.
  - **Accurate Single vs. Dual NVENC Integration:** Utilizes `_is_dual_nvenc()` to strictly assign single 8th Gen NVENC (with AV1) to midrange cards (RTX 4060 Ti, RTX 4060, RTX 4070) while reserving dual NVENC claims for verified flagship dies (RTX 4070 Ti, RTX 4080, RTX 4090). Dual NVENC pros accurately cite live streaming and video export acceleration rather than AI.
  - **Realistic Resolution Tiering & Anti-Hyperbole:** Employs `_get_gpu_tier()` and `_vram_label()` to avoid hyperbole (e.g. 12GB is described as balanced for 1440p texture headroom, never "هائلة", and 4K Ultra is only attributed to flagship GPUs).
  - **Neutral Technical Buyer Recommendations:** Generates targeted persona recommendations (`_build_who_should_buy()`) based on concrete technical justifications (CUDA/OptiX ecosystem, DLSS 3.5 Frame Gen exclusive, power efficiency vs pure raster FPS, large VRAM, open FSR 3.1, DisplayPort 2.1) with zero subjective bias.
  - **CPU & Laptop Argument Reversal Symmetry:** Implements modular, independent evaluators (`_build_one_cpu`, `_build_one_laptop`) to evaluate each processor or laptop independently against its rival. Reversing argument order `(a, b)` to `(b, a)` strictly preserves factual attribution (e.g. 14700K's 253W power draw and cooling demands remain in its cons, while 7800X3D's 96MB L3 cache remains in its pros; 2.5kg gaming laptops are never mislabeled as portable).
  - **Decoupled Equal-VRAM Cost-Per-Frame Tie Logic:** In `_build_value_budget_gpu`, cost-per-frame parity (`abs(avg_fps_lead_1440p - price_inc_pct) <= 2.5`) is decoupled from VRAM sizing. Pure value tie narratives (`تعادل في القيمة الصافية`, `لا يوجد فوز مطلق`) correctly trigger regardless of whether cards have identical VRAM (e.g. 16GB vs 16GB) or different capacities.
  - Universal GPU pros/cons generator: covers NVIDIA vs AMD, NVIDIA vs NVIDIA, and AMD vs AMD. AMD highlights 24GB VRAM (RX 7900 XTX) with ray tracing strictly excluded from AMD pros across all matchups; NVIDIA highlights DLSS 3.5, Frame Generation, and CUDA/OptiX.
- **`exporter.py`:**
  - Orchestrates comparison generation and builds Schema.org JSON-LD structured data graphs (`Product`, `AggregateOffer`, `Review`, `Rating`, `Organization`).
  - Passes calculated `fps_benchmarks` directly to `editorial_service.generate_verdict(item_a, item_b, fps_matrix=fps_benchmarks)` preventing redundant recalculation.
  - Uses transparent credibility terminology: `مقارنة معمارية وتحليلات الأداء المتوقعة في الألعاب`.
  - Writes formatted JSON to `web/src/data/comparisons/{slug}.json`.

---

## 3. Web UI Component Dependency Graph

```
BaseLayout.astro
 ├── Header.astro (Logo, Nav links, Dark mode toggle)
 ├── SchemaJsonLd.astro (Head injection)
 ├── [Page Body Content]
 │    ├── ComparisonHero.astro (Dual cards, vs pill, quick verdict, competitor advantage badge, <bdi dir="ltr"> prices & specs)
 │    ├── AdSlot.astro (Clean AdSense container, zero raw placeholder draft text, clean collapse)
 │    ├── PerformanceBars.astro (Progress bars, <bdi dir="ltr"> ratios)
 │    ├── SpecsTable.astro (Table with winner badges, <bdi dir="ltr"> values & percentages)
 │    ├── GamingFpsWidget.astro (Interactive resolution switcher, <bdi dir="ltr"> FPS values)
 │    ├── AdSlot.astro (Mid Article)
 │    ├── EditorialVerdict.astro (Gaming, Workstation, Value, Pros/Cons, Who Should Buy)
 │    ├── AffiliateWidget.astro (Multi-store buy cards)
 │    ├── AdSlot.astro (Bottom Slot)
 │    └── InternalLinksGrid.astro (pSEO related comparisons, <bdi dir="ltr"> scores)
 └── Footer.astro (Arabic about, legal disclosure, copyright)
```

### Category-Aware UI Component & Service Adaptations
- **Transparent Branding & Nomenclature (`EditorialVerdict.astro`):** Unified badge under `التحليل المعماري والهندسي (Technical Architecture Analysis)` with 📐 icon, and heading under `خلاصة التحليل المعماري: أيهما تختار ولمن الأفضلية؟`, eliminating contradictions between "رأي المحرر" and "AI Technical Verdict".
- **Affiliate Cards & Regulatory Compliance (`AffiliateWidget.astro`):**
  - Added the explicit label `سعر الإطلاق الرسمي الاسترشادي` above dollar amounts to prevent confusion with live market pricing.
  - Changed store description to `متاجر معتمدة` and added open marketplace buyer advisory notice: `تنبيه للمشترين: عند الشراء من المتاجر المفتوحة (مثل علي إكسبريس)، يُرجى التحقق من تقييم البائع والمراجعات الحقيقية لتفادي المنتجات المعاد تجديدها أو المعدلة.`.
  - Updated all affiliate anchor tags to include `rel="sponsored nofollow noopener"` compliant with Google Search Central guidelines.
- **Test Bench Methodology Disclosure (`GamingFpsWidget.astro`):** Added explicit disclosure of test bench parameters to the methodology note: `ملاحظة منهجية: معدلات الإطارات تقديرية محسوبة استناداً إلى اختبارات الأداء المعيارية الموثقة على منصة اختبار قياسية (معالج فئة عليا، 32GB DDR5، أحدث تعريفات التشغيل المستقرة) بإعدادات Ultra ودون تفعيل تقنيات رفع الدقة إلا إذا ذكر خلاف ذلك.`.
- **Overall Winner & Competitor Nuance Badges (`ComparisonHero.astro`):** Updated hero badge from absolute "الفائز الإجمالي" to category-aware "الأسرع في الأداء الرسومي" (for GPUs) and "الأعلى أداءً في البنشمارك" (for CPUs/laptops) to reflect raw benchmark score, while displaying complementary competitor badges (`💰 الأوفر في سعر الإطلاق` or `🌱 الأقل استهلاكاً للطاقة` or `⚡ الأعلى كفاءة لكل واط`) recognizing where the non-winner leads, and mutual `🤝 تعادل متقارب في الأداء` badges for statistical ties (< 3%). Hardened with null-safety and truthiness checks (`self?.launch_msrp_usd && opponent?.launch_msrp_usd`) to prevent JavaScript `null < 500` falsy edge cases.
- **UI Formatting & Mobile Responsiveness (`SpecsTable.astro`, `PerformanceBars.astro`, `ComparisonHero.astro`, `AdSlot.astro`):**
  - Added `whitespace-nowrap` to ratio pills (`{formatVal(val)} / 100`) and diff percentages to prevent awkward line breaks on narrow viewports.
  - Adjusted AdSlot outer margin to `my-4` and removed `min-height: 90px;` ensuring neat container margin collapse when empty.
- **Universal BiDi RTL Inversion Protection (`web/src/components/` & `web/src/pages/`):** All score ratios (`{formatVal(val)} / 100`), percentage deltas (`+{diff}%`), prices (`${formatVal(...)}`), gaming FPS values (`{fps} FPS`), and numeric specs (`{tdp_w}W`, `{vram_gb}GB`, etc.) across `ComparisonHero.astro`, `PerformanceBars.astro`, `SpecsTable.astro`, `GamingFpsWidget.astro`, `category/[category].astro`, `InternalLinksGrid.astro`, and `index.astro` are wrapped inside `<bdi dir="ltr">` elements, immunizing Arabic RTL pages from browser BiDi reversals.
- **`PerformanceBars.astro` & `ComparisonHero.astro`:** Dynamically alters both metric calculations and descriptive subtitles based on `isCpu = itemA.category === 'cpu' || itemB.category === 'cpu'`:
  - **Dynamic 100 Ceiling Normalization & Numeric Defenses:** Employs safe numeric coercion `val = typeof v === 'number' ? v : (parseFloat(v) || 0)` with `const maxVal = Math.max(100, valA, valB);` and `const widthPct = Math.min(100, Math.max(10, Math.round((val / maxVal) * 100)));` with dynamic `displayUnit = maxVal > 100 ? `/ ${formatVal(maxVal)}` : m.unit;`. Permanently prevents CSS bar overflow, `NaN` width properties, and text clipping inside `overflow-hidden` containers while guaranteeing mathematical soundness. Hero meters in `ComparisonHero.astro` are likewise clamped.
  - **CPU Comparison (`isCpu === true`):** Ray tracing metrics are omitted from the bars. The subtitle dynamically displays: *"أشرطة بيانية توضح الفارق النسبي في سرعة المعالجة وتعدد الأنوية وكفاءة استهلاك الطاقة."*
  - **GPU / Laptop Comparison:** Evaluates ray tracing metrics safely when scores are non-null. The subtitle displays: *"أشرطة بيانية توضح الفارق النسبي في مجالات المعالجة وتتبع الأشعة وكفاءة استهلاك الطاقة."*
  - **Statistical Margins:** Enforces the strict `< 3.0%` margin rule with `تعادل متقارب` badge.
- **`EditorialVerdict.astro`:** Adapts section headings based on `isCpu` to prevent irrelevant GPU terminology on CPU pages:
  - **CPU Comparison (`isCpu === true`):** Gaming card title renders: *"تحليل أداء الألعاب ومعالجة الإطارات (Gaming Performance & Frame Pacing)"*.
  - **GPU / Laptop Comparison:** Gaming card title renders: *"تحليل الألعاب وتتبع الأشعة (Gaming & Ray Tracing)"*.
- **`AiEditorialService` (`core/services/ai_editorial.py`):**
  - **Linguistic Polish & Elimination of Repetition in Laptop Recommendations:** Completely eradicated duplicate phrasing in `_build_who_should_buy` for laptops (where "مع الاستفادة من" and "شاشة" were previously repeated twice), combining into a single cohesive sentence with clean integer battery formatting (`90Wh` rather than `90.0Wh`). Standardized heavy laptop recommendation to use clean battery phrasing (`وبطارية بسعة 99.9Wh`).
  - **Laptop Gaming Lead in Quick Verdicts:** Injects `{fps_phrase}` into `_build_quick_verdict` for laptop matchups, dynamically surfacing the authentic ~36.4% gaming FPS gap between desktop-replacement and portable gaming chassis.
  - **Category-Aware Equal MSRP Budget Analysis:** Evaluates hardware category when launch MSRPs match. For CPUs, highlights architecture, cores, and cache (`السعر متطابق بين المعالجين`); for Laptops, highlights display, battery, and thermals; for GPUs, evaluates VRAM and ray tracing. Prevents GPU terminology from ever leaking into CPU or Laptop editorial reviews.
  - **Engine-Aware Game FPS Modeling & GPU Vendor Resolution (`core/services/fps_calculator.py`):** Integrates game engine affinity and vendor bias (`nvidia_bias`, `amd_bias`). Features `_get_gpu_vendor(item)` to accurately inspect mobile laptop discrete GPU silicon and architecture, ensuring mobile NVIDIA Ada GPUs receive genuine driver bias and engine adjustments across UE5 Lumen RT (Black Myth: Wukong), Source 2 eSports Reflex bounds (CS2), IW 9.0 AMD RDNA optimizations (Warzone), and Ubisoft Anvil (AC Mirage).
  - **PCIe 4.0 x8 Bus Bottleneck Con Exposure:** Identifies 8-lane GPUs (`HardwareSpec.is_8_lane_pcie`) and automatically injects critical Arabic cons warning about bus bottlenecks and stutter on older PCIe 3.0 motherboards.
  - **Precise Editorial Terminology:** Strictly separates DLSS 3 (Frame Generation) and DLSS 3.5 (Ray Reconstruction / إعادة بناء الأشعة). Accurately frames AMD FSR 3.1 open-source Frame Generation. Notes hardware AV1 encode/decode on both Ada Lovelace (NVENC 8th Gen) and RDNA 3 (VCN 4.0), while noting NVENC's software ecosystem advantage in production apps.
  - **Pricing Nuance & Savings Labeling (`SpecsTable.astro` & `ai_editorial.py`):** Displays clear savings labels (`أوفر بنسبة {diff}% (خصم من السعر الأعلى) مقارنة بسعر المنافس لصالح {winner}`) for MSRP rows, and frames competitor markup over the cheaper MSRP (`يرتفع سعر منافسه بنسبة ... عن السعر الأقل`). Evaluates retail market price revisions within a 4.0% tolerance window, preserving cost-per-frame parity narratives.
  - **Ray Tracing Disclosures (`GamingFpsWidget.astro` & `fps_calculator.py`):** Integrates explicit visual badges (`⚡ تتبع الأشعة مفعّل (RT ON)` for Cyberpunk 2077 and `💡 إضاءة Lumen العتادية` for Black Myth: Wukong) next to game titles, maintaining methodological honesty regarding heavy hardware RT workloads.
  - **CPU Data Cleanliness & Platform Longevity (`models.py`, `database.py`, `spec_engine.py`):** Enforces `ray_tracing_score = None` on CPUs. Treats process node comparison between Intel 7 (10nm Enhanced SuperFin) and TSMC 5nm as an informational tie explaining transistor density equivalents. Injects AM5 2027+ socket lifecycle longevity pros and LGA 1700 dead-end platform cons.
  - **Laptop Portability Classification & Realism (`ai_editorial.py`, `fps_calculator.py`, `seed_specs.json`):** Calibrates laptop thin-and-light threshold to `weight <= 1.9` kg with OLED recognition. Calibrates ASUS ROG Zephyrus G16 (RTX 4070 Mobile 105W) so it reflects authentic 105W mobile performance and does not beat desktop RX 7800 XT (263W) or RTX 4060 Ti in actual rendered FPS, establishing an authentic 35-45% mobile gaming performance gap behind the full 175W Lenovo Legion Pro 7i desktop-replacement rig.
  - **100 Ceiling & Non-Linear Inter-Tier GPU Scaling (`seed_specs.json`, `fps_calculator.py`, `ai_editorial.py`):** Enforces a strict <= 98.0 ceiling on all scores in `seed_specs.json` (no score exceeds 100). Uses non-linear scaling for scores above 85.0 in `fps_calculator.py`, achieving an authentic ~31.3% lead for RTX 4080 Super over RTX 4070 Super at 1440p, and ~37.9% lead for RX 7900 XTX over RX 7800 XT at 1440p.
  - **Phase 18 Hardware Expansion & Multi-Architecture Integration (`seed_specs.json`, `spec_engine.py`, `ai_editorial.py`, `generate_comparisons.py`):**
    - **Dual NVENC vs Single NVENC Silicon:** AD102 (RTX 4090) and AD103 (RTX 4070 Ti Super) feature dual 8th-Gen NVENC engines with AV1 acceleration, surfaced in editorial pros. AD107 (RTX 4060) accurately reflects a single NVENC engine.
    - **PCIe Lane Detection (8-lane PCIe 4.0 x8):** RTX 4060 and RX 7600 XT are identified as 8-lane cards (`pcie_lanes: 8`), with symmetrical Arabic diff summaries and cons addressing PCIe 3.0 bandwidth degradation when VRAM is saturated.
    - **Apple Silicon Unified Memory Architecture:** Recognizes `APPLE` vendor silicon (3nm M3 Max), 48GB Unified Memory with 300GB/s bandwidth, dual ProRes engines, and 100% sustained unthrottled performance on battery power with up to 22h battery life. Delineates macOS translation layer (Game Porting Toolkit) vs Windows native DirectX 12 and DLSS 3.
    - **Display Technology Matrix:** Differentiates Mini-LED (Liquid Retina XDR, Razer Dual-Mode 4K/FHD), OLED (true blacks, 0.2ms), and high-brightness IPS (500 nits, zero burn-in risk).
    - **Equal VRAM Phrasing Polish:** Handles identical VRAM capacities (e.g. RTX 4090 vs RX 7900 XTX, both 24GB) with exact Arabic phrasing `(بسعة متطابقة تبلغ 24GB لكلا البطاقتين)`.
    - **Phase 19: Contextual Rule Engine & Self-Auditing Quality Gate:**
      - **MacBook Pro 16 vs ROG Zephyrus G16 Realism:** Grounded Apple Silicon M3 Max gaming scores in `seed_specs.json` ensuring Windows RTX gaming laptops win native DirectX 12 titles. Implemented `platform_note_ar` and macOS warning banner in `GamingFpsWidget.astro` explaining translation layer (Metal/GPTK) performance overhead and anti-cheat restrictions.
      - **High-End GPU Scaling Calibration:** Added halo scaling in `fps_calculator.py` for >= 15000 CUDA cores / AD102 GPUs (RTX 4090) giving >= 6% index lead and >= 20% average FPS lead over RX 7900 XTX. Preserved statistical tie (< 3% index delta) between RTX 4080 Super and RX 7900 XTX. Added official revised retail price support (`revised_msrp_usd`) for RX 7900 XT ($749).
      - **Contextual Rule Engine Refactoring:** Sanitized power descriptions (never describe >= 260W GPU or >= 150W CPU as "منضبط" or "فقط"). Added 450W / 12VHPWR con for RTX 4090. Barred 4K gaming praise in VRAM pros for GPUs with index < 75.0. Added CPU core deficit cons for >= 30% fewer cores (7600X vs 14600K). Handled equal laptop TDP diffs as mutually providing full 175W TGP. Prevented battery pros and cons from coexisting on the same laptop. Differentiated buyer personas by price, mobility, and performance tier.
      - **Self-Auditing Quality Gate (`core/tests/test_quality_gate.py`):** Implemented automated audit tests asserting 7 core quality rules across all 15 comparison JSON files: score bounding in [0, 100], buyer persona differentiation (SequenceMatcher <= 0.75), coherence of pros/cons, realistic power claims, 4K VRAM gating, macOS platform gaming realism, and equal TDP neutrality.

---

## 4. How to Extend the Project

### Adding a New Hardware Spec (e.g. RTX 5080):
1. Open `core/data/seed_specs.json`.
2. Add the hardware item entry with verified specifications:
```json
{
  "id": "rtx-5080",
  "slug": "rtx-5080",
  "name": "NVIDIA GeForce RTX 5080",
  "category": "gpu",
  "brand": "NVIDIA",
  "release_year": 2025,
  "launch_msrp_usd": 1199.0,
  "architecture": "Blackwell",
  "process_node_nm": 3.0,
  "tdp_w": 350,
  "raw_specs": {
    "cuda_cores": 10752,
    "vram_gb": 16,
    "memory_type": "GDDR7",
    "bus_width_bit": 256
  },
  "benchmark_index": 96.0,
  "gaming_scores": { "raster_1080p": 98.0, "raster_1440p": 97.0, "raster_4k": 95.0 },
  "ray_tracing_score": 97.0,
  "efficiency_score": 89.0,
  "features": ["DLSS 4", "GDDR7 Memory", "5th Gen Tensor Cores"]
}
```
3. Run `scripts/run_pipeline.bat` (or run `seed_database.py` and `generate_comparisons.py`).
4. Rebuild Astro via `npm run build`.

### Adding a New Comparison Matchup:
1. Open `scripts/generate_comparisons.py`.
2. Add the tuple to `DEFAULT_MATCHUPS`:
   `("rtx-5080", "rtx-4080-super"),`
3. Run the generator script:
   `D:\tech_comparisons\.venv\Scripts\python.exe scripts/generate_comparisons.py`
4. Astro will automatically detect the new JSON file and build a static SSG page for it on next build.

### Running Automated Tests:
```powershell
& "D:\tech_comparisons\.venv\Scripts\python.exe" -m pytest "D:\tech_comparisons\core\tests" -v
```

---

## 5. SEO & Google Helpful Content Compliance Checklist
- [x] **Zero Thin Content:** Every page contains over 600 words of authentic technical analysis, categorized pros & cons, and target buyer personas.
- [x] **Schema.org Rich Snippets:** Valid `Product`, `Review`, and `AggregateOffer` JSON-LD embedded in `<head>`.
- [x] **Core Web Vitals:** Pre-rendered SSG with inline theme script prevents layout shift (CLS: 0), minimal CSS footprint, zero blocking external scripts.
- [x] **Internal Linking Grid:** Every comparison page links to 6 related comparisons in the same category to spread internal PageRank.
- [x] **Affiliate & FTC Transparency:** Prominent disclosure notice in `AffiliateWidget`, `Footer`, and `BaseLayout` sticky banner complying with FTC guidelines: *"إفصاح الشفافية: قد نحصل على عمولة تسويقية عند الشراء من خلال هذه الروابط دون أي تكلفة إضافية عليك"*.
- [x] **Credibility & Terminology Alignment:** Replaced unverified claims of "اختبارات فعلية" with authentic architectural comparisons and estimated performance analysis ("مقارنة معمارية وتحليلات الأداء المتوقعة").
- [x] **Mobile First & RTL:** Full bidirectional RTL styling optimized for mobile screens and desktop monitors.
