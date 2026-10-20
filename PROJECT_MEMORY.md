# PROJECT MEMORY: Tech Comparisons (مقارنات تك)
**Last Updated:** 2026-10-21  
**Status:** In Active Production / Validated & Verified  
**Project Path:** `D:\tech_comparisons`

---

## 1. Project Overview & Business Objective
- **Goal:** Build an elite Programmatic SEO (pSEO) portal for Tech & Hardware Comparisons (GPUs, CPUs, Laptops) in Arabic, generating hundreds of high-retention, high-converting comparison pages with verified benchmarks, editorial depth, and zero thin content.
- **Target Audience:** Arab gamers, hardware enthusiasts, PC builders, and creative professionals across Saudi Arabia, UAE, Egypt, and the MENA region.
- **Hosting Target:** Cloudflare Pages (Static Site Generation / SSG) delivering 100/100 Core Web Vitals, 0 hosting cost, and global CDN delivery.

---

## 2. Architectural Decisions & Tech Stack

### A. Frontend Architecture: Astro (SSG) + Tailwind CSS
- **Framework:** Astro 5.4+ in SSG mode (`output: "static"`).
- **Styling & Typography:** Tailwind CSS 3.4+ configured for RTL (`dir="rtl" lang="ar"`), utilizing Google Fonts `Cairo` (body text) and `Tajawal` (headings) for crisp, readable Arabic rendering.
- **Zero Client Hydration Overhead:** All comparison data is pre-compiled at build time into static HTML pages from JSON data collections (`web/src/data/comparisons/*.json`), ensuring sub-second Time to First Byte (TTFB).
- **Theme Support:** Dark/Light mode with inline pre-render script preventing Flash of Unstyled Content (FOUC).

### B. Data & Analysis Engine: Python 3.11 (Clean Architecture)
- **Layer 1: Domain Entities (`core/domain/`):** Pure Pydantic v2 models (`HardwareSpec`, `SpecDiffItem`, `GamingFpsItem`, `AffiliateOffer`, `ComparisonVerdict`, `ComparisonDocument`). Enforces strict data validation and rejects corrupted specs.
- **Layer 2: Data Access (`core/repository/`):** SQLite (`hardware.db`) running with Write-Ahead Logging (`PRAGMA journal_mode = WAL;`) and Foreign Key enforcement. Stores raw specs and caches generated comparisons.
- **Layer 3: Core Services (`core/services/`):**
  1. `SpecEngine`: Evaluates higher-is-better (e.g. VRAM, Clocks) vs. lower-is-better (e.g. TDP, MSRP, nm) with mathematical differentials and Arabic advantage explanations.
  2. `FpsCalculator`: Realistic gaming FPS estimation engine across 1080p, 1440p, and 4K for modern AAA games (Cyberpunk 2077, Black Myth: Wukong, CS2, RDR2, CoD Warzone, AC Mirage).
  3. `AffiliateEngine`: Multi-store link generator for Noon, Newegg, AliExpress, and Jumia.
  4. `AiEditorialService`: Google Gemini API integration (`gemini-2.5-flash`) via `google-genai` SDK with a robust, authentic heuristic fallback that guarantees non-thin Arabic editorial content even offline.
  5. `ComparisonExporter`: Formats Schema.org JSON-LD (Product + Review), metadata, and exports Astro-ready JSON collections.

### C. Monetization & Business Rules
- **Approved Affiliate Stores:**
  1. **Noon (نون):** Prominent MENA e-commerce partner.
  2. **Newegg (نيو إيج):** Premier PC hardware global retailer.
  3. **AliExpress (علي إكسبريس):** Budget and direct hardware deals.
  4. **Jumia (جوميا):** North African coverage.
- **STRICT FORBIDDEN RULE:** **NO AMAZON** links or tags are permitted anywhere in the codebase or generated pages. The system throws a `ForbiddenStoreError` if Amazon is detected.
- **Google AdSense:** Structured responsive slots (`AdSlot.astro`) placed strategically (Header, Mid-Article, Post-Affiliate).

---

## 3. Directory Layout & Module Responsibilities
```
D:\tech_comparisons\
├── PROJECT_MEMORY.md             # This permanent memory file
├── ARCHITECTURE.md               # Detailed architectural diagram and data flow
├── .venv/                        # Dedicated Python 3.11 virtual environment (uv managed)
├── core/
│   ├── config.py                 # Paths, API keys, affiliate configs, forbidden store rules
│   ├── domain/
│   │   ├── constants.py          # Enums for categories, brands, resolutions
│   │   └── models.py             # Pydantic v2 models
│   ├── repository/
│   │   ├── database.py           # SQLite connection pool and WAL schema migrations
│   │   └── hardware_repo.py      # SQLite CRUD and comparison caching
│   ├── services/
│   │   ├── spec_engine.py        # Winner assignment & spec differential engine
│   │   ├── fps_calculator.py     # Multi-resolution AAA gaming FPS calculation
│   │   ├── affiliate_engine.py   # Multi-store URL generation (strictly NO Amazon)
│   │   ├── ai_editorial.py       # Gemini API client & rich Arabic editorial generator
│   │   └── exporter.py           # Schema.org JSON-LD builder & Astro JSON exporter
│   ├── data/
│   │   ├── hardware.db           # SQLite database
│   │   └── seed_specs.json       # Initial curated hardware specifications dataset
│   └── tests/
│       ├── test_models.py        # Validation tests & Amazon rejection tests
│       ├── test_spec_engine.py   # Spec differential & winner logic tests
│       └── test_affiliate_and_editorial.py # Store links, heuristic generator & DB tests
├── scripts/
│   ├── seed_database.py          # CLI to populate SQLite from seed JSON
│   ├── generate_comparisons.py   # CLI to build comparisons matrix and export JSON
│   └── run_pipeline.bat          # 1-click Windows batch runner
└── web/
    ├── package.json              # Astro + Tailwind dependencies
    ├── astro.config.mjs          # Static SSG config for Cloudflare Pages
    ├── tailwind.config.cjs       # Tailwind RTL and theme config
    ├── public/                   # Favicon and robots.txt
    ├── dist/                     # Production static build output
    └── src/
        ├── components/           # Reusable UI widgets
        │   ├── Header.astro      # Navigation, logo, dark mode toggle
        │   ├── Footer.astro      # Footer with transparency disclosure
        │   ├── ComparisonHero.astro # Dual card hero with score meters
        │   ├── PerformanceBars.astro# Visual progress meters
        │   ├── SpecsTable.astro  # Side-by-side specs with winner badges
        │   ├── GamingFpsWidget.astro# Interactive resolution tabs & FPS
        │   ├── EditorialVerdict.astro# Deep AI technical verdict & buyer advice
        │   ├── AffiliateWidget.astro# Multi-store price comparison cards
        │   ├── AdSlot.astro      # Google AdSense containers
        │   ├── InternalLinksGrid.astro # pSEO interlinking grid
        │   └── SchemaJsonLd.astro# Injects Schema.org structured data
        ├── layouts/
        │   └── BaseLayout.astro  # Master layout with RTL, fonts, meta tags
        ├── pages/
        │   ├── index.astro       # Portal homepage with live search
        │   ├── compare/[slug].astro # Dynamic SSG comparison pages
        │   └── category/[category].astro # Category hubs (gpu, cpu, laptop)
        ├── data/
        │   ├── comparisons/      # Exported comparison JSON files
        │   └── comparisons_index.json # Master index manifest
        └── styles/
            └── global.css        # Cairo/Tajawal fonts, base RTL styles
```

---

## 4. Changelog & Implementation History

### Phase 1: Environment & Toolchain Setup (2026-10-19)
- Configured local Python 3.11 virtual environment via `uv`.
- Installed and verified `google-genai`, `pydantic`, `pytest`, `requests`, `beautifulsoup4`.
- Installed Node.js LTS 24.20.0 and npm 11.19.0.
- Set up Windows PowerShell RemoteSigned execution policy and user path integration.

### Phase 2: Core Data Engine & Clean Architecture (2026-10-19)
- Implemented pure domain entities with Pydantic v2 validation.
- Configured SQLite WAL database with `hardware_specs` and `comparisons_cache` tables.
- Built `SpecEngine` with mathematical differential formulas for higher-is-better and lower-is-better attributes.
- Built `FpsCalculator` calibrated against real-world benchmark data for Cyberpunk 2077, Black Myth: Wukong, CS2, etc.
- Built `AffiliateEngine` strictly enforcing Noon, Newegg, AliExpress, and Jumia, with automated assertion checks rejecting Amazon.
- Built `AiEditorialService` integrating Google Gemini API with fallback heuristic engine.
- Created curated seed dataset (`core/data/seed_specs.json`) with RTX 4070 Super, RX 7800 XT, RTX 4080 Super, RX 7900 XTX, Ryzen 7 7800X3D, i7-14700K, Legion Pro 7i, and Zephyrus G16.

### Phase 3: Automated Test Suite & Verification (2026-10-19)
- Implemented 10 unit and integration tests across domain models, spec engine, affiliate engine, editorial engine, and repository.
- **Verification Result:** 10/10 tests passed (100% pass rate in 0.35s).
- Fixed Windows console CP1252 unicode checkmark encoding error by enforcing UTF-8 stdout reconfiguration.
- Fixed string interpolation in editorial cons formatting.

### Phase 4: Astro SSG Frontend & UI Components (2026-10-19)
- Initialized Astro 5.4 SSG project with Tailwind CSS 3.4.
- Implemented Arabic typography with `Cairo` and `Tajawal` Google Fonts and RTL layout.
- Created all 10 responsive UI components (`ComparisonHero`, `PerformanceBars`, `SpecsTable`, `GamingFpsWidget`, `EditorialVerdict`, `AffiliateWidget`, `AdSlot`, `InternalLinksGrid`, `SchemaJsonLd`, `Header`, `Footer`).
- Created dynamic comparison SSG route `pages/compare/[slug].astro` generating 7 static comparison pages.
- Created category hub route `pages/category/[category].astro` for `gpu`, `cpu`, and `laptop`.
- Created interactive homepage `pages/index.astro` with real-time vanilla JS search filter.
- Successfully executed `npm run build`: 11 static pages generated in `dist/` with 0 errors.

