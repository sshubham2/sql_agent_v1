"""LangGraph Workflow Nodes for SQL Agent"""
import json
import os
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from agent.state import AgentState
from agent.prompts import (
    MEASURE_IDENTIFICATION_PROMPT,
    QUERY_REWRITE_PROMPT,
    SQL_GENERATION_PROMPT
)
from utils.json_loader import MeasureJSONLoader
from database.connection import DatabaseConnection


# Initialize LLM (will be configured in main)
llm = None


def initialize_llm(model: str = "gpt-4", temperature: float = 0, max_tokens: int = 2000):
    """Initialize the LLM for use in nodes"""
    global llm
    llm = ChatOpenAI(model=model, temperature=temperature, max_tokens=max_tokens)


# Node 1: Input Node
def input_node(state: AgentState) -> AgentState:
    """
    Initialize the workflow with user query and configuration

    Args:
        state: Current agent state

    Returns:
        Updated state
    """
    print("=" * 50)
    print("NODE 1: Input")
    print("=" * 50)
    print(f"User Query: {state['user_query']}")
    print(f"SQL Review Enabled: {state.get('sql_review_enabled', True)}")
    return state


# Node 2: Identify Measures and Dimensions
def identify_measures_node(state: AgentState) -> AgentState:
    """
    Use LLM to identify measures and dimensions from user query

    Args:
        state: Current agent state

    Returns:
        Updated state with identified_measures and identified_dimensions
    """
    print("\n" + "=" * 50)
    print("NODE 2: Identify Measures and Dimensions")
    print("=" * 50)

    user_query = state['user_query']

    # Prepare messages for LLM
    messages = [
        SystemMessage(content=MEASURE_IDENTIFICATION_PROMPT),
        HumanMessage(content=f"User Query: {user_query}")
    ]

    try:
        # Call LLM
        response = llm.invoke(messages)
        response_text = response.content.strip()

        print(f"LLM Response:\n{response_text}")

        # Parse JSON response
        # Extract JSON from markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        parsed = json.loads(response_text)

        state['identified_measures'] = parsed.get('measures', [])
        state['group_by_dimensions'] = parsed.get('group_by', [])
        state['user_filters'] = parsed.get('filters', [])
        state['identified_dimensions'] = state['group_by_dimensions']  # Backward compatibility

        print(f"Identified Measures: {state['identified_measures']}")
        print(f"Group By Dimensions: {state['group_by_dimensions']}")
        print(f"User Filters: {state['user_filters']}")

    except json.JSONDecodeError as e:
        print(f"Error parsing LLM response: {e}")
        state['error'] = f"Failed to parse measure identification: {e}"
    except Exception as e:
        print(f"Error in identify_measures_node: {e}")
        state['error'] = f"Error identifying measures: {e}"

    return state


# Node 3: Rewrite Query
def rewrite_query_node(state: AgentState) -> AgentState:
    """
    Rewrite user query with detailed measure information using JSON configs

    Args:
        state: Current agent state (should have measure_configs loaded)

    Returns:
        Updated state with rewritten_query
    """
    print("\n" + "=" * 50)
    print("NODE 3: Rewrite Query")
    print("=" * 50)

    user_query = state['user_query']
    measures = state.get('identified_measures', [])
    group_by = state.get('group_by_dimensions', [])
    user_filters = state.get('user_filters', [])
    measure_configs = state.get('measure_configs', {})

    # Prepare context for LLM with actual JSON configs
    # Extract ONLY the filters array to emphasize what should be used
    context_parts = [
        f"Original Query: {user_query}",
        f"Identified Measures: {', '.join(measures)}",
        f"Group By Dimensions: {', '.join(group_by)}",
        f"User Filter Conditions: {user_filters}",
        "",
        "Measure Configurations:",
    ]

    for measure_name, config in measure_configs.items():
        context_parts.append(f"\n{measure_name}:")
        context_parts.append(f"  - measure_name: {config.get('measure_name', '')}")
        context_parts.append(f"  - measure_code: {config.get('measure_code', '')}")
        context_parts.append(f"  - info_type: {config.get('info_type', '')}")
        context_parts.append(f"  - formula: {config.get('formula', '')}")
        context_parts.append(f"  - filters (USE ONLY THESE): {config.get('filters', [])}")

    context_parts.append("\nREMEMBER: Use ONLY the filters from measure config. User filter conditions should also be included in the WHERE clause.")

    context = "\n".join(context_parts)

    messages = [
        SystemMessage(content=QUERY_REWRITE_PROMPT),
        HumanMessage(content=context)
    ]

    try:
        # Call LLM
        response = llm.invoke(messages)
        rewritten = response.content.strip()

        state['rewritten_query'] = rewritten
        print(f"Rewritten Query:\n{rewritten}")

    except Exception as e:
        print(f"Error in rewrite_query_node: {e}")
        state['error'] = f"Error rewriting query: {e}"

    return state


