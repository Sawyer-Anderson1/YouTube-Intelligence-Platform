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
    """Load a JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# ========== Schema Validators ==========

def filename_to_query_type(filename: str) -> str:
    """Map filename to expected query_type."""
    name_lower = filename.lower()
    if 'claims' in name_lower:
        return 'claims'
    elif 'trends' in name_lower:
        return 'trends'
    elif 'narratives' in name_lower:
        return 'narratives'
    elif 'risk' in name_lower:
        return 'risk_factors'
    return 'unknown'

def validate_claims(data: dict) -> tuple[bool, str]:
    """Validate claims schema: {title: {'Quote':str, 'video_id':str, 'view_count':str/int, 'like_count':str/int, 'comment_count':str/int}}"""
    if not data:
        return False, "Empty claims dict"
    for title, item in data.items():
        if not isinstance(title, str) or not title.strip():
            return False, f"Invalid title: {title}"
        if not isinstance(item, dict):
            return False, f"Item not dict for claim '{title}'"
        required_keys = {'Quote', 'video_id', 'view_count', 'like_count', 'comment_count'}
        if not required_keys.issubset(item):
            return False, f"Missing keys in '{title}': {required_keys - set(item.keys())}"
        if not isinstance(item['Quote'], str) or not item['Quote'].strip():
            return False, f"Empty Quote in '{title}'"
        if not isinstance(item['video_id'], str) or not item['video_id'].strip():
            return False, f"Invalid video_id in '{title}'"
        for count_key in ['view_count', 'like_count', 'comment_count']:
            count = item[count_key]
            if not isinstance(count, (str, int)) or (isinstance(count, str) and not count.isdigit()) or int(count) < 0:
                return False, f"Invalid {count_key} '{count}' in '{title}'"
    return True, f"✓ {len(data)} valid claims"

def validate_trends_narratives(data: dict) -> tuple[bool, str]:
    """Validate trends/narratives: {title: {'Description':str, 'video_ids':list[str], totals:str/int}}"""
    if not data:
        return False, "Empty dict"
    for title, item in data.items():
        if not isinstance(title, str) or not title.strip():
            return False, f"Invalid title: {title}"
        if not isinstance(item, dict):
            return False, f"Item not dict for '{title}'"
        required_keys = {'Description', 'video_ids', 'total_view_count', 'total_like_count', 'total_comment_count'}
        if not required_keys.issubset(item):
            return False, f"Missing keys in '{title}': {required_keys - set(item.keys())}"
        if not isinstance(item['Description'], str) or not item['Description'].strip():
            return False, f"Empty Description in '{title}'"
        video_ids = item['video_ids']
        if not isinstance(video_ids, list) or not video_ids:
            return False, f"Invalid/empty video_ids in '{title}'"
        if not all(isinstance(vid, str) and vid.strip() for vid in video_ids):
            return False, f"Invalid video_ids in '{title}'"
        for count_key in ['total_view_count', 'total_like_count', 'total_comment_count']:
            count = item[count_key]
            if not isinstance(count, (str, int)) or (isinstance(count, str) and not count.isdigit()) or int(count) < 0:
                return False, f"Invalid {count_key} '{count}' in '{title}'"
    return True, f"✓ {len(data)} valid entries"

def validate_risk_factors(data: dict) -> tuple[bool, str]:
    """Validate risk_factors: {risk_title: description_str}"""
    if not data:
        return False, "Empty risk_factors dict"
    for title, desc in data.items():
        if not isinstance(title, str) or not title.strip():
            return False, f"Invalid title: {title}"
        if not isinstance(desc, str) or not desc.strip():
            return False, f"Empty description for '{title}'"
    return True, f"✓ {len(data)} valid risk factors"

# ========== Test Functions ==========

def test_response_format(data: dict[str, Any]) -> tuple[bool, str]:
    """Check if response is non-empty JSON dictionary."""
    if isinstance(data, dict) and data:
        return (True, "Response is a valid non-empty JSON dictionary")
    return (False, f"Response is not a non-empty dict, got {type(data).__name__}")
    


# ========== Test Runner ==========

def run_all_tests() -> dict[str, dict[str, tuple[bool, str]]]:
    """Run all schema validation tests on example outputs."""
    results = {}
    
    response_files = list(RESPONSES_DIR.glob("*.json"))
    
    for filepath in response_files:
        try:
            data = load_response(filepath)
            file_results = {"valid JSON Dict": test_response_format(data)}
            
            # Infer query_type and run specific schema tests
            query_type = filename_to_query_type(filepath.name)
            if query_type == 'claims':
                file_results['schema'] = validate_claims(data)
            elif query_type in ['trends', 'narratives']:
                file_results['schema'] = validate_trends_narratives(data)
            elif query_type == 'risk_factors':
                file_results['schema'] = validate_risk_factors(data)
            else:
                file_results['schema'] = (False, f"Unknown type: {query_type}")
            
            results[str(filepath)] = file_results
        except Exception as e:
            results[str(filepath)] = {"error": (False, str(e))}
    
    return results



def print_summary(results: dict[str, dict[str, tuple[bool, str]]]) -> None:
    """Print a summary of test results."""
    total = len(results)
    passed = 0
    failed = 0
    
    print("\n" + "=" * 60)
    print("LLM VALIDATION SUMMARY")
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