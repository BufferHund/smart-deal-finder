"""Utility functions for the Streamlit app"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
import json
import pandas as pd
from typing import List, Dict, Tuple, Optional
import re


def draw_bounding_boxes(
    image: np.ndarray,
    text_boxes: List[Dict],
    confidence_threshold: float = 0.5,
    show_text: bool = True,
    show_confidence: bool = False
) -> np.ndarray:
    """
    Draw bounding boxes on image

    Args:
        image: Input image as numpy array
        text_boxes: List of text boxes with bbox and confidence
        confidence_threshold: Minimum confidence to display
        show_text: Whether to show extracted text
        show_confidence: Whether to show confidence scores

    Returns:
        Image with bounding boxes drawn
    """
    # Convert to PIL for better text rendering
    if len(image.shape) == 2:
        pil_img = Image.fromarray(image).convert('RGB')
    else:
        pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

    draw = ImageDraw.Draw(pil_img)

    # Try to load a font, fall back to default if not available
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
        small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    for box in text_boxes:
        confidence = box.get('confidence', 1.0)

        if confidence < confidence_threshold:
            continue

        bbox = box['bbox']
        text = box.get('text', '')

        # Color based on confidence (green = high, yellow = medium, red = low)
        if confidence > 0.8:
            color = (0, 255, 0)  # Green
        elif confidence > 0.6:
            color = (255, 255, 0)  # Yellow
        else:
            color = (255, 165, 0)  # Orange

        # Draw rectangle
        draw.rectangle(
            [bbox['x_min'], bbox['y_min'], bbox['x_max'], bbox['y_max']],
            outline=color,
            width=3
        )

        # Draw text if requested
        if show_text and text:
            # Background for text
            text_display = text
            if show_confidence:
                text_display = f"{text} ({confidence:.2f})"

            # Position text above the box
            text_y = max(bbox['y_min'] - 25, 0)

            # Draw text background
            draw.rectangle(
                [bbox['x_min'], text_y, bbox['x_min'] + len(text_display) * 10, text_y + 20],
                fill=(0, 0, 0)
            )

            # Draw text
            draw.text(
                (bbox['x_min'] + 2, text_y),
                text_display,
                fill=color,
                font=small_font
            )

    return np.array(pil_img)


def extract_entities(text_boxes: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Extract structured entities from OCR text boxes

    Args:
        text_boxes: List of text boxes with text and bbox

    Returns:
        Dictionary of extracted entities by type
    """
    entities = {
        'prices': [],
        'discounts': [],
        'products': [],
        'units': [],
        'dates': [],
        'other': []
    }

    # Improved patterns for entity extraction
    # Price: Multiple patterns to handle different OCR outputs
    # Pattern 1: Standard with €
    price_pattern_standard = r'(\d+[,.]?\d{0,2})\s*€'
    # Pattern 2: € before number
    price_pattern_euro_first = r'€\s*(\d+[,.]?\d{0,2})'
    # Pattern 3: Just numbers that look like prices (2 decimals)
    price_pattern_decimal = r'\b(\d+[,.]\d{2})\b'
    # Pattern 4: EUR or Euro text
    price_pattern_eur = r'(\d+[,.]?\d{0,2})\s*(?:EUR|Euro|euro)'

    discount_pattern = r'(-?\d+)\s*%'
    # Enhanced discount patterns for common formats
    discount_pattern_alt = r'%\s*(-?\d+)'
    discount_pattern_minus = r'-\s*(\d+)\s*%'

    unit_pattern = r'(\d+\.?\d*)\s*(kg|g|l|ml|stk|stück|pack|dose|pckg|glas)'
    date_pattern = r'(\d{1,2}[./]\d{1,2}[./]\d{2,4})'

    # Common German stop words to filter out from products
    stop_words = {
        'oder', 'und', 'mit', 'von', 'für', 'der', 'die', 'das',
        'den', 'dem', 'ein', 'eine', 'einen', 'einem', 'zur', 'zum',
        'versch', 'verschiedene', 'ab', 'bis', 'je', 'pro', 'per',
        'vol', 'incl', 'inkl', 'zzgl', 'mwst', 'ca', 'bzw'
    }

    for box in text_boxes:
        text = box.get('text', '').strip()
        bbox = box.get('bbox', {})
        confidence = box.get('confidence', 0)

        if not text or len(text) < 2:
            continue

        # Check for price - try multiple patterns
        price_match = None
        price_value = None

        # Try pattern 1: number + €
        price_match = re.search(price_pattern_standard, text, re.IGNORECASE)
        if price_match:
            price_value = price_match.group(1)

        # Try pattern 2: € + number
        if not price_match:
            price_match = re.search(price_pattern_euro_first, text, re.IGNORECASE)
            if price_match:
                price_value = price_match.group(1)

        # Try pattern 3: EUR/Euro
        if not price_match:
            price_match = re.search(price_pattern_eur, text, re.IGNORECASE)
            if price_match:
                price_value = price_match.group(1)

        # Try pattern 4: Just decimal numbers (as fallback)
        # Only if text is short and looks like a standalone price
        if not price_match and len(text) <= 10:
            price_match = re.search(price_pattern_decimal, text)
            if price_match:
                price_value = price_match.group(1)

        if price_match and price_value:
            price_value = price_value.replace(',', '.')
            try:
                # Validate price is reasonable (0.01 to 999.99)
                price_float = float(price_value)
                if 0.01 <= price_float <= 999.99:
                    entities['prices'].append({
                        'text': text,
                        'value': price_value,
                        'bbox': bbox,
                        'confidence': confidence
                    })
                    continue
            except ValueError:
                pass

        # Check for discount - try multiple patterns
        discount_match = re.search(discount_pattern, text)
        discount_value = None

        if discount_match:
            discount_value = discount_match.group(1)
        else:
            # Try alternative patterns
            discount_match = re.search(discount_pattern_alt, text)
            if discount_match:
                discount_value = discount_match.group(1)
            else:
                discount_match = re.search(discount_pattern_minus, text)
                if discount_match:
                    discount_value = '-' + discount_match.group(1)

        if discount_match and discount_value:
            try:
                discount_int = int(discount_value)
                # Validate discount is reasonable (1% to 99%)
                if 1 <= abs(discount_int) <= 99:
                    entities['discounts'].append({
                        'text': text,
                        'value': str(discount_int),
                        'bbox': bbox,
                        'confidence': confidence
                    })
                    continue
            except ValueError:
                pass

        # Check for unit
        unit_match = re.search(unit_pattern, text, re.IGNORECASE)
        if unit_match:
            entities['units'].append({
                'text': text,
                'quantity': unit_match.group(1),
                'unit': unit_match.group(2).lower(),
                'bbox': bbox,
                'confidence': confidence
            })
            continue

        # Check for date
        date_match = re.search(date_pattern, text)
        if date_match:
            entities['dates'].append({
                'text': text,
                'value': date_match.group(1),
                'bbox': bbox,
                'confidence': confidence
            })
            continue

        # Check if it looks like a product name
        # Requirements:
        # 1. At least 4 characters long
        # 2. Contains at least 4 consecutive letters
        # 3. Not a common stop word
        # 4. Doesn't end with punctuation like comma
        text_lower = text.lower().rstrip('.,;:')

        if (len(text) >= 4 and
            re.search(r'[a-zA-ZäöüÄÖÜß]{4,}', text) and
            text_lower not in stop_words and
            not text_lower.endswith(('tiefgefroren', 'gekühlt', 'frisch'))):

            # Prefer capitalized words (brand names)
            if text[0].isupper():
                entities['products'].append({
                    'text': text.rstrip('.,;:'),
                    'bbox': bbox,
                    'confidence': confidence
                })
            # Also accept longer lowercase words
            elif len(text) >= 6:
                entities['products'].append({
                    'text': text.rstrip('.,;:'),
                    'bbox': bbox,
                    'confidence': confidence
                })
        else:
            entities['other'].append({
                'text': text,
                'bbox': bbox,
                'confidence': confidence
            })

    return entities


