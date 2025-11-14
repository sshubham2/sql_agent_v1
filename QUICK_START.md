# Quick Start Guide

## Setup (5 minutes)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Edit `.env` file with your credentials:

```env
OPENAI_API_KEY=sk-your-actual-api-key-here
DB_CONNECTION_STRING=DRIVER={MySQL ODBC 8.0 Driver};SERVER=your-server;DATABASE=your-db;USER=your-user;PASSWORD=your-password;
```

### 3. Update Table Schema

Edit `src/agent/prompts.py` and update `TABLE_SCHEMA_PROMPT` with your actual table information:

- Table name
- Column descriptions
- Available info_type, measure_code, report_aspect combinations

### 4. Add Your Measures

The `measures/` folder already has two example measures (CE.json, EAD.json).

To add your own:
- Copy one of the existing JSON files
- Update with your measure details
- Save with a descriptive filename (e.g., `LGD.json`)

## Running the Application

### Option 1: Using the launcher (Recommended)

```bash
python run.py
```

### Option 2: From src directory

```bash
cd src
python main.py
```

## Testing

### Run all tests:

```bash
python tests/run_all_tests.py
```

### Run individual tests:

```bash
# Test SQL validation (no DB needed)
python tests/test_sql_validation.py

# Test JSON loader (requires CE.json to exist)
python tests/test_json_loader.py

# Test database connection (requires .env configuration)
python tests/test_db_connection.py
```

## First Query Example

1. Launch the application: `python run.py`
2. Enter a query like: **"Show me current exposure by obligor"**
3. Click "Submit Query"
4. Review the rewritten query and click "Confirm Query"
5. Review the generated SQL (if enabled) and click "Confirm & Execute SQL"
6. View results and export to CSV

## Troubleshooting

### "attempted relative import beyond top-level package"
- **Solution**: Use `python run.py` from the root directory

### "No module named 'langgraph'"
- **Solution**: Run `pip install -r requirements.txt`

### "OPENAI_API_KEY not found"
- **Solution**: Edit `.env` file with your actual API key

### "Database connection failed"
- **Solution**: Check your `DB_CONNECTION_STRING` in `.env`
- Verify MySQL ODBC driver is installed
- Test with: `python tests/test_db_connection.py`

### "Configuration not found for measure: XYZ"
- **Solution**: Create `measures/XYZ.json` or use the GUI upload button
- Make sure the measure code matches what's in your query

## Directory Structure Reference

```
sql_agent_v1/
├── run.py                    ← Run this to launch the app
├── .env                      ← Configure your credentials here
├── config.yaml               ← App settings
├── measures/                 ← Add your measure JSONs here
│   ├── CE.json
│   └── EAD.json
├── src/
│   ├── main.py
│   └── ...
└── tests/                    ← Run tests from here
    └── run_all_tests.py
```

## Next Steps

1. **Customize prompts**: Edit `src/agent/prompts.py` to match your table schema
2. **Add more measures**: Create JSON files for all your measures
3. **Test thoroughly**: Run test scripts to verify everything works
4. **Start querying**: Use natural language to query your database!

## Support

- Check [README.md](README.md) for detailed documentation
- Review test scripts for usage examples
- Examine `measures/CE.json` for JSON structure reference