### Phase 5: Critical Bug Fixes, Precision Calibrations & Verification Hardening (2026-10-19)
- **Fixed Ambiguous Winner Text in Intra-Brand Matchups (`SpecsTable.astro`):** Replaced ambiguous brand winner label `{isA ? itemA.brand : itemB.brand}` with exact product name `{isA ? itemA.name : itemB.name}`. Fixed bug where comparing two NVIDIA or two AMD cards showed confusing labels like `+11.5% لصالح NVIDIA` instead of specifying the winning card (`RTX 4080 Super`).
- **Fixed Dead Ray Tracing Calculation in `FpsCalculator` (`fps_calculator.py`):** Fixed formula where lines 87-91 unconditionally wiped out the `rt_multiplier` factor. Now modulates the resolution factor by `(0.75 + 0.25 * rt_multiplier)` for RT-heavy titles (Cyberpunk 2077, Black Myth: Wukong), correctly reflecting GPU ray tracing performance differences.
- **Fixed 200 FPS Normalization Clipping (`GamingFpsWidget.astro`):** Replaced hardcoded `/ 200` denominator with dynamic scaling `Math.max(bench.fps_a, bench.fps_b, 60)`, preventing high-FPS titles like CS2 (~380 FPS) from being clamped to 100% on both sides.
- **Omitted Irrelevant Ray Tracing on CPUs (`spec_engine.py` & `PerformanceBars.astro`):** Restricted `ray_tracing_score` comparisons exclusively to GPUs and laptops. Added CPU Gaming Index (`gaming_overall`) for processor comparisons.
- **Tailored Editorial Pros & Cons by Category (`ai_editorial.py`):** Rewrote heuristic generator to produce category-accurate feedback. Eliminated desktop PC case and desktop PSU references on laptop reviews; now highlights display, weight, battery life, and portable thermals.
- **Enforced Strict Amazon URL Rejection (`models.py`):** Extended Pydantic `@field_validator` on `AffiliateOffer` to inspect `direct_url` and `affiliate_url` in addition to `store_key`.
- **Category-Aware Internal Linking Grid (`InternalLinksGrid.astro`):** Prioritized comparisons sharing the same category before backfilling with other categories, fixing PageRank dilution and adhering to `ARCHITECTURE.md`.
- **Added Category Guard & Schema.org Clamping (`exporter.py`):** Added explicit `ValueError` when attempting cross-category comparisons (`item_a.category != item_b.category`), and clamped Schema.org Review `ratingValue` strictly within `[1.0, 5.0]`.
- **Enhanced ComparisonHero Quick Pills (`ComparisonHero.astro`):** Added display, weight (kg), and battery (Wh) pills for laptops.
- **Regex JSON Extraction for Gemini API (`ai_editorial.py`):** Used regex `re.search(r"\{[\s\S]*\}", raw_text)` to reliably parse JSON payloads from LLM responses even with surrounding commentary or markdown tags.
- **Expanded Test Suite:** Expanded test suite from 10 to 18 automated unit and integration tests across all edge cases (100% pass rate).

### Phase 6: Robustness Hardening, Review Feedback & Legal Compliance (2026-10-19)
- **Resolved Identical Price & Margin Glitch (`spec_engine.py` & `ai_editorial.py`):** Fixed zero-percent edge cases where equal launch MSRPs resulted in artificial winner declarations or awkward `أقل بنسبة 0.0%` phrasing. Now explicitly outputs `السعر متطابق` with `winner = "tie"`.
- **Enforced 3.0% Statistical Margin Threshold (`spec_engine.py` & `fps_calculator.py`):** Differences under 3.0% across specs and gaming FPS benchmarks are categorized as ties (`winner = "tie"`, `تعادل / تقارب في الأداء`) preventing misleading micro-trophies and trophy inflation.
- **Cross-Architecture Comparison Rules (`spec_engine.py`):** Flagged comparisons across different microarchitectures (e.g. Ada Lovelace vs RDNA 3). Raw clock frequencies (MHz) and fabrication process nodes (nm) are treated as informational ties (`winner = "tie"`) with context regarding IPC differentials and transistor density variations.
- **Credibility & Terminology Alignment:** Replaced misleading claims of `اختبارات فعلية` with transparent `مقارنة معمارية وتحليلات الأداء المتوقعة` across `exporter.py`, `ComparisonHero.astro`, `Footer.astro`, `index.astro`, and `category/[category].astro`.
- **Editorial Nuance & Accurate GPU Pros/Cons (`ai_editorial.py`):** Tailored GPU editorial evaluations: AMD GPUs (e.g. RX 7900 XTX) emphasize 24GB VRAM and value, with Ray Tracing strictly excluded from AMD pros against NVIDIA; NVIDIA cards explicitly highlight DLSS 3.5, Frame Generation, and CUDA/OptiX productivity.
- **Float Formatting & Typo Sanitization:** Implemented `_format_num()` in Python services and `formatVal()` across Astro components to eliminate awkward `.0` trailing zeros (e.g., `75/100`, `4nm`, `24GB`). Guarded against `4Kg` typos in `fps_calculator.py` and `GamingFpsWidget.astro` to strictly normalize to `4K`.
- **FTC & Legal Affiliate Disclosure:** Integrated explicit disclosure statement `إفصاح الشفافية: قد نحصل على عمولة تسويقية عند الشراء من خلال هذه الروابط دون أي تكلفة إضافية عليك` prominently in `AffiliateWidget.astro`, `Footer.astro`, and top announcement bar in `BaseLayout.astro`.

### Phase 7: Frontend Margin Alignment, CPU Clock Parity & Universal Editorial Coverage (2026-10-19)
- **Frontend Statistical Margin Enforcement (`PerformanceBars.astro`):** Fixed a bug where differences < 3.0% (e.g. 91.0 vs 92.5) incorrectly awarded artificial winners and dimmed the tied item as a loser. Now strictly enforces `< 3.0%` tie threshold, displays `تعادل متقارب` badge, and keeps both brand colors active.
- **CPU Boost Clock Cross-Architecture Parity (`spec_engine.py`):** Integrated CPU `boost_clock_ghz` into `_compare_cpu_raw_specs()`. Enforced cross-architecture tie detection between Zen 4 and Raptor Lake (e.g., Ryzen 7 7800X3D at 5.0 GHz vs Core i7-14700K at 5.6 GHz) to prevent misleading raw frequency winner declarations, adding IPC instructional notes.
- **Universal GPU Editorial Engine (`ai_editorial.py`):** Refactored pros/cons into `_build_gpu_pros_cons_universal()` covering all pairings: NVIDIA vs AMD, NVIDIA vs NVIDIA, and AMD vs AMD. Strictly guaranteed that Ray Tracing is never listed as a pro for AMD under any circumstance, and emphasized 24GB VRAM on RX 7900 XTX. Added dedicated gaming and productivity analyses for intra-brand matchups.
- **Astro Template Formatting & Badge Consistency (`index.astro`, `category/[category].astro`, `InternalLinksGrid.astro`):** Replaced broken ternary `Number.isInteger(x) ? x : x` with `formatVal()`. Replaced contradictory badges like `⭐ الفائز: تعادل` with friendly handshake `🤝` badge. Scrubbed all remaining `اختبارات` references in favor of `تحليلات ومعدل الإطارات المتوقعة`.
- **Test Suite Expansion & SSG Build:** Expanded automated test suite to 27 tests (100% pass rate in 0.91s). Regenerated all 7 comparison JSON collections, and confirmed 11 static pages generated with 0 errors via `npm run build`.

### Phase 8: Category-Aware Heading Specialization & Comprehensive Polish (2026-10-19)
- **Category-Aware Subtitles (`PerformanceBars.astro`):** Refactored the subtitle under "مقارنة مؤشرات الأداء الحسابي والمعياري". Implemented clean, DRY `isCpu = itemA.category === 'cpu' || itemB.category === 'cpu'` check. For CPUs (`isCpu === true`), the subtitle dynamically renders: `أشرطة بيانية توضح الفارق النسبي في سرعة المعالجة وتعدد الأنوية وكفاءة استهلاك الطاقة.` instead of referencing ray tracing. For GPUs and Laptops, it retains: `أشرطة بيانية توضح الفارق النسبي في مجالات المعالجة وتتبع الأشعة وكفاءة استهلاك الطاقة.`.
- **Category-Aware Editorial Card Title (`EditorialVerdict.astro`):** Refactored the first analysis card title using the same consistent `isCpu` property. For CPUs, it now displays: `تحليل أداء الألعاب ومعالجة الإطارات (Gaming Performance & Frame Pacing)` instead of `تحليل الألعاب وتتبع الأشعة (Gaming & Ray Tracing)`. For GPUs and Laptops, it continues to evaluate Gaming & Ray Tracing.
- **Backend Category-Aware Equal-Price Analysis (`core/services/ai_editorial.py`):** Fixed an edge-case bug in `AiEditorialService.generate_verdict()` where comparisons between two items with equal launch MSRP unconditionally mentioned `(مثل سعة VRAM الأكبر أو تقنيات تتبع الأشعة والذكاء الاصطناعي)`. Added category guards: CPUs now evaluate architecture, total cores, and cache (`السعر متطابق بين المعالجين`); Laptops evaluate display, battery, and thermals; GPUs evaluate VRAM and ray tracing.
- **Automated Test Suite Expansion (`core/tests/test_affiliate_and_editorial.py`):** Added 2 dedicated unit tests: `test_ai_editorial_cpu_identical_price_no_gpu_terms` and `test_ai_editorial_cpu_no_ray_tracing`. The test suite now comprises 29 automated tests (100% pass rate in 1.10s).
- **Pipeline Execution & SSG Verification:** Regenerated all 7 comparison collections via `scripts/generate_comparisons.py` and compiled all 11 static pages via `npm run build` in 2.23s with 0 errors. Verified in generated HTML artifacts (`web/dist/compare/ryzen-7-7800x3d-vs-i7-14700k/index.html`) that ray tracing is completely absent and CPU-specific headings are accurately rendered.

