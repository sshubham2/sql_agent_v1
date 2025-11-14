"""Test script for database connection"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from dotenv import load_dotenv
from database.connection import DatabaseConnection


def test_connection():
    """Test database connection"""
    print("=" * 60)
    print("TEST: Database Connection")
    print("=" * 60)

    # Load environment
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(env_path)

    connection_string = os.getenv('DB_CONNECTION_STRING')

    if not connection_string:
        print("✗ FAILED: DB_CONNECTION_STRING not found in .env file")
        print("  Please configure the database connection string")
        return False

    print(f"\nConnection String: {connection_string[:50]}...")

    # Test connection
    print("\nAttempting to connect...")
    try:
        with DatabaseConnection(connection_string) as db:
            if db.test_connection():
                print("✓ SUCCESS: Database connection established")
                return True
            else:
                print("✗ FAILED: Could not establish database connection")
                return False
    except Exception as e:
        print(f"✗ FAILED: Exception occurred: {e}")
        return False


def test_query_execution():
    """Test executing a simple SELECT query"""
    print("\n" + "=" * 60)
    print("TEST: Query Execution")
    print("=" * 60)

    # Load environment
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(env_path)

    connection_string = os.getenv('DB_CONNECTION_STRING')

    if not connection_string:
        print("✗ SKIPPED: No database connection string")
        return False

    # Test simple query
    test_query = "SELECT 1 AS test_column"
    print(f"\nTest Query: {test_query}")

    try:
        with DatabaseConnection(connection_string) as db:
            results, error = db.execute_query(test_query)

            if error:
                print(f"✗ FAILED: {error}")
                return False

            if results and len(results) > 0:
                print(f"✓ SUCCESS: Query executed")
                print(f"  Result: {results}")
                return True
            else:
                print("✗ FAILED: No results returned")
                return False

    except Exception as e:
        print(f"✗ FAILED: Exception occurred: {e}")
        return False


def test_sql_validation():
    """Test SQL validation (only SELECT allowed)"""
    print("\n" + "=" * 60)
    print("TEST: SQL Validation")
    print("=" * 60)

    db = DatabaseConnection("")  # Empty connection string for validation only

    test_cases = [
        ("SELECT * FROM table", True, "Valid SELECT"),
        ("SELECT col FROM table WHERE id=1", True, "SELECT with WHERE"),
        ("INSERT INTO table VALUES (1)", False, "INSERT should fail"),
        ("UPDATE table SET col=1", False, "UPDATE should fail"),
        ("DELETE FROM table", False, "DELETE should fail"),
        ("DROP TABLE table", False, "DROP should fail"),
    ]

    all_passed = True

    for sql, should_pass, description in test_cases:
        is_valid, error_msg = db.validate_sql(sql)

        if should_pass and is_valid:
            print(f"✓ PASS: {description}")
        elif not should_pass and not is_valid:
            print(f"✓ PASS: {description} (correctly rejected)")
        else:
            print(f"✗ FAIL: {description}")
            print(f"  Expected: {'valid' if should_pass else 'invalid'}")
            print(f"  Got: {'valid' if is_valid else 'invalid'}")
            if error_msg:
                print(f"  Error: {error_msg}")
            all_passed = False

    return all_passed


def main():
    """Run all database tests"""
    print("\n" + "=" * 60)
    print("DATABASE CONNECTION TESTS")
    print("=" * 60)

    results = []

    # Test 1: Connection
    results.append(("Connection Test", test_connection()))

    # Test 2: Query Execution
    results.append(("Query Execution Test", test_query_execution()))

    # Test 3: SQL Validation
    results.append(("SQL Validation Test", test_sql_validation()))

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
