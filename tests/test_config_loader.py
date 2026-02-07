"""Tests for configuration loading and merging functionality."""

import unittest
import tempfile
import os
from pathlib import Path
from deckdex.config_loader import (
    load_yaml_config,
    _deep_merge,
    apply_env_overrides,
    build_processor_config,
    load_config
)
from deckdex.config import ProcessorConfig


class TestConfigLoader(unittest.TestCase):
    """Test configuration loader functions."""
    
    def test_deep_merge_simple(self):
        """Test deep merge with simple dictionaries."""
        base = {"a": 1, "b": 2}
        overlay = {"b": 3, "c": 4}
        result = _deep_merge(base, overlay)
        
        self.assertEqual(result["a"], 1)
        self.assertEqual(result["b"], 3)  # overlay wins
        self.assertEqual(result["c"], 4)
    
    def test_deep_merge_nested(self):
        """Test deep merge with nested dictionaries."""
        base = {
            "processing": {
                "batch_size": 20,
                "max_workers": 4
            },
            "api": {
                "scryfall": {
                    "max_retries": 3
                }
            }
        }
        overlay = {
            "processing": {
                "batch_size": 10  # Override only batch_size
            },
            "api": {
                "scryfall": {
                    "timeout": 5.0  # Add new field
                }
            }
        }
        result = _deep_merge(base, overlay)
        
        # Overlay value
        self.assertEqual(result["processing"]["batch_size"], 10)
        # Preserved base value
        self.assertEqual(result["processing"]["max_workers"], 4)
        # New field from overlay
        self.assertEqual(result["api"]["scryfall"]["timeout"], 5.0)
        # Preserved base value
        self.assertEqual(result["api"]["scryfall"]["max_retries"], 3)
    
    def test_load_yaml_config_with_profiles(self):
        """Test loading YAML config with different profiles."""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
default:
  processing:
    batch_size: 20
    max_workers: 4
  
development:
  processing:
    batch_size: 10
    max_workers: 2

production:
  processing:
    batch_size: 50
    max_workers: 8
""")
            temp_path = f.name
        
        try:
            # Test default profile
            config = load_yaml_config(temp_path, "default")
            self.assertEqual(config["processing"]["batch_size"], 20)
            self.assertEqual(config["processing"]["max_workers"], 4)
            
            # Test development profile (merges with default)
            config = load_yaml_config(temp_path, "development")
            self.assertEqual(config["processing"]["batch_size"], 10)
            self.assertEqual(config["processing"]["max_workers"], 2)
            
            # Test production profile (merges with default)
            config = load_yaml_config(temp_path, "production")
            self.assertEqual(config["processing"]["batch_size"], 50)
            self.assertEqual(config["processing"]["max_workers"], 8)
        finally:
            os.unlink(temp_path)
    
    def test_load_yaml_config_nonexistent_profile(self):
        """Test loading with non-existent profile falls back to default."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
default:
  processing:
    batch_size: 20
