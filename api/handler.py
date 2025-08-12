import pandas as pd
from flask import Flask, request, Response
from rossmann.Rossmann import Rossmann

# Instantiate Rossmann class once at startup
pipeline = Rossmann()

# initialize API
app = Flask( __name__ )

@app.route('/rossmann/predict', methods=['POST'] )
def rossmann_predict():
    test_json = request.get_json()
    
    if test_json: # there is data
        if isinstance( test_json, dict ): # unique example
            test_raw = pd.DataFrame ( test_json, index=[0] )
        else: # multiple example
            test_raw = pd.DataFrame( test_json, columns=test_json[0].keys() )

    # Apply the full preprocessing pipeline
    df_prepared = pipeline.preprocess(test_raw.copy())
    # prediction
    df_response = pipeline.get_prediction(test_raw, df_prepared)
    return df_response


if __name__ == '__main__':
    app.run( '0.0.0.0', port=8080, debug=True )