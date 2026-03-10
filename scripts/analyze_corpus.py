"""
Corpus Analyzer - Analyze and visualize corpus statistics
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict
from collections import Counter

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import FINAL_DATA_DIR, PROCESSED_DATA_DIR


def load_corpus(file_path: Path) -> List[Dict]:
    """Load corpus from JSONL file"""
    entries = []
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
    return entries


def analyze_corpus(entries: List[Dict]) -> Dict:
    """Perform detailed corpus analysis"""
    
    if not entries:
        return {"error": "No entries to analyze"}
    
    # Basic stats
    total = len(entries)
    
    # Error type analysis
    error_types = Counter()
    error_combinations = Counter()
    for entry in entries:
        types = entry.get("error_types", [])
        for t in types:
            error_types[t] += 1
        # Count combinations
        combo = tuple(sorted(set(types)))
        error_combinations[combo] += 1
    
    # Length analysis
    source_lengths = [len(e.get("source", "").split()) for e in entries]
    target_lengths = [len(e.get("target", "").split()) for e in entries]
    
    # Dataset distribution
    datasets = Counter(e.get("dataset", "unknown") for e in entries)
    
    # Character-level analysis
    source_chars = [len(e.get("source", "")) for e in entries]
    target_chars = [len(e.get("target", "")) for e in entries]
    
    return {
        "total_entries": total,
        "error_type_counts": dict(error_types.most_common()),
        "top_error_combinations": dict(error_combinations.most_common(10)),
        "dataset_distribution": dict(datasets),
        "length_stats": {
            "source_words": {
                "min": min(source_lengths),
                "max": max(source_lengths),
                "avg": sum(source_lengths) / len(source_lengths)
            },
            "target_words": {
                "min": min(target_lengths),
                "max": max(target_lengths),
                "avg": sum(target_lengths) / len(target_lengths)
            },
            "source_chars": {
                "min": min(source_chars),
                "max": max(source_chars),
                "avg": sum(source_chars) / len(source_chars)
            },
            "target_chars": {
                "min": min(target_chars),
                "max": max(target_chars),
                "avg": sum(target_chars) / len(target_chars)
            }
        }
    }


def print_analysis(analysis: Dict):
    """Print analysis in a formatted way"""
    
    print("\n" + "="*70)
    print("📊 CORPUS ANALYSIS REPORT")
    print("="*70)
    
    print(f"\n📝 Total Entries: {analysis['total_entries']}")
    
    print("\n🏷️ Error Type Distribution:")
    for error_type, count in analysis['error_type_counts'].items():
        pct = (count / analysis['total_entries']) * 100
        bar = "█" * int(pct / 2)
        print(f"   {error_type:10} {count:6} ({pct:5.1f}%) {bar}")
    
    print("\n📂 Dataset Distribution:")
    for dataset, count in analysis['dataset_distribution'].items():
        pct = (count / analysis['total_entries']) * 100
        print(f"   {dataset:20} {count:6} ({pct:5.1f}%)")
    
    print("\n📏 Length Statistics:")
    stats = analysis['length_stats']
    print(f"   Source (words): min={stats['source_words']['min']}, "
          f"max={stats['source_words']['max']}, "
          f"avg={stats['source_words']['avg']:.1f}")
    print(f"   Target (words): min={stats['target_words']['min']}, "
          f"max={stats['target_words']['max']}, "
          f"avg={stats['target_words']['avg']:.1f}")
    
    print("\n🔗 Top Error Combinations:")
    for combo, count in list(analysis['top_error_combinations'].items())[:5]:
        combo_str = " + ".join(combo) if combo else "None"
        pct = (count / analysis['total_entries']) * 100
        print(f"   {combo_str:30} {count:5} ({pct:4.1f}%)")
    
    print("\n" + "="*70)


def show_samples(entries: List[Dict], n: int = 5):
    """Show sample entries from the corpus"""
    
    print("\n" + "="*70)
    print("📝 SAMPLE ENTRIES")
    print("="*70)
    
    import random
    samples = random.sample(entries, min(n, len(entries)))
    
    for i, entry in enumerate(samples, 1):
        print(f"\n--- Sample {i} ---")
        print(f"ID: {entry.get('id', 'N/A')}")
        print(f"Source: {entry.get('source', 'N/A')}")
        print(f"Target: {entry.get('target', 'N/A')}")
        print(f"Errors: {', '.join(entry.get('error_types', ['N/A']))}")
        print(f"Dataset: {entry.get('dataset', 'N/A')}")


def main():
    """Main analysis function"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║     CORPUS ANALYZER                                                ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    
    # Try to load final corpus first
    corpus_file = FINAL_DATA_DIR / "full_corpus.jsonl"
    
    if not corpus_file.exists():
        # Try processed files
        all_entries = []
        for file_name in ["jfleg_pairs.jsonl", "synthetic_pairs.jsonl", "scraped_pairs.jsonl"]:
            file_path = PROCESSED_DATA_DIR / file_name
            if file_path.exists():
                entries = load_corpus(file_path)
                all_entries.extend(entries)
                print(f"✓ Loaded {len(entries)} from {file_name}")
        
        if not all_entries:
            print("\n⚠ No corpus data found. Run the data collection scripts first:")
            print("   python scripts/run.py --all")
            return
        
        entries = all_entries
    else:
        print(f"✓ Loading from {corpus_file}")
        entries = load_corpus(corpus_file)
    
    # Analyze
    analysis = analyze_corpus(entries)
    print_analysis(analysis)
    
    # Show samples
    show_samples(entries, n=5)
    
    # Save analysis
    output_file = FINAL_DATA_DIR / "detailed_analysis.json"
    FINAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Convert tuples to strings for JSON
    analysis_json = analysis.copy()
    analysis_json["top_error_combinations"] = {
        " + ".join(k): v for k, v in analysis["top_error_combinations"].items()
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_json, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Detailed analysis saved to: {output_file}")


if __name__ == "__main__":
    main()
