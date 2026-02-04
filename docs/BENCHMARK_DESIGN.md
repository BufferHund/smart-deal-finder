# Benchmark Design & Methodology

This document details the architectural design and evaluation methodology used in the Smart Deal Finder benchmarking suite (`prebench.py`).

## 1. Objective
The goal of the benchmark is to evaluate **End-to-End Information Extraction** capabilities of Vision-Language Models (VLMs). Unlike generic VQA benchmarks, this test measures the model's ability to:
1.  **Detect** multiple objects (deals) on a dense page.
2.  **Read** small text (prices, units) accurately.
3.  **Structure** the output into a strict JSON schema.

## 2. Dataset Structure
The benchmark utilizes the `dataset/images_uniform` directory.
- **Input**: High-resolution PNG images of supermarket brochures.
- **Ground Truth**: Corresponding JSON files in `*_annotated` directories.
- **Format**:
  ```json
  [
    {
      "product_name": "Nutella",
      "price": "2.99",
      "unit": "450g",
      "bbox": [0.1, 0.1, 0.2, 0.2]
    }
  ]
  ```

## 3. Evaluation Pipeline (`prebench.py`)

### A. Preprocessing
1.  **Normalization**: Text fields are normalized (lowercase, whitespace trimmed).
    - **Units**: Common abbreviations are standardized (e.g., "stueck" -> "stk", "gramm" -> "g").
    - **Prices**: Converted to floats for numeric comparison (Tolerance: ±0.01).
2.  **Prompting**: Models receive a standardized prompt requesting a JSON array.
    - *Page-Level Mode*: Full page image + "Extract ALL products" prompt.
    - *Crop-Level Mode*: Individual product crops + "Extract details" prompt (Optional).

### B. Matching Algorithm
To evaluate accuracy, we must first alignment the model's predictions with the ground truth list. This is done via `_match_deals`:
1.  **Similarity Metric**: Matches are found based on **Product Name** similarity.
    - Uses `difflib.SequenceMatcher` combined with Token Set Similarity.
    - **Threshold**: > 0.8 similarity required for a match.
2.  **Greedy Matching**: The best scoring prediction is assigned to each ground truth item.

### C. Metrics Calculation
Once matched, the system calculates:

| Metric | Definition |
| :--- | :--- |
| **JSON Success** | % of responses that are valid, parseable JSON. |
| **Recall (Deal Retrieval)** | (Matched Deals) / (Total GT Deals). Measures detection capability. |
| **Precision** | (Matched Deals) / (Total Predicted Deals). Measures hallucination rate. |
| **Price Accuracy** | % of *matched* items where `abs(pred_price - gt_price) <= 0.01`. |
| **Unit Accuracy** | % of *matched* items where unit text similarity > 0.5. |
| **E2E Recall** | Strict metric: % of GT deals where BOTH Price and Unit are correct. |

## 4. Model Integration
The benchmark script supports multiple backends:
- **Ollama**: Local inference via `http://localhost:11434`. (Used for qwen:vla, llava).
- **Google Gemini**: Via `google-genai` SDK using `gemini-2.5-flash` etc.
- **SiliconFlow**: Cloud API for DeepSeek-VL and Qwen-Cloud models.
- **Retry Logic**: Implements exponential backoff for Rate Limits (429) and Quota management.

## 5. Output & Logs
- **Console**: Live progress bar with per-sample elapsed time.
- **JSONL Logs**: Detailed line-by-line logs saved to `outputs_ollama_prebench/`.
  - Useful for debugging why a specific model failed (e.g., visual cropping vs hallucination).

## 6. Running the Benchmark
```bash
# Run on default set
python3 backend/services/prebench.py --models gemini-2.5-flash-lite

# Run specific number of samples
python3 backend/services/prebench.py --max_samples 50
```
