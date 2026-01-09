import os
import json
import argparse
import time
from typing import List, Dict, Any
from benchmark.data_loader import DataLoader
from benchmark.models import (
    GeminiModel, PaddleOCRModel, QwenOCRModel, DeepSeekOCRModel, 
    MockModel, GotOCRModel, Florence2Model, InternVL2Model
)
from benchmark.evaluator import Evaluator

def main():
    parser = argparse.ArgumentParser(description="Run Supermarket Brochure Data Extraction Benchmark")
    parser.add_argument("--limit", type=int, default=5, help="Limit number of images per chain for testing")
    parser.add_argument("--chains", type=str, help="Comma-separated list of chains to test (e.g. rewe,aldisued)")
    parser.add_argument("--gemini_api_key", type=str, default="AIzaSyAAYImGiSbT_emoKbCxTolGQ0KDEHBsldU", help="Gemini API Key")
    parser.add_argument("--model_filter", type=str, help="Comma-separated list of models to run (e.g., gemini,qwen)")
    
    args = parser.parse_args()

    # Initialize data
    base_data_dir = os.path.join(os.getcwd(), "data")
    loader = DataLoader(base_data_dir)
    available_chains = loader.get_available_chains()
    
    target_chains = args.chains.split(",") if args.chains else available_chains
    
    # Initialize models
    all_models = [
        GeminiModel(args.gemini_api_key, model_id="gemini-3-pro-preview"),
        GeminiModel(args.gemini_api_key, model_id="gemini-3-flash-preview"),
        GeminiModel(args.gemini_api_key, model_id="gemini-2.5-pro"),
        GeminiModel(args.gemini_api_key, model_id="gemini-2.5-flash"),
        GeminiModel(args.gemini_api_key, model_id="gemini-2.5-flash-lite"),
        PaddleOCRModel(),
        QwenOCRModel(),
        DeepSeekOCRModel(),
        GotOCRModel(),
        Florence2Model(),
        InternVL2Model()
    ]

    # Filter models if requested
    if args.model_filter:
        filters = [f.lower().strip() for f in args.model_filter.split(",")]
        models = [m for m in all_models if any(f in m.model_name.lower() for f in filters)]
    else:
        models = all_models

    evaluator = Evaluator(iou_threshold=0.3, name_sim_threshold=0.85)
    
    overall_report = {}

    print(f"\n{'='*80}")
    print(f"BENCHMARK START - IoU=0.5, NameSim=0.85")
    print(f"{'='*80}")

    for model in models:
        print(f"\n>>> Benchmarking Model: {model.model_name}")
        model_page_results = []
        
        for chain in target_chains:
            if chain not in available_chains:
                continue
                
            chain_data = loader.load_chain_data(chain)
            if args.limit:
                chain_data = chain_data[:args.limit]
            
            print(f"  Processing {len(chain_data)} images from {chain}...")
            
            for item in chain_data:
                image_path = item["image_path"]
                gt = item["ground_truth"]
                
                # Inference with latency tracking
                start_time = time.time()
                predictions = model.extract_deals(image_path)
                latency = time.time() - start_time
                
                # Evaluation
                page_result = evaluator.evaluate_page(predictions, gt)
                page_result["latency"] = latency
                model_page_results.append(page_result)
        
        # Aggregate
        if model_page_results:
            summary = evaluator.aggregate_results(model_page_results)
            overall_report[model.model_name] = summary
            
            det = summary['detection']
            fields = summary['field_accuracy_on_matches']
            e2e = summary['end_to_end_recall']
            
            print(f"  Results for {model.model_name}:")
            print(f"    Detection -> F1: {det['f1']:.3f} | Prec: {det['precision']:.3f} | Rec: {det['recall']:.3f}")
            print(f"    Fields    -> Name: {fields['product_name']:.3f} | Price: {fields['price']:.3f} | Unit: {fields['unit']:.3f}")
            print(f"    End-to-End-> Recall: {e2e:.3f} (Correct Box + Name + Price)")
        else:
            print(f"  No results for {model.model_name}")

    # Final Report Output
    print("\n" + "="*80)
    print("FINAL BENCHMARK REPORT")
    print("="*80)
    # Header
    print(f"{'Model':<20} | {'Det F1':<8} | {'E2E Rec':<8} | {'Price Acc':<10} | {'Name Acc':<10} | {'Latency(s)':<10}")
    print("-" * 105)
    
    for model_name, results in overall_report.items():
        det_f1 = results['detection']['f1']
        e2e = results['end_to_end_recall']
        price_acc = results['field_accuracy_on_matches'].get('price', 0)
        name_acc = results['field_accuracy_on_matches'].get('product_name', 0)
        avg_latency = results.get('avg_latency', 0)
        
        print(f"{model_name:<20} | {det_f1:<8.3f} | {e2e:<8.3f} | {price_acc:<10.3f} | {name_acc:<10.3f} | {avg_latency:<10.2f}")
    
    # Save to file
    with open("benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(overall_report, f, indent=2)
    print("\nDetailed results saved to benchmark_results.json")

if __name__ == "__main__":
    main()