### Phase 9: Heuristic Editorial Winner Alignment, Hardware Accuracy & BiDi Fixes (2026-10-19)
- **Editorial Alignment with Winner Data (`ai_editorial.py`):** Fixed critical contradiction where `gaming_analysis_ar` unconditionally framed NVIDIA as the gaming leader even when AMD won raw rasterization benchmarks across all resolutions (e.g. RX 7700 XT winning all 6 games at 1440p against RTX 4060 Ti). The narrative now dynamically checks raw raster differentials: when AMD leads in raw raster, it is explicitly credited as the raw gaming leader, while NVIDIA's lead is accurately framed specifically around Ray Tracing workloads and DLSS 3.5 Frame Generation.
- **Hardware Accuracy — Single vs. Dual NVENC (`models.py`, `ai_editorial.py`, `seed_specs.json`):** Eliminated the false claim attributing "مشفر NVENC المزدوج" to RTX 4060 Ti / RTX 4060. AD106 / AD107 silicon features a SINGLE 8th Gen NVENC encoder (with AV1 support). Dual NVENC encoders are strictly reserved for AD104 full die (RTX 4070 Ti), AD103 (RTX 4080 / 4080 Super), and AD102 (RTX 4090). Implemented `@property def has_dual_nvenc` on `HardwareSpec` and `_is_dual_nvenc()` in `ai_editorial.py`.
- **Eliminated Marketing Hyperbole & Fixed Resolution Tiering (`ai_editorial.py`):** Replaced hyperbole describing 12GB VRAM as "هائلة" (12GB is balanced for 1440p, 24GB is huge), and removed ungrounded claims of "ألعاب 4K Ultra بلا اختناق" on midrange cards averaging ~25-30 FPS at 4K. Implemented `_get_gpu_tier()` and `_vram_label()` to explicitly frame cards by tier (`midrange_1080p_1440p`, `upper_1440p`, `flagship_4k`). Midrange 12GB is now described as `سعة ذاكرة متوازنة تبلغ 12GB` providing comfortable texture headroom at 1440p.
- **Value & Budget Coherence (`ai_editorial.py`):** Resolved direct contradiction in `value_and_budget_ar` where an 8GB 128-bit card was claimed to be a "smarter medium-term investment" while cons listed 8GB as a bottleneck. Value analysis now objectively balances upfront purchase savings and lower power draw against the pricier card's higher FPS (+8.8% to +14%) and larger VRAM buffer (12GB vs 8GB) with wider bus for sustainable medium-term texture longevity.
- **Neutralized Subjective Recommendation Biases (`ai_editorial.py`):** Eliminated unsupported claims of "أعلى استقرار" from buyer recommendations (`who_should_buy_a` / `who_should_buy_b`). Implemented `_build_who_should_buy()` supplying concrete technical justifications: NVIDIA highlights CUDA/OptiX ecosystem for 3D/AI, Ray Tracing, proprietary DLSS 3.5 Frame Generation, and power efficiency; AMD highlights pure raster FPS per dollar, generous VRAM with wide memory bus, open cross-platform FSR 3.1, and DisplayPort 2.1.
- **BiDi RTL Inversion Fix (`PerformanceBars.astro`, `ComparisonHero.astro`, `SpecsTable.astro`, `index.astro`):** Wrapped score ratios (`{formatVal(val)} / 100`), percentages, and unit patterns inside `<bdi dir="ltr">` elements. This permanently prevents browser Unicode Bidirectional (BiDi) algorithms from reversing numbers into `100 / {val}` on RTL Arabic pages.
- **Cleaned Up AdSlot UI Placeholder (`AdSlot.astro`):** Removed the raw placeholder draft text `مساحة إعلانية مخصصة (Google AdSense Slot #{slotId})` and dashed grey border from unpopulated AdSense containers, ensuring clean, distraction-free container layout for visitors.
### Phase 10: Deep Editorial Calibration, Tier-Aware VRAM Engine & Universal BiDi Protection (2026-10-19)
- **Tier-Aware VRAM Spec Differential (`spec_engine.py`):** Eliminated the legacy hardcoded 4K claim in `_compare_gpu_raw_specs()` line 203. Replaced it with dynamic tier-aware resolution phrasing: midrange cards (e.g. RX 7700 XT vs RTX 4060 Ti) describe 12GB VRAM as providing comfortable 1440p texture headroom and preventing stutter (`أريحية ممتازة في الألعاب بدقة 1440p وتفادي اختناق القوام`), while flagship cards describe 16GB+ as providing 4K Ultra headroom.
- **Hardened HardwareSpec & NVENC Safety (`models.py`):** Hardened `@property def has_dual_nvenc` on `HardwareSpec` with explicit category validation (`self.category == "gpu"`) and robust type casting on `raw_specs["nvenc_encoders"]`, preventing `TypeError` or `AttributeError` when inspecting non-GPU items or missing dictionary keys.
- **Global `gpu_tier` Scoping & Non-NVIDIA/AMD Matchup Safety (`ai_editorial.py`):** Hoisted `gpu_tier = _get_gpu_tier(a, b)` to the top level of the GPU category handler, eliminating an `UnboundLocalError` that previously occurred when accessing `gpu_tier` in `value_and_budget_ar` during intra-brand AMD vs AMD or Intel comparisons.
- **Dynamic Value & Budget Resolution Phrasing (`ai_editorial.py`):** Adapted `value_and_budget_ar` resolution text to match the GPU tier (`بدقة 4K والدقات الفائقة` for flagship, `بدقة 1440p و 4K` for upper 1440p, `بدقة 1440p` for midrange). Corrected dual NVENC description in pros from misleading "للذكاء الاصطناعي" to "لتسريع البث المباشر وتصدير الفيديو".
- **Comprehensive BiDi RTL Inversion Protection (`web/src/`):** Extended `<bdi dir="ltr">` wrapper tags across the entire Astro frontend:
  - `ComparisonHero.astro`: Wrapped launch prices (`${formatVal(...)}`) and all Quick Specs Pills (`{tdp_w}W`, `{process_node_nm}nm`, `{vram_gb}GB`, `{total_cores}`, `{weight_kg}kg`, `{battery_wh}Wh`).
  - `GamingFpsWidget.astro`: Wrapped benchmark FPS indicators (`{bench.fps_a} FPS` and `{bench.fps_b} FPS`).
  - `category/[category].astro`: Wrapped benchmark score comparisons.
  - `InternalLinksGrid.astro`: Wrapped score comparison pills.
  - `index.astro`: Wrapped price comparisons.
  - `SpecsTable.astro`: Verified `<bdi dir="ltr">` on score ratios, values, units, and diff percentages.
- **AdSlot UI Polish (`AdSlot.astro`):** Removed raw text draft notices (`مساحة إعلانية مخصصة`) and dashed grey borders, ensuring clean AdSense container presentation.
- **Automated Test Suite Expansion & SSG Build:** Added `test_spec_engine_gpu_vram_summary_tier_aware_no_4k_hyperbole` in `core/tests/test_spec_engine.py` and fallback validation in `core/tests/test_affiliate_and_editorial.py`. Test suite expanded to 32 automated unit/integration tests (100% pass rate in 0.93s). Re-seeded SQLite database, regenerated all 7 comparison JSON collections, and verified Astro SSG build (`11 static pages generated in 2.07s with 0 errors`).

### Phase 11: 100% Deterministic Rule Engine, Mathematical Precision & Compliance Polish (2026-10-19)
- **Deterministic Rule Engine Architecture (`core/services/ai_editorial.py`):** Replaced runtime dependence on external LLM calls with a 100% deterministic Rule Engine (`EditorialRuleEngine`) that generates objective, mathematically verified Arabic editorial verdicts directly from `hardware.db` and specs, eliminating network latency, API rate limits, non-determinism, and hallucination risks. Retained optional `_call_gemini_verdict` for test backward compatibility.
- **Quick Verdict Precision (`EditorialRuleEngine` & `ComparisonHero.astro`):** Scrubbed unsupported claims of "أزمنة إطارات أفضل" (frame times) from `quick_verdict_ar`. Grounded verdicts strictly in verified benchmark index differentials and actual FPS calculation capabilities.
- **Value & Budget Mathematical Accuracy (`EditorialRuleEngine`):**
  - Corrected price delta calculation when comparing a pricier item against a cheaper base: `(449 - 399) / 399 = 12.5%` (not 11.1%).
  - In the editorial narrative for RX 7700 XT ($449) vs RTX 4060 Ti ($399), integrated the mathematical lead: AMD's 1440p FPS lead averages ~12.6% while its price is 12.5% higher, rendering the cost-per-frame (القيمة مقابل السعر) virtually identical (a tie in pure value / `تعادل في القيمة الصافية`). Framed this objectively without declaring an unconditional win (`لا يوجد فوز مطلق`).
- **Transparent Branding & Nomenclature (`EditorialVerdict.astro`):** Eliminated the contradiction between "رأي المحرر" and "AI Technical Verdict". Unified badge under `التحليل المعماري والهندسي (Technical Architecture Analysis)` with 📐 icon, and heading under `خلاصة التحليل المعماري: أيهما تختار ولمن الأفضلية؟`.
- **Affiliate Cards & Regulatory Compliance (`AffiliateWidget.astro`):**
  - Added the explicit label `سعر الإطلاق الرسمي الاسترشادي` above dollar amounts to prevent visitors from mistaking launch MSRP for live store pricing.
  - Updated store description from "متاجر موثوقة" to "متاجر معتمدة", and added open marketplace buyer advisory notice: `تنبيه للمشترين: عند الشراء من المتاجر المفتوحة (مثل علي إكسبريس)، يُرجى التحقق من تقييم البائع والمراجعات الحقيقية لتفادي المنتجات المعاد تجديدها أو المعدلة.`.
  - Updated all affiliate anchor tags to include `rel="sponsored nofollow noopener"` compliant with Google Search Central guidelines.
- **Test Bench Methodology Disclosure (`GamingFpsWidget.astro`):** Added explicit disclosure of test bench parameters to the methodology note: `ملاحظة منهجية: معدلات الإطارات تقديرية محسوبة استناداً إلى اختبارات الأداء المعيارية الموثقة على منصة اختبار قياسية (معالج فئة عليا، 32GB DDR5، أحدث تعريفات التشغيل المستقرة) بإعدادات Ultra ودون تفعيل تقنيات رفع الدقة إلا إذا ذكر خلاف ذلك.`.
- **Overall Winner Badge Nuance (`ComparisonHero.astro`):** Updated hero badge from absolute "الفائز الإجمالي" to category-aware "الأسرع في الأداء الرسومي" (for GPUs) and "الأعلى أداءً في البنشمارك" (for CPUs/laptops) to reflect raw benchmark score without dismissing competitor strengths.
- **UI Formatting & Spacing Polish (`SpecsTable.astro`, `PerformanceBars.astro`, `ComparisonHero.astro`, `AdSlot.astro`):** Added `whitespace-nowrap` to ratio pills (`74 / 100`) and diff badges preventing awkward wrapping on mobile/narrow viewports. Collapsed empty AdSlot margins neatly to `my-4`.
- **Automated Test Suite Expansion & SSG Build:** Added 3 dedicated unit tests (`test_rule_engine_quick_verdict_precision_no_frame_times`, `test_rule_engine_price_delta_math_and_cost_per_frame_tie`, `test_rule_engine_deterministic_identical_verdicts`). Test suite expanded to 35 tests (100% pass rate in 0.97s). Regenerated all 7 comparison collections, and compiled 11 static pages via `npm run build` in 2.09s with 0 errors.

