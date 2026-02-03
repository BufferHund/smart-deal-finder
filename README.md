# Smart Deal Finder

An intelligent application designed to extract, analyze, and organize product deals from supermarket brochures using state-of-the-art Vision-Language Models (VLMs).

## Project Goal

The primary objective of Smart Deal Finder is to automate the extraction of structured product data (price, quantity, name, brand) from unstructured promotional materials (PDF flyers, images). By leveraging advanced VLMs, we aim to surpass traditional OCR methods in handling complex layouts and multi-modal contexts found in retail brochures.

This project focuses on:
- **Accuracy**: minimizing hallucination in price and product details.
- **Efficiency**: optimizing latency for real-time applications.
- **Scalability**: handling diverse layouts from various supermarket chains.

## Dataset

We have curated a specialized dataset focusing on German supermarket chains to train and benchmark our models.

- **Real-world Data**: 299 brochure pages from major chains (Rewe, Aldi Süd, Edeka, Kaufland, Netto, Penny, Rossmann).
- **Annotations**: High-quality, human-validated annotations including bounding boxes, product names, prices, and units.
- **Synthetic Data**: A procedural generation pipeline (inspired by *SynthTIGER*) available to create infinite synthetic brochures for model fine-tuning.

[📄 View Detailed Dataset Guide](data/README.md)

## Benchmarking

We conducted an extensive evaluation of over 17 Vision-Language Models to determine the optimal engine for this task, balancing extraction recall with latency.

### Key Results
- **Production Winner**: **Gemini 2.5 Flash Lite** (2.2s latency, ~76% recall) - Best for real-time use.
- **Quality Winner**: **Gemini 3 Flash Preview** (10s latency, ~86% recall) - Best for deep scanning.
- **Baseline**: Traditional OCR extraction achieved <40% recall on complex layouts.

[📊 View Full Benchmark Report](docs/BENCHMARKS.md)

## Fine-Tuning Work

To further improve performance on specific layouts or new domains, the project includes a fine-tuning infrastructure:
- **Synthetic Generator**: `synthesis_flyer.py` allows generation of large-scale, annotated training data.
- **Goal**: Enable smaller, open-source models (e.g., Llama, Qwen) to achieve performance comparable to large cloud models through domain-specific training.

## Project Structure

- `smart-deal-app/`: The core application (Frontend + Backend).
- `data/`: Dataset, synthetic generation scripts, and data documentation.
- `docs/`: Technical documentation and reports.
- `_archive/`: Legacy code and backups.

## Quick Start

### Backend
```bash
cd smart-deal-app/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export GOOGLE_API_KEY="your_key"
uvicorn main:app --reload
```

### Frontend
```bash
cd smart-deal-app/frontend
npm install
npm run dev
```

## License
MIT License
