"""Utility functions for loading and managing measure JSON configurations"""
import json
import os
from typing import Dict, Optional, List
from pathlib import Path


class MeasureJSONLoader:
    """Handles loading and matching of measure configuration JSON files"""

    def __init__(self, measures_dir: str = "./measures", index_file: str = "./measure_index.json"):
        """
        Initialize the JSON loader

        Args:
            measures_dir: Directory containing measure JSON files
            index_file: Path to measure index file
        """
        self.measures_dir = Path(measures_dir)
        self.index_file = Path(index_file)
        self.index = {}
        self._load_index()

    def _load_index(self) -> None:
        """Load the measure index from file"""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r') as f:
                    data = json.load(f)
                    # Filter out comment keys
                    self.index = {k: v for k, v in data.items() if not k.startswith('_')}
            else:
                self.index = {}
        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse index file: {e}")
            self.index = {}
        except Exception as e:
            print(f"Warning: Error loading index file: {e}")
            self.index = {}

    def save_index(self) -> None:
        """Save the current index to file"""
        try:
            with open(self.index_file, 'w') as f:
                json.dump(self.index, f, indent=2)
        except Exception as e:
            print(f"Error saving index file: {e}")

    def scan_measures_directory(self) -> Dict[str, str]:
        """
        Scan the measures directory and rebuild the index

        Returns:
            Dictionary mapping aliases to JSON filenames
        """
        self.index = {}

        if not self.measures_dir.exists():
            print(f"Warning: Measures directory {self.measures_dir} does not exist")
            return self.index

        # Scan all JSON files in the directory
        for json_file in self.measures_dir.glob("*.json"):
            try:
                config = self.load_measure_config(json_file.name)
                if config:
                    # Add measure code
                    measure_code = config.get("measure_code", "")
                    if measure_code:
                        self.index[measure_code.lower()] = json_file.name

                    # Add measure name
                    measure_name = config.get("measure_name", "")
                    if measure_name:
                        self.index[measure_name.lower()] = json_file.name

                    # Add all aliases
                    aliases = config.get("aliases", [])
                    for alias in aliases:
                        self.index[alias.lower()] = json_file.name

            except Exception as e:
                print(f"Warning: Could not process {json_file.name}: {e}")

        # Save the rebuilt index
        self.save_index()
        return self.index

    def find_measure_json(self, measure_name: str) -> Optional[str]:
        """
        Find the JSON filename for a given measure name or alias

        Args:
            measure_name: Measure name or alias to search for

        Returns:
            JSON filename if found, None otherwise
        """
        # Normalize the search term
        search_term = measure_name.lower().strip()

        # Try exact match in index
        if search_term in self.index:
            return self.index[search_term]

        # If not found in index, try scanning directory
        print(f"Measure '{measure_name}' not found in index, scanning directory...")
        self.scan_measures_directory()

        # Try again after scanning
        if search_term in self.index:
            return self.index[search_term]

        # Still not found
        return None

    def load_measure_config(self, json_filename: str) -> Optional[Dict]:
        """
        Load a measure configuration from a JSON file

        Args:
            json_filename: Name of the JSON file (with or without .json extension)

        Returns:
            Dictionary containing measure configuration, None if error
        """
        # Ensure .json extension
        if not json_filename.endswith('.json'):
            json_filename += '.json'

        file_path = self.measures_dir / json_filename

        try:
            if not file_path.exists():
                print(f"Error: Measure file {file_path} does not exist")
                return None

            with open(file_path, 'r') as f:
                config = json.load(f)
                return config

        except json.JSONDecodeError as e:
            print(f"Error: Malformed JSON in {json_filename}: {e}")
            return None
        except Exception as e:
            print(f"Error loading {json_filename}: {e}")
            return None

    def get_measure_config(self, measure_name: str) -> Optional[Dict]:
        """
        Get measure configuration by name or alias (convenience method)

        Args:
            measure_name: Measure name or alias

        Returns:
            Dictionary containing measure configuration, None if not found
        """
        json_filename = self.find_measure_json(measure_name)
        if json_filename:
            return self.load_measure_config(json_filename)
        return None

    def load_multiple_measures(self, measure_names: List[str]) -> Dict[str, Dict]:
        """
        Load configurations for multiple measures

        Args:
            measure_names: List of measure names or aliases

        Returns:
            Dictionary mapping measure names to their configurations
            Only includes successfully loaded measures
        """
        configs = {}
        not_found = []

        for measure_name in measure_names:
            config = self.get_measure_config(measure_name)
            if config:
                configs[measure_name] = config
            else:
                not_found.append(measure_name)

        if not_found:
            print(f"Warning: Could not find configurations for: {', '.join(not_found)}")

        return configs

    def update_measure_index(self, measure_code: str, aliases: List[str], filename: str) -> None:
        """
        Update the index with a new measure or aliases

        Args:
            measure_code: Measure code
            aliases: List of aliases for the measure
            filename: JSON filename
        """
        # Add measure code
        self.index[measure_code.lower()] = filename

        # Add all aliases
        for alias in aliases:
            self.index[alias.lower()] = filename

        # Save updated index
        self.save_index()

    def list_available_measures(self) -> List[str]:
        """
        Get a list of all available measure codes

        Returns:
            List of unique JSON filenames
        """
        self.scan_measures_directory()
        return list(set(self.index.values()))


# Convenience functions for direct usage
def load_measure_index(index_file: str = "./measure_index.json") -> Dict[str, str]:
    """Load measure index from file"""
    loader = MeasureJSONLoader(index_file=index_file)
    return loader.index


def find_measure_json(measure_name: str, measures_dir: str = "./measures",
                      index_file: str = "./measure_index.json") -> Optional[str]:
    """Find JSON filename for a measure"""
    loader = MeasureJSONLoader(measures_dir=measures_dir, index_file=index_file)
    return loader.find_measure_json(measure_name)


def load_measure_config(json_filename: str, measures_dir: str = "./measures") -> Optional[Dict]:
    """Load a single measure configuration"""
    loader = MeasureJSONLoader(measures_dir=measures_dir)
    return loader.load_measure_config(json_filename)


def scan_measures_directory(measures_dir: str = "./measures",
                            index_file: str = "./measure_index.json") -> Dict[str, str]:
    """Scan measures directory and rebuild index"""
    loader = MeasureJSONLoader(measures_dir=measures_dir, index_file=index_file)
    return loader.scan_measures_directory()