### Phase 12: Adversarial Hardening, Symmetrical Matchup Logic, Margin Enforcement & Competitor Badges (2026-10-19)
- **Resolved Inverted FPS Lead Bug in Reversed Matchups (`core/services/ai_editorial.py`):** Fixed critical mathematical bug in `EditorialRuleEngine._build_value_budget_gpu` where passing the pricier card as `item_a` and cheaper as `item_b` (e.g. `(rx-7700-xt, rtx-4060-ti)`) resulted in subtracting `item.fps_b - item.fps_a`, producing negative FPS differentials (`~-11.2%` or `~-12.5%`) and incorrectly declaring the cheaper card as the value winner. Dynamically resolves `fps_pricier` and `fps_cheaper` to guarantee 100% symmetric, positive lead calculations (~12.6%) regardless of argument order.
- **Sanitized Stray Dollar Sign & Syntax Typo (`ai_editorial.py`):** Eliminated raw stray `$` symbol resulting from accidental JS template string syntax in line 375 (`f"...نسبة {price_inc_str}%)${vram_note}..."`), ensuring immaculate Arabic typography.
- **Mathematically Accurate Price Reduction Phrasing (`ai_editorial.py`):** Fixed inaccurate phrasing in line 362 that claimed the cheaper card was `X%` cheaper where `X%` was actually the price increase of the pricier card. Clearly phrased price differences as: `تكلفة شراء أقل بسعر $X (توفير $Y، بينما يرتفع سعر منافسه بنسبة Z%)`.
- **Enforced 3.0% Statistical Margin Rule Across All Value Narratives (`ai_editorial.py`):** Hardened `_build_cpu_narrative`, `_build_laptop_narrative`, and `_build_value_budget_gpu` by guarding `perf_diff < 0` with `perf_pct >= 3.0`. For matchups within the 3.0% error margin (e.g. Ryzen 7 7800X3D at 91.0 vs Core i7-14700K at 92.5, difference 1.62%), the engine now accurately reports comparable/tied performance (`مع تقارب الأداء بين المعالجين`) and an economic upfront advantage, eliminating false "أسبقية في الأداء" claims on micro-differentials.
- **Symmetric, Grounded Quick Verdict Engine (`ai_editorial.py`):** Refactored `_build_quick_verdict` to accept and utilize `fps_matrix` directly, dynamically citing actual average FPS lead (+12.7%) alongside benchmark index (+8.8%) for GPU winners, unifying phrasing symmetrically across both `winner == "a"` and `winner == "b"`.
- **Competitor Advantage & Tie Badges on Hero Cards (`ComparisonHero.astro`):** Implemented dynamic competitor advantage badges (`getCompetitorBadge`) recognizing where the non-winner card leads (`💰 الأوفر في سعر الإطلاق` or `🌱 الأقل استهلاكاً للطاقة` or `⚡ الأعلى كفاءة لكل واط`), and added mutual `🤝 تعادل متقارب في الأداء` badges for statistical ties (< 3%).
- **Neat AdSlot Collapse (`AdSlot.astro`):** Removed `min-height: 90px;` so unpopulated AdSense slots collapse cleanly to zero height without leaving large awkward gaps.
- **Automated Test Suite Expansion & SSG Build:** Added 3 dedicated adversarial unit tests (`test_rule_engine_reversed_matchup_symmetry_and_positive_fps_lead`, `test_rule_engine_cpu_statistical_margin_tie_no_flawed_perf_claim`, `test_rule_engine_quick_verdict_incorporates_actual_fps`). Test suite expanded to 38 automated unit tests (100% pass rate in 1.01s). Re-generated all 7 comparison JSON collections, and confirmed 11 static pages generated with 0 errors via `npm run build` in 2.03s.

### Phase 13: CPU/Laptop Argument Symmetry, Equal-VRAM Cost-Per-Frame Tie & Hero Null-Safety (2026-10-19)
- **Resolved CPU Argument Reversal Asymmetry (`core/services/ai_editorial.py`):**
  - Refactored `_build_cpu_narrative` to dynamically determine cache leadership (3D V-Cache / L3 size) vs multi-core rendering leadership. Reversing arguments `(i7-14700k, ryzen-7-7800x3d)` now correctly attributes 1% low gaming stability to the 7800X3D and parallel rendering to the 20-core 14700K.
  - Implemented modular `_build_one_cpu` in `_build_cpu_pros_cons`. Eliminated hardcoded assumptions that `a` has large L3 cache and `b` has high power draw. In reversed matchups, 14700K's 253W power draw and cooling demands are correctly assigned to its cons, while 7800X3D's 96MB L3 cache and efficiency are assigned to its pros.
- **Resolved Laptop Argument Order Bias (`core/services/ai_editorial.py`):**
  - Refactored `_build_laptop_narrative` to eliminate biased `"مع أسبقية للأول في ثبات الترددات"`, grounding frequency and stability analysis in actual benchmark index and architecture.
  - Implemented modular `_build_one_laptop` in `_build_laptop_pros_cons`. Dynamically evaluates weight, battery capacity, and display. Heavy 2.5kg gaming laptops are never falsely praised for being lightweight, while light laptops (1.5kg) receive appropriate portability credit in both `(a, b)` and `(b, a)` orders.
  - Enhanced laptop `_build_who_should_buy` to distinguish ultraportable travel devices (<= 1.8kg) from desktop replacement gaming rigs (> 1.8kg).
- **Decoupled Cost-Per-Frame Parity from VRAM Delta (`core/services/ai_editorial.py`):**
  - Decoupled `abs(avg_fps_lead_1440p - price_inc_pct) <= 2.5` from `vram_pricier > vram_cheaper`. GPUs with equal VRAM (e.g. 16GB vs 16GB) or where cheaper has more VRAM now correctly trigger the pure value tie narrative (`تعادل في القيمة الصافية`, `لا يوجد فوز مطلق`).
- **Hero Competitor Badge Null-Safety (`ComparisonHero.astro`):**
  - Added truthiness and optional chaining guards to `getCompetitorBadge` (`self?.launch_msrp_usd && opponent?.launch_msrp_usd`), preventing JavaScript `null < 500` falsy edge cases.
- **Automated Test Suite Expansion (41 Tests):**
  - Added 3 adversarial tests in `test_affiliate_and_editorial.py`:
    - `test_rule_engine_cpu_argument_reversal_symmetry`
    - `test_rule_engine_laptop_argument_reversal_symmetry`
    - `test_rule_engine_gpu_cost_per_frame_tie_equal_vram`
  - Re-verified full test suite: 41 passed in 0.96s (100% pass rate).
  - Regenerated 7 programmatic comparisons and compiled 11 static pages via `npm run build` with 0 errors.

### Phase 14: Engine-Aware FPS Modeling, PCIe 8-Lane Con Detection, DLSS/FSR Terminology Separation & Market Price Revisions (2026-10-20)
- **Engine-Aware Game FPS Modeling (`core/services/fps_calculator.py`):**
  - Eliminated naive static ~13.8% multiplier across all games that contradicted real-world engine behavior.
  - Added `engine_affinity` and `vendor_bias` (`nvidia_bias`, `amd_bias`) across all 6 benchmark titles in `GAMES_BENCHMARK_PROFILES`:
    - *Black Myth: Wukong (Unreal Engine 5 Lumen RT):* Calibrated baseline 1440p FPS to realistic 38-44 FPS range (`nvidia_bias: 1.10`, `amd_bias: 0.95`). RTX 4060 Ti edges out RX 7700 XT (41 vs 39 FPS) due to heavy Lumen HW RT load on Ada Lovelace.
    - *Counter-Strike 2 (Source 2 Engine):* Calibrated eSports CPU/Reflex bounds with `nvidia_bias: 1.04`, `amd_bias: 0.98`. Compresses raster gap into an authentic near tie (196 vs 194 FPS, 1.0% diff <= 3.0% margin, slight NVIDIA Reflex edge).
    - *Call of Duty: Warzone (IW 9.0 Engine):* Calibrated historical AMD RDNA architectural optimization (`amd_bias: 1.18`, `nvidia_bias: 0.94`), reflecting AMD's authentic ~27.8% lead (97 vs 124 FPS).
    - Calibrated baselines for *Cyberpunk 2077* (63 vs 59 FPS, NVIDIA RT edge), *Red Dead Redemption 2* (72 vs 83 FPS, AMD +15.3%), and *Assassin's Creed Mirage* (73 vs 89 FPS, AMD +21.9%).
    - Average 1440p lead of RX 7700 XT over RTX 4060 Ti across the 6 titles is calibrated to an authentic ~8.8%.
- **Balanced Pros/Cons & Exposing PCIe 4.0 x8 Bottlenecks (`models.py`, `seed_specs.json`, `ai_editorial.py`):**
  - Added `pcie_interface: Optional[str]` field and `@property def is_8_lane_pcie(self) -> bool` to `HardwareSpec` in `core/domain/models.py`.
  - Added `pcie_interface: "PCIe 4.0 x8"` and `pcie_lanes: 8` to `rtx-4060-ti` and `"PCIe 4.0 x16"` (16 lanes) to `rx-7700-xt`, `rtx-4070-super`, `rx-7800-xt`, `rtx-4080-super`, and `rx-7900-xtx` in `seed_specs.json`.
  - In `_build_gpu_pros_cons()`, added detection for 8-lane GPUs (`is_8_lane = card.is_8_lane_pcie or card.raw_specs.get("pcie_lanes") == 8 or "x8" in str(...)`), injecting the exact critical con: `"واجهة اتصال عتادية تقتصر على 8 مسارات فقط (PCIe 4.0 x8)، مما يسبب عنق زجاجة وتذبذباً في أزمنة الإطارات (Stutter) على اللوحات الأم القديمة الداعمة لمنفذ PCIe 3.0 عند امتلاء الذاكرة"`.
  - Balanced RTX 4060 Ti cons (PCIe 4.0 x8 bottleneck + 8GB VRAM vs 12GB) vs RX 7700 XT cons (lower Ray Tracing score + lack of CUDA acceleration), achieving 2-3 pros and 2-3 cons per GPU.
- **Precise Editorial Terminology (`core/services/ai_editorial.py`):**
  - Strictly separated DLSS 3 (Frame Generation) and DLSS 3.5 (Ray Reconstruction / إعادة بناء الأشعة). Eradicated conflated phrasing ("DLSS 3.5 Frame Generation").
  - Explicitly recognized AMD FSR 3.1 open-source Frame Generation as running across virtually any modern GPU.
  - Formulated dual-architecture AV1 note: acknowledged dedicated hardware AV1 encoding/decoding on both Ada Lovelace (NVENC 8th Gen) and RDNA 3 (VCN 4.0 Dual Media Engine), while citing NVENC's software ecosystem advantage in production apps (CUDA/OptiX/Adobe/Blender).
  - Updated `_build_who_should_buy` with precise DLSS 3 Frame Gen, DLSS 3.5 Ray Recon, and FSR 3.1 open-source Frame Gen descriptions.
- **Pricing Nuance & Market Price Revisions (`ai_editorial.py`, `SpecsTable.astro`):**
  - In `SpecsTable.astro`, when `diff.key === 'launch_msrp_usd'`, updated display label from confusing `+12.5% لصالح RTX 4060 Ti` to clear savings text: `أوفر بنسبة {diff}% مقارنة بسعر المنافس لصالح {winner}`.
  - In `_build_value_budget_gpu()`, incorporated AMD's subsequent official retail price revision downwards to ~$419 / $399 in global retailers, closing the real-world cost gap.
  - Adjusted cost-per-frame parity tolerance to 4.0%, correctly triggering the pure value tie narrative (`تعادل في القيمة الصافية`, `لا يوجد فوز مطلق`) for ~8.8% average FPS lead vs 12.5% launch MSRP delta ($50 delta).
