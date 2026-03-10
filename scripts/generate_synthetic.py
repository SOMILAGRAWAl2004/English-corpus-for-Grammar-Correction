"""
Synthetic Data Generator for English Grammar Correction Corpus
Generates grammatically incorrect sentences from clean text
"""

import os
import sys
import json
import random
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import requests
from tqdm import tqdm

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import SYNTHETIC_DIR, PROCESSED_DATA_DIR, SYNTHETIC_CONFIG


@dataclass
class ErrorEdit:
    """Represents a single error edit"""
    start: int
    end: int
    original: str
    replacement: str
    error_type: str


class SyntheticErrorGenerator:
    """Generate synthetic grammar errors from clean text"""
    
    def __init__(self):
        self.config = SYNTHETIC_CONFIG
        self._load_error_patterns()
    
    def _load_error_patterns(self):
        """Load error patterns for each error type"""
        
        # Subject-Verb Agreement errors
        self.sva_patterns = {
            # Third person singular: correct -> incorrect
            "goes": ["go", "goed"],
            "runs": ["run", "runned"],
            "plays": ["play", "playes"],
            "works": ["work"],
            "likes": ["like"],
            "wants": ["want"],
            "needs": ["need"],
            "comes": ["come"],
            "takes": ["take"],
            "makes": ["make"],
            "says": ["say"],
            "knows": ["know"],
            "thinks": ["think"],
            "sees": ["see"],
            "gets": ["get"],
            "gives": ["give"],
            "tells": ["tell"],
            "becomes": ["become"],
            "leaves": ["leave"],
            "feels": ["feel"],
            "tries": ["try"],
            "studies": ["study"],
            "carries": ["carry"],
            # Be verbs
            "is": ["are", "am", "be"],
            "are": ["is", "am"],
            "was": ["were", "is"],
            "were": ["was", "are"],
            "has": ["have"],
            "have": ["has"],
            # Negatives
            "doesn't": ["don't", "doesnt"],
            "don't": ["doesn't", "dont"],
            "hasn't": ["haven't", "hasnt"],
            "haven't": ["hasn't", "havent"],
            "isn't": ["aren't", "isnt"],
            "aren't": ["isn't", "arent"],
            "wasn't": ["weren't", "wasnt"],
            "weren't": ["wasn't", "werent"],
        }
        
        # Article errors
        self.article_patterns = {
            "a": ["an", "the", ""],
            "an": ["a", "the", ""],
            "the": ["a", "an", ""],
        }
        
        # Tense errors
        self.tense_patterns = {
            # Past tense -> present (incorrect for past context)
            "went": ["go", "goed", "gone"],
            "saw": ["see", "seen", "sawed"],
            "came": ["come", "comed"],
            "took": ["take", "taked", "tooked"],
            "made": ["make", "maked"],
            "said": ["say", "sayed"],
            "got": ["get", "getted", "geted"],
            "gave": ["give", "gived"],
            "found": ["find", "finded"],
            "told": ["tell", "telled"],
            "thought": ["think", "thinked"],
            "knew": ["know", "knowed"],
            "became": ["become", "becomed"],
            "left": ["leave", "leaved"],
            "felt": ["feel", "feeled"],
            "brought": ["bring", "bringed"],
            "bought": ["buy", "buyed"],
            "caught": ["catch", "catched"],
            "taught": ["teach", "teached"],
            "wrote": ["write", "writed"],
            "ate": ["eat", "eated"],
            "ran": ["run", "runned"],
            "sat": ["sit", "sitted"],
            "stood": ["stand", "standed"],
            "understood": ["understand", "understanded"],
            "heard": ["hear", "heared"],
            "read": ["readed"],  # Note: 'read' past tense pronunciation differs
            "spoke": ["speak", "speaked"],
            "drove": ["drive", "drived"],
            "sang": ["sing", "singed"],
            "swam": ["swim", "swimmed"],
            "flew": ["fly", "flied"],
            "grew": ["grow", "growed"],
            "threw": ["throw", "throwed"],
            "drew": ["draw", "drawed"],
            "wore": ["wear", "weared"],
            "broke": ["break", "breaked"],
            "chose": ["choose", "choosed"],
            "woke": ["wake", "waked"],
        }
        
        # Preposition errors
        self.preposition_patterns = {
            "in": ["on", "at", "into", ""],
            "on": ["in", "at", "onto", ""],
            "at": ["in", "on", "to", ""],
            "to": ["at", "in", "for", ""],
            "for": ["to", "of", "with", ""],
            "with": ["by", "for", "to", ""],
            "by": ["with", "from", "at", ""],
            "from": ["of", "by", "since", ""],
            "of": ["from", "for", "about", ""],
            "about": ["of", "on", "for", ""],
        }
        
        # Common spelling errors
        self.spelling_patterns = {
            "receive": ["recieve", "recive", "receeve"],
            "believe": ["beleive", "belive", "beleave"],
            "achieve": ["acheive", "achive", "acheeve"],
            "their": ["thier", "there", "they're"],
            "definitely": ["definately", "definitly", "definatly"],
            "separate": ["seperate", "seperete", "separete"],
            "occurred": ["occured", "occurrd", "ocurred"],
            "beginning": ["begining", "beggining", "begginning"],
            "necessary": ["neccessary", "necesary", "neccesary"],
            "accommodate": ["accomodate", "acommodate", "accomadate"],
            "occurrence": ["occurence", "occurrance", "occurance"],
            "recommend": ["recomend", "reccommend", "recommand"],
            "independent": ["independant", "indipendent", "independnet"],
            "professional": ["proffesional", "profesional", "proffessional"],
            "environment": ["enviroment", "enviornment", "enviorment"],
            "government": ["goverment", "gouvernment", "govenment"],
            "tomorrow": ["tommorow", "tommorrow", "tomorow"],
            "immediately": ["immediatly", "imediately", "immeadiatly"],
            "experience": ["experiance", "expirience", "experiense"],
            "different": ["diffrent", "differant", "diferent"],
            "beautiful": ["beautifull", "beutiful", "beautful"],
            "restaurant": ["restaraunt", "resturant", "restaurent"],
            "interesting": ["intresting", "intersting", "interesing"],
            "because": ["becuase", "becasue", "beacuse"],
            "through": ["trough", "thru", "throug"],
            "friend": ["freind", "frend", "freand"],
            "which": ["wich", "whitch", "witch"],
            "language": ["langauge", "languege", "lanuage"],
            "knowledge": ["knowlege", "knowlede", "knowladge"],
        }
        
        # Punctuation errors
        self.punctuation_patterns = {
            "it's": ["its", "its'"],
            "let's": ["lets", "lets'"],
            "don't": ["dont", "do'nt"],
            "can't": ["cant", "ca'nt"],
            "won't": ["wont", "wo'nt"],
            "didn't": ["didnt", "did'nt"],
            "couldn't": ["couldnt", "could'nt"],
            "wouldn't": ["wouldnt", "would'nt"],
            "shouldn't": ["shouldnt", "should'nt"],
            "they're": ["theyre", "their"],
            "you're": ["youre", "your"],
            "we're": ["were", "we'er"],
            "I'm": ["im", "Im"],
            "I'll": ["Ill", "ill"],
            "I've": ["Ive", "ive"],
        }
        
        # Word order patterns (these need context)
        self.adverb_placements = ["always", "never", "often", "usually", "sometimes", "rarely"]
    
    def introduce_sva_error(self, sentence: str) -> Tuple[str, Optional[ErrorEdit]]:
        """Introduce subject-verb agreement error"""
        words = sentence.split()
        
        for i, word in enumerate(words):
            word_lower = word.lower()
            if word_lower in self.sva_patterns:
                replacements = self.sva_patterns[word_lower]
                replacement = random.choice(replacements)
                
                # Preserve capitalization
                if word[0].isupper():
                    replacement = replacement.capitalize()
                
                original = word
                words[i] = replacement
                
                # Calculate character positions
                start = sum(len(w) + 1 for w in words[:i])
                end = start + len(original)
                
                return ' '.join(words), ErrorEdit(
                    start=start, end=end,
                    original=original, replacement=replacement,
                    error_type="SVA"
                )
        
        return sentence, None
    
    def introduce_article_error(self, sentence: str) -> Tuple[str, Optional[ErrorEdit]]:
        """Introduce article error (a, an, the)"""
        words = sentence.split()
        
        for i, word in enumerate(words):
            word_lower = word.lower()
            if word_lower in self.article_patterns:
                replacements = self.article_patterns[word_lower]
                replacement = random.choice(replacements)
                
                # If empty string, remove the article
                if replacement == "":
                    original = word
                    words.pop(i)
                    start = sum(len(w) + 1 for w in words[:i])
                    end = start + len(original) + 1  # +1 for space
                else:
                    if word[0].isupper():
                        replacement = replacement.capitalize()
                    original = word
                    words[i] = replacement
                    start = sum(len(w) + 1 for w in words[:i])
                    end = start + len(original)
                
                return ' '.join(words), ErrorEdit(
                    start=start, end=end,
                    original=original, replacement=replacement,
                    error_type="ART"
                )
        
        return sentence, None
    
    def introduce_tense_error(self, sentence: str) -> Tuple[str, Optional[ErrorEdit]]:
        """Introduce verb tense error"""
        words = sentence.split()
        
        for i, word in enumerate(words):
            word_lower = word.lower()
            if word_lower in self.tense_patterns:
                replacements = self.tense_patterns[word_lower]
                replacement = random.choice(replacements)
                
                if word[0].isupper():
                    replacement = replacement.capitalize()
                
                original = word
                words[i] = replacement
                
                start = sum(len(w) + 1 for w in words[:i])
                end = start + len(original)
                
                return ' '.join(words), ErrorEdit(
                    start=start, end=end,
                    original=original, replacement=replacement,
                    error_type="TENSE"
                )
        
        return sentence, None
    
    def introduce_spelling_error(self, sentence: str) -> Tuple[str, Optional[ErrorEdit]]:
        """Introduce spelling error"""
        words = sentence.split()
        
        for i, word in enumerate(words):
            # Remove punctuation for matching
            clean_word = re.sub(r'[^\w]', '', word.lower())
            if clean_word in self.spelling_patterns:
                replacements = self.spelling_patterns[clean_word]
                replacement = random.choice(replacements)
                
                # Preserve punctuation
                if word[-1] in '.,!?;:':
                    replacement = replacement + word[-1]
                
                if word[0].isupper():
                    replacement = replacement.capitalize()
                
                original = word
                words[i] = replacement
                
                start = sum(len(w) + 1 for w in words[:i])
                end = start + len(original)
                
                return ' '.join(words), ErrorEdit(
                    start=start, end=end,
                    original=original, replacement=replacement,
                    error_type="SPE"
                )
        
        return sentence, None
    
    def introduce_preposition_error(self, sentence: str) -> Tuple[str, Optional[ErrorEdit]]:
        """Introduce preposition error"""
        words = sentence.split()
        
        for i, word in enumerate(words):
            word_lower = word.lower()
            if word_lower in self.preposition_patterns:
                replacements = self.preposition_patterns[word_lower]
                replacement = random.choice(replacements)
                
                if replacement == "":
                    original = word
                    words.pop(i)
                    start = sum(len(w) + 1 for w in words[:i])
                    end = start + len(original) + 1
                else:
                    if word[0].isupper():
                        replacement = replacement.capitalize()
                    original = word
                    words[i] = replacement
                    start = sum(len(w) + 1 for w in words[:i])
                    end = start + len(original)
                
                return ' '.join(words), ErrorEdit(
                    start=start, end=end,
                    original=original, replacement=replacement,
                    error_type="PREP"
                )
        
        return sentence, None
    
    def introduce_punctuation_error(self, sentence: str) -> Tuple[str, Optional[ErrorEdit]]:
        """Introduce punctuation error (contractions)"""
        for original, replacements in self.punctuation_patterns.items():
            if original in sentence:
                replacement = random.choice(replacements)
                start = sentence.find(original)
                end = start + len(original)
                
                new_sentence = sentence.replace(original, replacement, 1)
                
                return new_sentence, ErrorEdit(
                    start=start, end=end,
                    original=original, replacement=replacement,
                    error_type="PUNCT"
                )
        
        return sentence, None
    
    def generate_errors(self, sentence: str) -> Dict:
        """Generate errors for a single sentence"""
        
        if len(sentence.split()) < self.config["min_sentence_length"]:
            return None
        
        if len(sentence.split()) > self.config["max_sentence_length"]:
            return None
        
        # Decide if this sentence should have errors
        if random.random() > self.config["error_injection_rate"]:
            return None
        
        # Select error types based on distribution
        error_generators = {
            "SVA": self.introduce_sva_error,
            "ART": self.introduce_article_error,
            "TENSE": self.introduce_tense_error,
            "SPE": self.introduce_spelling_error,
            "PREP": self.introduce_preposition_error,
            "PUNCT": self.introduce_punctuation_error,
        }
        
        # Randomly select which error types to apply
        num_errors = random.randint(1, self.config["max_errors_per_sentence"])
        
        distribution = self.config["error_type_distribution"]
        available_types = [t for t in error_generators.keys() if t in distribution]
        weights = [distribution.get(t, 0) for t in available_types]
        
        selected_types = random.choices(available_types, weights=weights, k=num_errors)
        
        # Apply errors
        current_sentence = sentence
        edits = []
        error_types = []
        
        for error_type in selected_types:
            generator = error_generators[error_type]
            new_sentence, edit = generator(current_sentence)
            
            if edit and new_sentence != current_sentence:
                current_sentence = new_sentence
                edits.append({
                    "original": edit.original,
                    "replacement": edit.replacement,
                    "type": edit.error_type
                })
                error_types.append(edit.error_type)
        
        # Only return if we actually introduced errors
        if current_sentence != sentence and edits:
            return {
                "source": current_sentence,  # Incorrect sentence
                "target": sentence,          # Original correct sentence
                "error_types": error_types,
                "edits": edits
            }
        
        return None


