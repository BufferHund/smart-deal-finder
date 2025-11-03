"""Region-based clustering for product card detection"""

import numpy as np
from typing import List, Dict, Tuple
from sklearn.cluster import DBSCAN


def cluster_text_boxes_into_regions(text_boxes: List[Dict], eps: float = 100, min_samples: int = 2) -> List[List[Dict]]:
    """
    Cluster text boxes into spatial regions (product cards)

    Args:
        text_boxes: List of text boxes with bbox
        eps: Maximum distance between boxes in same cluster
        min_samples: Minimum boxes to form a cluster

    Returns:
        List of clusters, each containing text boxes
    """
    if not text_boxes:
        return []

    # Extract center points of bounding boxes
    centers = []
    for box in text_boxes:
        bbox = box['bbox']
        center_x = (bbox['x_min'] + bbox['x_max']) / 2
        center_y = (bbox['y_min'] + bbox['y_max']) / 2
        centers.append([center_x, center_y])

    centers = np.array(centers)

    # Use DBSCAN clustering
    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='euclidean').fit(centers)

    labels = clustering.labels_

    # Group boxes by cluster
    clusters = {}
    for idx, label in enumerate(labels):
        if label == -1:  # Noise points
            continue

        if label not in clusters:
            clusters[label] = []

        clusters[label].append(text_boxes[idx])

    # Convert to list and sort by position
    cluster_list = list(clusters.values())

    # Sort clusters by position (top-to-bottom, left-to-right)
    def cluster_position(cluster):
        min_y = min(box['bbox']['y_min'] for box in cluster)
        min_x = min(box['bbox']['x_min'] for box in cluster)
        return (min_y, min_x)

    cluster_list.sort(key=cluster_position)

    return cluster_list


def get_region_bbox(text_boxes: List[Dict]) -> Dict:
    """Get bounding box that encompasses all text boxes in region"""
    if not text_boxes:
        return {'x_min': 0, 'y_min': 0, 'x_max': 0, 'y_max': 0}

    x_mins = [box['bbox']['x_min'] for box in text_boxes]
    y_mins = [box['bbox']['y_min'] for box in text_boxes]
    x_maxs = [box['bbox']['x_max'] for box in text_boxes]
    y_maxs = [box['bbox']['y_max'] for box in text_boxes]

    return {
        'x_min': min(x_mins),
        'y_min': min(y_mins),
        'x_max': max(x_maxs),
        'y_max': max(y_maxs)
    }


def extract_deal_from_region(region_boxes: List[Dict]) -> Dict:
    """
    Extract deal information from a single product card region

    Args:
        region_boxes: All text boxes in this region

    Returns:
        Deal dictionary with product_name, price, discount, unit
    """
    import re

    # Separate boxes by type
    prices = []
    discounts = []
    units = []
    products = []
    others = []

    # Price patterns
    price_patterns = [
        r'(\d+[,.]?\d{0,2})\s*€',
        r'€\s*(\d+[,.]?\d{0,2})',
        r'(\d+[,.]?\d{0,2})\s*(?:EUR|Euro)',
        r'\b(\d+[,.]\d{2})\b'
    ]

    # Discount patterns
    discount_patterns = [
        r'(-?\d+)\s*%',
        r'%\s*(-?\d+)',
        r'-\s*(\d+)\s*%'
    ]

    # Unit pattern
    unit_pattern = r'(\d+\.?\d*)\s*(kg|g|l|ml|stk|stück|pack|dose|pckg|glas)'

    for box in region_boxes:
        text = box['text'].strip()

        if not text or len(text) < 2:
            continue

        # Check for price
        is_price = False
        for pattern in price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value = match.group(1).replace(',', '.')
                    price_float = float(value)
                    if 0.01 <= price_float <= 999.99:
                        prices.append({
                            'text': text,
                            'value': value,
                            'confidence': box.get('confidence', 0),
                            'bbox': box['bbox']
                        })
                        is_price = True
                        break
                except ValueError:
                    pass

        if is_price:
            continue

        # Check for discount
        is_discount = False
        for pattern in discount_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    discount_value = int(match.group(1))
                    if 1 <= abs(discount_value) <= 99:
                        discounts.append({
                            'text': text,
                            'value': str(discount_value),
                            'confidence': box.get('confidence', 0),
                            'bbox': box['bbox']
                        })
                        is_discount = True
                        break
                except ValueError:
                    pass

        if is_discount:
            continue

        # Check for unit
        unit_match = re.search(unit_pattern, text, re.IGNORECASE)
        if unit_match:
            units.append({
                'text': text,
                'quantity': unit_match.group(1),
                'unit': unit_match.group(2),
                'confidence': box.get('confidence', 0),
                'bbox': box['bbox']
            })
            continue

        # Check if product name
        # Product: at least 3 letters, capitalized preferred
        if len(text) >= 3 and re.search(r'[a-zA-ZäöüÄÖÜß]{3,}', text):
            # Filter stop words
            text_lower = text.lower()
            stop_words = {'oder', 'und', 'mit', 'von', 'für', 'der', 'die', 'das', 'ab', 'je'}
            if text_lower not in stop_words:
                products.append({
                    'text': text,
                    'confidence': box.get('confidence', 0),
                    'bbox': box['bbox']
                })
        else:
            others.append(box)

    # Build deal from the region
    deal = {
        'product_name': None,
        'price': None,
        'discount': None,
        'unit': None,
        'region_bbox': get_region_bbox(region_boxes),
        'confidence': 0
    }

    # Get product name - prefer longest or highest confidence
    if products:
        # Sort by length (longer is usually the main product name)
        products_sorted = sorted(products, key=lambda x: len(x['text']), reverse=True)
        # Or combine multiple product words
        product_texts = [p['text'] for p in products_sorted[:2]]  # Take top 2
        deal['product_name'] = ' '.join(product_texts)
        deal['confidence'] = max(p['confidence'] for p in products)

    # Get price - prefer highest value (main price)
    if prices:
        prices_sorted = sorted(prices, key=lambda x: float(x['value']), reverse=True)
        deal['price'] = prices_sorted[0]['value']
        deal['confidence'] = max(deal['confidence'], prices_sorted[0]['confidence'])

    # Get discount
    if discounts:
        deal['discount'] = discounts[0]['value']

    # Get unit
    if units:
        unit_data = units[0]
        deal['unit'] = f"{unit_data['quantity']} {unit_data['unit']}"

    return deal


def create_deals_from_regions(text_boxes: List[Dict], eps: float = 120, min_samples: int = 2) -> List[Dict]:
    """
    Main function: Cluster text boxes into regions and extract deals

    Args:
        text_boxes: All OCR text boxes
        eps: Clustering distance parameter
        min_samples: Minimum boxes per cluster

    Returns:
        List of deals
    """
    # Cluster boxes into regions
    regions = cluster_text_boxes_into_regions(text_boxes, eps=eps, min_samples=min_samples)

    # Extract deal from each region
    deals = []
    for region in regions:
        deal = extract_deal_from_region(region)

        # Only keep deals with at least a price
        if deal['price'] is not None:
            deals.append(deal)

    return deals
