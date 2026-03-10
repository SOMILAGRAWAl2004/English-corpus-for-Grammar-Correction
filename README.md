# English Grammar Correction Corpus

A comprehensive toolkit for building an English grammar correction corpus from multiple sources including existing datasets, synthetic generation, and web scraping.

## 📁 Project Structure

```
English Corpus/
├── config/
│   ├── config.py           # Main configuration file
│   ├── error_types.json    # Error taxonomy (15 categories)
│   └── __init__.py
│
├── data/
│   ├── raw/                # Original downloaded/scraped data
│   │   ├── jfleg/          # JFLEG dataset
│   │   ├── conll2014/      # CoNLL-2014 (manual download)
│   │   ├── bea2019/        # BEA-2019 (manual download)
│   │   ├── lang8/          # Lang-8 (manual download)
│   │   ├── synthetic/      # Generated synthetic errors
│   │   └── scraped/        # Web scraped data
│   │
│   ├── processed/          # Cleaned and processed data
│   │   ├── jfleg_pairs.jsonl
│   │   ├── synthetic_pairs.jsonl
│   │   └── scraped_pairs.jsonl
│   │
│   └── final/              # Final train/dev/test splits
│       ├── train.jsonl
│       ├── dev.jsonl
│       ├── test.jsonl
│       ├── full_corpus.jsonl
│       └── corpus_statistics.json
│
├── scripts/
│   ├── download_datasets.py   # Download JFLEG and instructions for others
│   ├── generate_synthetic.py  # Generate synthetic errors
│   ├── scrape_reddit.py       # Scrape Reddit & Stack Exchange
│   ├── process_data.py        # Clean, validate, and split data
│   └── run.py                 # Main runner script
│
├── requirements.txt        # Python dependencies
├── .env.example           # Example environment variables
└── README.md              # This file
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd "c:\Users\Somil\OneDrive\Desktop\English Corpus"
pip install -r requirements.txt
```

### 2. Run the Complete Pipeline

```bash
python scripts/run.py --all
```

Or run individual steps:

```bash
# Step 1: Download existing datasets
python scripts/run.py --download

# Step 2: Generate synthetic data
python scripts/run.py --synthetic

# Step 3: Scrape web data (requires Reddit API keys)
python scripts/run.py --scrape

# Step 4: Process and create final corpus
python scripts/run.py --process

# Check status
python scripts/run.py --status
```

## 📊 Data Sources

### Automatic Downloads
| Dataset | Size | Description |
|---------|------|-------------|
| JFLEG | 2,265 pairs | Fluency-focused corrections |

### Manual Downloads Required
| Dataset | Size | Instructions |
|---------|------|--------------|
| CoNLL-2014 | 1,312 essays | [Request access](https://www.comp.nus.edu.sg/~nlp/conll14st.html) |
| BEA-2019 | 34,308 pairs | [Register](https://www.cl.cam.ac.uk/research/nl/bea2019st/) |
| Lang-8 | 100,000+ | [NAIST Extractor](https://github.com/tomo-wb/Lang8-NAIST-extractor) |
| FCE | 1,244 essays | [Request access](https://ilexir.co.uk/datasets/index.html) |

### Synthetic Generation
- Wikipedia articles
- News articles
- Project Gutenberg books
- Controlled error injection (SVA, articles, tense, spelling, etc.)

### Web Scraping (Optional)
- Reddit: r/EnglishLearning, r/grammar, r/IELTS
- Stack Exchange: English Language Learners

## 🏷️ Error Types

The corpus uses 15 error categories:

| Code | Error Type | Example |
|------|------------|---------|
| SPE | Spelling | recieve → receive |
| SVA | Subject-Verb Agreement | She go → She goes |
| ART | Article | I saw elephant → I saw an elephant |
| TENSE | Verb Tense | I see him yesterday → I saw him yesterday |
| VFORM | Verb Form | I enjoy to swim → I enjoy swimming |
| PREP | Preposition | interested for → interested in |
| PRON | Pronoun | Me and him → He and I |
| WO | Word Order | I always am → I am always |
| PUNCT | Punctuation | Lets go → Let's go |
| NOUN | Noun Number | many informations → a lot of information |
| WC | Word Choice | I made homework → I did homework |
| MW | Missing Word | I am student → I am a student |
| UW | Unnecessary Word | returned back → returned |
| CAP | Capitalization | i went to london → I went to London |
| OTHER | Other | Miscellaneous errors |

## 📄 Data Format

Each entry in the corpus follows this JSON format:

```json
{
  "id": "synthetic_000001",
  "source": "She go to school everyday.",
  "target": "She goes to school every day.",
  "error_types": ["SVA", "SPE"],
  "edits": [
    {"original": "go", "replacement": "goes", "type": "SVA"},
    {"original": "everyday", "replacement": "every day", "type": "SPE"}
  ],
  "dataset": "synthetic"
}
```

## ⚙️ Configuration

### Reddit API Setup (Optional)

1. Go to [Reddit Apps](https://www.reddit.com/prefs/apps)
2. Create a new "script" application
3. Copy credentials to `.env`:

```bash
cp .env.example .env
# Edit .env with your credentials
```

### Customizing Error Generation

Edit `config/config.py` to adjust:
- Error injection rate
- Error type distribution
- Sentence length limits
- Train/dev/test split ratios

## 📈 Expected Output

After running the complete pipeline:

| Split | Approximate Size |
|-------|-----------------|
| Train | ~10,000+ pairs |
| Dev | ~1,250 pairs |
| Test | ~1,250 pairs |

*Actual size depends on data sources used*

## 🔬 Next Steps

After building your corpus:

1. **Train a model**: Use GECToR, T5, or BART
2. **Evaluate**: Use ERRANT, M² scorer, or GLEU
3. **Iterate**: Add more data, refine error types

## 📚 References

- [JFLEG](https://github.com/keisks/jfleg) - Napoles et al., 2017
- [CoNLL-2014](https://www.comp.nus.edu.sg/~nlp/conll14st.html) - Ng et al., 2014
- [BEA-2019](https://www.cl.cam.ac.uk/research/nl/bea2019st/) - Bryant et al., 2019
- [ERRANT](https://github.com/chrisjbryant/errant) - Error Annotation Toolkit
- [GECToR](https://github.com/grammarly/gector) - Grammar Error Correction

## 📝 License

This project is for educational purposes. Individual datasets have their own licenses - please check before use in production.

---

Built with ❤️ for grammar correction research
