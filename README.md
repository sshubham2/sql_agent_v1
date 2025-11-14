# SQL Agent - Measure Query Assistant

A natural language SQL query agent built with LangGraph and Tkinter that helps users query database measures using conversational language.

## Features

- **Natural Language Processing**: Convert plain English queries into SQL statements
- **Measure-Specific Configuration**: Each measure has its own JSON configuration with formulas, filters, and grouping rules
- **Interactive GUI**: Tkinter-based interface with human-in-the-loop confirmations
- **LangGraph Workflow**: 8-node workflow for robust query processing
- **SQL Safety**: Only SELECT queries allowed, with validation
- **CSV Export**: Export query results to CSV files

## Architecture

### Workflow (8 Nodes)

```
1. Input Node → Receive user query
2. Identify Measures Node → LLM identifies measures and dimensions
3. Rewrite Query Node → LLM rewrites with technical details
4. Human Review Node 1 → User confirms/edits rewritten query
5. JSON Lookup Node → Load measure configs (abort if not found)
6. SQL Generation Node → Generate SQL using configs
7. Human Review Node 2 → Optional SQL review (toggleable)
8. Execute & Export Node → Execute query and export to CSV
```

## Installation

### Prerequisites

- Python 3.8+
- MySQL ODBC Driver 8.0 (or compatible)
- OpenAI API Key (or other LLM provider)

### Setup

1. **Clone or download this repository**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:

   Edit `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   DB_CONNECTION_STRING=DRIVER={MySQL ODBC 8.0 Driver};SERVER=localhost;DATABASE=your_db;USER=user;PASSWORD=pass;
   ```

4. **Configure application settings**:

   Edit `config.yaml` as needed:
   ```yaml
   sql_review_enabled: true
   default_export_dir: ./outputs
   measures_dir: ./measures
   ```

5. **Add measure configurations**:

   Create JSON files in `measures/` directory (see below)

## Measure Configuration

Each measure requires a separate JSON file in the `measures/` directory.

### Example: `measures/CE.json`

```json
{
  "measure_code": "CE",
  "measure_name": "Current Exposure",
  "aliases": [
    "CE",
    "Current Exposure",
    "current exposure",
    "Curr Exp",
    "curr exp"
  ],
  "info_type": "CE",
  "formula": "SUM(info_value)",
  "report_aspect": ["CREDIT", "CREDIT_ALD"],
  "filters": [
    "info_type='CE'",
    "measure_code='CE'",
    "report_aspect IN ('CREDIT','CREDIT_ALD')"
  ],
  "default_group_by": [
    "obligor_rdm_id",
    "product_group_code",
    "legal_entity",
    "is_internal"
  ]
}
```

### JSON Structure

- **measure_code**: Unique identifier for the measure
- **measure_name**: Full name of the measure
- **aliases**: List of alternative names (used for matching user queries)
- **info_type**: Database info_type value
- **formula**: SQL aggregation formula (e.g., `SUM(info_value)`)
- **report_aspect**: List of valid report_aspect values
- **filters**: SQL WHERE conditions required for this measure
- **default_group_by**: Default columns to group by

### Adding New Measures

1. Create a new JSON file in `measures/` directory
2. Use the GUI's "Upload Measure JSON" button, OR
3. Manually add the file and restart the application

The system will automatically scan and index all measure files.

## Usage

### Running the Application

```bash
cd src
python main.py
```

Or from the root directory:
```bash
python src/main.py
```

### GUI Workflow

1. **Enter Query**: Type your natural language query
   - Example: "Show me current exposure by obligor"

2. **Review Identified Measures**: The system shows identified measures and dimensions

3. **Review Rewritten Query**: Edit if needed, then click "Confirm Query"

4. **Review Generated SQL** (optional): If enabled, review and edit SQL before execution

5. **View Results**: Results displayed in table format

6. **Export**: Click "Export to CSV" to save results

### Example Queries

```
Show me CE by obligor
What is the total current exposure for internal products?
Give me EAD and CE grouped by legal entity
Show current exposure where legal entity is XYZ
```