def entities_to_dataframe(entities: Dict[str, List[Dict]]) -> pd.DataFrame:
    """
    Convert entities to a pandas DataFrame

    Args:
        entities: Dictionary of entities

    Returns:
        DataFrame with entity information
    """
    rows = []

    for entity_type, entity_list in entities.items():
        for entity in entity_list:
            row = {
                'Type': entity_type.capitalize(),
                'Text': entity['text'],
                'Confidence': f"{entity['confidence']:.2f}",
                'X': entity['bbox'].get('x_min', 0),
                'Y': entity['bbox'].get('y_min', 0)
            }

            # Add type-specific fields
            if 'value' in entity:
                row['Value'] = entity['value']
            if 'quantity' in entity:
                row['Quantity'] = entity['quantity']
            if 'unit' in entity:
                row['Unit'] = entity['unit']

            rows.append(row)

    return pd.DataFrame(rows)


def create_deals_from_entities(entities: Dict[str, List[Dict]]) -> List[Dict]:
    """
    Create structured deals by grouping nearby entities

    Args:
        entities: Dictionary of extracted entities

    Returns:
        List of deal dictionaries
    """
    deals = []

    # Get all entity types
    products = entities.get('products', [])
    prices = entities.get('prices', [])
    discounts = entities.get('discounts', [])
    units = entities.get('units', [])

    # Track which prices have been used
    used_prices = set()

    # Sort products by vertical position (top to bottom, left to right)
    products_sorted = sorted(products, key=lambda p: (p['bbox']['y_min'], p['bbox']['x_min']))

    for product in products_sorted:
        # Find closest price that hasn't been used yet
        min_distance = float('inf')
        closest_price = None
        closest_price_idx = None

        for idx, price in enumerate(prices):
            if idx in used_prices:
                continue

            # Calculate both horizontal and vertical distance
            h_distance = abs(product['bbox']['x_min'] - price['bbox']['x_min'])
            v_distance = abs(product['bbox']['y_min'] - price['bbox']['y_min'])

            # Price should be relatively close vertically (same product block)
            # and not too far horizontally
            if v_distance < 150 and h_distance < 400:
                # Weighted distance: vertical proximity is more important
                distance = v_distance * 2 + h_distance
                if distance < min_distance:
                    min_distance = distance
                    closest_price = price
                    closest_price_idx = idx

        # Only create deal if we found a reasonable price
        if closest_price is None:
            continue

        # Mark this price as used
        used_prices.add(closest_price_idx)

        deal = {
            'product_name': product['text'],
            'product_bbox': product['bbox'],
            'price': closest_price['value'],
            'price_bbox': closest_price['bbox'],
            'discount': None,
            'unit': None
        }

        # Find closest discount (within same product block)
        min_distance = float('inf')
        closest_discount = None

        for discount in discounts:
            v_distance = abs(product['bbox']['y_min'] - discount['bbox']['y_min'])
            h_distance = abs(product['bbox']['x_min'] - discount['bbox']['x_min'])

            if v_distance < 150 and h_distance < 400:
                distance = v_distance * 2 + h_distance
                if distance < min_distance:
                    min_distance = distance
                    closest_discount = discount

        if closest_discount:
            deal['discount'] = closest_discount['value']
            deal['discount_bbox'] = closest_discount['bbox']

        # Find closest unit
        min_distance = float('inf')
        closest_unit = None

        for unit in units:
            v_distance = abs(product['bbox']['y_min'] - unit['bbox']['y_min'])
            h_distance = abs(product['bbox']['x_min'] - unit['bbox']['x_min'])

            if v_distance < 100 and h_distance < 300:
                distance = v_distance * 2 + h_distance
                if distance < min_distance:
                    min_distance = distance
                    closest_unit = unit

        if closest_unit:
            deal['unit'] = f"{closest_unit.get('quantity', '')} {closest_unit.get('unit', '')}"
            deal['unit_bbox'] = closest_unit['bbox']

        deals.append(deal)

    return deals


