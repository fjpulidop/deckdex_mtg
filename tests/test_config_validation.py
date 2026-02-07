"""Tests for nested configuration dataclasses and validation."""

import unittest
from deckdex.config import (
    ProcessingConfig,
    ScryfallConfig,
    GoogleSheetsConfig,
    OpenAIConfig,
    ProcessorConfig
)


class TestProcessingConfig(unittest.TestCase):
    """Test ProcessingConfig validation."""
    
    def test_valid_config(self):
        """Test creating config with valid values."""
        config = ProcessingConfig(
            batch_size=20,
            max_workers=4,
            api_delay=0.1,
            write_buffer_batches=3
        )
        self.assertEqual(config.batch_size, 20)
        self.assertEqual(config.max_workers, 4)
    
    def test_invalid_batch_size(self):
        """Test that invalid batch size raises error."""
        with self.assertRaises(ValueError) as context:
            ProcessingConfig(batch_size=0)
        self.assertIn("batch_size must be > 0", str(context.exception))
        
        with self.assertRaises(ValueError):
            ProcessingConfig(batch_size=-5)
    
    def test_invalid_max_workers_low(self):
        """Test that invalid max_workers (too low) raises error."""
        with self.assertRaises(ValueError) as context:
            ProcessingConfig(max_workers=0)
        self.assertIn("max_workers must be between 1 and 10", str(context.exception))
    
    def test_invalid_max_workers_high(self):
        """Test that invalid max_workers (too high) raises error."""
        with self.assertRaises(ValueError) as context:
            ProcessingConfig(max_workers=15)
        self.assertIn("max_workers must be between 1 and 10", str(context.exception))
    
    def test_invalid_api_delay(self):
        """Test that negative api_delay raises error."""
        with self.assertRaises(ValueError) as context:
            ProcessingConfig(api_delay=-0.1)
        self.assertIn("api_delay must be >= 0", str(context.exception))
    
    def test_invalid_write_buffer_batches(self):
        """Test that invalid write_buffer_batches raises error."""
        with self.assertRaises(ValueError) as context:
            ProcessingConfig(write_buffer_batches=0)
        self.assertIn("write_buffer_batches must be >= 1", str(context.exception))


class TestScryfallConfig(unittest.TestCase):
    """Test ScryfallConfig validation."""
    
    def test_valid_config(self):
        """Test creating config with valid values."""
        config = ScryfallConfig(
            max_retries=3,
            retry_delay=0.5,
            timeout=10.0
        )
        self.assertEqual(config.max_retries, 3)
        self.assertEqual(config.timeout, 10.0)
    
    def test_invalid_max_retries(self):
        """Test that invalid max_retries raises error."""
        with self.assertRaises(ValueError) as context:
            ScryfallConfig(max_retries=0)
        self.assertIn("max_retries must be >= 1", str(context.exception))
    
    def test_invalid_retry_delay(self):
        """Test that negative retry_delay raises error."""
        with self.assertRaises(ValueError) as context:
            ScryfallConfig(retry_delay=-0.5)
        self.assertIn("retry_delay must be >= 0", str(context.exception))
    
    def test_invalid_timeout(self):
        """Test that invalid timeout raises error."""
        with self.assertRaises(ValueError) as context:
            ScryfallConfig(timeout=0)
        self.assertIn("timeout must be > 0", str(context.exception))


class TestGoogleSheetsConfig(unittest.TestCase):
    """Test GoogleSheetsConfig validation."""
    
    def test_valid_config(self):
        """Test creating config with valid values."""
        config = GoogleSheetsConfig(
            batch_size=500,
            max_retries=5,
            retry_delay=2.0,
            sheet_name="magic",
            worksheet_name="cards"
        )
        self.assertEqual(config.batch_size, 500)
        self.assertEqual(config.sheet_name, "magic")
    
    def test_invalid_batch_size(self):
        """Test that invalid batch size raises error."""
        with self.assertRaises(ValueError) as context:
            GoogleSheetsConfig(batch_size=0)
        self.assertIn("batch_size must be > 0", str(context.exception))
    
    def test_invalid_max_retries(self):
        """Test that invalid max_retries raises error."""
        with self.assertRaises(ValueError) as context:
            GoogleSheetsConfig(max_retries=0)
        self.assertIn("max_retries must be >= 1", str(context.exception))
    
    def test_invalid_retry_delay(self):
        """Test that negative retry_delay raises error."""
        with self.assertRaises(ValueError) as context:
            GoogleSheetsConfig(retry_delay=-1.0)
        self.assertIn("retry_delay must be >= 0", str(context.exception))


