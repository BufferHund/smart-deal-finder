# Smart Deal Finder - Backend

The backend for **Smart Deal Finder** is a high-performance API built with [FastAPI](https://fastapi.tiangolo.com/) and Python. It handles the heavy lifting of image processing, AI model orchestration (Gemini/Ollama), and data management.

## ⚡ Key Modules

- **AI Client** (`services/ai_client.py`): Unified interface for calling Gemini 2.0 and other models with retry logic, caching, and rate limiting.
- **Feature Router** (`services/feature_router.py`): Intelligent system that routes different content types (Brochure, Receipt) to their assigned models.
- **Model Router** (`services/model_router.py`): Handles the specific prompt engineering and response parsing for each extraction method.
- **API Routers** (`routers/`):
  - `admin_pro.py`: Endpoints for batch processing, benchmarks, and debug tools.
  - `agent.py`: Endpoints for chat and user interactions.

## 🛠️ Setup & Installation

### 1. Environment
Make sure you have Python 3.10+ installed.

```bash
# Create venv
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install deps
pip install -r requirements.txt
```

### 2. Configuration
The application relies on environment variables. You can export them directly or use a `.env` file (if configured).

- `GOOGLE_API_KEY`: Required for Gemini model access.

### 3. Running the Server

Use `uvicorn` to start the ASGI server:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- **API Docs**: Open `http://localhost:8000/docs` for the interactive Swagger UI.
- **Redoc**: Open `http://localhost:8000/redoc` for alternative documentation.

## 🧠 AI Models

The backend supports multiple "Extractors":
1.  **Gemini**: Uses Google's Multimodal models (Flash/Pro). High accuracy, low latency.
2.  **Local VLM**: Uses Ollama to run models like `llava`, `bakllava` on your local machine.
3.  **OCR**: Traditional Tesseract-based OCR (fallback).

Configuration for features is stored in `extractors/features.yaml`.