def calculate_bbox_distance(bbox1: Dict, bbox2: Dict) -> float:
    """
    Calculate distance between centers of two bounding boxes

    Args:
        bbox1: First bounding box
        bbox2: Second bounding box

    Returns:
        Euclidean distance between centers
    """
    x1 = (bbox1['x_min'] + bbox1['x_max']) / 2
    y1 = (bbox1['y_min'] + bbox1['y_max']) / 2

    x2 = (bbox2['x_min'] + bbox2['x_max']) / 2
    y2 = (bbox2['y_min'] + bbox2['y_max']) / 2

    return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)


def export_to_json(data: Dict, filename: str = "results.json") -> bytes:
    """
    Export data to JSON bytes

    Args:
        data: Data to export
        filename: Output filename

    Returns:
        JSON as bytes
    """
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    return json_str.encode('utf-8')


def export_to_csv(df: pd.DataFrame) -> bytes:
    """
    Export DataFrame to CSV bytes

    Args:
        df: DataFrame to export

    Returns:
        CSV as bytes
    """
    return df.to_csv(index=False).encode('utf-8')


def format_confidence_color(confidence: float) -> str:
    """
    Get color for confidence score

    Args:
        confidence: Confidence score (0-1)

    Returns:
        Color name for Streamlit
    """
    if confidence > 0.8:
        return "green"
    elif confidence > 0.6:
        return "orange"
    else:
        return "red"