# Node 4: Human Review Node 1 (Query Confirmation)
def human_review_node1(state: AgentState) -> AgentState:
    """
    Pause for human review of rewritten query
    This will be handled by GUI - this node just signals the pause

    Args:
        state: Current agent state

    Returns:
        Updated state (user_confirmed_query will be set by GUI)
    """
    print("\n" + "=" * 50)
    print("NODE 4: Human Review - Query Confirmation")
    print("=" * 50)
    print("Waiting for user to review and confirm the rewritten query...")
    print(f"Rewritten Query: {state.get('rewritten_query', '')}")

    # In actual implementation, this will pause and wait for GUI confirmation
    # For now, we'll auto-confirm if user_confirmed_query is not set
    if 'user_confirmed_query' not in state or not state['user_confirmed_query']:
        state['user_confirmed_query'] = state.get('rewritten_query', '')
        print("(Auto-confirmed for testing)")

    print(f"Confirmed Query: {state['user_confirmed_query']}")
    return state


# Node 5: JSON Lookup
def json_lookup_node(state: AgentState) -> AgentState:
    """
    Load measure configurations from JSON files
    Abort if any measure is not found

    Args:
        state: Current agent state

    Returns:
        Updated state with measure_configs or error
    """
    print("\n" + "=" * 50)
    print("NODE 5: JSON Lookup")
    print("=" * 50)

    measures = state.get('identified_measures', [])
    print(f"Looking up configurations for: {measures}")

    # Initialize JSON loader
    measures_dir = os.getenv('MEASURES_DIR', './measures')
    index_file = os.getenv('MEASURE_INDEX_FILE', './measure_index.json')
    loader = MeasureJSONLoader(measures_dir=measures_dir, index_file=index_file)

    # Load configurations for all identified measures
    configs = {}
    not_found = []

    for measure in measures:
        config = loader.get_measure_config(measure)
        if config:
            configs[measure] = config
            print(f"✓ Loaded config for {measure}")
        else:
            not_found.append(measure)
            print(f"✗ Config not found for {measure}")

    # Check if any measures were not found
    if not_found:
        error_msg = f"Configuration not found for measure(s): {', '.join(not_found)}. Please upload the required JSON configuration files."
        print(f"\n ERROR: {error_msg}")
        state['error'] = error_msg
        return state

    state['measure_configs'] = configs
    print(f"\n Successfully loaded {len(configs)} measure configuration(s)")

    return state


