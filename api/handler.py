import os
import pickle
import psutil
import logging
import pandas as pd
import xgboost as xgb
from flask import Flask, request, jsonify
from rossmann.Rossmann import Rossmann

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def log_memory_usage(context=""):
    """
    Logs the memory usage of the current process.

    Parameters
    ----------
    context : str, default=""
        An optional context string to help identify the memory log entry.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info().rss / (1024 * 1024)  # in MB
    logging.info(f"[MEMORY] {context} - Memory usage: {mem_info:.2f} MB")

def load_pickle(file_name):
    """
    Loads a .pkl file from the BASE_PATH directory.

    Parameters
    ----------
    file_name : str
        The name of the .pkl file to load.

    Returns
    -------
    object
        The object loaded from the .pkl file.
    """
    with open(f"../model/pre-processing/{file_name}", "rb") as f:
        return pickle.load(f)

log_memory_usage("Handler start")

# Single load of model and preprocessing objects
logging.info("Loading model and preprocessing objects...")

# Load XGBoost model from its native binary format for efficiency and stability
model = xgb.XGBRegressor()
# The path should be relative to BASE_PATH, without a leading slash.
model.load_model("../model/modeling/model_xgb_final.ubj")

scalers = {
    "competition_distance_scaler": load_pickle("robust_scaler_competition_distance.pkl"),
    "competition_time_month_scaler": load_pickle("robust_scaler_competition_time_month.pkl"),
    "promo_time_week_scaler": load_pickle("minmax_scaler_promo_time_week.pkl"),
    "year_scaler": load_pickle("minmax_scaler_year.pkl")
}
encoders = {
    "store_type_encoder": load_pickle("label_encoder_store_type.pkl"),
    "assortment_encoder": {"basic": 1, "extra": 2, "extended": 3},  # Assortment already defined
    "state_holiday_encoder": {"a": "public", "b": "easter", "c": "christmas", "0": "none"}
}
features_selected = load_pickle("list_features_selected.pkl")

log_memory_usage("After loading objects")

# Global Rossmann instance
rossmann = Rossmann(
    model=model,
    scalers=scalers,
    encoders=encoders,
    features_selected=features_selected
)

# Initialize Flask app
app = Flask(__name__)

@app.route("/rossmann/predict", methods=["POST"])
def rossmann_predict():
    """
    Makes a sales prediction based on the data received in JSON format.

    Parameters
    ----------
    test_json : dict or list
        A dictionary or list of dictionaries containing the input data.

    Returns
    -------
    str
        The prediction result in JSON format, with columns "Store", "DayOfWeek", "Date", "Sales", and "Prediction".
    """
    test_json = request.get_json()
    if not test_json:
        return jsonify({"error": "No data received"}), 400

    # Convert input JSON to DataFrame
    if isinstance(test_json, dict):
        df_raw = pd.DataFrame([test_json])
    else:
        df_raw = pd.DataFrame(test_json)

    log_memory_usage("Before preprocessing")
    df_prepared = rossmann.preprocess(df_raw)
    log_memory_usage("After preprocessing")
    df_response = rossmann.get_prediction(df_prepared)
    log_memory_usage("After prediction")

    return df_response

if __name__ == "__main__":
    app.run("0.0.0.0", port=8080)