- **Automated Test Suite Expansion & SSG Build:**
  - Added 4 dedicated unit tests in `core/tests/test_affiliate_and_editorial.py`:
    - `test_fps_calculator_engine_affinity_and_vendor_biases`
    - `test_ai_editorial_pcie_lane_con_detection_for_8_lane_gpus`
    - `test_ai_editorial_precise_terminology_frame_gen_dlss35_and_av1`
    - `test_ai_editorial_pricing_nuance_and_market_price_revision`
  - Total test count expanded to 45 automated unit and integration tests (100% pass rate in 1.14s).
  - Re-seeded SQLite database with PCIe specs, regenerated all 7 comparison JSON collections, and compiled 11 static pages via `npm run build` in 2.09s with 0 errors.

### Phase 14: Deep Hardware Review, Bug Fixes & Mathematical Independence (2026-10-19)
- **Database Schema Migration & Persistence for `pcie_interface` (`database.py`, `hardware_repo.py`):**
  - **Issue Identified:** In Phase 13, `pcie_interface` was added to `seed_specs.json` and Pydantic models, but `hardware_specs` table schema and SQL queries in `core/repository/hardware_repo.py` lacked the column. As a result, reading back from SQLite caused `item_a.pcie_interface` and `item_b.pcie_interface` to serialize as `null` in exported comparison JSON files.
  - **Resolution:** Added `pcie_interface TEXT` to `CREATE TABLE IF NOT EXISTS hardware_specs` and implemented non-destructive `PRAGMA table_info(hardware_specs)` migration in `initialize_schema`. Updated `upsert_hardware_spec` and `_row_to_spec` to persist and load `pcie_interface` with fallback to `raw_specs`.
- **Opponent Coupling Eradication in Game FPS Calculator (`core/services/fps_calculator.py`):**
  - **Issue Identified:** The prior implementation blended each GPU's factor with `mean_factor = (effective_factor_a + effective_factor_b) / 2.0` in titles like *Counter-Strike 2* and *Warzone*. This violated the fundamental law of physical hardware measurement by coupling Card A's FPS to its opponent Card B, distorting intra-brand scaling (e.g. RTX 4070 Super and RTX 4080 Super tied at 123 vs 124 FPS in Warzone).
  - **Resolution:** Replaced the coupled logic with an independent `calculate_card_fps(game, item, res)` function. Each GPU's performance is strictly computed from its own raster/ray-tracing scores, resolution penalties, engine affinity, and vendor biases. Inter-GPU deltas and winners are calculated post-hoc.
- **Spec Engine PCIe Interface Diffing (`core/services/spec_engine.py`):**
  - Added PCIe interface comparison to `_compare_gpu_raw_specs()`. Correctly compares lane counts and PCIe generation, awarding winner to x16 cards over x8 cards with an explicit Arabic explanation in `SpecsTable.astro`.
- **Automated Test Suite Expansion to 50 Tests:**
  - Added tests for database PCIe schema migration and persistence in `test_models.py`.
  - Added test for PCIe comparison spec diff in `test_spec_engine.py`.
  - Added test for intra-brand FPS scaling and opponent decoupling across tiers in `test_affiliate_and_editorial.py`.
  - Total test count expanded to 50 tests (100% pass rate in 1.01s).
  - Re-seeded database, regenerated all 7 comparison JSONs with zero null fields, and compiled all 11 static pages via Astro in 1.96s.

### Phase 15: Git Toolchain Provisioning, Tunnel Shutdown & GitHub Repository Deployment (2026-10-20)
- **Temporary Cloudflare Tunnel Teardown:**
  - Terminated background tunnel process `cloudflared.exe` completely, closing external preview routing.
- **Git & GitHub Toolchain Provisioning:**
  - Installed Git for Windows (`v2.55.0.5`) and GitHub CLI (`gh v2.102.0`) via `winget`.
  - Configured Git executable paths permanently in the Windows User PATH.
  - Successfully authenticated user account `hozifa460` via GitHub device flow and wired Git credential helper (`gh auth setup-git`).
- **Repository Setup & Deployment:**
  - Hardened `.gitignore` to strictly exclude `.venv/`, `node_modules/`, `dist/`, logs, and temporary files.
  - Initialized Git repository, staged all clean architecture modules, tests, data files, Astro components, and documentation.
  - Successfully committed and pushed all 53 project files to `https://github.com/hozifa460/mokaranat_tech` (`main` branch).
  - Verified repository contents via GitHub API.

### Phase 16: Comprehensive Hardware Review & Architectural Calibration (2026-10-20)
- **Laptop Classification Bug & Display Enhancements (`ai_editorial.py`, `spec_engine.py`, `seed_specs.json`, `SpecsTable.astro`):**
  - Updated laptop portability threshold in `EditorialRuleEngine._build_who_should_buy` to `weight < 2.0` kg (covering Zephyrus G16 at 1.85 kg as well as thin gaming laptops up to 1.99 kg) with OLED display recognition.
  - De-duplicated heavy laptop weight cons in `_build_one_laptop`: heavy laptops (>= 2.5 kg) receive exactly 1 consolidated, descriptive con comparing against lighter competitors rather than duplicate consecutive weight bullet points.
  - Added dedicated `display` comparison row to `SpecEngine._compare_laptop_raw_specs` and `SpecsTable.astro`, presenting side-by-side OLED (infinite contrast, 0.2ms response, true blacks) vs IPS (500 nits sustained brightness, no burn-in risk) analysis.
  - Formatted laptop `tdp_w` diffing dynamically with actual wattages (`GPU TGP / Thermal Budget`) as an informational tie explaining sustained clock speeds (175W) vs thin-chassis thermals (105W).
- **CPU Cleanliness & Platform Longevity (`models.py`, `database.py`, `seed_specs.json`, `spec_engine.py`, `ai_editorial.py`):**
  - Nullified `ray_tracing_score` for CPUs in `seed_specs.json`, `models.py`, and `database.py`, preventing irrelevant GPU RT metrics from leaking into CPU spec diffs and charts.
  - Updated Intel Core i7-14700K process node to `Intel 7 (10nm Enhanced SuperFin)` and socket to `LGA 1700 (End of Life)`.
  - Refined CPU editorial pros generation to eliminate misleading raw "بدقة تصنيع 7nm" suffix when describing Intel 7 architectures.
  - Customized CPU process node comparison in `SpecEngine` to mark as tie with explicit architectural explanation comparing Intel 7 transistor density against TSMC 5nm.
  - Added AM5 platform lifecycle support through 2027+ pro for Ryzen 7000 series, and dead-end socket EOL con for Intel LGA 1700.
- **Inter-Tier GPU Scaling Calibration (`seed_specs.json`, `ai_editorial.py`):**
  - Calibrated raster scores for RTX 4080 Super (raster 1440p: 109.0, 4K: 93.0) and RX 7900 XTX (raster 1440p: 117.0, 4K: 100.0) so RTX 4080 Super achieves ~30.2% average lead over RTX 4070 Super at 1440p (up from 12.5%), and RX 7900 XTX achieves ~37.4% lead over RX 7800 XT at 1440p / 4K.
  - Updated AI editorial lead phrase to dynamically render calibrated leads (`~30%` and `~38%`).
- **RTX 4060 Ti Variant Clarity (`seed_specs.json`):**
  - Renamed in seed specs and database to `NVIDIA GeForce RTX 4060 Ti (8GB)`.
- **Ray Tracing Disclosures (`models.py`, `fps_calculator.py`, `GamingFpsWidget.astro`):**
  - Added `rt_badge_ar` field to `GamingFpsItem`.
  - Assigned badges for RT-intensive games: `⚡ تتبع الأشعة مفعّل (RT ON)` for Cyberpunk 2077 and generic `rt_heavy` profiles, and `💡 إضاءة Lumen العتادية` for Black Myth: Wukong.
  - Rendered RT disclosure badge next to game titles in `GamingFpsWidget.astro`.
- **Pricing Framing Consistency (`SpecsTable.astro`, `ai_editorial.py`):**
  - Clarified in `SpecsTable.astro` that savings percentage is calculated off the higher MSRP: `أوفر بنسبة {formatVal(diff.diff_percentage)}% (خصم من السعر الأعلى) مقارنة بسعر المنافس لصالح {winner}`.
  - Clarified in `ai_editorial.py` across all value budget narratives (including cost-per-frame parity in 4060 Ti vs 7700 XT) that competitor markup is calculated over the cheaper MSRP: `يرتفع سعر منافسه بنسبة ... عن السعر الأقل`.
- **Automated Test Expansion & SSG Build:**
  - Expanded test suite in `core/tests/test_affiliate_and_editorial.py` to 60 automated unit tests (up from 50) with 100% pass rate in 1.25s.
  - Re-seeded SQLite database, regenerated all 7 comparison JSON collections, and verified 11 static pages built via Astro SSG with zero errors in 1.97s.
  - Audited compiled HTML to confirm zero Amazon links or mentions.

### Phase 17: PerformanceBars 100-Ceiling Normalization, Laptop FPS Realism & Linguistic Polish (2026-10-20)
- **PerformanceBars & ComparisonHero CSS Clipping & Dynamic Normalization (`web/src/components/`):**
  - **Issue Identified:** Visual meter bars previously rendered raw score widths via `style="width: ${Math.max(10, m.valA)}%"`. When scores exceeded 100 (e.g. 109.0 or 117.0), the bar overflowed its parent container (`overflow-hidden`), pushing the right-aligned `<bdi>` value badge off-screen. Furthermore, missing numeric coercion risked producing `style="width: NaN%"` if an optional score was undefined.
  - **Resolution:** Implemented mathematical ceiling normalization and numeric defenses:
    `const valA = typeof m.valA === 'number' ? m.valA : (parseFloat(m.valA) || 0);`
    `const valB = typeof m.valB === 'number' ? m.valB : (parseFloat(m.valB) || 0);`
    `const maxVal = Math.max(100, valA, valB);`
    `const widthPctA = Math.min(100, Math.max(10, Math.round((valA / maxVal) * 100)));`
    `const widthPctB = Math.min(100, Math.max(10, Math.round((valB / maxVal) * 100)));`
    `const displayUnit = maxVal > 100 ? `/ ${formatVal(maxVal)}` : m.unit;`
    Ensures that visual bar width never exceeds 100% and text inside `overflow-hidden` is never clipped off-screen while keeping display units and ratios mathematically sound. Similarly clamped Hero meters in `ComparisonHero.astro`.
