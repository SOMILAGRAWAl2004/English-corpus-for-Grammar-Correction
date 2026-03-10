"""
Download existing datasets for English Grammar Correction Corpus
Supports: JFLEG, and provides instructions for other datasets
"""

import os
import sys
import requests
from pathlib import Path
from tqdm import tqdm
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import (
    DATASET_URLS, JFLEG_DIR, CONLL_DIR, BEA_DIR, 
    RAW_DATA_DIR, PROCESSED_DATA_DIR
)


def download_file(url: str, save_path: Path, desc: str = None) -> bool:
    """Download a file from URL with progress bar"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(save_path, 'wb') as f:
            if total_size == 0:
                f.write(response.content)
            else:
                with tqdm(total=total_size, unit='iB', unit_scale=True, desc=desc) as pbar:
                    for data in response.iter_content(chunk_size=1024):
                        size = f.write(data)
                        pbar.update(size)
        
        print(f"✓ Downloaded: {save_path.name}")
        return True
        
    except requests.RequestException as e:
        print(f"✗ Failed to download {url}: {e}")
        return False


def download_jfleg():
    """Download JFLEG dataset from GitHub"""
    print("\n" + "="*60)
    print("📥 DOWNLOADING JFLEG DATASET")
    print("="*60)
    
    JFLEG_DIR.mkdir(parents=True, exist_ok=True)
    
    base_url = DATASET_URLS["jfleg"]["base_url"]
    
    files_to_download = [
        ("test/test.src", "test.src"),
        ("test/test.ref0", "test.ref0"),
        ("test/test.ref1", "test.ref1"),
        ("test/test.ref2", "test.ref2"),
        ("test/test.ref3", "test.ref3"),
        ("dev/dev.src", "dev.src"),
        ("dev/dev.ref0", "dev.ref0"),
        ("dev/dev.ref1", "dev.ref1"),
        ("dev/dev.ref2", "dev.ref2"),
        ("dev/dev.ref3", "dev.ref3"),
    ]
    
    success_count = 0
    for remote_path, local_name in files_to_download:
        url = base_url + remote_path
        save_path = JFLEG_DIR / local_name
        
        if save_path.exists():
            print(f"⏩ Already exists: {local_name}")
            success_count += 1
            continue
            
        if download_file(url, save_path, local_name):
            success_count += 1
    
    print(f"\n✓ JFLEG Download complete: {success_count}/{len(files_to_download)} files")
    return success_count == len(files_to_download)


def process_jfleg_to_pairs():
    """Convert JFLEG files to sentence pairs format"""
    print("\n" + "="*60)
    print("🔄 PROCESSING JFLEG TO SENTENCE PAIRS")
    print("="*60)
    
    output_data = []
    
    for split in ["dev", "test"]:
        src_file = JFLEG_DIR / f"{split}.src"
        
        if not src_file.exists():
            print(f"⚠ Source file not found: {src_file}")
            continue
        
        # Read source sentences
        with open(src_file, 'r', encoding='utf-8') as f:
            sources = [line.strip() for line in f.readlines()]
        
        # Read all reference corrections (4 annotators)
        references = []
        for i in range(4):
            ref_file = JFLEG_DIR / f"{split}.ref{i}"
            if ref_file.exists():
                with open(ref_file, 'r', encoding='utf-8') as f:
                    refs = [line.strip() for line in f.readlines()]
                references.append(refs)
        
        # Create sentence pairs
        for idx, source in enumerate(sources):
            # Get all reference corrections for this sentence
            refs = [references[i][idx] for i in range(len(references)) if idx < len(references[i])]
            
            # Use the first reference as the primary correction
            # (you can also store all references)
            if refs:
                pair = {
                    "id": f"jfleg_{split}_{idx:05d}",
                    "source": source,
                    "target": refs[0],
                    "all_references": refs,
                    "split": split,
                    "dataset": "jfleg"
                }
                output_data.append(pair)
    
    # Save processed data
    output_file = PROCESSED_DATA_DIR / "jfleg_pairs.jsonl"
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in output_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"✓ Processed {len(output_data)} sentence pairs")
    print(f"✓ Saved to: {output_file}")
    
    # Print statistics
    dev_count = sum(1 for item in output_data if item["split"] == "dev")
    test_count = sum(1 for item in output_data if item["split"] == "test")
    print(f"\n📊 Statistics:")
    print(f"   Dev set:  {dev_count} pairs")
    print(f"   Test set: {test_count} pairs")
    print(f"   Total:    {len(output_data)} pairs")
    
    return output_data


def print_manual_download_instructions():
    """Print instructions for datasets requiring manual download"""
    print("\n" + "="*60)
    print("📋 MANUAL DOWNLOAD REQUIRED FOR OTHER DATASETS")
    print("="*60)
    
    instructions = """
┌─────────────────────────────────────────────────────────────────────┐
│                        CoNLL-2014 DATASET                           │
├─────────────────────────────────────────────────────────────────────┤
│ 1. Visit: https://www.comp.nus.edu.sg/~nlp/conll14st.html          │
│ 2. Fill out the data request form                                  │
│ 3. Wait for approval email (usually 1-2 days)                      │
│ 4. Download and extract to: data/raw/conll2014/                    │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    BEA-2019 W&I+LOCNESS DATASET                     │
├─────────────────────────────────────────────────────────────────────┤
│ 1. Visit: https://www.cl.cam.ac.uk/research/nl/bea2019st/          │
│ 2. Register for CodaLab account if needed                          │
│ 3. Download the W&I+LOCNESS dataset                                │
│ 4. Extract to: data/raw/bea2019/                                   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         Lang-8 CORPUS                               │
├─────────────────────────────────────────────────────────────────────┤
│ Option 1 - NAIST Lang-8 Learner Corpora:                           │
│   https://sites.google.com/site/naaborlowweng/                      │
│                                                                     │
│ Option 2 - Lang-8 Extractor (GitHub):                              │
│   https://github.com/tomo-wb/Lang8-NAIST-extractor                 │
│                                                                     │
│ Extract to: data/raw/lang8/                                        │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                       FCE DATASET (Cambridge)                       │
├─────────────────────────────────────────────────────────────────────┤
│ 1. Visit: https://ilexir.co.uk/datasets/index.html                 │
│ 2. Request access to FCE dataset                                   │
│ 3. Download and extract to: data/raw/fce/                          │
└─────────────────────────────────────────────────────────────────────┘
"""
    print(instructions)


def main():
    """Main function to run all downloads"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║     ENGLISH GRAMMAR CORPUS - DATASET DOWNLOADER            ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    # Download JFLEG (automatic)
    if download_jfleg():
        process_jfleg_to_pairs()
    
    # Print instructions for manual downloads
    print_manual_download_instructions()
    
    print("\n" + "="*60)
    print("✅ DOWNLOAD SCRIPT COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("1. Manually download datasets listed above")
    print("2. Run: python scripts/generate_synthetic.py")
    print("3. Run: python scripts/scrape_reddit.py")
    print("4. Run: python scripts/process_data.py")


if __name__ == "__main__":
    main()
