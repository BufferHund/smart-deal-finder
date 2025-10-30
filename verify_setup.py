#!/usr/bin/env python
"""
Setup Verification Script for SmartDeal Project

This script checks if all required dependencies are installed correctly.
Run this after installing requirements to verify your setup.
"""

import sys
import importlib
import subprocess
from pathlib import Path


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f" {text}")
    print("=" * 60)


def check_python_version():
    """Check Python version"""
    print_header("Python Version")
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")

    if version.major == 3 and version.minor >= 8:
        print("✅ Python version is compatible (3.8+)")
        return True
    else:
        print("❌ Python 3.8 or higher is required")
        return False


def check_package(package_name, import_name=None):
    """Check if a Python package is installed"""
    if import_name is None:
        import_name = package_name

    try:
        module = importlib.import_module(import_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"✅ {package_name}: {version}")
        return True
    except ImportError:
        print(f"❌ {package_name}: Not installed")
        return False


def check_python_packages():
    """Check all required Python packages"""
    print_header("Python Packages")

    packages = [
        ("numpy", "numpy"),
        ("pandas", "pandas"),
        ("pillow", "PIL"),
        ("opencv-python", "cv2"),
        ("pytesseract", "pytesseract"),
        ("paddleocr", "paddleocr"),
        ("easyocr", "easyocr"),
        ("torch", "torch"),
        ("transformers", "transformers"),
        ("peft", "peft"),
        ("beautifulsoup4", "bs4"),
        ("requests", "requests"),
        ("streamlit", "streamlit"),
        ("matplotlib", "matplotlib"),
        ("seaborn", "seaborn"),
        ("pyyaml", "yaml"),
        ("tqdm", "tqdm"),
    ]

    results = []
    for package_name, import_name in packages:
        results.append(check_package(package_name, import_name))

    return all(results)


def check_system_dependencies():
    """Check system dependencies like Tesseract"""
    print_header("System Dependencies")

    # Check Tesseract
    try:
        result = subprocess.run(
            ["tesseract", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ Tesseract: {version_line}")
            tesseract_ok = True
        else:
            print("❌ Tesseract: Not found")
            tesseract_ok = False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Tesseract: Not found")
        print("   Install with: brew install tesseract (macOS)")
        print("   or: sudo apt-get install tesseract-ocr (Ubuntu)")
        tesseract_ok = False

    return tesseract_ok


def check_project_structure():
    """Check if project directories exist"""
    print_header("Project Structure")

    required_dirs = [
        "data/raw",
        "data/processed",
        "data/annotations",
        "src/data_collection",
        "src/preprocessing",
        "src/models",
        "src/evaluation",
        "src/app",
        "notebooks",
        "config",
        "tests"
    ]

    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"✅ {dir_path}")
        else:
            print(f"❌ {dir_path}: Missing")
            all_exist = False

    return all_exist


def check_config_files():
    """Check if configuration files exist"""
    print_header("Configuration Files")

    config_files = [
        "config/data_sources.yaml",
        "config/annotation_schema.json",
        "requirements.txt",
        "README.md",
        "QUICK_START.md"
    ]

    all_exist = True
    for file_path in config_files:
        path = Path(file_path)
        if path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}: Missing")
            all_exist = False

    return all_exist


def main():
    """Main verification function"""
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║        SmartDeal Setup Verification Script               ║
║        Supermarket Brochure Information Extraction       ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)

    results = []

    # Check Python version
    results.append(check_python_version())

    # Check project structure
    results.append(check_project_structure())

    # Check config files
    results.append(check_config_files())

    # Check Python packages
    results.append(check_python_packages())

    # Check system dependencies
    results.append(check_system_dependencies())

    # Summary
    print_header("Summary")

    if all(results):
        print("✅ All checks passed! Your setup is ready.")
        print("\nNext steps:")
        print("1. Read QUICK_START.md for usage instructions")
        print("2. Run data collection: python src/data_collection/scraper.py --list")
        print("3. Try the web app: streamlit run src/app/app.py")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("- Install missing packages: pip install -r requirements.txt")
        print("- Install Tesseract: brew install tesseract (macOS)")
        print("- Check if you're in the right directory")
        return 1


if __name__ == "__main__":
    sys.exit(main())
