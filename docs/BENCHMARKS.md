# VLM Benchmarking Report & Test Plan

## 1. Sanity Check Results (JSON Output)

We tested 17 installed Ollama models to verify if they can output valid JSON using the `format: "json"` flag.

### ✅ Passed Models (11/17)
These models correctly adhered to the JSON schema and are suitable for the extraction pipeline.
- `minicpm-v:8b` (Passed)
- `llava-llama3:8b` (Passed)
- `llava:7b` (Passed)
- `llava-phi3:3.8b` (Passed)
- `moondream:1.8b` (Passed)
- `granite3.2-vision:2b` (Passed)
- `gemma3:4b` (Passed)
- `ministral-3:3b` (Passed)
- `qwen2.5vl:7b` (Passed)
- `ministral-3:8b` (Passed)
- `qwen2.5vl:3b` (Passed)

### ❌ Failed Models
- `qwen3-vl:2b`, `qwen3-vl:8b`, `qwen3-vl:4b`: Failed to close JSON objects correctly or produced invalid formatting under the current prompt.
- `gemma3:270m`, `gemma3:1b`: Returned 500 errors (missing vision data weights in these small versions).

---

## 2. Current Benchmark Progress

**Mode**: Sequential (One model at a time)  
**Samples**: 5 per model  
**Data Source**: `dataset/images_uniform` (Supermarket flyers)

### Preliminary Results

| Model | JSON Success | E2E Recall | Price Accuracy | Avg Latency | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **gemini-3-flash-preview** | 100% | **85.6%** | **94.4%** | 10.7s | **SOTA (Quality).** Highest E2E Recall, but requires strict rate limiting (9 RPM). |
| **gemini-2.5-pro** | 100% | **84.9%** | **93.0%** | 23.9s | **Runner-up (Quality).** Almost matches Gemini-3, very stable, but slower. |
| **gemini-2.5-flash-lite** | 100% | **75.9%** | **94.2%** | **2.2s** | **SOTA (Efficiency).** Matches Flash quality, 5x faster, beats Devstral. |
| **gemini-2.5-flash** | 100% | 76.1% | 92.2% | 11.4s | Excellent, but overshadowed by Lite (speed) and Preview (quality). |
| **deepseek-vl2** (SiliconFlow) | 100% | 41.3% | 75.7% | 6.5s | **Mid-Tier.** Good retrieval (81%) but poor unit/details extraction (44%), dragging down overall score. |
| **THUDM/GLM-4.1V-9B-Thinking** | 0% | - | - | >60s | **Stuck/Timed Out.** Failed to return results on SiliconFlow. |
| **zai-org/GLM-4.5V** | 20% | ~0% | - | 34s | **Failed.** Extremely slow and found 0 deals in initial test. |
| **Qwen/Qwen3-VL-8B-Instruct** | 50% | 12.0% | 90.0% | var | **Unstable.** High timeout rate and only extracts 1 item/page. |
| **Qwen/Qwen3-VL-30B-A3B-Instruct** | 0% | ~5% | - | 28s | **Failed.** Identical to 8B: extremely poor recall (1 item/page). |
| **Qwen/Qwen3-VL-235B-A22B-Instruct** | 100% | ~14% | - | 6s | **Failed.** Surprising speed (6s) but equally poor recall (1 item/page). |
| **Qwen/Qwen2-VL-72B-Instruct** | 100% | ~14% | 16.7% | 13.4s | **Failed.** Low recall and hallucinated items (low precision). |
| **qwen2.5vl:3b** (Local CPU) | 100% | **100%** | **50%** | **113s** | **Slow but Accurate.** Surprisingly high recall (beats Cloud Qwen), but unusable latency on CPU (>2 min). |
| **granite3.2-vision:2b** (Local CPU) | ~10% | 0% | 25% | 34s | **Failed.** Hallucinations and low recall. Slow on CPU. |
| **bakllava:7b** (Local CPU) | 0% | 0% | - | 7s | **Failed.** Ouput is gibberish/hallucinations (e.g., "4 days ago") despite detailed prompts. |
| **devstral-small-2:24b-cloud** | 100% | 64.1% | 75.1% | 4.1s | Faster and more accurate than DeepSeek-VL2. |
| **gemini-2.5-flash-image** | 96% | 13.8% | 15.3% | 2.5s | **Specialized.** Extracts single items well but fails on full pages. |
| **qwen3-vl:235b-cloud** | 100% | 75.8% | 85.7% | 75.1s | Previous SOTA. Good but slow and expensive. |
| **gemma3:4b-cloud** | 100% | 4.2% | 6.9% | 6.4s | Fast but extremely conservative (1 item/page). |
| **gemma3:12b-cloud** | 100% | 4.3% | 5.6% | 9.9s | Very conservative. Faster than 27B but lower recall. |
| **gemma3:27b-cloud** | 100% | 6.6% | 8.4% | 12.7s | Conservative. Mostly extracts 1 item per page. |
| **ministral-3:3b-cloud** | 100% | 9.8% | 11.2% | 3.8s | Super fast, but only extracts 1 item/page. |
| **minicpm-v:8b** (Local) | 100% | 31.4% | 34.3% | 43.6s | Local baseline. High hallucination rate. |
| **moondream:1.8b** (Local) | 96% | 0.0% | 0.6% | 16.4s | **Not recommended.** Too small for full-page extraction. Extreme hallucinations. |
| **granite3.2-vision:2b** | 100% (2 items) | ~0% | ~0% | 50s | Unstable on full pages, hallucinated prices. |

