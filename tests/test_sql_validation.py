"""Test script for SQL validation"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database.connection import DatabaseConnection


def test_valid_sql_statements():
    """Test valid SQL statements (should pass)"""
    print("=" * 60)
    print("TEST: Valid SQL Statements")
    print("=" * 60)

    db = DatabaseConnection("")  # Empty connection for validation only

    valid_queries = [
        "SELECT * FROM table",
        "SELECT col1, col2 FROM table WHERE id = 1",
        "SELECT SUM(value) AS total FROM table GROUP BY category",
        "SELECT * FROM table ORDER BY date DESC",
        "SELECT * FROM table WHERE status = 'active' GROUP BY region ORDER BY count DESC",
        "SELECT a.id, b.name FROM table_a a JOIN table_b b ON a.id = b.id",
    ]

    all_passed = True

    for sql in valid_queries:
        is_valid, error_msg = db.validate_sql(sql)

        if is_valid:
            print(f"✓ PASS: {sql[:60]}...")
        else:
            print(f"✗ FAIL: {sql[:60]}...")
            print(f"  Error: {error_msg}")
            all_passed = False

    if all_passed:
        print(f"\n✓ SUCCESS: All valid queries passed")
    else:
        print(f"\n✗ FAILED: Some valid queries were rejected")

    return all_passed


def test_invalid_sql_statements():
    """Test invalid SQL statements (should fail)"""
    print("\n" + "=" * 60)
    print("TEST: Invalid SQL Statements (Should Be Rejected)")
    print("=" * 60)

    db = DatabaseConnection("")  # Empty connection for validation only

    invalid_queries = [
        ("INSERT INTO table VALUES (1, 2, 3)", "INSERT"),
        ("UPDATE table SET col = 1 WHERE id = 2", "UPDATE"),
        ("DELETE FROM table WHERE id = 1", "DELETE"),
        ("DROP TABLE table", "DROP"),
        ("CREATE TABLE table (id INT)", "CREATE"),
        ("ALTER TABLE table ADD COLUMN col INT", "ALTER"),
        ("TRUNCATE TABLE table", "TRUNCATE"),
    ]

    all_passed = True

    for sql, operation in invalid_queries:
        is_valid, error_msg = db.validate_sql(sql)

        if not is_valid:
            print(f"✓ PASS: {operation} correctly rejected")
        else:
            print(f"✗ FAIL: {operation} should have been rejected")
            print(f"  SQL: {sql}")
            all_passed = False

    if all_passed:
        print(f"\n✓ SUCCESS: All invalid queries were correctly rejected")
    else:
        print(f"\n✗ FAILED: Some invalid queries were accepted")

    return all_passed


def test_sql_with_comments():
    """Test SQL with comments"""
    print("\n" + "=" * 60)
    print("TEST: SQL with Comments")
    print("=" * 60)

    db = DatabaseConnection("")

    test_cases = [
        ("SELECT * FROM table -- this is a comment", True, "Single-line comment"),
        ("SELECT * FROM table /* multi-line\ncomment */", True, "Multi-line comment"),
        ("-- comment\nSELECT * FROM table", True, "Comment before SELECT"),
    ]

    all_passed = True

    for sql, should_pass, description in test_cases:
        is_valid, error_msg = db.validate_sql(sql)

        if (should_pass and is_valid) or (not should_pass and not is_valid):
            print(f"✓ PASS: {description}")
        else:
            print(f"✗ FAIL: {description}")
            print(f"  SQL: {sql}")
            if error_msg:
                print(f"  Error: {error_msg}")
            all_passed = False

    return all_passed


def test_sql_edge_cases():
    """Test SQL edge cases"""
    print("\n" + "=" * 60)
    print("TEST: SQL Edge Cases")
    print("=" * 60)

    db = DatabaseConnection("")

    test_cases = [
        ("SELECT * FROM user_insert_table", True, "Table name contains 'insert'"),
        ("SELECT description FROM table WHERE description LIKE '%update%'", True, "Column value contains 'update'"),
        ("", False, "Empty SQL"),
        ("   \n\n  ", False, "Only whitespace"),
    ]

    all_passed = True

    for sql, should_pass, description in test_cases:
        is_valid, error_msg = db.validate_sql(sql)

        if (should_pass and is_valid) or (not should_pass and not is_valid):
            print(f"✓ PASS: {description}")
        else:
            print(f"✗ FAIL: {description}")
            print(f"  SQL: '{sql}'")
            if error_msg:
                print(f"  Error: {error_msg}")
            all_passed = False

    return all_passed


def main():
    """Run all SQL validation tests"""
    print("\n" + "=" * 60)
    print("SQL VALIDATION TESTS")
    print("=" * 60)

    results = []

    # Test 1: Valid SQL
    results.append(("Valid SQL Statements", test_valid_sql_statements()))

    # Test 2: Invalid SQL
    results.append(("Invalid SQL Statements", test_invalid_sql_statements()))

    # Test 3: Comments
    results.append(("SQL with Comments", test_sql_with_comments()))

    # Test 4: Edge cases
    results.append(("SQL Edge Cases", test_sql_edge_cases()))

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
