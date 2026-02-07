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
```

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

### Interactive Command Line Interface

For a more user-friendly command-line experience, you can use the interactive CLI:

```commandline
python run_cli.py
```

The interactive CLI provides a menu-driven interface with the following features:
- Configure Google API credentials and OpenAI API key
- Process cards with or without OpenAI
- Update card prices
- Simple navigation through menus

<!-- Graphical interface removed: the project is terminal-only. -->

## Performance Improvements

The current version of the project includes several optimizations to improve performance and robustness:

1. **Parallel Processing**: Implementation of `ThreadPoolExecutor` to process multiple cards simultaneously.

2. **Caching System**: Use of `@lru_cache` to store API query results and avoid repeated calls.

3. **Batch Processing**: Updates to Google Sheets are done in batches to reduce the number of API calls.

4. **Selective Price Updates**: Only updates prices that have changed, significantly reducing API calls and processing time.

5. **Robust Error Handling**: Implementation of retries with exponential backoff to handle temporary failures.

6. **Static Typing**: Use of type hints to improve code quality and facilitate maintenance.

7. **Persistent HTTP Sessions**: Reuse of HTTP connections to reduce connection establishment overhead.

8. **API Query Optimization**: Improvement in how queries are made to the Scryfall API.

9. **Better Code Structure**: Clear separation of responsibilities and proper encapsulation.
10. **Interactive CLI**: Addition of a menu-driven command-line interface for environments without GUI support.

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