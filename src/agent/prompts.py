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
- Always filter by the required attributes (info_type, measure_code, and optionally report_aspect) as specified in the measure configuration
- Use the formula specified in the measure configuration (typically SUM(info_value))
- GROUP BY only the dimensions explicitly requested by the user
"""


MEASURE_IDENTIFICATION_PROMPT = f"""
{TABLE_SCHEMA_PROMPT}

## Your Task: Identify Measures, Grouping Dimensions, and Filters

You are analyzing a user's natural language query to identify:
1. **Measures**: Specific metrics being requested (e.g., Current Exposure, EAD, LEQ)
2. **Group By Dimensions**: Attributes to group results by (show data breakdown)
3. **Filter Conditions**: Specific values to filter on (narrow down data)

**CRITICAL RULES - GROUP BY vs FILTER:**

**GROUP BY** (when user wants to see data breakdown):
- Keywords: "by", "per", "grouped by", "for each", "breakdown by"
- Plural mentions WITHOUT specific value: "for products", "for obligors", "and dates"
- Multiple dimensions: "by product and date", "for products and entities"
- Example: "for products" (plural, no specific value) → GROUP BY product_group_code
- Example: "by obligor and date" → GROUP BY obligor_rdm_id, report_date

**FILTER** (when user specifies a particular value):
- Specific values mentioned: "for OTC product", "on 30th Sep", "where entity = ABC"
- Keywords with values: "where", "on", "as of", "for [specific value]"
- Singular with specific identifier: "for OTC", "on Sep 30", "internal products"
- Example: "for OTC product" (specific value) → FILTER product_group_code = 'OTC'
- Example: "on 30th Sep" (specific date) → FILTER report_date = '2024-09-30'

**Guidelines:**
- Prefer standard measure codes when possible (CE, LEQ, EAD instead of full names)
- If dimension mentioned WITHOUT specific value → GROUP BY
- If dimension mentioned WITH specific value → FILTER
- "for products and dates" = GROUP BY both (no values specified)
- "for OTC product on 30th Sep" = FILTER both (values specified)

**Output Format (JSON):**
{{
  "measures": ["CE"],
  "group_by": ["obligor_rdm_id"],
  "filters": [
    {{"column": "product_group_code", "value": "OTC"}},
    {{"column": "report_date", "value": "2024-09-30"}}
  ]
}}

**Examples:**

User Query: "Show me current exposure by obligor"
Output:
{{
  "measures": ["CE"],
  "group_by": ["obligor_rdm_id"],
  "filters": []
}}

User Query: "Give me LEQ for OTC products on 30th Sep"
Explanation: "OTC" is a specific value (FILTER), "30th Sep" is a specific date (FILTER)
Output:
{{
  "measures": ["LEQ"],
  "group_by": [],
  "filters": [
    {{"column": "product_group_code", "value": "OTC"}},
    {{"column": "report_date", "value": "2024-09-30"}}
  ]
}}

User Query: "Give me LEQ for OTC products and cob date"
Explanation: "OTC" is specific (FILTER), but "cob date" with no value means show breakdown BY date (GROUP BY)
Output:
{{
  "measures": ["LEQ"],
  "group_by": ["report_date"],
  "filters": [
    {{"column": "product_group_code", "value": "OTC"}}
  ]
}}

User Query: "Give me LEQ for products and cob date"
Explanation: "products" (plural, no value) = GROUP BY, "cob date" (no value) = GROUP BY
Output:
{{
  "measures": ["LEQ"],
  "group_by": ["product_group_code", "report_date"],
  "filters": []
}}

User Query: "What is the total CE for internal products grouped by legal entity?"
Explanation: "internal" is specific (FILTER), "grouped by legal entity" = GROUP BY
Output:
{{
  "measures": ["CE"],
  "group_by": ["legal_entity"],
  "filters": [
    {{"column": "is_internal", "value": "1"}}
  ]
}}

