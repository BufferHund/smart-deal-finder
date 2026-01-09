import numpy as np
from typing import List, Dict, Any, Tuple, Set

class Evaluator:
    """
    Evaluates model predictions against ground truth labels using strict 
    IoU-based Greedy Matching and specific field-level metrics.
    """
    def __init__(self, iou_threshold: float = 0.5, name_sim_threshold: float = 0.85):
        self.iou_threshold = iou_threshold
        self.name_sim_threshold = name_sim_threshold

    def calculate_iou(self, bbox1: List[float], bbox2: List[float]) -> float:
        """
        Calculate IoU between two bboxes [x_min, y_min, x_max, y_max].
        """
        if not bbox1 or not bbox2 or len(bbox1) != 4 or len(bbox2) != 4:
            return 0.0
            
        x_left = max(bbox1[0], bbox2[0])
        y_top = max(bbox1[1], bbox2[1])
        x_right = min(bbox1[2], bbox2[2])
        y_bottom = min(bbox1[3], bbox2[3])

        if x_right < x_left or y_bottom < y_top:
            return 0.0

        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
        area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
        
        union_area = area1 + area2 - intersection_area
        if union_area <= 0:
            return 0.0
            
        return intersection_area / union_area

    def normalize_price(self, price: str) -> str:
        """
        Normalize price string: 
        - Remove currency symbols
        - Replace ',' with '.'
        - Strip whitespace
        Example: "€1,99" -> "1.99"
        """
        if not price:
            return ""
        # Basic cleanup
        p = str(price).replace("€", "").replace("$", "").replace("je", "").strip()
        p = p.replace(",", ".")
        # Keep only digits and dots
        # filter(lambda x: x.isdigit() or x == '.', p) ... simplified:
        return p

    def levenshtein_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate normalized Levenshtein similarity (0 to 1).
        1.0 means exact match.
        """
        if not s1 and not s2:
            return 1.0
        if not s1 or not s2:
            return 0.0

        s1 = s1.lower().strip()
        s2 = s2.lower().strip()
        
        if s1 == s2:
            return 1.0

        len1, len2 = len(s1), len(s2)
        matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]

        for i in range(len1 + 1):
            matrix[i][0] = i
        for j in range(len2 + 1):
            matrix[0][j] = j

        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                cost = 0 if s1[i - 1] == s2[j - 1] else 1
                matrix[i][j] = min(
                    matrix[i - 1][j] + 1,      # deletion
                    matrix[i][j - 1] + 1,      # insertion
                    matrix[i - 1][j - 1] + cost # substitution
                )
        
        dist = matrix[len1][len2]
        max_len = max(len1, len2)
        if max_len == 0:
            return 1.0
            
        return 1.0 - (dist / max_len)

    def evaluate_page(self, predictions: List[Dict[str, Any]], ground_truth: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate a single page's predictions using global greedy matching.
        """
        # 1. Calculate all pairwise IoUs
        # List of tuples: (iou, pred_idx, gt_idx)
        candidates = []
        for p_idx, pred in enumerate(predictions):
            for g_idx, gt in enumerate(ground_truth):
                iou = self.calculate_iou(pred.get("bbox"), gt.get("bbox"))
                if iou > self.iou_threshold:
                    candidates.append((iou, p_idx, g_idx))
        
        # 2. Sort candidates by IoU descending (Greedy approach)
        candidates.sort(key=lambda x: x[0], reverse=True)
        
        matched_preds: Set[int] = set()
        matched_gts: Set[int] = set()
        matches = [] # List of (pred, gt)
        
        # 3. Assign matches
        for iou, p_idx, g_idx in candidates:
            if p_idx not in matched_preds and g_idx not in matched_gts:
                matched_preds.add(p_idx)
                matched_gts.add(g_idx)
                matches.append((predictions[p_idx], ground_truth[g_idx]))

        # 4. Metrics Calculation
        tp = len(matches)
        fp = len(predictions) - len(matched_preds)
        fn = len(ground_truth) - len(matched_gts)
        
        # Field Evaluation for Matched Pairs
        field_correct_counts = {
            "price": 0,
            "product_name": 0,
            "unit": 0,
            "e2e": 0 # IoU + Price + Name
        }
        
        for pred, gt in matches:
            # Price Accuracy (Exact normalized match)
            p_price = self.normalize_price(pred.get("price"))
            g_price = self.normalize_price(gt.get("price"))
            price_ok = (p_price == g_price)
            if price_ok:
                field_correct_counts["price"] += 1
                
            # Name Accuracy (Fuzzy match)
            name_sim = self.levenshtein_similarity(pred.get("product_name", ""), gt.get("product_name", ""))
            name_ok = (name_sim >= self.name_sim_threshold)
            if name_ok:
                field_correct_counts["product_name"] += 1
                
            # Unit Accuracy (Using fuzzy for now as units can be messy)
            unit_sim = self.levenshtein_similarity(pred.get("unit", ""), gt.get("unit", ""))
            if unit_sim >= 0.8: # Slightly lower threshold for units logic
                field_correct_counts["unit"] += 1

            # End-to-End Metric: Location (implied by match) + Price + Name
            if price_ok and name_ok:
                field_correct_counts["e2e"] += 1

        return {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "field_matches": tp, # The denominator for field accuracy
            "field_correct": field_correct_counts
        }

    def aggregate_results(self, all_page_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregates results from multiple pages.
        """
        total_tp = sum(res["tp"] for res in all_page_results)
        total_fp = sum(res["fp"] for res in all_page_results)
        total_fn = sum(res["fn"] for res in all_page_results)
        total_matched = sum(res["field_matches"] for res in all_page_results)
        
        # Detection Metrics
        det_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        det_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        det_f1 = 2 * (det_precision * det_recall) / (det_precision + det_recall) if (det_precision + det_recall) > 0 else 0
        
        # Field Level Metrics (Accuracy over Matched Pairs)
        field_metrics = {}
        for key in ["price", "product_name", "unit"]:
            correct = sum(res["field_correct"][key] for res in all_page_results)
            # Accuracy is usually defined relative to the number of correctly detected objects
            # i.e., "Of the objects we found, how many had correct prices?"
            acc = correct / total_matched if total_matched > 0 else 0
            field_metrics[key] = round(acc, 4)
            
        # End-to-End Metric (Relative to Total Ground Truth)
        # E2E Recall = (Correct detections with correct content) / Total GT
        # This is a strict standard: you missed it if you didn't extract it perfectly.
        total_e2e_correct = sum(res["field_correct"]["e2e"] for res in all_page_results)
        total_gt = total_tp + total_fn
        e2e_score = total_e2e_correct / total_gt if total_gt > 0 else 0
        
        # Latency Aggregation
        latencies = [res.get("latency", 0) for res in all_page_results if "latency" in res]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
                
        return {
            "detection": {
                "precision": round(det_precision, 4),
                "recall": round(det_recall, 4),
                "f1": round(det_f1, 4)
            },
            "field_accuracy_on_matches": field_metrics,
            "end_to_end_recall": round(e2e_score, 4),
            "avg_latency": round(avg_latency, 2),
            "total_gt": total_gt,
            "total_predictions": total_tp + total_fp
        }
