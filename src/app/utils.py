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

    # Patterns for entity extraction
    price_pattern = r'(\d+[,.]?\d{0,2})\s*€?'
    discount_pattern = r'(-?\d+)\s*%'
    unit_pattern = r'(\d+\.?\d*)\s*(kg|g|l|ml|stk|stück|pack|dose)'
    date_pattern = r'(\d{1,2}[./]\d{1,2}[./]\d{2,4})'

    for box in text_boxes:
        text = box.get('text', '').strip()
        bbox = box.get('bbox', {})
        confidence = box.get('confidence', 0)

        if not text:
            continue

        # Check for price
        price_match = re.search(price_pattern, text, re.IGNORECASE)
        if price_match:
            entities['prices'].append({
                'text': text,
                'value': price_match.group(1).replace(',', '.'),
                'bbox': bbox,
                'confidence': confidence
            })
            continue

        # Check for discount
        discount_match = re.search(discount_pattern, text)
        if discount_match:
            entities['discounts'].append({
                'text': text,
                'value': discount_match.group(1),
                'bbox': bbox,
                'confidence': confidence
            })
            continue

        # Check for unit
        unit_match = re.search(unit_pattern, text, re.IGNORECASE)
        if unit_match:
            entities['units'].append({
                'text': text,
                'quantity': unit_match.group(1),
                'unit': unit_match.group(2),
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

        # Check if it looks like a product name (mostly letters, reasonable length)
        if len(text) > 3 and re.search(r'[a-zA-ZäöüÄÖÜß]{3,}', text):
            entities['products'].append({
                'text': text,
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

    # Simple heuristic: group entities that are close together
    products = entities.get('products', [])
    prices = entities.get('prices', [])
    discounts = entities.get('discounts', [])
    units = entities.get('units', [])

    for product in products:
        deal = {
            'product_name': product['text'],
            'product_bbox': product['bbox'],
            'price': None,
            'discount': None,
            'unit': None
        }

        # Find closest price
        min_distance = float('inf')
        closest_price = None

        for price in prices:
            distance = calculate_bbox_distance(product['bbox'], price['bbox'])
            if distance < min_distance:
                min_distance = distance
                closest_price = price

        if closest_price and min_distance < 200:  # Threshold for proximity
            deal['price'] = closest_price['value']
            deal['price_bbox'] = closest_price['bbox']

        # Find closest discount
        min_distance = float('inf')
        closest_discount = None

        for discount in discounts:
            distance = calculate_bbox_distance(product['bbox'], discount['bbox'])
            if distance < min_distance:
                min_distance = distance
                closest_discount = discount

        if closest_discount and min_distance < 200:
            deal['discount'] = closest_discount['value']
            deal['discount_bbox'] = closest_discount['bbox']

        # Find closest unit
        min_distance = float('inf')
        closest_unit = None

        for unit in units:
            distance = calculate_bbox_distance(product['bbox'], unit['bbox'])
            if distance < min_distance:
                min_distance = distance
                closest_unit = unit

        if closest_unit and min_distance < 150:
            deal['unit'] = f"{closest_unit.get('quantity', '')} {closest_unit.get('unit', '')}"
            deal['unit_bbox'] = closest_unit['bbox']

        # Only add deal if we found at least a price
        if deal['price'] is not None:
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