class WikipediaDataSource:
    """Fetch clean sentences from Wikipedia"""
    
    def __init__(self):
        self.api_url = "https://en.wikipedia.org/api/rest_v1/page/random/summary"
        self.wiki_api = "https://en.wikipedia.org/w/api.php"
    
    def get_random_sentences(self, count: int = 100) -> List[str]:
        """Get random sentences from Wikipedia articles"""
        sentences = []
        
        print(f"📚 Fetching sentences from Wikipedia...")
        
        with tqdm(total=count, desc="Fetching Wikipedia sentences") as pbar:
            attempts = 0
            max_attempts = count * 3  # Allow some failures
            
            while len(sentences) < count and attempts < max_attempts:
                attempts += 1
                try:
                    # Get random article
                    response = requests.get(self.api_url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        extract = data.get("extract", "")
                        
                        # Split into sentences
                        article_sentences = self._split_sentences(extract)
                        
                        for sent in article_sentences:
                            if self._is_valid_sentence(sent):
                                sentences.append(sent)
                                pbar.update(1)
                                if len(sentences) >= count:
                                    break
                
                except Exception as e:
                    continue
        
        return sentences[:count]
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _is_valid_sentence(self, sentence: str) -> bool:
        """Check if sentence is valid for our corpus"""
        words = sentence.split()
        
        # Length check
        if len(words) < 5 or len(words) > 50:
            return False
        
        # Should start with capital letter
        if not sentence[0].isupper():
            return False
        
        # Should end with punctuation
        if sentence[-1] not in '.!?':
            return False
        
        # Avoid sentences with too many special characters
        special_count = sum(1 for c in sentence if c in '()[]{}@#$%^&*')
        if special_count > 2:
            return False
        
        # Avoid sentences with numbers (dates, statistics)
        number_count = sum(1 for c in sentence if c.isdigit())
        if number_count > 5:
            return False
        
        return True


class NewsDataSource:
    """Fetch clean sentences from news articles"""
    
    def __init__(self):
        self.sample_sentences = [
            "The government announced new policies to address climate change.",
            "Scientists have discovered a new species of bird in the Amazon rainforest.",
            "The economy showed signs of recovery in the third quarter.",
            "Researchers have developed a new treatment for the disease.",
            "The company reported record profits in its quarterly earnings.",
            "Experts warn that immediate action is needed to prevent further damage.",
            "The president addressed the nation in a televised speech.",
            "Local authorities have implemented new safety measures.",
            "The study found that regular exercise improves mental health.",
            "International leaders met to discuss global security issues.",
            "The new technology could revolutionize the way we communicate.",
            "Environmental groups have called for stricter regulations.",
            "The museum will host a special exhibition next month.",
            "Healthcare professionals recommend annual check-ups for everyone.",
            "The university announced a new scholarship program for students.",
            "Weather forecasters predict heavy rainfall throughout the week.",
            "The team celebrated their victory with fans at the stadium.",
            "Economists predict steady growth for the coming year.",
            "The organization has launched a campaign to raise awareness.",
            "Transportation officials have announced major infrastructure improvements.",
        ]
    
    def get_sentences(self, count: int = 100) -> List[str]:
        """Get sentences - using samples for demo, can be extended with News API"""
        sentences = []
        
        # Duplicate and shuffle sample sentences
        while len(sentences) < count:
            sentences.extend(self.sample_sentences)
        
        random.shuffle(sentences)
        return sentences[:count]


class GutenbergDataSource:
    """Fetch sentences from Project Gutenberg books"""
    
    def __init__(self):
        self.sample_sentences = [
            "She walked slowly through the garden, admiring the beautiful flowers.",
            "The old man sat by the window, watching the rain fall gently on the street.",
            "He opened the letter with trembling hands, not knowing what to expect.",
            "The children played happily in the park until the sun began to set.",
            "She smiled warmly at the stranger who had helped her find her way.",
            "The house stood alone at the end of the road, surrounded by tall trees.",
            "He remembered the days when life was simpler and full of joy.",
            "The wind howled through the empty streets as night fell over the city.",
            "She carefully placed the book back on the shelf where it belonged.",
            "They had traveled for many days before finally reaching their destination.",
            "The young woman looked out at the sea, dreaming of distant lands.",
            "He worked diligently every day, hoping to provide a better life for his family.",
            "The music filled the room with a sense of peace and tranquility.",
            "She had never seen anything so beautiful in all her life.",
            "The story had been passed down through generations of the family.",
            "He knew that this moment would change everything forever.",
            "The sun rose slowly over the mountains, painting the sky in shades of gold.",
            "She held the photograph close to her heart, remembering happier times.",
            "The journey had been long and difficult, but they had finally arrived.",
            "He stood at the crossroads, uncertain which path to take.",
        ]
    
    def get_sentences(self, count: int = 100) -> List[str]:
        """Get sample sentences - can be extended with actual Gutenberg texts"""
        sentences = []
        
        while len(sentences) < count:
            sentences.extend(self.sample_sentences)
        
        random.shuffle(sentences)
        return sentences[:count]


def generate_synthetic_corpus(num_pairs: int = 10000, use_wikipedia: bool = True):
    """Generate synthetic grammar error corpus"""
    
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║     SYNTHETIC ERROR GENERATOR                              ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    generator = SyntheticErrorGenerator()
    
    # Collect clean sentences from various sources
    all_sentences = []
    
    if use_wikipedia:
        wiki_source = WikipediaDataSource()
        wiki_sentences = wiki_source.get_random_sentences(num_pairs // 2)
        all_sentences.extend(wiki_sentences)
        print(f"✓ Collected {len(wiki_sentences)} sentences from Wikipedia")
    
    news_source = NewsDataSource()
    news_sentences = news_source.get_sentences(num_pairs // 4)
    all_sentences.extend(news_sentences)
    print(f"✓ Collected {len(news_sentences)} sentences from News")
    
    gutenberg_source = GutenbergDataSource()
    gutenberg_sentences = gutenberg_source.get_sentences(num_pairs // 4)
    all_sentences.extend(gutenberg_sentences)
    print(f"✓ Collected {len(gutenberg_sentences)} sentences from Gutenberg")
    
    # Generate errors
    print(f"\n🔄 Generating synthetic errors...")
    synthetic_pairs = []
    
    for idx, sentence in enumerate(tqdm(all_sentences, desc="Generating errors")):
        result = generator.generate_errors(sentence)
        if result:
            result["id"] = f"synthetic_{idx:06d}"
            result["dataset"] = "synthetic"
            synthetic_pairs.append(result)
    
    # Save to file
    SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)
    output_file = SYNTHETIC_DIR / "synthetic_pairs.jsonl"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in synthetic_pairs:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    # Also save to processed folder
    processed_file = PROCESSED_DATA_DIR / "synthetic_pairs.jsonl"
    with open(processed_file, 'w', encoding='utf-8') as f:
        for item in synthetic_pairs:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"\n✓ Generated {len(synthetic_pairs)} synthetic error pairs")
    print(f"✓ Saved to: {output_file}")
    print(f"✓ Also saved to: {processed_file}")
    
    # Print statistics
    print("\n📊 Error Type Distribution:")
    error_counts = {}
    for pair in synthetic_pairs:
        for error_type in pair["error_types"]:
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
    
    for error_type, count in sorted(error_counts.items(), key=lambda x: -x[1]):
        pct = (count / len(synthetic_pairs)) * 100
        print(f"   {error_type}: {count} ({pct:.1f}%)")
    
    return synthetic_pairs


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate synthetic grammar errors")
    parser.add_argument("--count", type=int, default=5000, 
                        help="Number of sentence pairs to generate")
    parser.add_argument("--no-wikipedia", action="store_true",
                        help="Skip Wikipedia (use offline sources only)")
    
    args = parser.parse_args()
    
    generate_synthetic_corpus(
        num_pairs=args.count,
        use_wikipedia=not args.no_wikipedia
    )
    
    print("\n✅ Synthetic data generation complete!")
    print("\nNext steps:")
    print("1. Run: python scripts/scrape_reddit.py")
    print("2. Run: python scripts/process_data.py")


if __name__ == "__main__":
    main()