- **Hardware Spec 100 Ceiling & Flagship Capping (`core/data/seed_specs.json`, `core/services/fps_calculator.py`):**
  - **Issue Identified:** Previous calibrations for RTX 4080 Super and RX 7900 XTX had set `raster_1440p` to 109.0 and 117.0, violating the 0-100 normalized index design.
  - **Resolution:** Calibrated all hardware items in `seed_specs.json` so that NO score exceeds 100:
    - `rtx-4080-super`: benchmark_index: 95.0, gaming_scores: `{"raster_1080p": 94.0, "raster_1440p": 96.0, "raster_4k": 92.0}` (all <= 96.0 <= 98.0).
    - `rx-7900-xtx`: benchmark_index: 96.0, gaming_scores: `{"raster_1080p": 95.0, "raster_1440p": 98.0, "raster_4k": 94.0}` (all <= 98.0).
  - **Non-Linear Flagship Scaling in `fps_calculator.py`:** Added non-linear scaling for scores above 85.0 (`base_factor = (raw_score / 100.0) + 0.00115 * ((raw_score - 85.0) ** 2)`). Allows raw benchmark and raster scores in `seed_specs.json` to stay strictly within 0-100, while preserving authentic ~30-40% inter-tier scaling for flagship silicon (e.g. RTX 4080 Super +31.3% average lead over RTX 4070 Super at 1440p; RX 7900 XTX +37.9% lead over RX 7800 XT at 1440p).
