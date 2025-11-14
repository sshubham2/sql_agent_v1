"""Run all test scripts"""
import sys
import subprocess
from pathlib import Path


def run_test_script(script_path):
    """
    Run a test script and return success status

    Args:
        script_path: Path to test script

    Returns:
        True if all tests passed, False otherwise
    """
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True
        )

        # Print output
        print(result.stdout)
        if result.stderr:
            print(result.stderr)

        return result.returncode == 0

    except Exception as e:
        print(f"Error running {script_path.name}: {e}")
        return False


def main():
    """Run all test scripts"""
    print("=" * 70)
    print("RUNNING ALL TESTS")
    print("=" * 70)

    tests_dir = Path(__file__).parent

    # Define test scripts in order
    test_scripts = [
        "test_sql_validation.py",
        "test_json_loader.py",
        "test_db_connection.py",
    ]

    results = []

    for script_name in test_scripts:
        script_path = tests_dir / script_name

        if not script_path.exists():
            print(f"\n✗ SKIPPED: {script_name} not found")
            results.append((script_name, False))
            continue

        print(f"\n{'=' * 70}")
        print(f"Running: {script_name}")
        print('=' * 70)

        success = run_test_script(script_path)
        results.append((script_name, success))

        print(f"\n{'=' * 70}")
        if success:
            print(f"✓ {script_name}: ALL TESTS PASSED")
        else:
            print(f"✗ {script_name}: SOME TESTS FAILED")
        print('=' * 70)

    # Final summary
    print("\n" + "=" * 70)
    print("FINAL TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for script_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {script_name}")

    print(f"\nTotal: {passed}/{total} test scripts passed")
    print("=" * 70)

    # Notes
    print("\nNotes:")
    print("- SQL Validation tests don't require database connection")
    print("- JSON Loader tests require measures/CE.json to exist")
    print("- Database Connection tests require valid .env configuration")
    print("\nMake sure to:")
    print("1. Configure .env with your OpenAI API key and database connection")
    print("2. Create at least one measure JSON file (e.g., measures/CE.json)")
    print("3. Ensure your database is accessible")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
