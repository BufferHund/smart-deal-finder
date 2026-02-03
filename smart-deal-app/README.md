# 🛍️ Smart Deal Finder

**Smart Deal Finder** is an AI-powered application designed to intelligently extract, analyze, and organize product deals from supermarket flyers and receipts. It leverages advanced Vision Language Models (VLMs) like **Google Gemini 2.0** and local **Ollama** models to turn static images into structured data.

## ✨ Key Features

- **🧠 AI-Powered Extraction**: Automatically detects products, prices, and discounts from complex flyer layouts using State-of-the-Art Vision models.
- **🎛️ Feature Intelligence**: Smart routing system that assigns different tasks (e.g., "Brochure Reading" vs. "Receipt Scanning") to the most efficient model (Speed vs. Accuracy).
- **📊 Admin Dashboard**: A comprehensive Next.js interface for:
  - Uploading and processing batches of flyers.
  - Comparing AI model performance (Gemini vs. Local VLM vs. OCR).
  - Managing logs and audit trails.
- **🎨 Modern UI**:
  - **Dark Mode**: sleek, professional "Obsidian/Slate" theme.
  - **Mobile Ready**: Fully responsive design accessible via LAN (e.g., on your iPhone).
- **⚙️ Configurable**: Easily switch extraction engines, adjust prompts, and fine-tune model parameters without restarting.

## 🛠️ Tech Stack

### Frontend
- **Framework**: [Next.js 14](https://nextjs.org/) (App Router)
- **Styling**: [Tailwind CSS v4](https://tailwindcss.com/)
- **Icons**: [Lucide React](https://lucide.dev/)
- **State Management**: React Hooks

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **AI Integration**:
  - `google-generativeai` for Gemini 2.0 Flash/Pro
  - `ollama` for local inference (Llava, Bakllava)
- **Data Processing**: Pillow (PIL), PyYAML

## 🚀 Getting Started

### Prerequisites
- **Node.js** (v18+)
- **Python** (v3.10+)
- **Google Cloud API Key** (for Gemini features)

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export GOOGLE_API_KEY="your_api_key_here"

# Run the server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
*The backend will be available at `http://localhost:8000` (API docs at `/docs`).*

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```
*The app will be available at `http://localhost:3000`.*

## 📱 Mobile Access (LAN)

To access the application from your phone on the same Wi-Fi network:

1. Find your computer's local IP address (e.g., `192.168.1.187`).
2. Ensure both Frontend (`npm run dev`) and Backend (`uvicorn ... --host 0.0.0.0`) are running.
3. Open your mobile browser and go to `http://192.168.1.187:3000`.

*Note: The frontend is configured to automatically proxy API requests to the backend, so everything works out of the box!*

## 📂 Project Structure

- `frontend/`: Next.js application source code.
- `backend/`: FastAPI server and AI logic.
  - `routers/`: API endpoints (Admin, Agent, etc.).
  - `services/`: Core business logic (AI Client, Model Router).
  - `extractors/`: Configuration for feature-specific models (`features.yaml`).
- `data/`: Storage for uploaded flyers and database files (ignored by git).
