"""
Tests for LLM response validation.
Validates that the LLM returns properly formatted JSON responses
matching the expected schema for each query type.
"""
import json
from pathlib import Path
from typing import Any

# Path to sample transcripts for testing
RESPONSES_DIR = Path(__file__).parent.parent / "data" / "example_output"

# Query types defined in rag.py
QUERY_TYPES = ['claims', 'trends', 'narratives', 'risk_factors']


def load_response(filepath: Path) -> dict[str, Any]:
    """Load a response JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# ========== Test Functions ==========

def test_response_format(transcript: dict[str, Any]) -> tuple[bool, str]:
    """Check if response is JSON dictionary."""
    if isinstance(transcript, dict):
        return (True, "Response is a valid JSON dictionary")
    return (False, f"Response is not a dictionary, got {type(transcript).__name__}")
    



# ========== Test Runner ==========

def run_all_tests() -> dict[str, dict[str, tuple[bool, str]]]:
    """Run all tests on all transcripts."""
    results = {}
    
    response_files = list(RESPONSES_DIR.glob("*.json"))
    
    for filepath in response_files:
        try:
            transcript = load_response(filepath)
            results[str(filepath)] = {
                "valid JSON Dict": test_response_format(transcript),
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