""")
            temp_path = f.name
        
        try:
            config = load_yaml_config(temp_path, "nonexistent")
            # Should fall back to default
            self.assertEqual(config["processing"]["batch_size"], 20)
        finally:
            os.unlink(temp_path)


class TestEnvOverrides(unittest.TestCase):
    """Test environment variable overrides."""
    
    def setUp(self):
        """Save original environment."""
        self.original_env = os.environ.copy()
    
    def tearDown(self):
        """Restore original environment."""
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_apply_env_overrides_int(self):
        """Test applying integer environment variable overrides."""
        config = {
            "processing": {
                "batch_size": 20
            }
        }
        os.environ["DECKDEX_PROCESSING_BATCH_SIZE"] = "30"
        
        result = apply_env_overrides(config)
        self.assertEqual(result["processing"]["batch_size"], 30)
        self.assertIsInstance(result["processing"]["batch_size"], int)
    
    def test_apply_env_overrides_float(self):
        """Test applying float environment variable overrides."""
        config = {
            "processing": {
                "api_delay": 0.1
            }
        }
        os.environ["DECKDEX_PROCESSING_API_DELAY"] = "0.2"
        
        result = apply_env_overrides(config)
        self.assertEqual(result["processing"]["api_delay"], 0.2)
        self.assertIsInstance(result["processing"]["api_delay"], float)
    
    def test_apply_env_overrides_bool_true(self):
        """Test applying boolean true environment variable overrides."""
        config = {
            "api": {
                "openai": {
                    "enabled": False
                }
            }
        }
        
        for true_value in ["true", "True", "1", "yes", "Yes"]:
            os.environ["DECKDEX_OPENAI_ENABLED"] = true_value
            result = apply_env_overrides(config.copy())
            self.assertTrue(result["api"]["openai"]["enabled"], f"Failed for value: {true_value}")
    
    def test_apply_env_overrides_bool_false(self):
        """Test applying boolean false environment variable overrides."""
        config = {
            "api": {
                "openai": {
                    "enabled": True
                }
            }
        }
        
        for false_value in ["false", "False", "0", "no", "No"]:
            os.environ["DECKDEX_OPENAI_ENABLED"] = false_value
            result = apply_env_overrides(config.copy())
            self.assertFalse(result["api"]["openai"]["enabled"], f"Failed for value: {false_value}")
    
    def test_apply_env_overrides_string(self):
        """Test applying string environment variable overrides."""
        config = {
            "api": {
                "google_sheets": {
                    "sheet_name": "magic"
                }
            }
        }
        os.environ["DECKDEX_GOOGLE_SHEETS_SHEET_NAME"] = "my_custom_sheet"
        
        result = apply_env_overrides(config)
        self.assertEqual(result["api"]["google_sheets"]["sheet_name"], "my_custom_sheet")
    
    def test_apply_env_overrides_ignores_non_deckdex(self):
        """Test that non-DECKDEX_ variables are ignored."""
        config = {
            "processing": {
                "batch_size": 20
            }
        }
        os.environ["SOME_OTHER_VAR"] = "30"
        
        result = apply_env_overrides(config)
        self.assertEqual(result["processing"]["batch_size"], 20)  # Unchanged


class TestBuildProcessorConfig(unittest.TestCase):
    """Test building ProcessorConfig from merged sources."""
    
    def test_build_processor_config_defaults(self):
        """Test building config with default values."""
        yaml_config = {
            "processing": {
                "batch_size": 20,
                "max_workers": 4,
                "api_delay": 0.1,
                "write_buffer_batches": 3
            },
            "api": {
                "scryfall": {
                    "max_retries": 3,
                    "retry_delay": 0.5,
                    "timeout": 10.0
                },
                "google_sheets": {
                    "batch_size": 500,
                    "max_retries": 5,
                    "retry_delay": 2.0,
                    "sheet_name": "magic",
                    "worksheet_name": "cards"
                },
                "openai": {
                    "enabled": False,
                    "model": "gpt-3.5-turbo",
                    "max_tokens": 150,
                    "temperature": 0.7,
                    "max_retries": 3
                }
            }
        }
        
        config = build_processor_config(yaml_config)
        
        self.assertIsInstance(config, ProcessorConfig)
        self.assertEqual(config.processing.batch_size, 20)
        self.assertEqual(config.scryfall.max_retries, 3)
        self.assertEqual(config.google_sheets.sheet_name, "magic")
        self.assertEqual(config.openai.model, "gpt-3.5-turbo")
    
    def test_build_processor_config_with_cli_overrides(self):
        """Test building config with CLI overrides."""
        yaml_config = {
            "processing": {
                "batch_size": 20,
                "max_workers": 4,
                "api_delay": 0.1,
                "write_buffer_batches": 3
            },
            "api": {
                "scryfall": {},
                "google_sheets": {},
                "openai": {}
            }
        }
        
        cli_overrides = {
            "processing": {
                "batch_size": 50,
                "max_workers": 8
            }
        }
        
        config = build_processor_config(yaml_config, cli_overrides=cli_overrides)
        
        self.assertEqual(config.processing.batch_size, 50)
        self.assertEqual(config.processing.max_workers, 8)
        self.assertEqual(config.processing.api_delay, 0.1)  # Not overridden


class TestPriorityOrder(unittest.TestCase):
    """Test configuration priority order: YAML < ENV < CLI."""
    
    def setUp(self):
        """Save original environment."""
        self.original_env = os.environ.copy()
    
    def tearDown(self):
        """Restore original environment."""
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_priority_yaml_only(self):
        """Test that YAML values are used when no overrides."""
        yaml_config = {
            "processing": {
                "batch_size": 20,
                "max_workers": 4,
                "api_delay": 0.1,
                "write_buffer_batches": 3
            },
            "api": {"scryfall": {}, "google_sheets": {}, "openai": {}}
        }
        
        config = build_processor_config(yaml_config)
        self.assertEqual(config.processing.batch_size, 20)
    
    def test_priority_env_over_yaml(self):
        """Test that ENV overrides YAML."""
        yaml_config = {
            "processing": {
                "batch_size": 20,
                "max_workers": 4,
                "api_delay": 0.1,
                "write_buffer_batches": 3
            },
            "api": {"scryfall": {}, "google_sheets": {}, "openai": {}}
        }
        
        os.environ["DECKDEX_PROCESSING_BATCH_SIZE"] = "30"
        yaml_config = apply_env_overrides(yaml_config)
        
        config = build_processor_config(yaml_config)
        self.assertEqual(config.processing.batch_size, 30)
    
    def test_priority_cli_over_all(self):
        """Test that CLI overrides both YAML and ENV."""
        yaml_config = {
            "processing": {
                "batch_size": 20,
                "max_workers": 4,
                "api_delay": 0.1,
                "write_buffer_batches": 3
            },
            "api": {"scryfall": {}, "google_sheets": {}, "openai": {}}
        }
        
        os.environ["DECKDEX_PROCESSING_BATCH_SIZE"] = "30"
        yaml_config = apply_env_overrides(yaml_config)
        
        cli_overrides = {
            "processing": {
                "batch_size": 40
            }
        }
        
        config = build_processor_config(yaml_config, cli_overrides=cli_overrides)
        self.assertEqual(config.processing.batch_size, 40)


if __name__ == '__main__':
    unittest.main()
