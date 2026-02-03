# 🛍️ Smart Deal Finder

An AI-powered application that intelligently extracts, analyzes, and organizes product deals from supermarket flyers and receipts.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **🧠 AI Extraction** | Uses Gemini 2.0 Flash/Pro and local Ollama VLMs to extract deals from complex flyer layouts |
| **🎛️ Feature Intelligence** | Smart routing system that assigns tasks to optimal models (Speed vs. Accuracy) |
| **📊 Admin Dashboard** | Batch upload, model comparison, analytics, and audit logging |
| **🎨 Modern UI** | Dark mode, mobile-responsive, accessible via LAN |
| **🗺️ Store Map** | Leaflet-based map with nearby store discovery |
| **👨‍🍳 AI Chef** | Recipe suggestions based on your shopping list and deals |

## 🚀 Quick Start

### Prerequisites
- **Node.js** v18+
- **Python** v3.10+
- **Google Cloud API Key** (for Gemini features)

### 1. Backend

```bash
cd smart-deal-react/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set API Key
export GOOGLE_API_KEY="your_key_here"

# Run server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend

```bash
cd smart-deal-react/frontend

npm install
npm run dev
```

**Open**: http://localhost:3000

## 📱 Mobile Access (LAN)

Access from your phone on the same Wi-Fi:
1. Find your computer's IP (e.g., `192.168.1.100`)
2. Ensure both servers are running with `--host 0.0.0.0`
3. Open `http://192.168.1.100:3000` on your phone

## 📂 Project Structure

```
smart-deal-finder/
├── smart-deal-app/          # ⭐ Main Application
│   ├── backend/               # FastAPI API Server
│   │   ├── routers/           # API endpoints
│   │   ├── services/          # Business logic (AI Client, Model Router)
│   │   └── extractors/        # AI model plugins
│   ├── frontend/              # Next.js Web App
│   │   ├── src/app/           # Pages (Home, Admin, Shopper)
│   │   └── src/components/    # Reusable UI components
│   └── docker-compose.yml     # Container deployment
├── docs/                      # Documentation
├── tests/                     # Test suite
├── _archive/                  # Legacy code (gitignored)
└── README.md                  # This file
```

## 🛠️ Tech Stack

| Layer | Technologies |
|-------|--------------|
| **Frontend** | Next.js 14, Tailwind CSS v4, Lucide Icons |
| **Backend** | FastAPI, Uvicorn, TinyDB |
| **AI** | Google Gemini 2.0, Ollama (LLaVA, Bakllava) |
| **Maps** | Leaflet, Overpass API |

## 🧪 VLM Benchmark Results

We tested 20+ Vision Language Models on 50 supermarket flyer pages. Here are the results:

### 🏆 Top Performers

| Model | E2E Recall | Price Acc | Latency | Recommendation |
|-------|------------|-----------|---------|----------------|
| **gemini-3-flash-preview** | 85.6% | 94.4% | 10.7s | 🥇 Best Quality |
| **gemini-2.5-pro** | 84.9% | 93.0% | 23.9s | 🥈 Runner-up |
| **gemini-2.5-flash-lite** | 75.9% | 94.2% | **2.2s** | ⚡ Best Speed |
| gemini-2.5-flash | 76.1% | 92.2% | 11.4s | Good Balance |
| qwen3-vl:235b-cloud | 75.8% | 85.7% | 75.1s | Google Alt |

### 📉 Other Models Tested

| Model | E2E Recall | Notes |
|-------|------------|-------|
| deepseek-vl2 (SiliconFlow) | 41.3% | Good retrieval, poor details |
| devstral-small-2:24b | 64.1% | Fast but lower accuracy |
| Qwen3-VL (8B/30B/235B) | ~5-14% | Poor recall (1 item/page) |
| Local Ollama (LLaVA, etc.) | 0-15% | Too slow on CPU, hallucinations |

### 💡 Recommendations

1. **Production Default**: `gemini-2.5-flash-lite` — 76% recall at 2.2s
2. **Deep Scan Mode**: `gemini-3-flash-preview` — 86% recall (rate limited)
3. **Backup**: `qwen3-vl:235b-cloud` if Google API unavailable

## 📄 Documentation

- [Backend README](smart-deal-react/backend/README.md) - API setup and modules
- [Frontend README](smart-deal-react/frontend/README.md) - UI components and scripts
- [Docker Guide](DOCKER_GUIDE.md) - Container deployment

## 🎯 Target Supermarkets

Aldi · REWE · Edeka · Lidl · Penny · Netto · Kaufland

## 📜 License

MIT License
