"""Database connection and query execution module"""
import pyodbc
import re
from typing import List, Dict, Optional, Any


class DatabaseConnection:
    """Manages MySQL database connections via ODBC"""

    def __init__(self, connection_string: str):
        """
        Initialize database connection

        Args:
            connection_string: ODBC connection string
        """
        self.connection_string = connection_string
        self.connection: Optional[pyodbc.Connection] = None
        self.cursor: Optional[pyodbc.Cursor] = None

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def connect(self) -> bool:
        """
        Establish database connection

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.connection = pyodbc.connect(self.connection_string)
            self.cursor = self.connection.cursor()
            print("Database connection established successfully")
            return True
        except pyodbc.Error as e:
            print(f"Database connection error: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error connecting to database: {e}")
            return False

    def test_connection(self) -> bool:
        """
        Test if database connection is active

        Returns:
            True if connection is active, False otherwise
        """
        try:
            if self.connection is None:
                return False
            # Try a simple query
            self.cursor.execute("SELECT 1")
            self.cursor.fetchone()
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False

    def validate_sql(self, sql: str) -> tuple[bool, Optional[str]]:
        """
        Validate that SQL contains only allowed operations

        Args:
            sql: SQL statement to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Remove comments and normalize whitespace
        sql_clean = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
        sql_clean = re.sub(r'/\*.*?\*/', '', sql_clean, flags=re.DOTALL)
        sql_clean = sql_clean.upper().strip()

        # Check if it starts with SELECT
        if not sql_clean.startswith('SELECT'):
            return False, "Only SELECT statements are allowed"

        # Forbidden keywords/operations
        forbidden_keywords = [
            'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
            'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE',
            'CALL', 'MERGE', 'REPLACE', 'INTO'
        ]

        for keyword in forbidden_keywords:
            # Use word boundaries to avoid false positives (e.g., SELECT_INTO_OUTFILE)
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, sql_clean):
                return False, f"Forbidden operation detected: {keyword}"

        # Allowed keywords check (must contain SELECT)
        allowed_keywords = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING', 'LIMIT']

        return True, None

    def execute_query(self, sql: str) -> tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
        """
        Execute a SELECT query and return results

        Args:
            sql: SQL SELECT statement

        Returns:
            Tuple of (results as list of dicts, error_message)
            If successful: (results, None)
            If error: (None, error_message)
        """
        # Validate SQL
        is_valid, error_msg = self.validate_sql(sql)
        if not is_valid:
            return None, f"SQL Validation Error: {error_msg}"

        # Check connection
        if self.connection is None or self.cursor is None:
            return None, "Database connection not established"

        try:
            # Execute query
            self.cursor.execute(sql)

            # Fetch all results
            rows = self.cursor.fetchall()

            # Get column names
            if self.cursor.description:
                columns = [column[0] for column in self.cursor.description]
            else:
                return [], None  # No results

            # Convert to list of dictionaries
            results = []
            for row in rows:
                row_dict = {}
                for i, column in enumerate(columns):
                    row_dict[column] = row[i]
                results.append(row_dict)

            return results, None

        except pyodbc.Error as e:
            error_msg = f"Database query error: {e}"
            print(error_msg)
            return None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error executing query: {e}"
            print(error_msg)
            return None, error_msg

    def execute_query_to_dataframe(self, sql: str):
        """
        Execute query and return results as pandas DataFrame

        Args:
            sql: SQL SELECT statement

        Returns:
            Tuple of (DataFrame, error_message)
            If successful: (DataFrame, None)
            If error: (None, error_message)
        """
        import pandas as pd

        # Validate SQL
        is_valid, error_msg = self.validate_sql(sql)
        if not is_valid:
            return None, f"SQL Validation Error: {error_msg}"

        # Check connection
        if self.connection is None:
            return None, "Database connection not established"

        try:
            df = pd.read_sql(sql, self.connection)
            return df, None
        except Exception as e:
            error_msg = f"Error executing query to DataFrame: {e}"
            print(error_msg)
            return None, error_msg

    def close(self) -> None:
        """Close database connection"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            print("Database connection closed")
        except Exception as e:
            print(f"Error closing database connection: {e}")


# Convenience function
def create_connection(connection_string: str) -> DatabaseConnection:
    """
    Create and return a database connection

    Args:
        connection_string: ODBC connection string

    Returns:
        DatabaseConnection instance
    """
    return DatabaseConnection(connection_string)
