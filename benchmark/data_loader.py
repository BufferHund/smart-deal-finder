import os
import json
import glob
from typing import List, Dict, Any, Optional

class DataLoader:
    """
    Loads supermarket brochure images and their corresponding ground truth annotations.
    """
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.image_uniform_dir = os.path.join(base_dir, "images_uniform")
        
    def get_available_chains(self) -> List[str]:
        """Returns a list of supermarket chains that have annotated data."""
        chains = []
        if not os.path.exists(self.image_uniform_dir):
            return chains
            
        for entry in os.listdir(self.image_uniform_dir):
            if os.path.isdir(os.path.join(self.image_uniform_dir, entry)) and not entry.endswith("_annotated"):
                ann_dir = os.path.join(self.image_uniform_dir, f"{entry}_annotated")
                if os.path.exists(ann_dir):
                    chains.append(entry)
        return chains

    def load_chain_data(self, chain: str) -> List[Dict[str, Any]]:
        """
        Loads all images and annotations for a specific chain.
        Returns a list of dicts: {"image_path": str, "ground_truth": List[Dict]}
        """
        image_dir = os.path.join(self.image_uniform_dir, chain)
        ann_dir = os.path.join(self.image_uniform_dir, f"{chain}_annotated")
        
        data = []
        if not os.path.exists(image_dir) or not os.path.exists(ann_dir):
            return data
            
        # Look for JSON files in the annotated directory
        ann_files = glob.glob(os.path.join(ann_dir, "*.json"))
        
        for ann_file in ann_files:
            # The annotation file name usually matches the image name (with .json instead of .png)
            base_name = os.path.basename(ann_file).replace(".json", "")
            image_path = os.path.join(image_dir, f"{base_name}.png")
            
            if os.path.exists(image_path):
                with open(ann_file, "r", encoding="utf-8") as f:
                    try:
                        gt = json.load(f)
                        data.append({
                            "image_path": image_path,
                            "ground_truth": gt,
                            "chain": chain,
                            "filename": base_name
                        })
                    except json.JSONDecodeError:
                        print(f"Warning: Failed to decode JSON from {ann_file}")
                        
        return data

    def load_all_data(self) -> List[Dict[str, Any]]:
        """Loads data from all available chains."""
        all_data = []
        for chain in self.get_available_chains():
            all_data.extend(self.load_chain_data(chain))
        return all_data

if __name__ == "__main__":
    # Test the data loader
    loader = DataLoader(r"c:\Users\zack\Downloads\smart-deal-finder\data")
    chains = loader.get_available_chains()
    print(f"Available chains: {chains}")
    for chain in chains:
        chain_data = loader.load_chain_data(chain)
        print(f"Loaded {len(chain_data)} samples for {chain}")
