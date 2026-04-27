# !/usr/bin/env python3
"""
Tests for claims verification against video transcripts with fuzzy matching.
Handles grammar variations, 1-2 word changes using normalization + similarity.
"""
import argparse
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

# Paths
CLAIMS_PATH = Path(__file__).parent.parent / "data" / "example_output" / "claims.json"
VIDEO_METRICS_PATH = Path(__file__).parent.parent / "data" / "video_metrics.json"
CHANNEL_VIDS_PATH = Path(__file__).parent.parent / "data" / "channel_vids.json"
TRANSCRIPTS_DIR = Path(__file__).parent.parent / "data" / "transcripts"

# LLM Setup - Different model from rag.py for quote verification
if not os.getenv("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY environment variable required for LLM quote verification")
model = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.0,
    max_tokens=2048,
    api_key=os.getenv("GROQ_API_KEY")
)

QUOTE_PROMPT = ChatPromptTemplate.from_template("""
You are verifying if a specific quote appears in a transcript.

Strictly analyze: Does the quote appear VERBATIM, PARAPHRASED, or SEMANTICALLY EQUIVALENT in the transcript?

Answer ONLY one line:
YES, brief reason (1 sentence)
or
NO, brief reason (1 sentence)

Quote: {quote}
Transcript: {transcript}
""")

def load_json(path: Path) -> Dict[str, Any]:
    """Load JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    
def get_transcript_text(transcript: list[dict[str, Any]]) -> str:
    """Extract all text from transcript segments."""
    return " ".join(seg.get("text", "") for seg in transcript if "text" in seg)

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
    video_id = claim_data.get("video_id")  # Assume quote dict has video_id
    if not video_id:
        return False, "No video_id in claim data"

    transcript_path = find_transcript_path(video_id, video_metrics, channel_vids)
    if not transcript_path or not transcript_path.exists():
        return False, f"No transcript found for {video_id}"

    try:
        transcript_data = load_transcript(transcript_path)
        transcript_text = get_transcript_text(transcript_data)
    except Exception as e:
        return False, f"Failed to load transcript: {str(e)}"

    result = model.invoke(QUOTE_PROMPT.format(quote=claim_data["Quote"], transcript=transcript_text))
    content = result.content.strip()
    print("=== RAW LLM ===")
    print(repr(content))
    print("=== END RAW ===")

    # Parse YES/NO format
    content_upper = content.upper()
    if content_upper.startswith("YES"):
        reason = content[3:].strip(", ").strip() or "LLM confirmed match"
        return True, reason
    elif content_upper.startswith("NO"):
        reason = content[2:].strip(", ").strip() or "LLM found no match"
        return False, reason
    else:
        # Fallback: simple keyword check
        quote_lower = claim_data["quote"].lower()
        text_lower = transcript_text.lower()
        if quote_lower in text_lower:
            return True, "Fallback: exact substring match"
        return False, f"Parse failed, no match: {content[:100]}..."

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