class TestOpenAIConfig(unittest.TestCase):
    """Test OpenAIConfig validation."""
    
    def test_valid_config(self):
        """Test creating config with valid values."""
        config = OpenAIConfig(
            enabled=True,
            model="gpt-4",
            max_tokens=150,
            temperature=0.7,
            max_retries=3
        )
        self.assertEqual(config.model, "gpt-4")
        self.assertTrue(config.enabled)
    
    def test_invalid_max_tokens(self):
        """Test that invalid max_tokens raises error."""
        with self.assertRaises(ValueError) as context:
            OpenAIConfig(max_tokens=0)
        self.assertIn("max_tokens must be > 0", str(context.exception))
    
    def test_invalid_temperature_low(self):
        """Test that temperature below 0.0 raises error."""
        with self.assertRaises(ValueError) as context:
            OpenAIConfig(temperature=-0.1)
        self.assertIn("temperature must be between 0.0 and 1.0", str(context.exception))
    
    def test_invalid_temperature_high(self):
        """Test that temperature above 1.0 raises error."""
        with self.assertRaises(ValueError) as context:
            OpenAIConfig(temperature=1.5)
        self.assertIn("temperature must be between 0.0 and 1.0", str(context.exception))
    
    def test_invalid_max_retries(self):
        """Test that invalid max_retries raises error."""
        with self.assertRaises(ValueError) as context:
            OpenAIConfig(max_retries=0)
        self.assertIn("max_retries must be >= 1", str(context.exception))


class TestProcessorConfig(unittest.TestCase):
    """Test ProcessorConfig with nested configs."""
    
    def test_create_with_defaults(self):
        """Test creating ProcessorConfig with all defaults."""
        config = ProcessorConfig()
        
        # Check nested configs exist
        self.assertIsInstance(config.processing, ProcessingConfig)
        self.assertIsInstance(config.scryfall, ScryfallConfig)
        self.assertIsInstance(config.google_sheets, GoogleSheetsConfig)
        self.assertIsInstance(config.openai, OpenAIConfig)
        
        # Check default values
        self.assertEqual(config.processing.batch_size, 20)
        self.assertEqual(config.scryfall.max_retries, 3)
        self.assertEqual(config.google_sheets.sheet_name, "magic")
        self.assertFalse(config.openai.enabled)
    
    def test_backwards_compatibility_properties(self):
        """Test that legacy properties still work."""
        config = ProcessorConfig()
        
        # These properties delegate to nested configs
        self.assertEqual(config.batch_size, config.processing.batch_size)
        self.assertEqual(config.max_workers, config.processing.max_workers)
        self.assertEqual(config.api_delay, config.processing.api_delay)
        self.assertEqual(config.use_openai, config.openai.enabled)
        self.assertEqual(config.sheet_name, config.google_sheets.sheet_name)
        self.assertEqual(config.worksheet_name, config.google_sheets.worksheet_name)
    
    def test_limit_validation(self):
        """Test that limit validation works."""
        with self.assertRaises(ValueError) as context:
            ProcessorConfig(limit=0)
        self.assertIn("limit must be > 0", str(context.exception))
    
    def test_resume_from_validation(self):
        """Test that resume_from validation works."""
        with self.assertRaises(ValueError) as context:
            ProcessorConfig(resume_from=0)
        self.assertIn("resume_from must be >= 1", str(context.exception))


if __name__ == '__main__':
    unittest.main()
