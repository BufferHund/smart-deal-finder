# VLM Benchmarking & Performance Report

## Overview
We conducted an extensive benchmark of over 17 Vision-Language Models (VLMs) to identify the optimal engine for the Smart Deal Finder. The goal was to balance **extraction accuracy** (recall of deals) with **latency** and **cost**.

## Key Findings

### 🏆 The Winner: Gemini 2.5 Flash Lite
- **Role**: Default Production Engine
- **Why**: Unbeatable speed-to-accuracy ratio.
- **Metrics**: 
  - **Latency**: ~2.2s per page (vs 10s+ for others)
  - **Recall**: 75.9% (High quality for speed)
  - **Price Accuracy**: 94.2%

### 🥈 Runner Up: Gemini 3 Flash Preview
- **Role**: Deep Scan / Quality Mode
- **Why**: Highest extraction quality but rate-limited.
- **Metrics**:
  - **Recall**: 85.6% (SOTA)
  - **Latency**: ~10.7s

## Benchmark Summary Table

| Model | JSON Success | E2E Recall | Price Accuracy | Avg Latency | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Gemini 2.5 Flash Lite** | 100% | 75.9% | 94.2% | **2.2s** | ✅ **Production** |
| **Gemini 3 Flash Preview** | 100% | **85.6%** | **94.4%** | 10.7s | ✅ **High Quality** |
| **Devstral Small 24B** | 100% | 64.1% | 75.1% | 4.1s | ⚠️ Good Alternative |
| **DeepSeek VL2** | 100% | 41.3% | 75.7% | 6.5s | ⚠️ Mid-Tier |
| **Qwen 2.5 VL 3B** (CPU) | 100% | 100% | 50% | 113s | ❌ Too Slow |
| **Llava/Bakllava** | ~0% | 0% | - | 7s | ❌ Failed |

## Methodology
- **Dataset**: Sequential run on 5-50 pages from the `dataset/images_uniform` dataset.
- **Hardware**: Validated on both Cloud APIs (Google, Mistral) and Local Inference (SiliconFlow, Ollama CPU).
- **Metric Definitions**:
  - **JSON Success**: Ability to output valid structured JSON.
  - **E2E Recall**: Percentage of deals correctly identified vs human ground truth.
  - **Price Accuracy**: Correctness of price extraction for identified items.
