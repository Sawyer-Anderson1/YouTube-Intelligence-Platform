"""
Tests for transcript validation.
Validates uniqueness, English language, word count, and relevant terms.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import langdetect
from langdetect.lang_detect_exception import LangDetectException

# Path to sample transcripts for testing
TRANSCRIPTS_DIR = Path(__file__).parent.parent / "data" / "transcripts"

# Path to transcripts directory
# TRANSCRIPTS_DIR = Path(__file__).parent.parent / "tests" / "test_data"

# Thresholds
MIN_WORD_COUNT = 20
LANGUAGE_CONFIDENCE_THRESHOLD = 0.80
TERMS_TO_CHECK = [' ai ', '.ai', ' ai.', 'artificial intelligence', 'generative ai',
                  'language model', 'AI model', 'model training', 'llm', 'neural network', 'ai bubble', 'machine learning',
                  'chatgpt', 'chat gpt', 'agent', 'claude', 'gemini', 'moltbook',
                  'openclaw', 'grok', 'OpenAI', 'Nvidia']
# 'ai' removed to prevent false positives (e.g. "ai" in "said", "wait", etc.)


def load_transcript(filepath: Path) -> list[dict[str, Any]]:
    """Load a transcript JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def get_transcript_text(transcript: list[dict[str, Any]]) -> str:
    """Extract all text from transcript segments."""
    return " ".join(seg.get("text", "") for seg in transcript if "text" in seg)


def get_transcript_hash(transcript: list[dict[str, Any]]) -> str:
    """Generate hash for transcript content."""
    text = get_transcript_text(transcript)
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def detect_language(text: str) -> tuple[str, float]:
    """
    Detect language and return (language_code, confidence).
    Returns ('unknown', 0.0) if detection fails.
    """
    if not text or len(text.strip()) < 20:
        return "unknown", 0.0
    
    try:
        # langdetect returns list of (language, probability) sorted by prob
        results = langdetect.detect_langs(text)
        if results:
            return results[0].lang, results[0].prob
        return "unknown", 0.0
    except LangDetectException:
        return "unknown", 0.0


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


# ========== Test Functions ==========

def test_transcript_uniqueness(transcript: list[dict[str, Any]], all_hashes: set[str]) -> tuple[bool, str]:
    """Check if transcript is unique (not a duplicate)."""
    transcript_hash = get_transcript_hash(transcript)
    if transcript_hash in all_hashes:
        return False, f"Duplicate transcript found (hash: {transcript_hash})"
    all_hashes.add(transcript_hash)
    return True, "Unique"


def test_is_english(transcript: list[dict[str, Any]]) -> tuple[bool, str]:
    """Check if transcript is in English."""
    text = get_transcript_text(transcript)
    lang, confidence = detect_language(text)
    
    if lang != "en":
        return False, f"Language is '{lang}' (confidence: {confidence:.2f})"
    
    if confidence < LANGUAGE_CONFIDENCE_THRESHOLD:
        return False, f"Low confidence: {confidence:.2f} < {LANGUAGE_CONFIDENCE_THRESHOLD}"
    
    return True, f"English (confidence: {confidence:.2f})"


def test_has_terms(transcript: list[dict[str, Any]]) -> tuple[bool, str]:
    """Check if transcript contains required terms."""
    text = get_transcript_text(transcript)
    found_terms = [term for term in TERMS_TO_CHECK if term.lower() in text.lower()]
    
    if not found_terms:
        return False, f"No required terms found in transcript."
    
    return True, f"Found terms: {found_terms}"


def test_min_word_count(transcript: list[dict[str, Any]]) -> tuple[bool, str]:
    """Check minimum word count."""
    text = get_transcript_text(transcript)
    word_count = count_words(text)
    
    if word_count < MIN_WORD_COUNT:
        return False, f"Word count {word_count} < {MIN_WORD_COUNT}"
    
    return True, f"Word count: {word_count}"


# ========== Test Runner ==========

def run_all_tests() -> dict[str, dict[str, tuple[bool, str]]]:
    """Run all tests on all transcripts."""
    results = {}
    all_hashes = set()
    
    transcript_files = list(TRANSCRIPTS_DIR.glob("*_transcript_*.json"))
    
    for filepath in transcript_files:
        try:
            transcript = load_transcript(filepath)
            results[str(filepath)] = {
                "uniqueness": test_transcript_uniqueness(transcript, all_hashes),
                "is_english": test_is_english(transcript),
                "min_word_count": test_min_word_count(transcript),
                "has_terms": test_has_terms(transcript),
            }
        except Exception as e:
            results[str(filepath)] = {"error": (False, str(e))}
    
    return results


def print_summary(results: dict[str, dict[str, tuple[bool, str]]]) -> None:
    """Print a summary of test results."""
    total = len(results)
    passed = 0
    failed = 0
    
    print("\n" + "=" * 60)
    print("TRANSCRIPT VALIDATION SUMMARY")
    print("=" * 60)
    
    # Count by test type
    test_types = set()
    for file_results in results.values():
        test_types.update(k for k in file_results.keys() if k != "error")
    
    for test_name in sorted(test_types):
        test_passed = sum(1 for r in results.values() if test_name in r and r[test_name][0])
        test_failed = total - test_passed
        status = "✓" if test_passed == total else "✗"
        print(f"{status} {test_name}: {test_passed}/{total} passed")
    
    print("-" * 60)
    
    # Overall pass/fail
    for filepath, file_results in results.items():
        file_passed = sum(1 for v in file_results.values() if isinstance(v, tuple) and v[0])
        file_total = len([v for v in file_results.values() if isinstance(v, tuple)])
        
        if file_passed == file_total:
            passed += 1
        else:
            failed += 1
            # Print failed files
            print(f"✗ FAILED: {Path(filepath).name}")
            for test_name, (passed_test, msg) in file_results.items():
                if not passed_test:
                    print(f"  - {test_name}: {msg}")
    
    print("-" * 60)
    print(f"TOTAL: {passed} passed, {failed} failed, {total} total")
    print("=" * 60)


if __name__ == "__main__":
    results = run_all_tests()
    print_summary(results)
