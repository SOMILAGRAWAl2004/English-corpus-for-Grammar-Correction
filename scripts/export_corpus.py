"""
Export Corpus - Export corpus to various formats
Supports: JSON, JSONL, CSV, TSV, and model-specific formats
"""

import os
import sys
import json
import csv
from pathlib import Path
from typing import List, Dict
import argparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import FINAL_DATA_DIR


def load_jsonl(file_path: Path) -> List[Dict]:
    """Load data from JSONL file"""
    entries = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    return entries


def export_to_json(entries: List[Dict], output_path: Path):
    """Export to pretty-printed JSON"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    print(f"✓ Exported to JSON: {output_path}")


def export_to_csv(entries: List[Dict], output_path: Path):
    """Export to CSV format"""
    if not entries:
        return
    
    fieldnames = ['id', 'source', 'target', 'error_types', 'dataset']
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for entry in entries:
            row = {
                'id': entry.get('id', ''),
                'source': entry.get('source', ''),
                'target': entry.get('target', ''),
                'error_types': ','.join(entry.get('error_types', [])),
                'dataset': entry.get('dataset', '')
            }
            writer.writerow(row)
    
    print(f"✓ Exported to CSV: {output_path}")


def export_to_tsv(entries: List[Dict], output_path: Path):
    """Export to TSV format (common for NLP)"""
    with open(output_path, 'w', encoding='utf-8') as f:
        # Header
        f.write("source\ttarget\terror_types\n")
        
        for entry in entries:
            source = entry.get('source', '').replace('\t', ' ')
            target = entry.get('target', '').replace('\t', ' ')
            errors = ','.join(entry.get('error_types', []))
            f.write(f"{source}\t{target}\t{errors}\n")
    
    print(f"✓ Exported to TSV: {output_path}")


def export_to_parallel(entries: List[Dict], output_dir: Path, prefix: str = "corpus"):
    """Export to parallel text format (source and target in separate files)"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    src_file = output_dir / f"{prefix}.src"
    tgt_file = output_dir / f"{prefix}.tgt"
    
    with open(src_file, 'w', encoding='utf-8') as src_f, \
         open(tgt_file, 'w', encoding='utf-8') as tgt_f:
        
        for entry in entries:
            src_f.write(entry.get('source', '') + '\n')
            tgt_f.write(entry.get('target', '') + '\n')
    
    print(f"✓ Exported parallel files:")
    print(f"   Source: {src_file}")
    print(f"   Target: {tgt_file}")


def export_to_fairseq(entries: List[Dict], output_dir: Path):
    """Export in format suitable for Fairseq training"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    splits = {
        'train': [],
        'valid': [],
        'test': []
    }
    
    # Try to load from split files
    for split in splits.keys():
        split_file = FINAL_DATA_DIR / f"{split}.jsonl"
        if split == 'dev':
            split_file = FINAL_DATA_DIR / "dev.jsonl"
        if split_file.exists():
            splits[split] = load_jsonl(split_file)
    
    # If no splits found, use provided entries
    if not any(splits.values()):
        from random import shuffle
        shuffle(entries)
        n = len(entries)
        splits['train'] = entries[:int(n*0.8)]
        splits['valid'] = entries[int(n*0.8):int(n*0.9)]
        splits['test'] = entries[int(n*0.9):]
    
    # Handle dev -> valid renaming
    if not splits['valid'] and 'dev' in splits:
        splits['valid'] = splits.pop('dev')
    
    for split_name, split_entries in splits.items():
        if split_entries:
            src_file = output_dir / f"{split_name}.src"
            tgt_file = output_dir / f"{split_name}.tgt"
            
            with open(src_file, 'w', encoding='utf-8') as src_f, \
                 open(tgt_file, 'w', encoding='utf-8') as tgt_f:
                
                for entry in split_entries:
                    src_f.write(entry.get('source', '') + '\n')
                    tgt_f.write(entry.get('target', '') + '\n')
            
            print(f"✓ {split_name}: {len(split_entries)} pairs")
    
    print(f"\nFairseq format exported to: {output_dir}")


def export_to_huggingface(entries: List[Dict], output_dir: Path):
    """Export in Hugging Face datasets format"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create dataset_dict.json
    dataset_info = {
        "description": "English Grammar Correction Corpus",
        "features": {
            "id": {"dtype": "string"},
            "source": {"dtype": "string"},
            "target": {"dtype": "string"},
            "error_types": {"dtype": "string"}
        },
        "splits": ["train", "validation", "test"]
    }
    
    with open(output_dir / "dataset_info.json", 'w') as f:
        json.dump(dataset_info, f, indent=2)
    
    # Export each split
    splits = ['train', 'dev', 'test']
    
    for split in splits:
        split_file = FINAL_DATA_DIR / f"{split}.jsonl"
        output_split = 'validation' if split == 'dev' else split
        
        if split_file.exists():
            split_entries = load_jsonl(split_file)
            
            # Convert to HF format
            hf_entries = []
            for entry in split_entries:
                hf_entries.append({
                    "id": entry.get("id", ""),
                    "source": entry.get("source", ""),
                    "target": entry.get("target", ""),
                    "error_types": ",".join(entry.get("error_types", []))
                })
            
            output_file = output_dir / f"{output_split}.jsonl"
            with open(output_file, 'w', encoding='utf-8') as f:
                for entry in hf_entries:
                    f.write(json.dumps(entry) + '\n')
            
            print(f"✓ {output_split}: {len(hf_entries)} entries")
    
    print(f"\nHugging Face format exported to: {output_dir}")


def main():
    """Main export function"""
    parser = argparse.ArgumentParser(description="Export corpus to various formats")
    parser.add_argument("--format", type=str, default="all",
                        choices=["json", "csv", "tsv", "parallel", "fairseq", "huggingface", "all"],
                        help="Export format")
    parser.add_argument("--output", type=str, default=None,
                        help="Output directory")
    
    args = parser.parse_args()
    
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║     CORPUS EXPORTER                                                ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    
    # Load corpus
    corpus_file = FINAL_DATA_DIR / "full_corpus.jsonl"
    
    if not corpus_file.exists():
        print(f"⚠ Corpus not found at {corpus_file}")
        print("Run the processing pipeline first: python scripts/run.py --all")
        return
    
    entries = load_jsonl(corpus_file)
    print(f"✓ Loaded {len(entries)} entries from corpus")
    
    # Set output directory
    output_dir = Path(args.output) if args.output else FINAL_DATA_DIR / "exports"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    formats = [args.format] if args.format != "all" else ["json", "csv", "tsv", "parallel", "fairseq", "huggingface"]
    
    print(f"\n📤 Exporting to: {output_dir}\n")
    
    for fmt in formats:
        if fmt == "json":
            export_to_json(entries, output_dir / "corpus.json")
        elif fmt == "csv":
            export_to_csv(entries, output_dir / "corpus.csv")
        elif fmt == "tsv":
            export_to_tsv(entries, output_dir / "corpus.tsv")
        elif fmt == "parallel":
            export_to_parallel(entries, output_dir / "parallel")
        elif fmt == "fairseq":
            export_to_fairseq(entries, output_dir / "fairseq")
        elif fmt == "huggingface":
            export_to_huggingface(entries, output_dir / "huggingface")
    
    print(f"\n✅ Export complete!")
    print(f"Files saved to: {output_dir}")


if __name__ == "__main__":
    main()
