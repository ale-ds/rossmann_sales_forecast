import os
import json
import logging
import requests
import pandas as pd
from flask import Flask, request, Response
from dotenv import load_dotenv
from typing import Union, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Load environment variables from .env file
load_dotenv()

# Constants
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
API_URL = os.environ.get('API_URL', 'https://rossmann-model-bgly.onrender.com/rossmann/predict')

if not TOKEN:
    raise ValueError("The environment variable TELEGRAM_BOT_TOKEN is not set.")

def send_message(chat_id: int, text: str) -> None:
    """Sends a message to a specific Telegram chat."""
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    payload = {'chat_id': chat_id, 'text': text}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        logging.info(f"Message sent to chat_id {chat_id} with status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send message to chat_id {chat_id}: {e}")

# Load and merge datasets once at startup to avoid repeated I/O
try:
    df_test_raw = pd.read_csv('test.csv')
    df_store_raw = pd.read_csv('store.csv')
    # Merge test dataset + store
    df_merged = pd.merge(df_test_raw, df_store_raw, how='left', on='Store')
    logging.info("Test and store datasets loaded and merged successfully.")
except FileNotFoundError as e:
    logging.error(f"Error loading data files: {e}. Make sure 'test.csv' and 'store.csv' are in the correct directory.")
    df_merged = pd.DataFrame() # Create an empty dataframe to avoid crashing on startup

def load_dataset(store_id: int) -> str:
    """Filters the dataset for a specific store and prepares it for prediction."""
    if df_merged.empty:
        logging.error("The merged dataframe is empty. Cannot process request.")
        return 'error'
        
    # Choose store for prediction
    df_test = df_merged[df_merged['Store'] == store_id].copy()

    if df_test.empty:
        logging.warning(f"No data found for store_id: {store_id}")
        return 'error'

    # Remove closed days and rows with null 'Open' status
    df_test = df_test.loc[(df_test['Open'] == 1) & (~df_test['Open'].isnull())]
    
    if df_test.empty:
        logging.warning(f"No open days found for store_id: {store_id} in the test set.")
        return 'error'

    df_test = df_test.drop('Id', axis=1)

    # Convert DataFrame to JSON
    data = json.dumps(df_test.to_dict(orient='records'))
    return data

def predict(data: str) -> Optional[pd.DataFrame]:
    """Calls the prediction API and returns the result as a DataFrame."""
    headers = {'Content-type': 'application/json'}
    logging.info(f"Sending data to API: {data[:500]}...") # Log first 500 chars
    try:
        response = requests.post(API_URL, data=data, headers=headers)
        response.raise_for_status()
        logging.info(f"API call successful with status code {response.status_code}")
        
        response_json = response.json()
        if not response_json:
            logging.warning("Prediction API returned an empty response.")
            return None
            
        return pd.DataFrame(response_json)
    except requests.exceptions.RequestException as e:
        logging.error(f"API call failed: {e}")
        return None
    except json.JSONDecodeError:
        logging.error(f"Failed to decode JSON from API response. Response text: {response.text}")
        return None

def parse_message(message: dict) -> Tuple[Optional[int], Union[int, str]]:
    """Parses the chat_id and store_id from the incoming message."""
    try:
        chat_id = message['message']['chat']['id']
        store_id_str = message['message']['text']

        # Basic validation for command-like format
        if not store_id_str.startswith('/'):
            return chat_id, 'error'

        store_id_str = store_id_str.replace('/', '')
        store_id = int(store_id_str)
        return chat_id, store_id
    except (KeyError, ValueError, AttributeError):
        # Safely get chat_id even if other keys are missing
        chat_id_safe = message.get('message', {}).get('chat', {}).get('id')
        return chat_id_safe, 'error'

# API initialize
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method != 'POST':
        return '<h1>Rossmann Telegram BOT</h1>'

    message = request.get_json()
    if not message:
        logging.warning("Received an empty POST request.")
        return Response('Error', status=400)

    chat_id, store_id = parse_message(message)

    if store_id == 'error' or not chat_id:
        if chat_id:
            send_message(chat_id, 'Invalid Store ID. Please send a valid store number (e.g., /24).')
        return Response('Ok', status=200)

    # loading data
    data = load_dataset(store_id)
    if data == 'error':
        send_message(chat_id, f'Store {store_id} is not available for prediction or is closed during the forecast period.')
        return Response('Ok', status=200)

    # prediction
    df_prediction = predict(data)
    if df_prediction is None:
        send_message(chat_id, 'Sorry, I could not get a prediction at this time. Please try again later.')
        return Response('Ok', status=200)

    # calculation
    df_sum = df_prediction[['Store', 'Prediction']].groupby('Store').sum().reset_index()
    
    if df_sum.empty:
        send_message(chat_id, f'No predictions could be calculated for Store {store_id}.')
        return Response('Ok', status=200)

    # send message
    store = df_sum['Store'].values[0]
    prediction_value = df_sum['Prediction'].values[0]
    msg = f'Store Number {store} will sell R${prediction_value:,.2f} in the next 6 weeks.'
    
    send_message(chat_id, msg)
    return Response('Ok', status=200)

if __name__ == '__main__':  
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
