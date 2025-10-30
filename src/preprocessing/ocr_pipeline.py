"""OCR pipeline for extracting text from brochure images"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np
from PIL import Image
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OCRPipeline:
    """Pipeline for OCR processing of brochure images"""

    def __init__(
        self,
        ocr_engine: str = 'paddleocr',
        output_format: str = 'json',
        languages: List[str] = None
    ):
        """
        Initialize OCR pipeline

        Args:
            ocr_engine: OCR engine to use ('paddleocr', 'tesseract', 'easyocr')
            output_format: Output format ('json', 'txt', 'xml')
            languages: List of languages for OCR (default: ['de', 'en'])
        """
        self.ocr_engine = ocr_engine.lower()
        self.output_format = output_format
        self.languages = languages or ['de', 'en']

        # Initialize OCR engine
        self.ocr = self._initialize_ocr()

        logger.info(f"Initialized OCR pipeline with {self.ocr_engine}")

    def _initialize_ocr(self):
        """Initialize the specified OCR engine"""

        if self.ocr_engine == 'paddleocr':
            try:
                from paddleocr import PaddleOCR
                return PaddleOCR(
                    use_angle_cls=True,
                    lang='en',  # PaddleOCR uses 'en' for English/German
                    show_log=False
                )
            except ImportError:
                logger.error("PaddleOCR not installed. Install with: pip install paddleocr")
                raise

        elif self.ocr_engine == 'tesseract':
            try:
                import pytesseract
                return pytesseract
            except ImportError:
                logger.error("Pytesseract not installed. Install with: pip install pytesseract")
                raise

        elif self.ocr_engine == 'easyocr':
            try:
                import easyocr
                return easyocr.Reader(self.languages)
            except ImportError:
                logger.error("EasyOCR not installed. Install with: pip install easyocr")
                raise

        else:
            raise ValueError(f"Unsupported OCR engine: {self.ocr_engine}")

    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Preprocess image for better OCR results

        Args:
            image_path: Path to input image

        Returns:
            Preprocessed image as numpy array
        """
        # Read image
        img = cv2.imread(image_path)

        if img is None:
            raise ValueError(f"Could not read image: {image_path}")

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray)

        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )

        return thresh

    def extract_text_paddleocr(self, image: np.ndarray) -> List[Dict]:
        """
        Extract text using PaddleOCR

        Args:
            image: Input image

        Returns:
            List of text boxes with coordinates and text
        """
        result = self.ocr.ocr(image, cls=True)

        extracted_data = []
        if result and result[0]:
            for line in result[0]:
                box = line[0]  # Bounding box coordinates
                text_info = line[1]  # (text, confidence)

                extracted_data.append({
                    'text': text_info[0],
                    'confidence': float(text_info[1]),
                    'bbox': {
                        'x_min': int(min(p[0] for p in box)),
                        'y_min': int(min(p[1] for p in box)),
                        'x_max': int(max(p[0] for p in box)),
                        'y_max': int(max(p[1] for p in box))
                    }
                })

        return extracted_data

    def extract_text_tesseract(self, image: np.ndarray) -> List[Dict]:
        """
        Extract text using Tesseract

        Args:
            image: Input image

        Returns:
            List of text boxes with coordinates and text
        """
        import pytesseract

        # Get detailed data from Tesseract
        data = pytesseract.image_to_data(
            image,
            lang='+'.join(self.languages),
            output_type=pytesseract.Output.DICT
        )

        extracted_data = []
        n_boxes = len(data['text'])

        for i in range(n_boxes):
            if int(data['conf'][i]) > 0:  # Filter out low confidence
                text = data['text'][i].strip()
                if text:
                    extracted_data.append({
                        'text': text,
                        'confidence': float(data['conf'][i]) / 100.0,
                        'bbox': {
                            'x_min': data['left'][i],
                            'y_min': data['top'][i],
                            'x_max': data['left'][i] + data['width'][i],
                            'y_max': data['top'][i] + data['height'][i]
                        }
                    })

        return extracted_data

    def extract_text_easyocr(self, image: np.ndarray) -> List[Dict]:
        """
        Extract text using EasyOCR

        Args:
            image: Input image

        Returns:
            List of text boxes with coordinates and text
        """
        result = self.ocr.readtext(image)

        extracted_data = []
        for detection in result:
            box, text, confidence = detection

            extracted_data.append({
                'text': text,
                'confidence': float(confidence),
                'bbox': {
                    'x_min': int(min(p[0] for p in box)),
                    'y_min': int(min(p[1] for p in box)),
                    'x_max': int(max(p[0] for p in box)),
                    'y_max': int(max(p[1] for p in box))
                }
            })

        return extracted_data

    def process_image(self, image_path: str, preprocess: bool = True) -> Dict:
        """
        Process a single image with OCR

        Args:
            image_path: Path to input image
            preprocess: Whether to preprocess the image

        Returns:
            Dictionary containing extracted data
        """
        logger.info(f"Processing: {image_path}")

        # Load image
        if preprocess:
            image = self.preprocess_image(image_path)
        else:
            image = cv2.imread(image_path)

        # Extract text based on OCR engine
        if self.ocr_engine == 'paddleocr':
            text_data = self.extract_text_paddleocr(image)
        elif self.ocr_engine == 'tesseract':
            text_data = self.extract_text_tesseract(image)
        elif self.ocr_engine == 'easyocr':
            text_data = self.extract_text_easyocr(image)
        else:
            raise ValueError(f"Unsupported OCR engine: {self.ocr_engine}")

        result = {
            'image_path': image_path,
            'ocr_engine': self.ocr_engine,
            'text_boxes': text_data,
            'num_boxes': len(text_data)
        }

        logger.info(f"Extracted {len(text_data)} text boxes")
        return result

    def save_results(self, results: Dict, output_path: str):
        """
        Save OCR results to file

        Args:
            results: OCR results dictionary
            output_path: Path to output file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if self.output_format == 'json':
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

        elif self.output_format == 'txt':
            with open(output_file, 'w', encoding='utf-8') as f:
                for box in results['text_boxes']:
                    f.write(f"{box['text']}\n")

        logger.info(f"Results saved to: {output_path}")

    def process_directory(
        self,
        input_dir: str,
        output_dir: str,
        extensions: List[str] = None
    ) -> List[Dict]:
        """
        Process all images in a directory

        Args:
            input_dir: Input directory containing images
            output_dir: Output directory for results
            extensions: List of file extensions to process

        Returns:
            List of results for all processed images
        """
        if extensions is None:
            extensions = ['.jpg', '.jpeg', '.png', '.pdf']

        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results = []
        image_files = []

        for ext in extensions:
            image_files.extend(input_path.glob(f'*{ext}'))

        logger.info(f"Found {len(image_files)} images to process")

        for image_file in image_files:
            try:
                result = self.process_image(str(image_file))
                results.append(result)

                # Save individual result
                output_file = output_path / f"{image_file.stem}.json"
                self.save_results(result, str(output_file))

            except Exception as e:
                logger.error(f"Error processing {image_file}: {e}")

        # Save combined results
        combined_output = output_path / "all_results.json"
        with open(combined_output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logger.info(f"Processed {len(results)} images")
        return results


def main():
    """Main entry point for OCR pipeline"""
    import argparse

    parser = argparse.ArgumentParser(description="OCR pipeline for brochure images")
    parser.add_argument('--input', required=True, help='Input directory or file')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--engine', default='paddleocr', choices=['paddleocr', 'tesseract', 'easyocr'])
    parser.add_argument('--format', default='json', choices=['json', 'txt'])
    parser.add_argument('--no-preprocess', action='store_true', help='Disable preprocessing')

    args = parser.parse_args()

    pipeline = OCRPipeline(ocr_engine=args.engine, output_format=args.format)

    input_path = Path(args.input)
    if input_path.is_dir():
        pipeline.process_directory(args.input, args.output)
    else:
        result = pipeline.process_image(args.input, preprocess=not args.no_preprocess)
        output_file = Path(args.output) / f"{input_path.stem}.json"
        pipeline.save_results(result, str(output_file))


if __name__ == '__main__':
    main()