### 💡 Recommendations

1.  **For Production (Default)**: **`gemini-2.5-flash-lite`**
    *   **Reason**: Unbeatable speed-to-accuracy ratio. 76% Recall at 2.2s.

2.  **For Maximum Quality**: **`gemini-3-flash-preview`**
    *   **Reason**: If you can tolerate ~10s latency (due to rate limiting), it provides the highest recall (86%). Ideal for "Deep Scan" mode.

3.  **Backup Options**:
    *   `qwen3-vl:235b-cloud` if Google API is unavailable.

---

## 3. Future Test Plan

To ensure stability and maximum hardware focus, we have shifted to a **"One Model per Command"** strategy.

### Phase 1: Selective Performance Audit (Current)
- **Goal**: Test models of interest sequentially with 10-20 samples.
- **Metric**: Evaluate accuracy vs. latency specifically for smaller models (2B-4B).

### Phase 2: High-Stake Sequential Evaluation
- **Selection**: Top performers from Phase 1.
- **Setup**: Dedicated runs with larger datasets (50+ samples).
- **Optimization**: Test `--crop-level` (giving models cropped item images instead of full pages) to see if recall improves.

### Phase 3: Fine-Tuning/Prompt Iteration
- Adjust the system prompt for models with high overprediction (like MiniCPM) to be more conservative.
- Test smaller "ready-to-use" local models (Moondream, Granite) for low-latency tasks (e.g., simple shelf price checks).

---

## 4. Operational Guidelines

1. **Sequential Execution**: Never run multiple benchmarks in parallel to prevent GPU VRAM contention.
2. **Incremental Auto-Save**: Always use the version of `prebench.py` that saves results after *each* model.
4. **Detailed Design**: See [BENCHMARK_DESIGN.md](BENCHMARK_DESIGN.md) for the full technical specification of metrics and matching logic.

---

## 5. Fine-Tuning Benchmark Evaluation (Phase 2)

As part of the fine-tuning phase (using `Llama-3.2-11B-Vision`), we have introduced a **new, stricter evaluation standard** that assesses the model's ability to understand layout, not just extract text.

### Key Logic Comparison

| Feature | Legacy Benchmark (`benchmark/run.py`) | New Fine-Tuning Benchmark (`dataset/benchmark_ollama.py`) |
| :--- | :--- | :--- |
| **Primary Goal** | **Text Extraction**: Can the model find the text? | **Object Detection + Extraction**: Can the model find *where* the deal is? |
| **Matching Logic** | High confidence text match (`difflib` ratio > 0.8) | Relaxed text match (`ratio` > 0.5) to tolerate OCR errors, verified by geometry. |
| **Bounding Box** | Ignored / Not required. | **Mandatory**. Requires normalized `[x1, y1, x2, y2]` coordinates. |
| **Metric: BBox Accuracy** | N/A | Calculated as **IoU > 0.5** (Intersection over Union). |
| **Metric: Price Accuracy** | Numeric tolerance (±0.01) | Strict string normalization match (e.g., "1.99" == "1.99"). |

### Evaluation Pipeline (New)

The new benchmark follows this strict verification flow for each predicted item:

1.  **Name Matching** (Candidate Selection):
    *   Find the ground truth item with the highest name similarity.
    *   Threshold: **> 0.5** (allows for minor OCR typos or partial brand names).
2.  **Attribute Verification** (If Name Matches):
    *   **Price**: Must match exactly after normalization (removing currency symbols).
    *   **Geometry**: Calculate IoU (Intersection over Union) between Predicted BBox and Ground Truth BBox.
3.  **Success Criteria**:
    *   An item is only considered "Perfect" if Name matches AND Price matches AND IoU > 0.5.

### Why the Change?
The legacy benchmark allowed "hallucinations of location" (e.g., finding the price but not knowing where it is). The new fine-tuning goal is to produce a model that can **precisely locate** deals on a crowded flyer page to enable downstream UI features like "Click to Select Deal".
