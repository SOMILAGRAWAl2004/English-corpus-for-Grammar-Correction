"""
Configuration settings for English Grammar Correction Corpus
"""

import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
SCRIPTS_DIR = BASE_DIR / "scripts"
CONFIG_DIR = BASE_DIR / "config"

# Data subdirectories
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
FINAL_DATA_DIR = DATA_DIR / "final"

# Raw data subdirectories
JFLEG_DIR = RAW_DATA_DIR / "jfleg"
CONLL_DIR = RAW_DATA_DIR / "conll2014"
BEA_DIR = RAW_DATA_DIR / "bea2019"
LANG8_DIR = RAW_DATA_DIR / "lang8"
SYNTHETIC_DIR = RAW_DATA_DIR / "synthetic"
SCRAPED_DIR = RAW_DATA_DIR / "scraped"

# Create all directories
for dir_path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, FINAL_DATA_DIR,
                 JFLEG_DIR, CONLL_DIR, BEA_DIR, LANG8_DIR, 
                 SYNTHETIC_DIR, SCRAPED_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Dataset URLs
DATASET_URLS = {
    "jfleg": {
        "base_url": "https://raw.githubusercontent.com/keisks/jfleg/master/",
        "test_src": "test/test.src",
        "test_ref0": "test/test.ref0",
        "test_ref1": "test/test.ref1",
        "test_ref2": "test/test.ref2",
        "test_ref3": "test/test.ref3",
        "dev_src": "dev/dev.src",
        "dev_ref0": "dev/dev.ref0",
        "dev_ref1": "dev/dev.ref1",
        "dev_ref2": "dev/dev.ref2",
        "dev_ref3": "dev/dev.ref3",
    },
    "conll2014": {
        "info_url": "https://www.comp.nus.edu.sg/~nlp/conll14st.html",
        "description": "Requires registration - download manually"
    },
    "bea2019": {
        "info_url": "https://www.cl.cam.ac.uk/research/nl/bea2019st/",
        "description": "Requires registration - download manually"
    }
}

# Synthetic data generation settings
SYNTHETIC_CONFIG = {
    "error_injection_rate": 0.3,  # 30% of sentences will have errors
    "max_errors_per_sentence": 3,
    "min_sentence_length": 5,
    "max_sentence_length": 50,
    "error_type_distribution": {
        "SVA": 0.20,      # Subject-verb agreement
        "ART": 0.18,      # Article errors
        "TENSE": 0.15,    # Tense errors
        "SPE": 0.12,      # Spelling errors
        "PREP": 0.10,     # Preposition errors
        "PUNCT": 0.08,    # Punctuation
        "WO": 0.05,       # Word order
        "NOUN": 0.05,     # Noun number
        "WC": 0.04,       # Word choice
        "OTHER": 0.03    # Other
    }
}

# Web scraping settings
SCRAPING_CONFIG = {
    "reddit": {
        "subreddits": [
            "EnglishLearning",
            "grammar",
            "IELTS",
            "languagelearning",
            "learnEnglish"
        ],
        "posts_per_subreddit": 500,
        "comments_per_post": 50
    },
    "stackexchange": {
        "sites": ["ell", "english"],  # English Language Learners, English Language & Usage
        "questions_per_site": 1000
    }
}

# Reddit API credentials (fill in .env file)
REDDIT_CONFIG = {
    "client_id": os.getenv("REDDIT_CLIENT_ID", ""),
    "client_secret": os.getenv("REDDIT_CLIENT_SECRET", ""),
    "user_agent": os.getenv("REDDIT_USER_AGENT", "GrammarCorpusCollector/1.0")
}

# News API key (fill in .env file)
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

# Output formats
OUTPUT_FORMATS = ["json", "jsonl", "csv", "tsv"]
DEFAULT_OUTPUT_FORMAT = "jsonl"

# Train/Dev/Test split ratios
SPLIT_RATIOS = {
    "train": 0.8,
    "dev": 0.1,
    "test": 0.1
}

# Quality thresholds
QUALITY_CONFIG = {
    "min_word_count": 3,
    "max_word_count": 100,
    "min_error_types": 1,
    "require_correction_difference": True
}
