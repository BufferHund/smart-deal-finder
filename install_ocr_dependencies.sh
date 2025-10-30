#!/bin/bash

# SmartDeal OCR Dependencies Installation Script
# This script installs all required OCR engines and their dependencies

echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║        SmartDeal OCR Dependencies Installer              ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "⚠️  This script is optimized for macOS"
    echo "   For Linux, use the manual installation instructions below"
    echo ""
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Step 1: Install Tesseract (system dependency)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Installing Tesseract OCR (system dependency)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if command_exists tesseract; then
    echo "✅ Tesseract already installed:"
    tesseract --version | head -1
    echo ""
else
    echo "📦 Installing Tesseract via Homebrew..."

    # Check if Homebrew is installed
    if ! command_exists brew; then
        echo "❌ Homebrew not found. Please install it first:"
        echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi

    echo "   Running: brew install tesseract"
    brew install tesseract

    # Install additional language data (German)
    echo "   Installing German language data..."
    brew install tesseract-lang

    if command_exists tesseract; then
        echo "✅ Tesseract installed successfully!"
        tesseract --version | head -1
    else
        echo "❌ Tesseract installation failed"
        exit 1
    fi
fi

echo ""

# Step 2: Install Python OCR packages
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Installing Python OCR packages"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: Virtual environment not activated"
    echo "   It's recommended to activate your virtual environment first:"
    echo "   source venv/bin/activate"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install pytesseract
echo "📦 Installing pytesseract..."
pip install pytesseract
if [ $? -eq 0 ]; then
    echo "✅ pytesseract installed successfully"
else
    echo "❌ pytesseract installation failed"
fi
echo ""

# Install PaddleOCR
echo "📦 Installing PaddleOCR (this may take a few minutes)..."
echo "   Note: PaddleOCR requires paddlepaddle"
pip install paddlepaddle
pip install paddleocr
if [ $? -eq 0 ]; then
    echo "✅ PaddleOCR installed successfully"
else
    echo "⚠️  PaddleOCR installation had issues (this is optional)"
fi
echo ""

# Install EasyOCR
echo "📦 Installing EasyOCR (this may take a few minutes)..."
pip install easyocr
if [ $? -eq 0 ]; then
    echo "✅ EasyOCR installed successfully"
else
    echo "⚠️  EasyOCR installation had issues (this is optional)"
fi
echo ""

# Step 3: Verify installations
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Verifying installations"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Running verification script..."
python verify_setup.py

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Installation Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "1. Test OCR with a sample image:"
echo "   python src/preprocessing/ocr_pipeline.py --help"
echo ""
echo "2. Launch the web application:"
echo "   ./run_app.sh"
echo ""
echo "3. If you encounter issues, check:"
echo "   - Tesseract path: which tesseract"
echo "   - Python packages: pip list | grep -E 'tesseract|paddle|easyocr'"
echo ""
