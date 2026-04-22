# !/usr/bin/env python3
"""
Tests for claims verification against video transcripts with fuzzy matching.
Handles grammar variations, 1-2 word changes using normalization + similarity.
"""
import argparse
import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Paths
CLAIMS_PATH = Path(__file__).parent.parent / "data" / "example_output" / "claims.json"
VIDEO_METRICS_PATH = Path(__file__).parent.parent / "data" / "video_metrics.json"
CHANNEL_VIDS_PATH = Path(__file__).parent.parent / "data" / "channel_vids.json"
TRANSCRIPTS_DIR = Path(__file__).parent.parent / "data" / "transcripts"

def load_json(path: Path) -> Dict[str, Any]:
    """Load JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    
def get_transcript_text(transcript: list[dict[str, Any]]) -> str:
    """Extract all text from transcript segments."""
    return " ".join(seg.get("text", "") for seg in transcript if "text" in seg)

def normalize_text(text: str) -> tuple[str, set[str]]:
    """Normalize: lower, remove punct, tokenize words for similarity checks."""
    # Lower and remove punct/non-word
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    text = ' '.join(text.split())  # normalize spaces
    words = set(text.split())
    return text, words

def load_claims() -> Dict[str, Dict[str, str]]:
    """Load claims from JSON."""
    return load_json(CLAIMS_PATH)

def find_transcript_path(video_id: str, video_metrics: Dict[str, Dict], channel_vids: Dict[str, List[str]]) -> Optional[Path]:
    """Find transcript file path for given video_id using mappings."""
    if video_id not in video_metrics:
        return None
    metrics = video_metrics[video_id]
    channel_id = metrics.get("channel_id")
    if not channel_id:
        return None
    
    if channel_id not in channel_vids:
        return None
    vids_list = channel_vids[channel_id]
    try:
        index = vids_list.index(video_id) + 1  # 1-based
        filename = f"{channel_id}_transcript_{index}.json"
        transcript_path = TRANSCRIPTS_DIR / filename
        if transcript_path.exists():
            return transcript_path
    except ValueError:
        pass
    return None

def load_transcript(transcript_path: Path) -> List[Dict[str, Any]]:
    """Load transcript JSON."""
    return load_json(transcript_path)

def test_quote_in_transcript(claim_title: str, claim_data: Dict[str, str], video_metrics: Dict, channel_vids: Dict) -> Tuple[bool, str]:
    """Test quote in transcript with fuzzy matching for variations."""
    video_id = claim_data["video_id"]
    quote = claim_data["Quote"].strip()
    if not quote:
        return False, "Empty quote"
    
    transcript_path = find_transcript_path(video_id, video_metrics, channel_vids)
    if not transcript_path or not transcript_path.exists():
        return False, f"No transcript for '{video_id}'"
    
    try:
        transcript = load_transcript(transcript_path)
        full_text = get_transcript_text(transcript)
        
        # Normalize
        full_norm, full_words = normalize_text(full_text)
        quote_norm, quote_words = normalize_text(quote)
        # Search in sentences for better precision
        sentences = re.split(r'[.!?]+', full_text)
        best_sim = 0
        best_msg = ""
        for sent in sentences:
            sent_norm, sent_words = normalize_text(sent)
            sim = SequenceMatcher(None, quote_norm, sent_norm).ratio()
            if sim > best_sim:
                best_sim = sim
                overlap = len(quote_words.intersection(sent_words)) / len(quote_words.union(sent_words)) if quote_words else 0
                best_msg = f"best sent sim {sim:.1%} overlap {overlap:.1%}"
        similarity = best_sim
        
        # Exact match
        if quote.lower() in full_text.lower():
            return True, f"Exact match in {transcript_path.name}"
        
        # Sentence-level fuzzy
        if best_sim > 0.7:
            return True, f"Sent match (sim {best_sim:.1%}) in {transcript_path.name}"
        
        # Word overlap
        if quote_words:
            overlap = len(quote_words.intersection(full_words)) / len(quote_words.union(full_words))
            if overlap > 0.5:
                return True, f"Word match ({overlap:.1%}) in {transcript_path.name}"
        
        return False, f"No match (sim {best_sim:.1%}) in {transcript_path.name}\nQuote: '{quote}'"
    except Exception as e:
        return False, f"Error: {str(e)}"

def run_all_tests(claims_path: Optional[Path] = None) -> Dict[str, Dict[str, Tuple[bool, str]]]:
    """Run all claim verification tests."""
    if claims_path is None:
        claims_path = CLAIMS_PATH
    
    claims = load_json(claims_path)
    video_metrics = load_json(VIDEO_METRICS_PATH)
    channel_vids = load_json(CHANNEL_VIDS_PATH)
    
    results = {}
    for title, data in claims.items():
        results[title] = {
            "quote_verified": test_quote_in_transcript(title, data, video_metrics, channel_vids)
        }
    return results

def print_summary(results: Dict[str, Dict[str, Tuple[bool, str]]]) -> None:
    """Print test results summary."""
    total = len(results)
    passed = sum(1 for r in results.values() if r["quote_verified"][0])
    failed = total - passed
    
    print("\n" + "=" * 60)
    print("CLAIMS VERIFICATION SUMMARY (Fuzzy Anti-Hallucination)")
    print("=" * 60)
    
    print(f"✓ quote_verified: {passed}/{total}")
    print("-" * 60)
    
    for title, tests in results.items():
        status, msg = tests["quote_verified"]
        icon = "✓" if status else "✗"
        print(f"{icon} {title}")
        print(f"  {msg}")
    
    print("-" * 60)
    print(f"TOTAL verified: {passed}/{total}")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify claims vs transcripts with fuzzy matching")
    parser.add_argument("--claims", type=Path, default=CLAIMS_PATH)
    args = parser.parse_args()
    
    results = run_all_tests(args.claims)
    print_summary(results)

