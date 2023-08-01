![Logo](images/Deckdex.png)
# DeckDex MTG 

The goal of this project is to automate the collection of information about Magic: The Gathering cards using the Scryfall API and store the information in a Google Sheet. The project also uses the OpenAI API to provide game strategies and tiers for the cards (is optional because is a paid service).

With the data in the Google Sheets, you will be able to create decks more easily, as well as obtain additional information about your cards, such as prices in Euros or inferences made by OpenAI about the cards themselves.

In addition, this Google Sheet could be used with ChatGPT, Bard, or other artificial intelligences as a database for asking questions in the future.

## Features

1. Fetches card information via the [Scryfall API](https://scryfall.com/docs/api).
2. Stores card information in a Google Sheet.
3. Uses the OpenAI API to provide game strategies and tiers for the cards:
   4. Game strategies: chatgpt will classify the game strategy of the card for you (aggro, control, etc).
   5. Tiers: chatgpt will classify the card in a Tier list way for you (Top, High, Mid, Bottom).

## Requirements

To run this project, you will need to have Python 3.6 or higher. You will also need to install the project's dependencies, which are listed in the `requirements.txt` file.

In addition, you will need:

- A JSON credentials file for authenticating with the [Google Sheets API](https://developers.google.com/sheets/api/quickstart/python) with Python.
- An OpenAI API key.
- A Google Sheet in your account with the next columns in the row 1:
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

To run the project without openai api, you can use the following command:

```commandline
python main.py
```

Or with openai api:

```commandline
python main.py --use_openai
```

## Contributions

Contributions are welcome. Please open an issue to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)