## Configuration

### System Prompts

Update table schema and available measures in `src/agent/prompts.py`:

```python
TABLE_SCHEMA_PROMPT = """
**Table Name:** risk_measures

**Column Descriptions:**
- info_type: Type of measure
- measure_code: Measure code
- report_aspect: Reporting aspect
...
"""
```

### LLM Settings

Edit `config.yaml`:

```yaml
llm:
  model: gpt-4
  temperature: 0
  max_tokens: 2000
```

## Testing

Run all tests:
```bash
cd tests
python run_all_tests.py
```

Run individual test suites:
```bash
python tests/test_sql_validation.py
python tests/test_json_loader.py
python tests/test_db_connection.py
```

### Test Coverage

- **SQL Validation**: Tests allowed/forbidden SQL operations
- **JSON Loader**: Tests measure loading and alias matching
- **Database Connection**: Tests ODBC connection and query execution

## Project Structure

```
sql_agent_v1/
├── .env                          # Environment variables
├── .gitignore
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── config.yaml                   # Application configuration
├── measure_index.json            # Auto-generated alias index
├── measures/                     # Measure JSON configurations
│   ├── CE.json
│   └── ...
├── outputs/                      # CSV exports
├── src/
│   ├── main.py                  # Entry point
│   ├── agent/
│   │   ├── graph.py             # LangGraph workflow
│   │   ├── nodes.py             # Workflow nodes
│   │   ├── state.py             # State schema
│   │   └── prompts.py           # System prompts
│   ├── database/
│   │   └── connection.py        # Database connection
│   ├── gui/
│   │   └── app.py               # Tkinter GUI
│   └── utils/
│       └── json_loader.py       # JSON utilities
└── tests/
    ├── test_db_connection.py
    ├── test_json_loader.py
    ├── test_sql_validation.py
    └── run_all_tests.py
```

## Troubleshooting

### Issue: "OPENAI_API_KEY not found"
- Solution: Configure `.env` file with your API key

### Issue: "Database connection failed"
- Solution: Check `DB_CONNECTION_STRING` in `.env`
- Ensure MySQL ODBC driver is installed
- Verify database is accessible

### Issue: "Configuration not found for measure"
- Solution: Create JSON file for the measure in `measures/` directory
- Use "Upload Measure JSON" button in GUI
- Check that aliases match your query terms

### Issue: "SQL Validation Error"
- Solution: The system only allows SELECT queries
- Ensure generated SQL doesn't contain INSERT/UPDATE/DELETE/DROP

### Issue: "Module not found"
- Solution: Install dependencies: `pip install -r requirements.txt`

## Security Notes

- **SQL Injection Protection**: Only SELECT statements allowed
- **No Data Modification**: INSERT/UPDATE/DELETE/DROP are blocked
- **Parameterized Queries**: Use proper SQL escaping
- **Environment Variables**: Keep `.env` file secure and never commit it

## Customization

### Using Different LLM Providers

Edit `src/agent/nodes.py` to change LLM provider:

```python
# For Anthropic Claude
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic(model="claude-3-opus-20240229")

# For Azure OpenAI
from langchain_openai import AzureChatOpenAI
llm = AzureChatOpenAI(...)
```

### Customizing GUI

Edit `src/gui/app.py` to modify layout, colors, or add features.

### Adding New Workflow Nodes

1. Define node function in `src/agent/nodes.py`
2. Add node to workflow in `src/agent/graph.py`
3. Update state schema in `src/agent/state.py` if needed

## Contributing

To add new features:
1. Update the workflow graph in `src/agent/graph.py`
2. Add corresponding nodes in `src/agent/nodes.py`
3. Update GUI if needed in `src/gui/app.py`
4. Add tests in `tests/`
5. Update this README

## License

This project is provided as-is for internal use.

## Support

For issues or questions, please refer to:
- Code documentation in source files
- Test scripts for usage examples
- This README for configuration help
