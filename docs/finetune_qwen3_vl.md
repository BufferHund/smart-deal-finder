# Qwen3-VL (8B) Supermarket Deal Extraction Finetune

This guide documents the Qwen3-VL 8B finetuning script and the inline pre/post evaluation added in `qwen3_vl_(8b)_vision_supermarket.py`.
It is written in three tiers so you can pick the depth you need.

## Tier 1: Quick Start (5 minutes)

1) Place data under `data/images_uniform` (see Tier 2 for expected layout).
2) Run the script:

```
python qwen3_vl_(8b)_vision_supermarket.py
```

3) Watch for two summaries:
- Prebench (before training)
- Prebench (after training)

The summaries are saved at:

```
outputs_qwen3_vl/prebench_inline/prebench_before_training_summary.json
outputs_qwen3_vl/prebench_inline/prebench_after_training_summary.json
```

Compare `f1`, `deal_retrieval_rate`, and `safe_deal_rate` to see if finetuning helps.

## Tier 2: How the Script Works

### What it does
- Builds training samples from annotated pages.
- Finetunes Qwen3-VL with LoRA using Unsloth.
- Runs an inline prebench evaluation **before** and **after** training.

### Data layout (expected)
The script scans for folders ending with `_annotated` under `data/images_uniform`:

```
data/images_uniform/
  store_A_annotated/
    0001.json
    0002.json
  store_A/
    0001.jpg
    0002.jpg
```

Each `*.json` is a list of deal objects with `bbox` and fields.

### Key switches at the top
- `STAGE` selects a training preset (see `STAGE_CONFIGS`).
- `RUN_PREBENCH`, `RUN_POSTBENCH` control pre/post evaluation.
- `BENCH_MAX_SAMPLES` limits how many pages are benchmarked.
- `BENCH_MAX_NEW_TOKENS` caps generation length in prebench.

### Why the prebench exists
Trainer metrics do not use generate-by-default in this setup, so they can be misleading.
The prebench runs real generation and parses the JSON output to compute practical metrics.

## Tier 3: Advanced Notes and Tuning

### Training scale
- `val_fast` is a small sanity run.
- For more reliable results, increase `max_samples`, `max_steps`, or use `dev`.
- If validation loss rises after step ~60, consider reducing `max_steps` or learning rate.

### Evaluation stability
You may see metrics like 0.5 if the eval set is tiny. Increase:
- `eval_max_samples`
- `BENCH_MAX_SAMPLES`

### Troubleshooting
- **Prebench is slow**: reduce `BENCH_MAX_SAMPLES` or `BENCH_MAX_NEW_TOKENS`.
- **No samples found**: verify the `_annotated` folder structure and filenames.
- **CUDA OOM**: reduce `batch_size`, increase `grad_accum`, or use smaller `max_steps`.

## Reproducibility
- Random seed is set via `SEED`.
- LoRA setup is stable across runs when the dataset is fixed.

## Outputs
- LoRA model saved to:
  - `lora_model_qwen3_vl/`
- Prebench logs:
  - `outputs_qwen3_vl/prebench_inline/*.jsonl`
  - `outputs_qwen3_vl/prebench_inline/*_summary.json`

## Metrics glossary
- **deal_retrieval_rate**: recall over ground-truth deals.
- **precision**: fraction of predicted deals that match a ground-truth deal.
- **safe_deal_rate**: deals with correct price and unit.
- **price_reliability**: price correctness among matched deals.