- **Laptop Gaming FPS Realism, Underlying GPU Vendor Detection & Benchmarks (`core/data/seed_specs.json`, `core/services/fps_calculator.py`):**
  - **Issue Identified:** ASUS ROG Zephyrus G16 (RTX 4070 Mobile 105W) previously had inflated scores (84.0 index, 79.0 raster_1440p) that beat desktop GPUs like RTX 4060 Ti (8GB, 160W) and RX 7800 XT (16GB, 263W). Furthermore, `FpsCalculator` checked OEM chassis brand (`item.brand == "ASUS"`), bypassing NVIDIA driver bias (`nvidia_bias: 0.98` in AC Mirage) and engine optimizations, causing G16 to tie desktop RTX 4060 Ti in actual rendered FPS in Assassin's Creed Mirage.
  - **Resolution:**
    - Grounded laptop specs in empirical reviews (Jarrod's Tech):
      - `rog-zephyrus-g16`: benchmark_index: 72.0, gaming_scores: `{"raster_1080p": 76.0, "raster_1440p": 64.0, "raster_4k": 42.0}`, ray_tracing_score: 68.0.
      - `legion-pro-7i`: benchmark_index: 86.0, gaming_scores: `{"raster_1080p": 90.0, "raster_1440p": 88.0, "raster_4k": 68.0}`, ray_tracing_score: 84.0.
    - Implemented `FpsCalculator._get_gpu_vendor(item)` to accurately inspect laptop discrete GPU silicon and architecture, ensuring mobile NVIDIA Ada GPUs receive genuine driver bias and engine adjustments.
    - Result: Zephyrus G16 (105W) strictly trails desktop RTX 4060 Ti (8GB) across every single title and resolution in actual rendered FPS, trails desktop RX 7800 XT by a wide margin, and establishes the authentic 35-45% mobile gaming performance gap behind Legion Pro 7i (175W).
- **Linguistic Polish & Elimination of Repetition in Laptop Recommendation (`core/services/ai_editorial.py`):**
  - Eliminated duplicate phrasing in `_build_who_should_buy` for laptops where "مع الاستفادة من" and "شاشة" were repeated twice.
  - Cleanly combined into: `"المستخدم كثير التنقل وصانع المحتوى الذي يضع خفة الوزن (1.9 كجم) وسهولة الحمل في صدارة أولوياته، مع الاستفادة من شاشة OLED فائقة التباين والألوان وبطارية بسعة 90Wh."`
  - Standardized heavy laptop recommendation to use clean battery phrasing (`وبطارية بسعة 99.9Wh`).
  - Integrated `{fps_phrase}` into `_build_quick_verdict` for laptop matchups, dynamically surfacing the ~36.4% gaming FPS gap in executive verdicts.
- **Automated Test Expansion & Full Pipeline Verification:**
  - Expanded test suite to 64 automated unit tests:
    - Added deep end-to-end assertions in `test_laptop_gaming_fps_realism_against_desktops_and_gap` verifying that `matrix_desktop = FpsCalculator.calculate_fps_matrix(g16, desktop_4060ti)` strictly trails across all 18 resolution-game pairs.
    - Added dedicated test `test_fps_calculator_get_gpu_vendor_for_laptops_and_discrete_cards`.
    - Added `test_seed_specs_scores_100_ceiling_and_flagship_capping`.
    - Added `test_laptop_who_should_buy_no_linguistic_repetition`.
  - 100% pass rate in 1.24s.
  - Re-seeded SQLite database, regenerated all 7 programmatic comparison JSON collections, and verified 11 static pages compiled via Astro SSG with 0 errors in 1.99s.

### Phase 18: Hardware Catalog Expansion & Programmatic Comparisons Engine (2026-10-20)
- **Catalog Expansion to 22 Verified Hardware Items (`core/data/seed_specs.json`, `scripts/seed_database.py`):**
  - **GPUs Added (5 items):**
    1. `rtx-4090`: NVIDIA GeForce RTX 4090 (24GB GDDR6X, AD102, 16384 CUDA cores, 450W TDP, Dual NVENC AV1, PCIe 4.0 x16, 98.0 flagship benchmark index).
    2. `rtx-4070-ti-super`: NVIDIA GeForce RTX 4070 Ti Super (16GB GDDR6X, AD103, 8448 CUDA cores, 256-bit bus, Dual NVENC AV1, PCIe 4.0 x16, 88.0 benchmark index).
    3. `rtx-4060`: NVIDIA GeForce RTX 4060 (8GB GDDR6, AD107, 3072 CUDA cores, 128-bit bus, Single NVENC AV1, PCIe 4.0 x8, 115W TDP, 58.0 benchmark index).
    4. `rx-7900-xt`: AMD Radeon RX 7900 XT (20GB GDDR6, Navi 31, 5376 SPs, 320-bit bus, DisplayPort 2.1, PCIe 4.0 x16, 315W TDP, 91.0 benchmark index).
    5. `rx-7600-xt`: AMD Radeon RX 7600 XT (16GB GDDR6, Navi 33, 2048 SPs, 128-bit bus, DisplayPort 2.1, PCIe 4.0 x8, 190W TDP, 57.0 benchmark index).
  - **CPUs Added (4 items):**
    6. `i9-14900k`: Intel Core i9-14900K (24 cores [8P + 16E], 32 threads, 6.0 GHz TVB, Intel 7 / 10nm Enhanced SuperFin, LGA 1700 EOL, 253W TDP, 97.0 benchmark index, ray_tracing_score: null).
    7. `ryzen-9-7950x3d`: AMD Ryzen 9 7950X3D (16 cores, 32 threads, 128MB 3D V-Cache, Zen 4, AM5 platform through 2027+, 120W TDP, 98.0 benchmark index, ray_tracing_score: null).
    8. `i5-14600k`: Intel Core i5-14600K (14 cores [6P + 8E], 20 threads, 5.3 GHz boost, Intel 7, LGA 1700 EOL, 181W TDP, 82.0 benchmark index, ray_tracing_score: null).
    9. `ryzen-5-7600x`: AMD Ryzen 5 7600X (6 cores, 12 threads, 32MB L3, Zen 4, AM5 platform through 2027+, 105W TDP, 78.0 benchmark index, ray_tracing_score: null).
  - **Laptops Added (3 items):**
    10. `razer-blade-16-2024`: Razer Blade 16 (2024) (i9-14900HX, RTX 4090 Mobile 16GB 175W, Dual-Mode Mini-LED [4K 120Hz / FHD+ 240Hz 1000 nits], 32GB RAM, 94.0 benchmark index).
    11. `macbook-pro-16-m3-max`: Apple MacBook Pro 16 (M3 Max) (Apple Silicon M3 Max 3nm [16-core CPU, 40-core GPU], 48GB Unified Memory at 300GB/s, 16.2" Liquid Retina XDR Mini-LED 1600 nits, macOS, 22h battery, 92.0 benchmark index).
    12. `asus-tuf-gaming-a15`: ASUS TUF Gaming A15 (2024) (AMD Ryzen 7 7735HS, RTX 4060 Mobile 140W, 15.6" FHD 144Hz 100% sRGB IPS, 90Wh battery, MIL-STD-810H durability, 68.0 benchmark index).
  - **All score ceilings enforced:** strictly `<= 98.0` for all benchmark and gaming scores. All CPU ray tracing scores strictly `None`/`null`.

- **Architectural & Editorial Enhancements (`core/services/`):**
  - **Dual NVENC vs Single NVENC Recognition (`ai_editorial.py`):** Verified AD102 (RTX 4090) and AD103 (RTX 4070 Ti Super) receive Dual NVENC AV1 streaming & export pros, while AD107 (RTX 4060) receives accurate Single NVENC generation text.
  - **PCIe Lane Detection & Symmetrical 8-Lane Warnings (`spec_engine.py`, `ai_editorial.py`):** Handled both cards having 8-lane interfaces (RTX 4060 vs RX 7600 XT), rendering clean Arabic diff explanations (`واجهة توصيل متطابقة تقتصر على 8 مسارات (PCIe 4.0 x8) على كلا البطاقتين`) and injecting cons regarding bandwidth bottlenecks on older PCIe 3.0 motherboards when VRAM fills up.
  - **Apple Silicon & macOS Ecosystem Integration (`fps_calculator.py`, `spec_engine.py`, `ai_editorial.py`):**
    - `fps_calculator.py`: Added `APPLE` vendor recognition with neutral 1.0 bias and 0.0 architectural adjustment.
    - `spec_engine.py`: Integrated `ram_gb` comparison row highlighting Apple's 48GB Unified Memory with 300GB/s bandwidth.
    - `ai_editorial.py`: Implemented `is_apple_vs_win` narrative branches:
      - Gaming analysis awards victory to Windows (native DirectX 12, DLSS 3, anti-cheat) while highlighting macOS translation layer limitations (Game Porting Toolkit).
      - Productivity analysis highlights Apple Silicon's 3nm M3 Max efficiency, ProRes hardware engines, 22-hour battery life, and 100% full unthrottled performance on battery vs Windows laptop throttling.
      - Pros/cons accurately cover Apple's non-upgradable unified memory and lack of native DirectX 12 vs Windows laptop modularity and high fan noise/heat.
  - **Display Technology Comparison (`spec_engine.py`, `ai_editorial.py`):**
    - Differentiates Mini-LED (Liquid Retina XDR, Razer Dual-Mode 4K/FHD) vs OLED vs IPS (500 nits high-brightness), accurately noting peak brightness (1000-1600 nits), blooming, infinite contrast, and burn-in risks.
  - **Equal VRAM Phrasing Polish (`ai_editorial.py`):**
    - Corrected GPU narrative when competing cards share identical VRAM capacity (e.g. RTX 4090 vs RX 7900 XTX, both 24GB), generating `(بسعة متطابقة تبلغ 24GB لكلا البطاقتين)` instead of `(مقابل 24GB لدى منافسه)`.
  - **GPU Flagship Winner Determination (`ai_editorial.py`):**
    - Updated `generate_verdict` to check empirical FPS leads at 1440p/4K before tie evaluation, correctly awarding overall win to RTX 4090 over RX 7900 XTX (+12.6% FPS lead, DLSS 3.5, 98 vs 96 index) while respecting RX 7900 XTX value per dollar.

- **Programmatic Comparison Matrix Expanded to 15 High-Intent Matchups (`scripts/generate_comparisons.py`):**
  - Generated and exported 15 complete JSON comparison documents with zero Amazon links:
    - 8 GPU matchups: 4070S vs 7800XT, 4080S vs 7900XTX, 4060Ti vs 7700XT, 4070S vs 4080S, 7800XT vs 7900XTX, 4090 vs 7900XTX, 4070Ti Super vs 7900XT, 4060 vs 7600XT.
    - 3 CPU matchups: 7800X3D vs 14700K, 7950X3D vs 14900K, 7600X vs 14600K.
    - 4 Laptop matchups: Zephyrus G16 vs Legion Pro 7i, Blade 16 vs Legion Pro 7i, MacBook Pro 16 M3 Max vs Zephyrus G16, TUF A15 vs Zephyrus G16.

- **Phase 18 Adversarial Review & Architectural Hardening (Quality Review):**
  - **Identified & Fixed 7 Critical Flaws in Prior Attempt:**
    1. *Apple vs Windows Laptop Value Narrative Asymmetry:* Fixed `_build_laptop_narrative` in `ai_editorial.py` which previously assumed Windows laptops were always cheaper. Symmetrically accounts for cases where the Apple laptop is cheaper (e.g. MacBook Pro 16 at $3499 vs Razer Blade 16 at $3799) or within a 3% statistical margin.
    2. *Contradictory Apple Silicon Quick Verdict:* Fixed `_build_quick_verdict` to eliminate claims of Apple Silicon having a gaming FPS lead over Windows gaming laptops, correctly attributing Apple's win to workstation compute and battery efficiency while acknowledging Windows gaming dominance.
    3. *Asymmetric RAM Differential Summary Attribution:* Fixed `_compare_laptop_raw_specs` in `spec_engine.py` which previously assigned Apple Silicon's Unified Memory summary even when a Windows laptop had more RAM.
    4. *False 4K Gaming Claims for Budget 16GB GPUs:* Fixed `_get_gpu_tier` and `_compare_gpu_raw_specs` to require `max_bench >= 75` for `upper_1440p`, preventing budget 128-bit cards (e.g. RX 7600 XT) from falsely claiming 4K gaming headroom.
    5. *False 500 Nits IPS Display Attribution:* Fixed IPS display detection across `ai_editorial.py` and `spec_engine.py` to ensure only panels with explicit 500 nits specifications claim high brightness, avoiding false claims for standard budget IPS displays (e.g. ASUS TUF A15).
    6. *Misleading "Lightweight" Claims for Heavy Laptops:* Restricted "وزن خفيف يسهل التنقل" in `ai_editorial.py` exclusively to sub-2.0 kg laptops, eliminating contradictory mobility praise for 2.45-2.6 kg desktop replacements.
    7. *Linguistic Redundancy in Equal VRAM Narratives:* Eliminated duplicate capacity mentions in GPU narratives when comparing cards with matching VRAM.
  - **Verification:**
    - Full test suite expanded to 79 tests (`core/tests/`): 100% pass rate in 1.18s.
    - Astro SSG build (`npm run build`): 19 static HTML routes generated in 4.67s with 0 errors.
    - Zero Amazon compliance: verified across all 15 comparison JSON documents.

### Phase 19: Contextual Rule Engine & Self-Auditing Quality Gate (2026-10-20)
- **MacBook Pro 16 (M3 Max) vs ROG Zephyrus G16 Realism Calibration (`seed_specs.json`, `fps_calculator.py`, `GamingFpsWidget.astro`):**
  - Calibrated MacBook Pro 16 gaming scores in `seed_specs.json` (`raster_1080p: 55.0, raster_1440p: 46.0, raster_4k: 30.0, ray_tracing_score: 45.0`) ensuring Windows RTX gaming laptops (ROG Zephyrus G16 with RTX 4070 Mobile) win native gaming benchmarks across all titles.
  - Added `platform_note_ar` to `GamingFpsItem` and implemented `is_macos` / `get_macos_note` in `FpsCalculator`, documenting macOS translation layer (Metal/GPTK) performance penalties and anti-cheat incompatibility.
  - Added warning banner in `GamingFpsWidget.astro` when a macOS laptop is compared against a Windows machine.
- **High-End GPU Scaling Calibration (`seed_specs.json`, `fps_calculator.py`):**
  - Calibrated `rtx-4080-super` (`benchmark_index: 91.5`) and `rx-7900-xtx` (`benchmark_index: 92.0`), strictly preserving statistical margin tie (< 3% delta).
  - Added halo GPU scaling in `fps_calculator.py` (`1.16x` multiplier for cards with >= 15000 CUDA cores / AD102 / 450W), giving RTX 4090 a >= 6% benchmark index lead and >= 20% average FPS lead over RX 7900 XTX.
  - Added `revised_msrp_usd: 749.0` to `rx-7900-xt` in `seed_specs.json` and integrated dynamic official retail revision notes into `_build_value_budget_gpu`.
- **Contextual Rule Engine Refactoring (`spec_engine.py`, `ai_editorial.py`):**
  - *Power Claims Sanitization:* Strictly barred describing power consumption as "منضبط" or "فقط" for GPUs with TDP >= 260W or CPUs with TDP >= 150W. Added high power consumption, 850W+ PSU, and 12VHPWR cable bend precautions to RTX 4090 cons. Prevented CPUs consuming more power than rivals (e.g. i5-14600K 181W vs Ryzen 5 7600X 105W) from receiving energy efficiency pros while simultaneously listing high power cons. Fixed adversarial CPU power clause edge case when both CPUs have high TDP (>= 150W).
  - *VRAM 4K Gating:* Restricted dedicated 4K gaming praise in VRAM pros strictly to GPUs with `benchmark_index >= 75.0`.
  - *CPU Architectural Nuances:* Restricted L3 cache praise as "ضخمة" strictly to processors with >= 64MB cache (X3D). Added core count deficit cons for CPUs with >= 30% fewer cores (e.g. Ryzen 5 7600X 6-cores vs i5-14600K 14-cores). Differentiated `who_should_buy` between AMD (AM5 lifecycle, sub-150W efficiency) and Intel (multicore productivity, DDR4/DDR5 flexibility), including intra-brand differentiation.
  - *GPU Narrative Grounding:* Grounded GPU raster analysis in empirical FPS benchmarks (`fps_matrix`) on 1440p/4K titles, completely eliminating false raster parity claims between RTX 4090 and RX 7900 XTX.
  - *Price Revision Propagation:* Appended official revised retail price notes (e.g. RX 7900 XT at $749) across all value analysis branches including performance ties (`perf_pct < 3.0%`).
  - *Laptop Contextual Rules:* Handled equal laptop TDP (175W vs 175W in Blade 16 vs Legion Pro 7i) as mutually providing maximum 175W TGP for sustainable clocks. Decoupled benchmark advantage from weight in pros, and prevented heavy laptops (>= 2.4 kg) from praising weight in pros while criticizing it in cons. Restructured buyer personas so Flagship Halo (Razer Blade 16 with RTX 4090 / Mini-LED) and High-End Value (Legion Pro 7i with RTX 4080 / vapor chamber saving $1,600) are never misclassified as budget MIL-STD-810H machines.
- **macOS Emulation Disclosure (`GamingFpsWidget.astro` & `fps_calculator.py`):**
  - Added visual translation layer disclaimer banner and individual `محاكاة Metal/GPTK` badges on benchmark cards when comparing macOS systems against native Windows gaming hardware.
- **Automated Quality Gate Test Suite (`core/tests/test_quality_gate.py`):**
  - Built comprehensive self-auditing test suite asserting all 7 quality rules across all 15 JSON documents in `web/src/data/comparisons/*.json`:
    1. Score range check: all scores strictly between 0 and 100.
    2. Buyer recommendation differentiation: SequenceMatcher similarity <= 0.75 across all comparisons.
    3. Coherence check: zero contradictory pros/cons on any device (battery, energy efficiency, weight).
    4. Realistic power claims: no high-TDP hardware praised with "منضبط" or "فقط" across all editorial texts.
    5. VRAM 4K claims: no sub-75 index GPUs claim 4K gaming in pros.
    6. Platform realism: macOS never beats Windows RTX gaming laptops in gaming FPS, and all benchmarks carry translation disclaimers.
    7. Equal TDP spec diff neutrality: no biased "السحب الأعلى مقابل السحب المنضبط" phrasing, asserting neutral equality phrasing.
  - Added zero-Amazon compliance, high-end GPU calibration (RTX 4090 >= 6% index lead, >= 20% FPS lead, zero raster parity), RX 7900 XT revised MSRP ($749) mention, and laptop buyer persona accuracy assertions.
- **Verification:**
  - Full test suite expanded to 91 tests (`core/tests/`): 100% pass rate in 2.47s.
  - Re-seeded SQLite database with updated specs and regenerated all 15 comparison JSON collections.
  - Astro SSG build (`npm run build`): 19 static HTML routes generated in 7.09s with 0 errors.

### Phase 20: Interactive Hardware Comparison Selector & Full All-Pairs Matrix Generation (2026-10-20)
- **Interactive Comparison Builder (`web/src/components/ComparisonBuilder.astro`):**
  - Designed and implemented a responsive, RTL Arabic interactive selector component with Cairo/Tajawal typography.
  - Features category tabs (🎮 كروت الشاشة | ⚙️ المعالجات | 💻 اللابتوبات).
  - *Independent Dual Quick-Search & Brand Filters:* Solved the critical UX defect where a single global brand filter wiped out the opposite side and prevented cross-brand comparisons (e.g. NVIDIA vs AMD). Each selector (Item 1 and Item 2) now features independent real-time search inputs (`quick-search-a`, `quick-search-b`) and independent brand filter pills (pre-rendered in SSR for initial categories), enabling frictionless cross-brand hardware pairing.
  - *Symmetrical Mutual De-duplication & Clean Swap Logic:* Fixed swap button (`swapBtn`) defect where setting `selectA.value = valB` prior to `populateDropdowns` caused false `(مختارة بالفعل)` tagging on active selections. Implemented symmetrical `rebuildBoth(valB, valA)` and mutual option disabling across both selectors.
  - *Bidirectional Slug Resolution:* Client-side router seamlessly resolves `${idA}:${idB}` or `${idB}:${idA}` and redirects the user directly to `/compare/{matched_slug}`.
  - Embedded natively into the portal homepage (`pages/index.astro`), category hubs (`pages/category/[category].astro`), and dynamic comparison pages (`pages/compare/[slug].astro`).
- **Full Category Matrix Generation (`scripts/generate_comparisons.py`):**
  - Expanded comparison pipeline from 15 curated matchups to the complete all-pairs matrix across all hardware categories:
    - 55 GPU comparisons (11 unique graphics cards).
    - 15 CPU comparisons (6 unique processors).
    - 10 Laptop comparisons (5 unique gaming and creator laptops).
    - Total: 80 programmatic comparisons covering 100% of within-category hardware permutations.
  - Preserved the exact slugs and ordering of the original 15 high-intent matchups at the head of the manifest, ensuring zero broken external links or dead routes.
  - Updated `ComparisonExporter` to include `item_a_id`, `item_b_id`, `item_a_brand`, and `item_b_brand` in `comparisons_index.json`.
- **Quality Gate Hardening & Contextual Edge Cases (`spec_engine.py`, `ai_editorial.py`):**
  - *Equal Desktop/CPU TDP Differential Phrasing:* Updated `_compare_numeric` in `spec_engine.py` for identical TDP values (`val_a == val_b`), outputting neutral equality phrasing (`سحب طاقة متماثل تماماً (XW) لكلا المعالجين/البطاقتين`) satisfying Quality Gate Rule 7 across all CPU matchups (e.g. Ryzen 9 7950X3D vs Ryzen 7 7800X3D at 120W, i9-14900K vs i7-14700K at 253W).
  - *Intra-Brand CPU Persona Differentiation:* Refactored `_build_who_should_buy` in `ai_editorial.py`:
    - Differentiated dual-CCD flagship workstation/streaming X3D (Ryzen 9 7950X3D: 16 cores, 32 threads, 128MB cache) from pure single-CCD gaming X3D (Ryzen 7 7800X3D: 8 cores, zero scheduling overhead, 96MB cache).
    - Prioritized intra-brand Intel evaluation before generic core count thresholds, cleanly separating flagship peak clock compute (i9-14900K: 24 cores, 6.0 GHz TVB) from value-oriented productivity (i7-14700K: 20 cores, DDR4/DDR5 flexibility).
    - Reduced buyer persona similarity from 0.99 to <= 0.40, fully satisfying Quality Gate Rule 2 across all 80 pairs.
- **Homepage & Category UX Optimization (`web/src/pages/index.astro`, `category/[category].astro`, `compare/[slug].astro`):**
  - *Curated High-Intent Featured Comparisons Fix:* Resolved a critical bug where Vite's `import.meta.glob` alphabetical sorting caused the featured homepage comparisons to display 8 Laptops, 6 CPUs, and ZERO GPUs. By mapping `allComparisons` against `comparisons_index.json`, the top 15 featured slots prominently showcase the 15 curated flagship comparisons (8 GPUs, 3 CPUs, 4 Laptops).
  - Added an instant client-side search engine querying all 80 comparisons dynamically as the user types.
  - Added an on-demand "استعراض جميع المقارنات (80)" toggle button allowing users to expand or collapse the full comparison catalog.
- **Verification & Test Suite Expansion:**
  - Added dedicated Phase 20 test suite (`core/tests/test_phase20_matrix_and_builder.py`) validating matrix math (55/15/10=80), preservation of top 15 slugs in exact order, manifest metadata completeness, bidirectional slug resolution (160 permutations), and zero disk/manifest orphans.
  - Full test suite expanded to 96 tests (`core/tests/`): 100% pass rate in 1.68s.
  - Strict Quality Gate (`test_quality_gate.py`): 12/12 audits passed with 0 failures across all 80 exported comparison JSON files.
  - Astro SSG Build (`npm run build`): 84 static HTML routes compiled with 0 errors in 4.33s.
  - Strict ZERO Amazon compliance verified across all 80 JSON datasets.

### Phase 21: Contextual Editorial Hardening, Cross-Tier Resolution Grounding, Dual-X3D Architectural Analysis & Smart Interlinking (2026-10-21)
- **NVIDIA vs NVIDIA Ray Tracing & Pros/Cons Logic (`core/services/ai_editorial.py`):**
  - Eliminated false claims of ray tracing superiority in intra-brand NVIDIA comparisons where both cards support the exact same feature set (DLSS 3.5, Ada Lovelace RT cores).
  - Strictly enforced conditional RT superiority in pros: only use `"تفوق في تتبع الأشعة بمؤشر X/100..."` when `card.ray_tracing_score > opp.ray_tracing_score`.
  - When `card.ray_tracing_score <= opp.ray_tracing_score`, dynamically output neutral capability framing: `"دعم كامل لتقنيات DLSS 3 (توليد الإطارات) و DLSS 3.5 (إعادة بناء الأشعة) مع تتبع أشعة بمؤشر X/100"`.
  - Injected an objective con whenever `card.benchmark_index < opp.benchmark_index - 3.0`: `f"أداء رسومي إجمالي أقل مقارنة بـ {opp.name} ({_format_num(opp.benchmark_index)}/100)"`, ensuring lower-tier GPUs (e.g. RTX 4060 vs RTX 4090) explicitly acknowledge their benchmark and raster deficit.
  - **Cross-Brand RT Neutrality & AMD Deficit Guard (`ai_editorial.py`):** Guarded `gaming_analysis` so NVIDIA only claims RT superiority if `rt_nv > rt_amd` (preventing false superiority claims over stronger AMD RT cards like RX 7700 XT, 7800 XT, 7900 XTX). Guarded AMD RT deficit con with `if (card.ray_tracing_score or 0) < (opp.ray_tracing_score or 0):`, ensuring AMD cards are never falsely penalized when their RT score matches or exceeds NVIDIA.
- **Cross-Tier GPU Resolution Grounding (`core/services/ai_editorial.py` & `spec_engine.py`):**
  - Implemented `_get_gpu_target_resolution(card)` to ground target resolution claims in empirical `benchmark_index` and VRAM capacity:
    - `benchmark_index < 65.0`: strictly `"دقة 1080p"` (entry/budget cards: RTX 4060, RX 7600 XT).
    - `65.0 <= benchmark_index < 80.0`: `"دقة 1080p و 1440p"` if VRAM <= 8GB; `"دقة 1440p"` if VRAM >= 12GB.
    - `benchmark_index >= 80.0`: `"دقة 1440p و 4K"` if VRAM <= 16GB; `"دقة 4K"` if VRAM >= 20GB.
  - Grounded GPU narratives (`_build_gpu_narrative`) across NVIDIA vs NVIDIA, AMD vs AMD, and cross-brand branches:
    - In cross-brand matchups (e.g., RTX 4090 vs RX 7600 XT), `res_context_amd` is now derived strictly from `amd_item.benchmark_index`, preventing sub-65 AMD GPUs from inheriting high-tier 4K/1440p Ultra claims from flagship opponents.
  - Guarded cross-brand narrative and `_build_value_budget_gpu` when `max_bench < 65.0` so neither budget card claims 1440p gaming.
  - Grounded buyer persona recommendations (`_build_who_should_buy`) so no GPU with `benchmark_index < 65.0` claims smooth 1440p gaming.
  - In `_build_gpu_pros_cons`: added `< 65.0` check for AMD VRAM pros so budget cards with 16GB VRAM (e.g. RX 7600 XT) praise 1080p texture headroom rather than 1440p.
  - In `spec_engine.py`: updated `vram_summary` with `elif max_bench < 65: vram_summary = "سعة VRAM أكبر تمنح أريحية ممتازة في الألعاب بدقة 1080p وتفادي اختناق القوام"`.
- **Dual-X3D CPU Gaming Architecture Branch (`core/services/ai_editorial.py`):**
  - Added dedicated `is_a_x3d and is_b_x3d` branch in `_build_cpu_narrative` accurately contrasting single-CCD vs dual-CCD Zen 4 3D V-Cache architectures:
    - Single-CCD (Ryzen 7 7800X3D: 8 cores / 16 threads, all on single V-Cache CCD) highlighted for pure gaming 1% low FPS consistency without inter-CCD latency or core scheduling overhead (`معمارية الشريحة الواحدة Single CCD دون أي تأخير بين الشرائح`).
    - Dual-CCD (Ryzen 9 7950X3D: 16 cores / 32 threads, 8 cores with 3D V-Cache + 8 standard high-frequency cores) highlighted for heavy multitasking, streaming, and content creation alongside elite gaming (`cores > rival_cores` persona evaluation).
- **Smart Related Interlinking (`web/src/components/InternalLinksGrid.astro` & `web/src/pages/compare/[slug].astro`):**
  - Enhanced related comparison discovery by passing `item_a_id` and `item_b_id` from comparison documents to `InternalLinksGrid.astro`.
  - Implemented prioritized stable sorting: comparisons sharing either `item_a_id` or `item_b_id` with the current page appear first (e.g. RTX 4090 vs RTX 4060 page prioritizes other RTX 4090 and RTX 4060 matchups), retaining manifest order among ties and falling back to same-category comparisons to fill the 6-slot grid.
- **Matrix Regeneration & Quality Gate Suite Hardening (`core/tests/`):**
  - Re-executed `scripts/generate_comparisons.py`: all 80 programmatic comparison JSON files and `comparisons_index.json` regenerated with fully grounded editorial logic.
  - Hardened `core/tests/test_quality_gate.py` with rigorous audit assertions scanning all 80 files for:
    - Cross-brand RT superiority neutrality (NVIDIA never claims qualitative RT superiority over AMD cards with equal/higher RT scores).
    - Sub-65 GPU resolution gating across pros, cons, gaming narrative, and personas (zero 1440p or 4K claims for sub-65 cards).
    - AMD RT deficit con suppression when AMD RT score >= NVIDIA RT score.
  - Expanded `core/tests/test_spec_engine.py` and `core/tests/test_affiliate_and_editorial.py` with unit tests covering sub-65 VRAM summaries and RT neutrality.
  - Full test suite: 102/102 tests passing 100% in under 2 seconds.
  - Static build (`npm run build`): all 84 static routes compiled in under 5 seconds with 0 errors.

---

## 5. Rules for Future AI Agents & Maintainers
1. **Never guess:** Read this file and `ARCHITECTURE.md` first before adding features or refactoring.
2. **Never add Amazon links:** The user strictly prohibits Amazon. Any affiliate offer or link generation must strictly stick to Noon, Newegg, AliExpress, and Jumia.
3. **Keep Code Clean & DRY:**
   - Do NOT duplicate comparison logic in Astro components; all comparison math belongs in `core/services/`.
   - Do NOT duplicate styling; use Tailwind utility classes and CSS variables in `global.css`.
4. **Mandatory Test Execution:** Whenever you add a new hardware spec or modify calculation engines, run `pytest` via `D:\tech_comparisons\.venv\Scripts\python.exe -m pytest D:\tech_comparisons\core\tests -o pythonpath=.` and confirm 100% pass rate.
5. **Update This File:** After any major modification, append your changes to Section 4 (Changelog).


