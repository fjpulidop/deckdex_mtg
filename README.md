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