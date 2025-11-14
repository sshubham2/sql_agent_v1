"""System Prompts for LangGraph Agent Nodes"""

# Table schema and metadata (to be customized by user)
TABLE_SCHEMA_PROMPT = """
## Database Table Schema

**Table Name:** [TO BE CONFIGURED BY USER]

**Table Description:**
This table contains risk measures and metrics data.

**Column Descriptions:**
- `info_type`: Type of information/measure (e.g., CE, EAD, LGD)
- `measure_code`: Measure code identifier
- `report_aspect`: Reporting aspect (e.g., CREDIT, CREDIT_ALD)
- `info_value`: Numeric value for the measure
- `obligor_rdm_id`: Obligor identifier
- `product_group_code`: Product group code
- `legal_entity`: Legal entity identifier
- `is_internal`: Internal/External flag
- [Additional columns to be added by user]

**Available Measure Combinations:**
To extract any measure, you need 3 pieces of information:
1. `info_type` - Type of measure
2. `measure_code` - Measure code
3. `report_aspect` - Reporting aspect value(s)

**Example Combinations:**
- Current Exposure (CE): info_type='CE', measure_code='CE', report_aspect IN ('CREDIT', 'CREDIT_ALD')
- [Additional combinations to be added by user]

**Important Notes:**
- Always filter by all three attributes (info_type, measure_code, report_aspect) for accurate results
- Use the formula specified in the measure configuration (typically SUM(info_value))
- Default grouping columns ensure proper aggregation
"""


MEASURE_IDENTIFICATION_PROMPT = f"""
{TABLE_SCHEMA_PROMPT}

## Your Task: Identify Measures and Dimensions

You are analyzing a user's natural language query to identify:
1. **Measures**: Specific metrics being requested (e.g., Current Exposure, EAD)
2. **Dimensions**: Attributes to group or filter by (e.g., obligor, product, date)

**Guidelines:**
- Prefer standard measure codes when possible (CE instead of "Current Exposure")
- Look for keywords indicating aggregation (sum, total, count, average)
- Identify grouping dimensions (by obligor, by product, etc.)
- Identify filtering dimensions (where, for specific, only)

**Output Format (JSON):**
{{
  "measures": ["CE", "EAD"],
  "dimensions": ["obligor_rdm_id", "product_group_code", "legal_entity"]
}}

**Examples:**

User Query: "Show me current exposure by obligor"
Output:
{{
  "measures": ["CE"],
  "dimensions": ["obligor_rdm_id"]
}}

User Query: "What is the total CE and EAD for internal products grouped by legal entity?"
Output:
{{
  "measures": ["CE", "EAD"],
  "dimensions": ["legal_entity", "is_internal"]
}}

Now analyze the user's query and return ONLY the JSON output.
"""


QUERY_REWRITE_PROMPT = """
## Your Task: Rewrite Query with Detailed Measure Information

You are given:
1. Original user query
2. Identified measures with their JSON configurations
3. Identified dimensions

**IMPORTANT**: Use the EXACT values from the JSON configurations. Do NOT make up or assume values.

Rewrite the query to include full technical details about the measures, making it clear what data needs to be extracted.

**Guidelines:**
- Use the measure_name from JSON config for full names
- Use the EXACT info_type, measure_code, and report_aspect values from the JSON config
- Use the formula from JSON config (e.g., SUM(info_value))
- Clarify the aggregation method from the formula
- Make grouping explicit using dimensions
- Keep the query natural but technically precise
- If a measure doesn't have report_aspect in the JSON, don't mention it

**Example:**

Original Query: "Show me LEQ by obligor"
Measure Config:
{{
  "measure_code": "EPE",
  "measure_name": "Loan Equivalent",
  "info_type": "LEQ",
  "formula": "SUM(info_value)",
  "filters": ["info_type='LEQ'", "measure_code='EPE'"]
}}
Identified Dimensions: ["obligor_rdm_id"]

Rewritten Query:
"Calculate the Loan Equivalent (LEQ) measure by summing info_value, where info_type='LEQ' and measure_code='EPE'. Group the results by obligor_rdm_id to show loan equivalent per obligor."

Now rewrite the user's query using the EXACT values from the provided measure configurations.
"""


SQL_GENERATION_PROMPT = f"""
{TABLE_SCHEMA_PROMPT}

## Your Task: Generate SQL Statement

You are given:
1. User's confirmed query (rewritten with details)
2. Measure configurations (JSON) for each identified measure
3. Identified dimensions

Generate a SQL SELECT statement that:
- Uses ONLY SELECT, WHERE, GROUP BY, and ORDER BY clauses
- Applies the formula from measure config (e.g., SUM(info_value))
- Includes all required filters from measure config
- Groups by default_group_by columns + user-requested dimensions
- Uses proper SQL syntax for MySQL

**IMPORTANT CONSTRAINTS:**
- NO INSERT, UPDATE, DELETE, DROP, or other modification statements
- NO subqueries unless absolutely necessary
- Use clear column aliases for calculated measures
- Ensure all filters are properly combined with AND

**SQL Format:**
```sql
SELECT
    [grouping_columns],
    [measure_formula] AS [measure_name]
FROM [table_name]
WHERE [all_required_filters]
GROUP BY [all_grouping_columns]
ORDER BY [if requested]
```

**Example:**

Measure Config for CE:
{{
  "formula": "SUM(info_value)",
  "filters": ["info_type='CE'", "measure_code='CE'", "report_aspect IN ('CREDIT','CREDIT_ALD')"],
  "default_group_by": ["obligor_rdm_id", "product_group_code"]
}}

Dimensions: ["obligor_rdm_id"]

Generated SQL:
```sql
SELECT
    obligor_rdm_id,
    product_group_code,
    SUM(info_value) AS current_exposure
FROM risk_measures
WHERE info_type='CE'
    AND measure_code='CE'
    AND report_aspect IN ('CREDIT','CREDIT_ALD')
GROUP BY obligor_rdm_id, product_group_code
ORDER BY obligor_rdm_id
```

Now generate the SQL statement for the given query and configurations.
Return ONLY the SQL statement, no explanations.
"""
