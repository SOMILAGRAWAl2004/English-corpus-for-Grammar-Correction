"""
Data Processing Pipeline for English Grammar Correction Corpus
Cleans, validates, and standardizes all collected data
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Set
from collections import Counter
from tqdm import tqdm

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import (
    PROCESSED_DATA_DIR, FINAL_DATA_DIR, 
    QUALITY_CONFIG, SPLIT_RATIOS
)


class DataCleaner:
    """Clean and validate corpus entries"""
    
    def __init__(self):
        self.config = QUALITY_CONFIG
        self.seen_pairs: Set[str] = set()
        self.stats = {
            "total_input": 0,
            "valid": 0,
            "removed_duplicates": 0,
            "removed_too_short": 0,
            "removed_too_long": 0,
            "removed_no_difference": 0,
            "removed_invalid": 0
        }
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        # Remove excessive punctuation
        text = re.sub(r'([.!?]){2,}', r'\1', text)
        
        return text
    
    def is_valid_entry(self, entry: Dict) -> bool:
        """Check if entry meets quality criteria"""
        source = entry.get("source", "")
        target = entry.get("target", "")
        
        if not source or not target:
            return False
        
        source_words = source.split()
        target_words = target.split()
        
        # Check minimum word count
        if len(source_words) < self.config["min_word_count"]:
            self.stats["removed_too_short"] += 1
            return False
        
        if len(target_words) < self.config["min_word_count"]:
            self.stats["removed_too_short"] += 1
            return False
        
        # Check maximum word count
        if len(source_words) > self.config["max_word_count"]:
            self.stats["removed_too_long"] += 1
            return False
        
        if len(target_words) > self.config["max_word_count"]:
            self.stats["removed_too_long"] += 1
            return False
        
        # Check that source and target are different
        if self.config["require_correction_difference"]:
            if source.lower().strip() == target.lower().strip():
                self.stats["removed_no_difference"] += 1
                return False
        
        return True
    
    def is_duplicate(self, entry: Dict) -> bool:
        """Check if this entry is a duplicate"""
        # Create a normalized key from source and target
        source = entry.get("source", "").lower().strip()
        target = entry.get("target", "").lower().strip()
        key = f"{source}|||{target}"
        
        if key in self.seen_pairs:
            self.stats["removed_duplicates"] += 1
            return True
        
        self.seen_pairs.add(key)
        return False
    
    def process_entry(self, entry: Dict) -> Optional[Dict]:
        """Process a single entry"""
        self.stats["total_input"] += 1
        
        # Clean text
        entry["source"] = self.clean_text(entry.get("source", ""))
        entry["target"] = self.clean_text(entry.get("target", ""))
        
        # Validate
        if not self.is_valid_entry(entry):
            return None
        
        # Check duplicates
        if self.is_duplicate(entry):
            return None
        
        self.stats["valid"] += 1
        return entry
    
    def process_file(self, input_file: Path) -> List[Dict]:
        """Process all entries from a file"""
        entries = []
        
        if not input_file.exists():
            print(f"⚠ File not found: {input_file}")
            return entries
        
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    entry = json.loads(line)
                    processed = self.process_entry(entry)
                    if processed:
                        entries.append(processed)
                except json.JSONDecodeError:
                    self.stats["removed_invalid"] += 1
                    continue
        
        return entries
    
    def print_stats(self):
        """Print processing statistics"""
        print("\n📊 Processing Statistics:")
        print(f"   Total input:        {self.stats['total_input']}")
        print(f"   Valid entries:      {self.stats['valid']}")
        print(f"   Removed duplicates: {self.stats['removed_duplicates']}")
        print(f"   Removed too short:  {self.stats['removed_too_short']}")
        print(f"   Removed too long:   {self.stats['removed_too_long']}")
        print(f"   Removed no diff:    {self.stats['removed_no_difference']}")
        print(f"   Removed invalid:    {self.stats['removed_invalid']}")


class CorpusStatistics:
    """Generate statistics for the corpus"""
    
    @staticmethod
    def calculate_stats(entries: List[Dict]) -> Dict:
        """Calculate corpus statistics"""
        stats = {
            "total_pairs": len(entries),
            "avg_source_length": 0,
            "avg_target_length": 0,
            "error_type_distribution": {},
            "dataset_distribution": {},
            "sentence_length_distribution": {}
        }
        
        if not entries:
            return stats
        
        source_lengths = []
        target_lengths = []
        error_types = Counter()
        datasets = Counter()
        length_buckets = Counter()
        
        for entry in entries:
            # Length statistics
            source_words = len(entry.get("source", "").split())
            target_words = len(entry.get("target", "").split())
            source_lengths.append(source_words)
            target_lengths.append(target_words)
            
            # Length buckets
            bucket = (source_words // 10) * 10
            bucket_label = f"{bucket}-{bucket+9} words"
            length_buckets[bucket_label] += 1
            
            # Error types
            for error_type in entry.get("error_types", ["UNKNOWN"]):
                error_types[error_type] += 1
            
            # Datasets
            dataset = entry.get("dataset", "unknown")
            datasets[dataset] += 1
        
        stats["avg_source_length"] = sum(source_lengths) / len(source_lengths)
        stats["avg_target_length"] = sum(target_lengths) / len(target_lengths)
        stats["error_type_distribution"] = dict(error_types.most_common())
        stats["dataset_distribution"] = dict(datasets.most_common())
        stats["sentence_length_distribution"] = dict(sorted(length_buckets.items()))
        
        return stats
    
    @staticmethod
    def print_stats(stats: Dict):
        """Print statistics in a nice format"""
        print("\n" + "="*60)
        print("📊 CORPUS STATISTICS")
        print("="*60)
        
        print(f"\n📝 Size:")
        print(f"   Total sentence pairs: {stats['total_pairs']}")
        print(f"   Avg source length: {stats['avg_source_length']:.1f} words")
        print(f"   Avg target length: {stats['avg_target_length']:.1f} words")
        
        print(f"\n🏷️ Error Type Distribution:")
        for error_type, count in stats['error_type_distribution'].items():
            pct = (count / stats['total_pairs']) * 100
            print(f"   {error_type}: {count} ({pct:.1f}%)")
        
        print(f"\n📂 Dataset Distribution:")
        for dataset, count in stats['dataset_distribution'].items():
            pct = (count / stats['total_pairs']) * 100
            print(f"   {dataset}: {count} ({pct:.1f}%)")
        
        print(f"\n📏 Sentence Length Distribution:")
        for bucket, count in stats['sentence_length_distribution'].items():
            pct = (count / stats['total_pairs']) * 100
            print(f"   {bucket}: {count} ({pct:.1f}%)")


class DataSplitter:
    """Split data into train/dev/test sets"""
    
    def __init__(self, ratios: Dict[str, float] = None):
        self.ratios = ratios or SPLIT_RATIOS
    
    def split(self, entries: List[Dict]) -> Dict[str, List[Dict]]:
        """Split entries into train/dev/test"""
        import random
        random.shuffle(entries)
        
        total = len(entries)
        train_size = int(total * self.ratios["train"])
        dev_size = int(total * self.ratios["dev"])
        
        splits = {
            "train": entries[:train_size],
            "dev": entries[train_size:train_size + dev_size],
            "test": entries[train_size + dev_size:]
        }
        
        return splits
    
    def save_splits(self, splits: Dict[str, List[Dict]], output_dir: Path):
        """Save splits to files"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for split_name, entries in splits.items():
            output_file = output_dir / f"{split_name}.jsonl"
            with open(output_file, 'w', encoding='utf-8') as f:
                for entry in entries:
                    f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            
            print(f"✓ Saved {split_name}: {len(entries)} entries -> {output_file}")


