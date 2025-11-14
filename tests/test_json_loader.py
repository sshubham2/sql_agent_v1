"""Test script for JSON loader utilities"""
import os
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.json_loader import MeasureJSONLoader


def test_load_measure_index():
    """Test loading measure index"""
    print("=" * 60)
    print("TEST: Load Measure Index")
    print("=" * 60)

    index_file = Path(__file__).parent.parent / 'measure_index.json'

    try:
        loader = MeasureJSONLoader(index_file=str(index_file))
        print(f"✓ SUCCESS: Index loaded")
        print(f"  Index entries: {len(loader.index)}")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def test_scan_measures_directory():
    """Test scanning measures directory"""
    print("\n" + "=" * 60)
    print("TEST: Scan Measures Directory")
    print("=" * 60)

    measures_dir = Path(__file__).parent.parent / 'measures'
    index_file = Path(__file__).parent.parent / 'measure_index.json'

    try:
        loader = MeasureJSONLoader(
            measures_dir=str(measures_dir),
            index_file=str(index_file)
        )

        index = loader.scan_measures_directory()
        num_measures = len(set(index.values()))

        print(f"✓ SUCCESS: Directory scanned")
        print(f"  Found {num_measures} measure(s)")
        print(f"  Total aliases: {len(index)}")

        if num_measures > 0:
            print(f"\n  Available measures:")
            for filename in set(index.values()):
                print(f"    - {filename}")

        return True

    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def test_find_measure_by_code():
    """Test finding measure by exact code"""
    print("\n" + "=" * 60)
    print("TEST: Find Measure by Code (CE)")
    print("=" * 60)

    measures_dir = Path(__file__).parent.parent / 'measures'
    index_file = Path(__file__).parent.parent / 'measure_index.json'

    try:
        loader = MeasureJSONLoader(
            measures_dir=str(measures_dir),
            index_file=str(index_file)
        )

        # Test finding CE
        json_file = loader.find_measure_json("CE")

        if json_file:
            print(f"✓ SUCCESS: Found measure 'CE'")
            print(f"  JSON file: {json_file}")
            return True
        else:
            print(f"✗ FAILED: Could not find measure 'CE'")
            print(f"  Note: Make sure CE.json exists in measures/ directory")
            return False

    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def test_find_measure_by_alias():
    """Test finding measure by alias"""
    print("\n" + "=" * 60)
    print("TEST: Find Measure by Alias (Current Exposure)")
    print("=" * 60)

    measures_dir = Path(__file__).parent.parent / 'measures'
    index_file = Path(__file__).parent.parent / 'measure_index.json'

    try:
        loader = MeasureJSONLoader(
            measures_dir=str(measures_dir),
            index_file=str(index_file)
        )

        # Test finding by alias
        json_file = loader.find_measure_json("Current Exposure")

        if json_file:
            print(f"✓ SUCCESS: Found measure by alias 'Current Exposure'")
            print(f"  JSON file: {json_file}")
            return True
        else:
            print(f"✗ FAILED: Could not find measure by alias 'Current Exposure'")
            return False

    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def test_case_insensitive_matching():
    """Test case-insensitive matching"""
    print("\n" + "=" * 60)
    print("TEST: Case-Insensitive Matching")
    print("=" * 60)

    measures_dir = Path(__file__).parent.parent / 'measures'
    index_file = Path(__file__).parent.parent / 'measure_index.json'

    try:
        loader = MeasureJSONLoader(
            measures_dir=str(measures_dir),
            index_file=str(index_file)
        )

        test_cases = ["ce", "CE", "Ce", "cE"]
        all_passed = True

        for test_case in test_cases:
            json_file = loader.find_measure_json(test_case)
            if json_file:
                print(f"✓ PASS: Found '{test_case}' -> {json_file}")
            else:
                print(f"✗ FAIL: Could not find '{test_case}'")
                all_passed = False

        if all_passed:
            print(f"\n✓ SUCCESS: All case variations matched")
            return True
        else:
            return False

    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def test_load_measure_config():
    """Test loading measure configuration"""
    print("\n" + "=" * 60)
    print("TEST: Load Measure Configuration")
    print("=" * 60)

    measures_dir = Path(__file__).parent.parent / 'measures'

    try:
        loader = MeasureJSONLoader(measures_dir=str(measures_dir))

        config = loader.load_measure_config("CE.json")

        if config:
            print(f"✓ SUCCESS: Loaded CE.json configuration")
            print(f"  Measure Code: {config.get('measure_code')}")
            print(f"  Measure Name: {config.get('measure_name')}")
            print(f"  Formula: {config.get('formula')}")
            print(f"  Aliases: {len(config.get('aliases', []))}")
            return True
        else:
            print(f"✗ FAILED: Could not load CE.json")
            print(f"  Note: Make sure CE.json exists in measures/ directory")
            return False

    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def test_measure_not_found():
    """Test measure not found scenario"""
    print("\n" + "=" * 60)
    print("TEST: Measure Not Found (Should Fail Gracefully)")
    print("=" * 60)

    measures_dir = Path(__file__).parent.parent / 'measures'
    index_file = Path(__file__).parent.parent / 'measure_index.json'

    try:
        loader = MeasureJSONLoader(
            measures_dir=str(measures_dir),
            index_file=str(index_file)
        )

        # Try to find non-existent measure
        json_file = loader.find_measure_json("NONEXISTENT_MEASURE")

        if json_file is None:
            print(f"✓ SUCCESS: Correctly returned None for non-existent measure")
            return True
        else:
            print(f"✗ FAILED: Should have returned None but got: {json_file}")
            return False

    except Exception as e:
        print(f"✗ FAILED: Exception should not be raised: {e}")
        return False


def main():
    """Run all JSON loader tests"""
    print("\n" + "=" * 60)
    print("JSON LOADER TESTS")
    print("=" * 60)

    results = []

    # Test 1: Load index
    results.append(("Load Measure Index", test_load_measure_index()))

    # Test 2: Scan directory
    results.append(("Scan Measures Directory", test_scan_measures_directory()))

    # Test 3: Find by code
    results.append(("Find Measure by Code", test_find_measure_by_code()))

    # Test 4: Find by alias
    results.append(("Find Measure by Alias", test_find_measure_by_alias()))

    # Test 5: Case-insensitive
    results.append(("Case-Insensitive Matching", test_case_insensitive_matching()))

    # Test 6: Load config
    results.append(("Load Measure Configuration", test_load_measure_config()))

    # Test 7: Not found
    results.append(("Measure Not Found", test_measure_not_found()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
