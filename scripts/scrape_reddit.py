"""
Reddit Scraper for English Grammar Correction Corpus
Scrapes corrections and grammar discussions from language learning subreddits
"""

import os
import sys
import json
import re
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import praw
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False
    print("⚠ PRAW not installed. Run: pip install praw")

from tqdm import tqdm
from dotenv import load_dotenv

from config.config import SCRAPED_DIR, PROCESSED_DATA_DIR, SCRAPING_CONFIG, REDDIT_CONFIG

# Load environment variables
load_dotenv()


@dataclass
class GrammarCorrection:
    """Represents a grammar correction pair from Reddit"""
    id: str
    source: str  # Original incorrect text
    target: str  # Corrected text
    error_types: List[str]
    subreddit: str
    post_id: str
    score: int
    created_utc: float
    dataset: str = "reddit"


class RedditGrammarScraper:
    """Scrape grammar corrections from Reddit"""
    
    def __init__(self):
        if not PRAW_AVAILABLE:
            raise ImportError("PRAW is required. Install with: pip install praw")
        
        client_id = os.getenv("REDDIT_CLIENT_ID", REDDIT_CONFIG.get("client_id", ""))
        client_secret = os.getenv("REDDIT_CLIENT_SECRET", REDDIT_CONFIG.get("client_secret", ""))
        user_agent = os.getenv("REDDIT_USER_AGENT", REDDIT_CONFIG.get("user_agent", ""))
        
        if not client_id or not client_secret:
            print("\n" + "="*60)
            print("⚠ REDDIT API CREDENTIALS NOT FOUND")
            print("="*60)
            print("""
To use Reddit scraping, you need to:

1. Go to: https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Fill in:
   - Name: GrammarCorpusCollector
   - Type: script
   - Description: Collecting grammar corrections for research
   - Redirect URI: http://localhost:8080
4. Copy the client_id (under the app name) and client_secret
5. Create a .env file with:
   
   REDDIT_CLIENT_ID=your_client_id
   REDDIT_CLIENT_SECRET=your_client_secret
   REDDIT_USER_AGENT=GrammarCorpusCollector/1.0

6. Run this script again
""")
            self.reddit = None
            return
        
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        
        self.config = SCRAPING_CONFIG["reddit"]
        self.corrections = []
        
        # Patterns for finding corrections
        self.correction_patterns = [
            # "X should be Y" pattern
            r'"([^"]+)"\s*should\s*be\s*"([^"]+)"',
            r"'([^']+)'\s*should\s*be\s*'([^']+)'",
            # "Instead of X, use Y" pattern
            r'instead\s+of\s+"([^"]+)",?\s*use\s+"([^"]+)"',
            r"instead\s+of\s+'([^']+)',?\s*use\s+'([^']+)'",
            # "X not Y" pattern
            r'"([^"]+)",?\s*not\s*"([^"]+)"',
            # "Correct: X" after showing incorrect
            r'incorrect:?\s*"([^"]+)"[^"]*correct:?\s*"([^"]+)"',
            # "X -> Y" or "X → Y" pattern
            r'"([^"]+)"\s*[-→>]+\s*"([^"]+)"',
            # "*X" correction pattern (asterisk correction)
            r'\*([A-Za-z][^\s*]{2,})',
        ]
    
    def extract_corrections(self, text: str) -> List[Dict]:
        """Extract grammar corrections from text"""
        corrections = []
        
        for pattern in self.correction_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    incorrect, correct = match[0], match[1]
                    
                    # Basic validation
                    if len(incorrect) > 3 and len(correct) > 3:
                        if incorrect.lower() != correct.lower():
                            corrections.append({
                                "source": incorrect,
                                "target": correct
                            })
        
        return corrections
    
    def classify_error(self, source: str, target: str) -> List[str]:
        """Simple error classification based on difference"""
        errors = []
        
        source_words = source.lower().split()
        target_words = target.lower().split()
        
        # Check for article changes
        articles = {'a', 'an', 'the'}
        if any(w in articles for w in source_words) or any(w in articles for w in target_words):
            if set(source_words) & articles != set(target_words) & articles:
                errors.append("ART")
        
        # Check for verb changes (simple heuristic)
        verb_endings = ['s', 'ed', 'ing']
        for sw, tw in zip(source_words, target_words):
            if sw != tw:
                for ending in verb_endings:
                    if sw.endswith(ending) or tw.endswith(ending):
                        errors.append("VERB")
                        break
        
        # Check for spelling (similar words)
        for sw, tw in zip(source_words, target_words):
            if sw != tw and self._edit_distance(sw, tw) <= 2:
                errors.append("SPE")
                break
        
        # Default to OTHER if no specific error detected
        if not errors:
            errors.append("OTHER")
        
        return list(set(errors))
    
    def _edit_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein edit distance"""
        if len(s1) < len(s2):
            return self._edit_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def scrape_subreddit(self, subreddit_name: str, limit: int = 100) -> List[GrammarCorrection]:
        """Scrape corrections from a subreddit"""
        if not self.reddit:
            return []
        
        corrections = []
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Get posts from different time ranges
            for post in tqdm(subreddit.hot(limit=limit), 
                           desc=f"r/{subreddit_name}", 
                           total=limit):
                
                # Check post title and body
                all_text = post.title + " " + (post.selftext or "")
                extracted = self.extract_corrections(all_text)
                
                for idx, corr in enumerate(extracted):
                    correction = GrammarCorrection(
                        id=f"reddit_{post.id}_{idx}",
                        source=corr["source"],
                        target=corr["target"],
                        error_types=self.classify_error(corr["source"], corr["target"]),
                        subreddit=subreddit_name,
                        post_id=post.id,
                        score=post.score,
                        created_utc=post.created_utc
                    )
                    corrections.append(correction)
                
                # Check comments
                try:
                    post.comments.replace_more(limit=0)
                    for comment in post.comments.list()[:50]:
                        extracted = self.extract_corrections(comment.body)
                        for idx, corr in enumerate(extracted):
                            correction = GrammarCorrection(
                                id=f"reddit_{comment.id}_{idx}",
                                source=corr["source"],
                                target=corr["target"],
                                error_types=self.classify_error(corr["source"], corr["target"]),
                                subreddit=subreddit_name,
                                post_id=post.id,
                                score=comment.score,
                                created_utc=comment.created_utc
                            )
                            corrections.append(correction)
                except Exception:
                    pass
                
                # Rate limiting
                time.sleep(0.1)
        
        except Exception as e:
            print(f"Error scraping r/{subreddit_name}: {e}")
        
        return corrections
    
    def scrape_all(self) -> List[GrammarCorrection]:
        """Scrape all configured subreddits"""
        all_corrections = []
        
        for subreddit in self.config["subreddits"]:
            corrections = self.scrape_subreddit(
                subreddit, 
                limit=self.config["posts_per_subreddit"]
            )
            all_corrections.extend(corrections)
            print(f"✓ r/{subreddit}: {len(corrections)} corrections")
        
        return all_corrections


class StackExchangeScraper:
    """Scrape grammar corrections from Stack Exchange"""
    
    def __init__(self):
        self.base_url = "https://api.stackexchange.com/2.3"
        self.config = SCRAPING_CONFIG["stackexchange"]
    
    def scrape_site(self, site: str, limit: int = 100) -> List[Dict]:
        """Scrape questions from a Stack Exchange site"""
        corrections = []
        
        try:
            url = f"{self.base_url}/questions"
            params = {
                "site": site,
                "pagesize": min(limit, 100),
                "order": "desc",
                "sort": "votes",
                "filter": "withbody"
            }
            
            import requests
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                questions = data.get("items", [])
                
                for q in questions:
                    # Extract corrections from question title and body
                    text = q.get("title", "") + " " + q.get("body", "")
                    
                    # Simple extraction - look for quoted text pairs
                    quoted = re.findall(r'"([^"]+)"', text)
                    
                    for i in range(len(quoted) - 1):
                        if len(quoted[i]) > 3 and len(quoted[i+1]) > 3:
                            corrections.append({
                                "id": f"stackexchange_{q['question_id']}_{i}",
                                "source": quoted[i],
                                "target": quoted[i+1],
                                "error_types": ["OTHER"],
                                "site": site,
                                "question_id": q["question_id"],
                                "score": q.get("score", 0),
                                "dataset": "stackexchange"
                            })
        
        except Exception as e:
            print(f"Error scraping {site}: {e}")
        
        return corrections
    
    def scrape_all(self) -> List[Dict]:
        """Scrape all configured Stack Exchange sites"""
        all_corrections = []
        
        for site in self.config["sites"]:
            print(f"📚 Scraping {site}.stackexchange.com...")
            corrections = self.scrape_site(
                site,
                limit=self.config["questions_per_site"]
            )
            all_corrections.extend(corrections)
            print(f"✓ {site}: {len(corrections)} potential corrections")
        
        return all_corrections


def create_demo_data() -> List[Dict]:
    """Create demo data when Reddit API is not available"""
    
    demo_corrections = [
        {
            "id": "demo_001",
            "source": "I goed to the store yesterday.",
            "target": "I went to the store yesterday.",
            "error_types": ["TENSE"],
            "source_type": "demo",
            "dataset": "scraped_demo"
        },
        {
            "id": "demo_002",
            "source": "She don't like pizza.",
            "target": "She doesn't like pizza.",
            "error_types": ["SVA"],
            "source_type": "demo",
            "dataset": "scraped_demo"
        },
        {
            "id": "demo_003",
            "source": "I have went there before.",
            "target": "I have gone there before.",
            "error_types": ["VFORM"],
            "source_type": "demo",
            "dataset": "scraped_demo"
        },
        {
            "id": "demo_004",
            "source": "He is more taller than me.",
            "target": "He is taller than me.",
            "error_types": ["OTHER"],
            "source_type": "demo",
            "dataset": "scraped_demo"
        },
        {
            "id": "demo_005",
            "source": "I am interesting in music.",
            "target": "I am interested in music.",
            "error_types": ["WC"],
            "source_type": "demo",
            "dataset": "scraped_demo"
        },
        {
            "id": "demo_006",
            "source": "She suggested me to go.",
            "target": "She suggested that I go.",
            "error_types": ["OTHER"],
            "source_type": "demo",
            "dataset": "scraped_demo"
        },
        {
            "id": "demo_007",
            "source": "I look forward to see you.",
            "target": "I look forward to seeing you.",
            "error_types": ["VFORM"],
            "source_type": "demo",
            "dataset": "scraped_demo"
        },
        {
            "id": "demo_008",
            "source": "Me and him went to the park.",
            "target": "He and I went to the park.",
            "error_types": ["PRON"],
            "source_type": "demo",
            "dataset": "scraped_demo"
        },
        {
            "id": "demo_009",
            "source": "I have many informations.",
            "target": "I have a lot of information.",
            "error_types": ["NOUN"],
            "source_type": "demo",
            "dataset": "scraped_demo"
        },
        {
            "id": "demo_010",
            "source": "She plays very well tennis.",
            "target": "She plays tennis very well.",
            "error_types": ["WO"],
            "source_type": "demo",
            "dataset": "scraped_demo"
        },
    ]
    
    return demo_corrections


def main():
    """Main scraping function"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║     WEB SCRAPER FOR GRAMMAR CORRECTIONS                    ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    all_corrections = []
    
    # Try Reddit scraping
    print("\n📱 REDDIT SCRAPING")
    print("="*40)
    
    try:
        if PRAW_AVAILABLE:
            reddit_scraper = RedditGrammarScraper()
            if reddit_scraper.reddit:
                reddit_corrections = reddit_scraper.scrape_all()
                all_corrections.extend([asdict(c) for c in reddit_corrections])
                print(f"\n✓ Total Reddit corrections: {len(reddit_corrections)}")
            else:
                print("⚠ Skipping Reddit (no credentials)")
        else:
            print("⚠ PRAW not installed, skipping Reddit")
    except Exception as e:
        print(f"⚠ Reddit scraping failed: {e}")
    
    # Try Stack Exchange scraping
    print("\n📚 STACK EXCHANGE SCRAPING")
    print("="*40)
    
    try:
        se_scraper = StackExchangeScraper()
        se_corrections = se_scraper.scrape_all()
        all_corrections.extend(se_corrections)
        print(f"\n✓ Total Stack Exchange corrections: {len(se_corrections)}")
    except Exception as e:
        print(f"⚠ Stack Exchange scraping failed: {e}")
    
    # Add demo data if nothing was scraped
    if len(all_corrections) == 0:
        print("\n⚠ No data scraped. Creating demo dataset...")
        demo_data = create_demo_data()
        all_corrections.extend(demo_data)
        print(f"✓ Created {len(demo_data)} demo corrections")
    
    # Save to file
    SCRAPED_DIR.mkdir(parents=True, exist_ok=True)
    output_file = SCRAPED_DIR / "scraped_corrections.jsonl"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in all_corrections:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    # Also save to processed folder
    processed_file = PROCESSED_DATA_DIR / "scraped_pairs.jsonl"
    with open(processed_file, 'w', encoding='utf-8') as f:
        for item in all_corrections:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"\n✓ Saved {len(all_corrections)} corrections to: {output_file}")
    print(f"✓ Also saved to: {processed_file}")
    
    # Statistics
    print("\n📊 Statistics:")
    datasets = {}
    for item in all_corrections:
        ds = item.get("dataset", "unknown")
        datasets[ds] = datasets.get(ds, 0) + 1
    
    for ds, count in datasets.items():
        print(f"   {ds}: {count} corrections")
    
    print("\n✅ Scraping complete!")
    print("\nNext steps:")
    print("1. Run: python scripts/process_data.py")
    print("2. Run: python scripts/merge_corpus.py")
    
    return all_corrections


if __name__ == "__main__":
    main()
