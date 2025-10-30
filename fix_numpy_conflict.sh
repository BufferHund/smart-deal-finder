#!/bin/bash

# Fix NumPy version conflict
# EasyOCR upgraded NumPy to 2.x but other packages need NumPy 1.x

echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║        Fixing NumPy Version Conflict                     ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

echo "The issue: EasyOCR upgraded NumPy to 2.2.6, but most packages"
echo "need NumPy 1.x. We'll downgrade NumPy and reinstall affected packages."
echo ""

# Step 1: Downgrade NumPy
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Downgrading NumPy to 1.26.4"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

pip install "numpy<2.0,>=1.21"

echo ""

# Step 2: Reinstall affected packages
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Reinstalling affected packages"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Reinstall packages that had issues
echo "📦 Reinstalling pandas..."
pip install --force-reinstall --no-deps pandas

echo ""
echo "📦 Reinstalling matplotlib..."
pip install --force-reinstall --no-deps matplotlib

echo ""
echo "📦 Reinstalling scipy..."
pip install --force-reinstall --no-deps scipy

echo ""
echo "📦 Reinstalling scikit-learn..."
pip install --force-reinstall --no-deps scikit-learn

echo ""

# Step 3: Verify installations
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Verifying installations"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python -c "import numpy; print('NumPy version:', numpy.__version__)"
python -c "import pandas; print('Pandas: OK')"
python -c "import matplotlib; print('Matplotlib: OK')"
python -c "import pytesseract; print('Pytesseract: OK')"
python -c "from paddleocr import PaddleOCR; print('PaddleOCR: OK')"
python -c "import easyocr; print('EasyOCR: OK')"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Fix Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Now run: python verify_setup.py"
echo ""
