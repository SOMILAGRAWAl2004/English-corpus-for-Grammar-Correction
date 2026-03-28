"""
Download academic and large-scale grammar datasets via HuggingFace
"""

import os
import sys
import json
from pathlib import Path
from tqdm import tqdm

try:
    from datasets import load_dataset
except ImportError:
    print("Please install the datasets library: pip install datasets")
    sys.exit(1)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, HF_TOKEN

def download_academic_dataset(num_pairs=50000):
    """
    Download a subset of Lang-8 grammar correction dataset.
    This is extremely high quality and massive (1 million+ pairs minimum).
    """
    print(f"\n" + "="*60)
    print(f"📥 DOWNLOADING LANG-8 ACADEMIC DATASET - {num_pairs} pairs")
    print("="*60)
    
    output_file = PROCESSED_DATA_DIR / "academic_pairs.jsonl"
    
    try:
        print("Connecting to HuggingFace Hub...")
        dataset = load_dataset("rahuln2002/GED-lang8-cleaned", split="train", streaming=True)
        
        output_data = []
        
        print(f"Downloading and extracting {num_pairs} pairs...")
        for item in tqdm(dataset):
            if len(output_data) >= num_pairs:
                break
            
            # This dataset uses '0' = incorrect sentence, '1' = corrected sentence
            source = str(item.get("0", "")).strip()
            target = str(item.get("1", "")).strip()
                
            if source and target and len(source) > 5 and len(target) > 5:
                if source != target:
                    pair = {
                        "id": f"lang8_{len(output_data):07d}",
                        "source": source,
                        "target": target,
                        "dataset": "lang8"
                    }
                    output_data.append(pair)
                
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in output_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
                
        print(f"✓ Saved {len(output_data)} pairs to {output_file}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to download academic dataset: {e}")
        return False

def main():
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║     ACADEMIC DATASET DOWNLOADER (HUGGINGFACE)              ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Download 50,000 pairs
    download_academic_dataset(num_pairs=50000)
    
    print("\n✅ Academic Dataset script finished!")

if __name__ == "__main__":
    main()