User Query: "Show me EAD by product and obligor for 30th Sep"
Explanation: "by product and obligor" = GROUP BY both, "30th Sep" is specific date (FILTER)
Output:
{{
  "measures": ["EAD"],
  "group_by": ["product_group_code", "obligor_rdm_id"],
  "filters": [
    {{"column": "report_date", "value": "2024-09-30"}}
  ]
}}

Now analyze the user's query and return ONLY the JSON output.
"""


QUERY_REWRITE_PROMPT = """
## Your Task: Rewrite Query with Detailed Measure Information

You are given:
1. Original user query
2. Identified measures with their JSON configurations
3. Identified dimensions

**CRITICAL RULES:**
1. Use ONLY the fields that exist in the JSON configuration
2. Do NOT add fields like report_aspect if they are not in the "filters" array
3. Do NOT make assumptions about filter values - use EXACTLY what's in the JSON
4. Different measures have different filter requirements - respect each measure's specific configuration

Rewrite the query to include full technical details about the measures, making it clear what data needs to be extracted.

**Guidelines:**
- Use the measure_name from JSON config for full names
- Extract filter conditions ONLY from the "filters" array in the JSON
- Use the formula from JSON config (e.g., SUM(info_value))
- Clarify the aggregation method from the formula
- Make grouping explicit using dimensions
- Keep the query natural but technically precise

**Example 1 - Measure WITHOUT report_aspect:**

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

**Example 2 - Measure WITH report_aspect:**

Original Query: "Show me CE by obligor"
Measure Config:
{{
  "measure_code": "CE",
  "measure_name": "Current Exposure",
  "info_type": "CE",
  "formula": "SUM(info_value)",
  "filters": ["info_type='CE'", "measure_code='CE'", "report_aspect IN ('CREDIT','CREDIT_ALD')"]
}}
Identified Dimensions: ["obligor_rdm_id"]

Rewritten Query:
"Calculate the Current Exposure (CE) measure by summing info_value, where info_type='CE', measure_code='CE', and report_aspect is in ('CREDIT', 'CREDIT_ALD'). Group the results by obligor_rdm_id to show exposure per obligor."

**IMPORTANT**: Copy the filter conditions EXACTLY from the "filters" array. Do not add any filters that are not listed there.

Now rewrite the user's query using ONLY the filters from the provided measure configurations.
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
- Groups by ONLY the user-requested dimensions (if any)
- Uses proper SQL syntax for MySQL

**IMPORTANT CONSTRAINTS:**
- NO INSERT, UPDATE, DELETE, DROP, or other modification statements
- NO subqueries unless absolutely necessary
- Use clear column aliases for calculated measures
- Ensure all filters are properly combined with AND
- CRITICAL: Use ONLY the dimensions explicitly requested by the user in GROUP BY clause
- Do NOT add default_group_by columns unless the user specifically requested them

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

**Example 1 - With User-Requested Dimensions:**

Measure Config for CE:
{{
  "formula": "SUM(info_value)",
  "filters": ["info_type='CE'", "measure_code='CE'", "report_aspect IN ('CREDIT','CREDIT_ALD')"]
}}

User-Requested Dimensions: ["product_group_code", "report_date"]

Generated SQL:
```sql
SELECT
    product_group_code,
    report_date,
    SUM(info_value) AS current_exposure
FROM risk_measures
WHERE info_type='CE'
    AND measure_code='CE'
    AND report_aspect IN ('CREDIT','CREDIT_ALD')
GROUP BY product_group_code, report_date
ORDER BY product_group_code, report_date
```

**Example 2 - No Grouping (Aggregate Only):**

Measure Config for LEQ:
{{
  "formula": "SUM(info_value)",
  "filters": ["info_type='LEQ'", "measure_code='EPE'"]
}}

User-Requested Dimensions: []

Generated SQL:
```sql
SELECT
    SUM(info_value) AS loan_equivalent
FROM risk_measures
WHERE info_type='LEQ'
    AND measure_code='EPE'
```

Now generate the SQL statement for the given query and configurations.
Return ONLY the SQL statement, no explanations.
"""