# Node 6: SQL Generation
def sql_generation_node(state: AgentState) -> AgentState:
    """
    Generate SQL statement using measure configs and LLM

    Args:
        state: Current agent state

    Returns:
        Updated state with generated_sql
    """
    print("\n" + "=" * 50)
    print("NODE 6: SQL Generation")
    print("=" * 50)

    confirmed_query = state.get('user_confirmed_query', '')
    measure_configs = state.get('measure_configs', {})
    dimensions = state.get('identified_dimensions', [])

    # Prepare context for LLM
    context = f"""
User's Confirmed Query:
{confirmed_query}

Measure Configurations:
{json.dumps(measure_configs, indent=2)}

Requested Dimensions:
{', '.join(dimensions)}

Generate the SQL statement following the constraints in the system prompt.
"""

    messages = [
        SystemMessage(content=SQL_GENERATION_PROMPT),
        HumanMessage(content=context)
    ]

    try:
        # Call LLM
        response = llm.invoke(messages)
        sql = response.content.strip()

        # Clean up SQL (remove markdown code blocks if present)
        if "```sql" in sql:
            sql = sql.split("```sql")[1].split("```")[0].strip()
        elif "```" in sql:
            sql = sql.split("```")[1].split("```")[0].strip()

        state['generated_sql'] = sql
        print(f"Generated SQL:\n{sql}")

        # Validate SQL
        from database.connection import DatabaseConnection
        temp_conn = DatabaseConnection("")  # Just for validation
        is_valid, error_msg = temp_conn.validate_sql(sql)

        if not is_valid:
            print(f"\n⚠ WARNING: SQL Validation Failed: {error_msg}")
            state['error'] = f"Generated SQL validation failed: {error_msg}"

    except Exception as e:
        print(f"Error in sql_generation_node: {e}")
        state['error'] = f"Error generating SQL: {e}"

    return state


# Node 7: Human Review Node 2 (SQL Confirmation) - Conditional
def human_review_node2(state: AgentState) -> AgentState:
    """
    Optionally pause for human review of generated SQL
    This is conditional based on sql_review_enabled setting

    Args:
        state: Current agent state

    Returns:
        Updated state (user_confirmed_sql will be set by GUI if enabled)
    """
    print("\n" + "=" * 50)
    print("NODE 7: Human Review - SQL Confirmation (Optional)")
    print("=" * 50)

    sql_review_enabled = state.get('sql_review_enabled', True)

    if sql_review_enabled:
        print("SQL Review is ENABLED - waiting for user confirmation...")
        print(f"Generated SQL:\n{state.get('generated_sql', '')}")

        # In actual implementation, this will pause and wait for GUI confirmation
        # For now, auto-confirm if not set
        if 'user_confirmed_sql' not in state or not state['user_confirmed_sql']:
            state['user_confirmed_sql'] = state.get('generated_sql', '')
            print("(Auto-confirmed for testing)")
    else:
        print("SQL Review is DISABLED - skipping confirmation")
        state['user_confirmed_sql'] = state.get('generated_sql', '')

    return state


# Node 8: Execute and Export
def execute_and_export_node(state: AgentState) -> AgentState:
    """
    Execute SQL query and export results to CSV

    Args:
        state: Current agent state

    Returns:
        Updated state with execution_results and csv_path
    """
    print("\n" + "=" * 50)
    print("NODE 8: Execute and Export")
    print("=" * 50)

    sql = state.get('user_confirmed_sql') or state.get('generated_sql', '')
    print(f"Executing SQL:\n{sql}")

    # Get database connection string
    # Check state first, then environment variable
    connection_string = state.get('connection_string') or os.getenv('DB_CONNECTION_STRING', '')

    if not connection_string:
        error_msg = "Database connection string not configured. Please set DB_CONNECTION_STRING in .env file or provide connection_string in state."
        print(f"ERROR: {error_msg}")
        state['error'] = error_msg
        return state

    print(f"Using connection: {connection_string[:20]}...")

    try:
        # Connect and execute
        with DatabaseConnection(connection_string) as db:
            df, error_msg = db.execute_query_to_dataframe(sql)

            if error_msg:
                print(f"ERROR: {error_msg}")
                state['error'] = error_msg
                return state

            # Store results
            results = df.to_dict('records')
            state['execution_results'] = results

            print(f"\n✓ Query executed successfully!")
            print(f"  Rows returned: {len(results)}")
            print(f"  Columns: {list(df.columns)}")

            # Preview first few rows
            if len(results) > 0:
                print(f"\nFirst 3 rows (preview):")
                print(df.head(3).to_string())

            # Export to CSV (will be handled by GUI file dialog in actual implementation)
            # For now, we'll just set a placeholder path
            state['csv_path'] = None  # Will be set by GUI
            print("\n(CSV export will be handled by GUI file dialog)")

    except Exception as e:
        error_msg = f"Error executing query: {e}"
        print(f"ERROR: {error_msg}")
        state['error'] = error_msg

    return state
