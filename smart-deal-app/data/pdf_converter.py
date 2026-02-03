# pdf_converter.py
# This module converts PDF files to images and processes them to ensure uniform size.
# It uses pdf2image for conversion and Pillow for image processing.
# Required libraries: pdf2image, Pillow

from PIL import Image, ImageOps
from pdf2image import convert_from_path
import os


def convert_to_pics(market_name, dpi=200):
    """
    Convert PDF files in the specified market directory to PNG images.
    Each page of the PDF is saved as a separate PNG file.
    
    Args:
        market_name (str): The name of the market (directory containing PDF files).
        dpi (int): The resolution for the converted images.
    Returns:
        None
    """
    input_dir = os.path.join("raw", market_name)
    output_dir = os.path.join("images", market_name)
    os.makedirs(output_dir, exist_ok=True)

    for pdf_file in os.listdir(input_dir):
        # Process only PDF files
        if pdf_file.endswith(".pdf"):
            pdf_path = os.path.join(input_dir, pdf_file)
            pages = convert_from_path(pdf_path, dpi=dpi)
            for i, page in enumerate(pages):
                # Save each page as a PNG file
                img_name = f"{pdf_file.replace('.pdf', '')}_page_{i+1}.png"
                save_path = os.path.join(output_dir, img_name)
                page.save(save_path, "PNG")
                print(f"Saved {save_path}")


def process_pics(market_name, target_size=(1024, 1448)):
    """
    Resize and pad images in the specified market directory to ensure uniform size.
    Args:
        market_name (str): The name of the market (directory containing images).
        target_size (tuple): The desired size (width, height) for the output images.
    Returns:
        None
    """
    input_dir = os.path.join("images", market_name)
    output_dir =os.path.join("images_uniform", market_name)
    os.makedirs(output_dir, exist_ok=True)

    def resize_and_pad(img_path, save_path, size=target_size):
        """
        Resize and pad an image to the target size.
        Args:
            img_path (str): Path to the input image.
            save_path (str): Path to save the processed image.
            size (tuple): Target size (width, height).
        Returns:
            None
        """
        img = Image.open(img_path).convert("RGB")
        img.thumbnail(size, Image.LANCZOS)

        # Calculate padding to center the image
        delta_w = size[0] - img.size[0]
        delta_h = size[1] - img.size[1]
        padding = (delta_w // 2, delta_h // 2, delta_w - delta_w // 2, delta_h - delta_h // 2)

        new_img = ImageOps.expand(img, padding, fill=(255, 255, 255))
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        new_img.save(save_path)

    # Process each PNG image in the input directory
    for file in os.listdir(input_dir):
        if file.lower().endswith(".png"):
            in_path = os.path.join(input_dir, file)
            out_path = os.path.join(output_dir, file)

            resize_and_pad(in_path, out_path)

            print(f"Processed {out_path}")


if __name__ == "__main__":
    market_names = os.listdir("raw")
    market_names = [market_name for market_name in market_names if not market_name.startswith(".")]
    for market_name in market_names:
        convert_to_pics(market_name)
        process_pics(market_name)
