![Logo](images/Deckdex.png)

# DeckDex MTG

- DeckDex MTG is a project designed to automate the collection of Magic: The Gathering card information using the Scryfall API and store that information in a Google Sheet. Additionally, it optionally utilizes the OpenAI API to provide game strategies and tiers for the cards. 
- By storing data in Google Sheets, you'll be able to build decks more easily and gain additional insights about your cards such as their prices in Euros. Plus, this Google Sheet can serve as a database for querying with artificial intelligences like ChatGPT, Bard, and others in the future.
- It also includes a feature for updating card prices, allowing users to keep track of the market value of their card collection.

## Features

1. Fetches card information using the [Scryfall API](https://scryfall.com/docs/api).
2. Stores card information in a Google Sheet.
3. Optionally uses the OpenAI API to provide:
   - Game strategies: ChatGPT will classify the game strategy of the card for you (aggro, control, etc).
   - Tiers: ChatGPT will classify the card in a tier list for you (Top, High, Mid, Bottom).
4. Selective price updates: Only updates prices that have changed, saving API calls and processing time.
5. Provides command-line interfaces:
   - Command-line interface for automation and scripting
   - Interactive command-line interface for ease of use

## Requirements

To run this project, you'll need Python 3.6 or higher installed on your machine. You will also need to install the project's dependencies listed in the `requirements.txt` file.

Additionally, you will need:

- A JSON credentials file for authentication with the [Google Sheets API](https://developers.google.com/sheets/api/quickstart/python) using Python.
- An OpenAI API key (if you opt to use this feature).
- A Google Sheet in your account with the following columns in the first row:
```commandline
Name,English name,Type,Description,Keywords,Mana Cost,Cmc,Color,Identity,Colors,Strength,Resistance,Rarity,Price,Release,Date,Set ID,Set Name,Number in Set,Edhrec,Rank,Game Strategy,Tier
```
- You have to write the card names in the "Name" column, row by row. The script will add the information for you in the other columns.
  - Please, remember to share the google sheet with the service account email, as is specified in the [Google Sheets API](https://developers.google.com/sheets/api/quickstart/python).

## Environment Setup

1. Clone this repository.
2. Create a Python virtual environment and install the project's dependencies using pip:

```commandline
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Set up the necessary environment variables. You can do this by creating a `.env` file at the root of the project with the following format:
```commandline
GOOGLE_API_CREDENTIALS=/path/to/credentials.json
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-3.5-turbo
```

Note: `OPENAI_MODEL` is optional and defaults to `gpt-3.5-turbo`. You can change it to other models like `gpt-4` if needed.

## Configuration

DeckDex MTG uses a flexible configuration system that supports multiple environments and easy parameter tuning.

### Configuration Files

The configuration is managed through `config.yaml` with three built-in profiles:

- **default**: Balanced settings for general use (current production values)
- **development**: Conservative settings for local development and debugging
- **production**: Aggressive settings optimized for processing thousands of cards

### Configuration Priority

Configuration values are applied in this order (low to high priority):

1. **YAML configuration file** (`config.yaml`)
2. **Environment variables** (DECKDEX_* prefix)
3. **CLI flags** (highest priority)

### Using Profiles

Select a profile with the `--profile` flag:

```commandline
# Use default profile (balanced)
python main.py

# Use development profile (conservative, easier debugging)
python main.py --profile development

# Use production profile (optimized for thousands of cards)
python main.py --profile production
```

**Profile Comparison:**

| Setting | Default | Development | Production |
|---------|---------|-------------|------------|
| Batch Size | 20 | 10 | 50 |
| Workers | 4 | 2 | 8 |
| API Delay | 0.1s | 0.2s | 0.05s |
| Write Buffer | 3 batches | 2 batches | 5 batches |

### Environment Variable Overrides

Override any configuration value using environment variables with the `DECKDEX_` prefix:

```commandline
# Override processing settings
export DECKDEX_PROCESSING_BATCH_SIZE=30
export DECKDEX_PROCESSING_MAX_WORKERS=6

# Override API settings
export DECKDEX_SCRYFALL_MAX_RETRIES=5
export DECKDEX_OPENAI_ENABLED=true

# Run with overrides
python main.py
```

### CLI Flag Overrides

CLI flags have the highest priority and override both YAML and environment variables:

```commandline
# Override specific settings
python main.py --profile production --batch-size 100 --workers 10

# Mix profile with custom overrides
python main.py --profile development --api-delay 0.15
```

### Viewing Resolved Configuration

Display the final resolved configuration (after applying all overrides):

```commandline
# Show default configuration
python main.py --show-config

# Show production profile configuration
python main.py --profile production --show-config

# Show configuration with all overrides applied
python main.py --profile production --batch-size 100 --show-config
```

### Custom Configuration File

Use a custom configuration file:

```commandline
python main.py --config /path/to/custom-config.yaml --profile production
```

### Configuration Template

A fully documented configuration template is available at `config.example.yaml`. Copy it to create your own custom configuration:

```commandline
cp config.example.yaml my-config.yaml
# Edit my-config.yaml with your settings
python main.py --config my-config.yaml
```

### Available Configuration Options

**Processing Settings:**
- `batch_size`: Number of cards per batch (default: 20)
- `max_workers`: Parallel workers (1-10, default: 4)
- `api_delay`: Delay between API calls in seconds (default: 0.1)
- `write_buffer_batches`: Batches before writing to sheets (default: 3)

**Scryfall API:**
- `max_retries`: Retry attempts (default: 3)
- `retry_delay`: Base delay between retries (default: 0.5s)
- `timeout`: Request timeout (default: 10.0s)

**Google Sheets API:**
- `batch_size`: Internal batch size (default: 500)
- `max_retries`: Retry attempts (default: 5)
- `retry_delay`: Base delay for backoff (default: 2.0s)
- `sheet_name`: Spreadsheet name (default: "magic")
- `worksheet_name`: Worksheet name (default: "cards")

**OpenAI API:**
- `enabled`: Enable/disable OpenAI enrichment (default: false)
- `model`: Model to use (default: "gpt-3.5-turbo")
- `max_tokens`: Max tokens per completion (default: 150)
- `temperature`: Creativity level 0.0-1.0 (default: 0.7)
- `max_retries`: Retry attempts (default: 3)

**Security Note:** Secrets (API keys, credentials paths) should NEVER be stored in `config.yaml`. Always use environment variables or `.env` file for sensitive data.

## Running the Tests

To run the project's tests, you can use the following command:

```commandline
python -m unittest discover -s tests
```

## Running the Project

### Command Line Interface

To run the project without OpenAI API, you can use the following command:

```commandline
python main.py
```

Or with OpenAI API:

```commandline
python main.py --use_openai
```

To update the prices of the cards:
```commandline
python main.py --update_prices
```

**Price Update Behavior:**
- The price update feature now uses **incremental writes** to Google Sheets, improving progress visibility and resilience
- Price changes are written every 60 cards (3 batches) by default, instead of waiting until all verifications complete
- If the process is interrupted, you can resume from where it left off using `--resume-from`
- Maximum data loss window: 60 cards (vs. all cards in previous versions)
- Expected execution time: ~130 seconds for 1000 cards (~25 seconds longer than before, but with much better progress tracking)

### Advanced CLI Options

The CLI supports numerous configuration options for fine-tuning performance and behavior:

#### Configuration Profiles
```commandline
# Use pre-configured profiles
python main.py --profile development
python main.py --profile production

# Show resolved configuration
python main.py --show-config
python main.py --profile production --show-config
```

#### Performance Configuration
```commandline
# Configure batch size and workers
python main.py --batch-size 50 --workers 8

# Adjust API rate limiting
python main.py --api-delay 0.2 --max-retries 10
```

#### Testing and Debugging
```commandline
# Dry-run mode (simulate without writing)
python main.py --dry-run --verbose

# Process only a few cards for testing
python main.py --limit 10 --verbose

# Resume from a specific row (e.g., after interruption)
python main.py --resume-from 100

# Resume price updates after interruption
python main.py --update_prices --resume-from 350
```

**Resuming After Interruption:**

If a price update is interrupted, you'll see a hint at the end showing the exact row to resume from:
```
💡 To resume from here: --resume-from 450
```

This allows you to continue from where the process stopped, minimizing rework. The incremental write feature ensures that price changes are saved every 60 cards, so at most 60 cards of progress will need to be re-verified.

#### Custom Google Sheets Configuration
```commandline
# Use different spreadsheet/worksheet
python main.py --sheet-name "my_collection" --worksheet-name "standard_cards"

# Override credentials path
python main.py --credentials-path "/path/to/creds.json"
```

#### Full Options Reference

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--profile PROFILE` | str | default | Configuration profile (default, development, production) |
| `--config PATH` | str | config.yaml | Path to custom configuration file |
| `--show-config` | flag | false | Display resolved configuration and exit |
| `--use_openai` | flag | false | Enable OpenAI enrichment for strategy and tier |
| `--update_prices` | flag | false | Update only prices (not full card data) |
| `--dry-run` | flag | false | Simulate execution without writing to Sheets |
| `-v, --verbose` | flag | false | Enable detailed DEBUG-level logging |
| `--batch-size N` | int | 20 | Cards to process per batch |
| `--workers N` | int | 4 | Number of parallel workers (1-10) |
| `--api-delay SECONDS` | float | 0.1 | Delay between API requests (Scryfall rate limiting) |
| `--max-retries N` | int | 5 | Maximum retry attempts for failed requests |
| `--credentials-path PATH` | str | - | Path to Google API credentials (overrides env var) |
| `--sheet-name NAME` | str | magic | Name of the Google spreadsheet |
| `--worksheet-name NAME` | str | cards | Name of the worksheet |
| `--limit N` | int | - | Process only N cards (useful for testing) |
| `--resume-from ROW` | int | - | Resume processing from row N (1-indexed) |

For complete help:
```commandline
python main.py --help
```

<!-- Graphical interface removed: the project is terminal-only. -->

## Performance Improvements

The current version of the project includes several optimizations to improve performance and robustness:

1. **Parallel Processing**: Implementation of `ThreadPoolExecutor` to process multiple cards simultaneously.

2. **Caching System**: Use of `@lru_cache` to store API query results and avoid repeated calls.

3. **Batch Processing**: Updates to Google Sheets are done in batches to reduce the number of API calls.

4. **Selective Price Updates**: Only updates prices that have changed, significantly reducing API calls and processing time.

5. **Incremental Price Writes**: Price changes are now written to Google Sheets progressively (every 60 cards) during verification, providing:
   - Real-time progress visibility in the spreadsheet
   - Minimal data loss on interruption (max 60 cards vs. all cards previously)
   - Ability to resume with `--resume-from` after any interruption
   - Clear progress notifications showing write operations

6. **Robust Error Handling**: Implementation of retries with exponential backoff to handle temporary failures.

7. **Static Typing**: Use of type hints to improve code quality and facilitate maintenance.

8. **Persistent HTTP Sessions**: Reuse of HTTP connections to reduce connection establishment overhead.

9. **API Query Optimization**: Improvement in how queries are made to the Scryfall API.

10. **Better Code Structure**: Clear separation of responsibilities and proper encapsulation.

11. **Enhanced CLI**: Comprehensive command-line interface with 13+ configuration options for performance tuning and testing.

These improvements result in:
- Faster processing speed
- Lower resource usage
- Greater robustness against errors
- Better code maintainability
- Improved user experience

## Contributions

Contributions are welcome. Please open an issue to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)

### Actualización de Precios

La aplicación ofrece dos modos para actualizar los precios de las cartas:

1. **Actualización selectiva (recomendada)**: Solo actualiza los precios que han cambiado desde la última actualización, comparando los precios actuales con los nuevos de Scryfall. Esta opción es más eficiente y reduce el número de solicitudes a la API.

2. **Actualización completa**: Actualiza todos los precios, independientemente de si han cambiado o no.

Ambas opciones están disponibles en la interfaz de línea de comandos.

## Migration Notes

### Configuration System Migration

If you have custom scripts or automation that uses DeckDex MTG, the configuration system changes are **100% backwards compatible**. All existing commands continue to work without modification.

**No changes required for:**
- `python main.py`
- `python main.py --use_openai`
- `python main.py --update_prices`
- `python main.py --batch-size 50 --workers 8`
- All existing CLI flags continue working exactly as before

**Optional improvements you can make:**

1. **Use profiles instead of CLI flags:**
   ```commandline
   # Before (still works)
   python main.py --batch-size 50 --workers 8 --api-delay 0.05
   
   # After (simpler, using production profile)
   python main.py --profile production
   ```

2. **Create custom configuration files:**
   ```commandline
   # Copy and customize
   cp config.example.yaml my-config.yaml
   
   # Use your custom config
   python main.py --config my-config.yaml
   ```

3. **Use environment variables for overrides:**
   ```commandline
   # Set once in your environment
   export DECKDEX_PROCESSING_BATCH_SIZE=30
   export DECKDEX_PROCESSING_MAX_WORKERS=6
   
   # Run without CLI flags
   python main.py
   ```

**For CI/CD pipelines:**
- Existing scripts work without changes
- Consider using `--profile production` for optimized performance
- Use `DECKDEX_*` environment variables for environment-specific settings

**Breaking changes:** None. All existing functionality is preserved.

### Removal of run_cli.py

The `run_cli.py` interactive CLI has been removed as it was incomplete and referenced non-existent modules. All functionality is now available through the enhanced `main.py` CLI with comprehensive command-line options.

**Before:**
```commandline
python run_cli.py
```

**After:**
```commandline
python main.py --verbose  # for detailed output
python main.py --dry-run  # to test without writing
```

All previous `python main.py` commands continue to work without changes.