def main():
    """Main processing pipeline"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║     DATA PROCESSING PIPELINE                               ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    cleaner = DataCleaner()
    all_entries = []
    
    # Process all data files from processed directory
    print("\n📂 Loading data files...")
    
    data_files = [
        PROCESSED_DATA_DIR / "jfleg_pairs.jsonl",
        PROCESSED_DATA_DIR / "synthetic_pairs.jsonl",
        PROCESSED_DATA_DIR / "stackexchange_pairs.jsonl",
        PROCESSED_DATA_DIR / "academic_pairs.jsonl",
    ]
    
    for data_file in data_files:
        if data_file.exists():
            print(f"\n📄 Processing: {data_file.name}")
            entries = cleaner.process_file(data_file)
            all_entries.extend(entries)
            print(f"   ✓ Loaded {len(entries)} valid entries")
        else:
            print(f"⚠ Not found: {data_file.name}")
    
    cleaner.print_stats()
    
    if not all_entries:
        print("\n⚠ No data to process. Run the data collection scripts first:")
        print("   python scripts/download_datasets.py")
        print("   python scripts/generate_synthetic.py")
        print("   python scripts/scrape_reddit.py")
        return
    
    # Calculate and print statistics
    stats = CorpusStatistics.calculate_stats(all_entries)
    CorpusStatistics.print_stats(stats)
    
    # Split into train/dev/test
    print("\n🔀 Splitting data into train/dev/test...")
    splitter = DataSplitter()
    splits = splitter.split(all_entries)
    
    # Save splits
    print("\n💾 Saving final corpus...")
    splitter.save_splits(splits, FINAL_DATA_DIR)
    
    # Save statistics
    stats_file = FINAL_DATA_DIR / "corpus_statistics.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved statistics to: {stats_file}")
    
    # Save full corpus
    full_corpus_file = FINAL_DATA_DIR / "full_corpus.jsonl"
    with open(full_corpus_file, 'w', encoding='utf-8') as f:
        for entry in all_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    print(f"✓ Saved full corpus to: {full_corpus_file}")
    
    print("\n" + "="*60)
    print("✅ DATA PROCESSING COMPLETE!")
    print("="*60)
    print(f"\nFinal corpus location: {FINAL_DATA_DIR}")
    print(f"Total pairs: {len(all_entries)}")
    print(f"  - Train: {len(splits['train'])}")
    print(f"  - Dev:   {len(splits['dev'])}")
    print(f"  - Test:  {len(splits['test'])}")
    
    return all_entries


if __name__ == "__main__":
    main()
