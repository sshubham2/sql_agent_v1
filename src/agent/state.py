"""Agent State Schema for LangGraph Workflow"""
from typing import TypedDict, List, Dict, Optional


class AgentState(TypedDict):
    """State schema for the SQL Agent workflow"""

    # Input
    user_query: str

    # Identification phase
    identified_measures: List[str]
    identified_dimensions: List[str]

    # Query rewrite phase
    rewritten_query: str
    user_confirmed_query: str

    # JSON lookup phase
    measure_configs: Dict  # Only contains configs for identified measures

    # SQL generation phase
    generated_sql: str
    user_confirmed_sql: Optional[str]

    # Execution phase
    execution_results: Optional[List[Dict]]
    csv_path: Optional[str]

    # Error handling
    error: Optional[str]

    # Configuration
    sql_review_enabled: bool
