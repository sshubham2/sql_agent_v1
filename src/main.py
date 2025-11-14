"""Main entry point for SQL Agent application"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import yaml


def load_configuration():
    """Load environment variables and configuration"""
    # Load .env file
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(env_path)

    # Load config.yaml
    config_path = Path(__file__).parent.parent / 'config.yaml'
    config = {}

    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    else:
        print(f"Warning: Config file not found at {config_path}")
        config = {
            'sql_review_enabled': True,
            'default_export_dir': './outputs',
            'measures_dir': './measures',
            'measure_index_file': './measure_index.json',
            'llm': {
                'model': 'gpt-4',
                'temperature': 0,
                'max_tokens': 2000
            }
        }

    return config


def initialize_llm(config):
    """Initialize the LLM for agent nodes"""
    from agent.nodes import initialize_llm

    llm_config = config.get('llm', {})
    model = llm_config.get('model', 'gpt-4')
    temperature = llm_config.get('temperature', 0)
    max_tokens = llm_config.get('max_tokens', 2000)

    print(f"Initializing LLM: {model}")
    initialize_llm(model=model, temperature=temperature, max_tokens=max_tokens)


def check_environment():
    """Check if required environment variables are set"""
    required_vars = ['OPENAI_API_KEY', 'DB_CONNECTION_STRING']
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("\n" + "=" * 60)
        print("WARNING: Missing required environment variables:")
        print("=" * 60)
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease configure these in the .env file")
        print("=" * 60 + "\n")

        if 'OPENAI_API_KEY' in missing_vars:
            print("Note: The LLM will not work without an API key")

        if 'DB_CONNECTION_STRING' in missing_vars:
            print("Note: Database queries will not work without a connection string")

        # Ask user if they want to continue anyway
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)


def setup_directories(config):
    """Create necessary directories if they don't exist"""
    dirs = [
        config.get('measures_dir', './measures'),
        config.get('default_export_dir', './outputs')
    ]

    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)


def main():
    """Main entry point"""
    print("=" * 60)
    print("SQL Agent - Measure Query Assistant")
    print("=" * 60)

    # Load configuration
    print("\nLoading configuration...")
    config = load_configuration()

    # Check environment
    print("Checking environment variables...")
    check_environment()

    # Setup directories
    print("Setting up directories...")
    setup_directories(config)

    # Initialize LLM
    try:
        initialize_llm(config)
        print("✓ LLM initialized")
    except Exception as e:
        print(f"✗ Failed to initialize LLM: {e}")
        print("  The application may not work correctly without a valid API key")

    # Scan for measure configurations
    print("\nScanning for measure configurations...")
    try:
        from utils.json_loader import scan_measures_directory
        measures_dir = config.get('measures_dir', './measures')
        index_file = config.get('measure_index_file', './measure_index.json')
        index = scan_measures_directory(measures_dir=measures_dir, index_file=index_file)

        num_measures = len(set(index.values()))
        print(f"✓ Found {num_measures} measure configuration(s)")

        if num_measures == 0:
            print("  Note: No measure configurations found. You can upload them via the GUI.")

    except Exception as e:
        print(f"✗ Error scanning measures: {e}")

    # Launch GUI
    print("\nLaunching GUI...")
    print("=" * 60 + "\n")

    try:
        from gui.app import launch_gui
        launch_gui()
    except KeyboardInterrupt:
        print("\n\nApplication terminated by user")
    except Exception as e:
        print(f"\nError launching GUI: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
