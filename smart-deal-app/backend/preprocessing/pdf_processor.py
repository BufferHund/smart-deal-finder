"""PDF processing module for converting PDF pages to images"""

import os
from pathlib import Path
from typing import List, Optional, Tuple
import logging
from PIL import Image
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PDFProcessor:
    """Process PDF files and convert to images for OCR"""

    def __init__(self, dpi: int = 300):
        """
        Initialize PDF processor

        Args:
            dpi: DPI for PDF to image conversion (default: 300)
        """
        self.dpi = dpi
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if required libraries are available"""
        try:
            import pypdfium2
            self.pdf_lib = 'pypdfium2'
            self.pypdfium2 = pypdfium2
            logger.info("Using pypdfium2 for PDF processing")
        except ImportError:
            try:
                import pdf2image
                self.pdf_lib = 'pdf2image'
                self.pdf2image = pdf2image
                logger.info("Using pdf2image for PDF processing")
            except ImportError:
                try:
                    import PyPDF2
                    self.pdf_lib = 'PyPDF2'
                    self.PyPDF2 = PyPDF2
                    logger.warning("Only PyPDF2 available - limited functionality")
                except ImportError:
                    logger.error("No PDF library available")
                    raise ImportError(
                        "No PDF processing library found. Install one of: "
                        "pypdfium2, pdf2image, or PyPDF2"
                    )

    def get_page_count(self, pdf_path: str) -> int:
        """
        Get number of pages in PDF

        Args:
            pdf_path: Path to PDF file

        Returns:
            Number of pages
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if self.pdf_lib == 'pypdfium2':
            pdf = self.pypdfium2.PdfDocument(str(pdf_path))
            return len(pdf)

        elif self.pdf_lib == 'pdf2image':
            from pdf2image import pdfinfo_from_path
            info = pdfinfo_from_path(str(pdf_path))
            return info['Pages']

        elif self.pdf_lib == 'PyPDF2':
            with open(pdf_path, 'rb') as f:
                reader = self.PyPDF2.PdfReader(f)
                return len(reader.pages)

        return 0

    def pdf_to_images_pypdfium2(
        self,
        pdf_path: str,
        output_dir: Optional[str] = None,
        page_numbers: Optional[List[int]] = None
    ) -> List[np.ndarray]:
        """
        Convert PDF to images using pypdfium2

        Args:
            pdf_path: Path to PDF file
            output_dir: Optional directory to save images
            page_numbers: Optional list of page numbers (1-indexed)

        Returns:
            List of images as numpy arrays
        """
        pdf = self.pypdfium2.PdfDocument(str(pdf_path))
        images = []

        if page_numbers is None:
            page_numbers = range(1, len(pdf) + 1)

        for page_num in page_numbers:
            # Convert to 0-indexed
            page_idx = page_num - 1

            if page_idx < 0 or page_idx >= len(pdf):
                logger.warning(f"Page {page_num} out of range")
                continue

            page = pdf[page_idx]

            # Render page to bitmap
            bitmap = page.render(
                scale=self.dpi / 72,  # 72 is default DPI
                rotation=0
            )

            # Convert to PIL Image
            pil_image = bitmap.to_pil()

            # Convert to numpy array
            img_array = np.array(pil_image)

            images.append(img_array)

            # Save if output directory specified
            if output_dir:
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)

                filename = f"{Path(pdf_path).stem}_page_{page_num:03d}.png"
                filepath = output_path / filename

                pil_image.save(filepath)
                logger.info(f"Saved page {page_num} to {filepath}")

        return images

    def pdf_to_images_pdf2image(
        self,
        pdf_path: str,
        output_dir: Optional[str] = None,
        page_numbers: Optional[List[int]] = None
    ) -> List[np.ndarray]:
        """
        Convert PDF to images using pdf2image

        Args:
            pdf_path: Path to PDF file
            output_dir: Optional directory to save images
            page_numbers: Optional list of page numbers (1-indexed)

        Returns:
            List of images as numpy arrays
        """
        from pdf2image import convert_from_path

        # Convert pages
        if page_numbers:
            # pdf2image uses 1-indexed pages
            first_page = min(page_numbers)
            last_page = max(page_numbers)
            pil_images = convert_from_path(
                pdf_path,
                dpi=self.dpi,
                first_page=first_page,
                last_page=last_page
            )

            # Filter to requested pages
            page_set = set(page_numbers)
            pil_images = [
                img for i, img in enumerate(pil_images, start=first_page)
                if i in page_set
            ]
        else:
            pil_images = convert_from_path(pdf_path, dpi=self.dpi)

        # Convert to numpy arrays
        images = [np.array(img) for img in pil_images]

        # Save if output directory specified
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            for i, pil_image in enumerate(pil_images, start=1):
                page_num = page_numbers[i-1] if page_numbers else i
                filename = f"{Path(pdf_path).stem}_page_{page_num:03d}.png"
                filepath = output_path / filename

                pil_image.save(filepath)
                logger.info(f"Saved page {page_num} to {filepath}")

        return images

    def pdf_to_images(
        self,
        pdf_path: str,
        output_dir: Optional[str] = None,
        page_numbers: Optional[List[int]] = None
    ) -> List[np.ndarray]:
        """
        Convert PDF pages to images

        Args:
            pdf_path: Path to PDF file
            output_dir: Optional directory to save images
            page_numbers: Optional list of specific page numbers (1-indexed)

        Returns:
            List of images as numpy arrays
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        logger.info(f"Converting PDF: {pdf_path}")
        logger.info(f"Using library: {self.pdf_lib}")

        if self.pdf_lib == 'pypdfium2':
            return self.pdf_to_images_pypdfium2(pdf_path, output_dir, page_numbers)

        elif self.pdf_lib == 'pdf2image':
            return self.pdf_to_images_pdf2image(pdf_path, output_dir, page_numbers)

        elif self.pdf_lib == 'PyPDF2':
            raise NotImplementedError(
                "PyPDF2 doesn't support PDF to image conversion. "
                "Please install pypdfium2 or pdf2image"
            )

        return []

    def get_first_page_image(self, pdf_path: str) -> np.ndarray:
        """
        Get first page of PDF as image (for preview)

        Args:
            pdf_path: Path to PDF file

        Returns:
            First page as numpy array
        """
        images = self.pdf_to_images(pdf_path, page_numbers=[1])
        return images[0] if images else None

    def get_page_image(self, pdf_path: str, page_number: int) -> np.ndarray:
        """
        Get specific page as image

        Args:
            pdf_path: Path to PDF file
            page_number: Page number (1-indexed)

        Returns:
            Page as numpy array
        """
        images = self.pdf_to_images(pdf_path, page_numbers=[page_number])
        return images[0] if images else None

    def batch_process_pdfs(
        self,
        pdf_dir: str,
        output_dir: str,
        page_numbers: Optional[List[int]] = None
    ) -> List[Tuple[str, List[str]]]:
        """
        Batch process multiple PDF files

        Args:
            pdf_dir: Directory containing PDF files
            output_dir: Directory to save converted images
            page_numbers: Optional list of page numbers to extract

        Returns:
            List of tuples (pdf_name, [image_paths])
        """
        pdf_dir = Path(pdf_dir)
        output_dir = Path(output_dir)

        if not pdf_dir.exists():
            raise FileNotFoundError(f"PDF directory not found: {pdf_dir}")

        results = []

        # Find all PDF files
        pdf_files = list(pdf_dir.glob('*.pdf'))
        logger.info(f"Found {len(pdf_files)} PDF files")

        for pdf_file in pdf_files:
            try:
                logger.info(f"Processing: {pdf_file.name}")

                # Create subdirectory for this PDF
                pdf_output_dir = output_dir / pdf_file.stem
                pdf_output_dir.mkdir(parents=True, exist_ok=True)

                # Convert PDF
                self.pdf_to_images(
                    str(pdf_file),
                    str(pdf_output_dir),
                    page_numbers
                )

                # Get list of generated images
                image_files = sorted(pdf_output_dir.glob('*.png'))
                image_paths = [str(f) for f in image_files]

                results.append((pdf_file.name, image_paths))

            except Exception as e:
                logger.error(f"Error processing {pdf_file.name}: {e}")

        return results


def main():
    """Main entry point for PDF processing"""
    import argparse

    parser = argparse.ArgumentParser(description="PDF to Image Converter")
    parser.add_argument('--input', required=True, help='Input PDF file or directory')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--pages', nargs='+', type=int, help='Specific pages to extract (1-indexed)')
    parser.add_argument('--dpi', type=int, default=300, help='DPI for conversion (default: 300)')

    args = parser.parse_args()

    processor = PDFProcessor(dpi=args.dpi)
    input_path = Path(args.input)

    if input_path.is_file():
        # Process single PDF
        images = processor.pdf_to_images(
            str(input_path),
            args.output,
            args.pages
        )
        print(f"✅ Converted {len(images)} pages")

    elif input_path.is_dir():
        # Batch process
        results = processor.batch_process_pdfs(
            str(input_path),
            args.output,
            args.pages
        )
        print(f"✅ Processed {len(results)} PDF files")

    else:
        print(f"❌ Invalid input path: {input_path}")
        return 1

    return 0



def convert_pdf_to_images(pdf_path: str) -> List[np.ndarray]:
    """Helper function to convert PDF to images using default settings"""
    processor = PDFProcessor()
    return processor.pdf_to_images(pdf_path)

if __name__ == '__main__':
    import sys
    sys.exit(main())
