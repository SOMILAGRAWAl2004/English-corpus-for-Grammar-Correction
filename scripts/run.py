"""
Main Runner Script for English Grammar Correction Corpus
Run the complete pipeline or individual steps
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import DATA_DIR, PROCESSED_DATA_DIR, FINAL_DATA_DIR


def print_banner():
    """Print welcome banner"""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║     🔤 ENGLISH GRAMMAR CORRECTION CORPUS GENERATOR 🔤               ║
║                                                                      ║
║     A comprehensive toolkit for building grammar correction          ║
║     datasets from multiple sources                                   ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """)


def run_download():
    """Run dataset download"""
    print("\n" + "="*70)
    print("STEP 1: DOWNLOADING EXISTING DATASETS")
    print("="*70)
    
    from scripts.download_datasets import main as download_main
    download_main()


def run_synthetic():
    """Run synthetic data generation"""
    print("\n" + "="*70)
    print("STEP 2: GENERATING SYNTHETIC DATA")
    print("="*70)
    
    from scripts.generate_synthetic import generate_synthetic_corpus
    generate_synthetic_corpus(num_pairs=5000, use_wikipedia=True)


def run_scraping():
    """Run web scraping"""
    print("\n" + "="*70)
    print("STEP 3: SCRAPING WEB DATA")
    print("="*70)
    
    from scripts.scrape_reddit import main as scrape_main
    scrape_main()


def run_processing():
    """Run data processing"""
    print("\n" + "="*70)
    print("STEP 4: PROCESSING AND FINALIZING CORPUS")
    print("="*70)
    
    from scripts.process_data import main as process_main
    process_main()


def run_all():
    """Run the complete pipeline"""
    print_banner()
    
    print("\n🚀 Running complete pipeline...\n")
    
    # Step 1: Download existing datasets
    run_download()
    
    # Step 2: Generate synthetic data
    run_synthetic()
    
    # Step 3: Scrape web data
    run_scraping()
    
    # Step 4: Process and finalize
    run_processing()
    
    # Final summary
    print("\n" + "="*70)
    print("🎉 CORPUS GENERATION COMPLETE!")
    print("="*70)
    
    print(f"""
Your corpus is ready at: {FINAL_DATA_DIR}

Files created:
  📄 train.jsonl     - Training data (80%)
  📄 dev.jsonl       - Development/validation data (10%)
  📄 test.jsonl      - Test data (10%)
  📄 full_corpus.jsonl - Complete corpus
  📄 corpus_statistics.json - Corpus statistics

Next steps:
  1. Review the data quality
  2. Train your grammar correction model
  3. Evaluate on the test set

Suggested models to try:
  - GECToR (https://github.com/grammarly/gector)
  - T5 fine-tuning
  - BART fine-tuning

Good luck with your project! 🎓
    """)


def show_status():
    """Show current status of data collection"""
    print_banner()
    print("\n📊 CORPUS STATUS\n")
    
    files_to_check = {
        "JFLEG (Downloaded)": PROCESSED_DATA_DIR / "jfleg_pairs.jsonl",
        "Synthetic Data": PROCESSED_DATA_DIR / "synthetic_pairs.jsonl",
        "Scraped Data": PROCESSED_DATA_DIR / "scraped_pairs.jsonl",
        "Final Train Set": FINAL_DATA_DIR / "train.jsonl",
        "Final Dev Set": FINAL_DATA_DIR / "dev.jsonl",
        "Final Test Set": FINAL_DATA_DIR / "test.jsonl",
    }
    
    for name, path in files_to_check.items():
        if path.exists():
            # Count lines
            with open(path, 'r', encoding='utf-8') as f:
                count = sum(1 for _ in f)
            print(f"  ✅ {name}: {count} entries")
        else:
            print(f"  ❌ {name}: Not found")
    
    print("\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="English Grammar Correction Corpus Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py --all          # Run complete pipeline
  python run.py --download     # Download existing datasets only
  python run.py --synthetic    # Generate synthetic data only
  python run.py --scrape       # Scrape web data only
  python run.py --process      # Process collected data only
  python run.py --status       # Show current status
        """
    )
    
    parser.add_argument("--all", action="store_true", 
                        help="Run the complete pipeline")
    parser.add_argument("--download", action="store_true",
                        help="Download existing datasets (JFLEG, etc.)")
    parser.add_argument("--synthetic", action="store_true",
                        help="Generate synthetic error data")
    parser.add_argument("--scrape", action="store_true",
                        help="Scrape Reddit and Stack Exchange")
    parser.add_argument("--process", action="store_true",
                        help="Process and finalize corpus")
    parser.add_argument("--status", action="store_true",
                        help="Show current data collection status")
    
    args = parser.parse_args()
    
    # If no arguments, show help
    if not any(vars(args).values()):
        parser.print_help()
        print("\n💡 Tip: Use --status to see current progress, or --all to run everything\n")
        return
    
    if args.status:
        show_status()
        return
    
    if args.all:
        run_all()
        return
    
    # Run individual steps
    if args.download:
        run_download()
    
    if args.synthetic:
        run_synthetic()
    
    if args.scrape:
        run_scraping()
    
    if args.process:
        run_processing()


if __name__ == "__main__":
    main()
