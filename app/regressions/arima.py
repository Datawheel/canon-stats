from functools import reduce
from sklearn.metrics import mean_squared_error
from statsmodels.tsa.arima_model import ARIMA
import json
import numpy as np
import pandas as pd
import requests
import sys
import warnings


def evaluate_arima_model(X, arima_order):
    # prepare training dataset
    train_size = int(len(X) * 0.66)
    train, test = X[0:train_size], X[train_size:]
    history = [x for x in train]

    # make predictions
    predictions = list()
    for t in range(len(test)):
        model = ARIMA(history, order=arima_order)
        model_fit = model.fit(disp=0)
        yhat = model_fit.forecast()[0]
        predictions.append(yhat)
        history.append(test[t])

    # calculate out of sample error
    error = mean_squared_error(test, predictions)
    return error


# evaluate combinations of p, d and q values for an ARIMA model
def evaluate_models(dataset, p_values, d_values, q_values):
    dataset = dataset.astype("float32")
    best_score, best_cfg = float("inf"), None
    for p in p_values:
        for d in d_values:
            for q in q_values:
                order = (p, d, q)
                try:
                    mse = evaluate_arima_model(dataset, order)
                    if mse < best_score:
                        best_score, best_cfg = mse, order
                except:
                    continue
    return (best_cfg)


def arima(API, params):

    r = requests.get(API, params=params)
    df = pd.DataFrame(r.json()["data"])
    measures = params["measures"].split(",")
    X = pd.DataFrame(df, columns=measures).set_index(df["Year"])
    

    if (params.get("pred") == None):
        n_pred = 10
    else:
        n_pred = int(params.get("pred"))  

    if (params.get("args") == None):
        p_values = range(3)
        d_values = range(3)
        q_values = range(3)
        warnings.filterwarnings("ignore")
        best_cfg = evaluate_models(X.values, p_values, d_values, q_values)
    else:
        best_cfg = eval(params["args"]) 

    model = ARIMA(X.values, order=best_cfg)
    results = model.fit(disp=0)
    
    start_index = len(X)
    end_index = len(X) + n_pred
    forecast = results.predict(start=start_index, end=end_index)
    forecast_list = forecast.tolist()

    data = {
        "results": [
            {"name": "exog_name", "value": model.exog_names},
            {"name": "params", "value": results.params},
            {"name": "bse", "value": results.bse},
            {"name": "t_values", "value": results.tvalues},
            {"name": "p_values", "value": results.pvalues},
            # {"name": "low_cof_int", "value": results.conf_int()[0]},
            # {"name": "upp_cof_int", "value": results.conf_int()[1]}
        ]
    }

    data["model_info"] = results.model.__class__.__name__
    df_list = []

    for item in data["results"]:
        df = pd.DataFrame(item["value"]).reset_index().rename(
            columns={"index": "id", 0: item["name"]})
        df_list.append(df)

    df = reduce(lambda x, y: pd.merge(x, y, on="id", how="inner"), df_list)
    df = df.drop(["id"], axis=1)

    return {
        "Model_info":[ 
            {"args_used" : best_cfg},
            {"n_of_predictions" : n_pred},
            {"model_info" : results.model.__class__.__name__},
            {"method" : model.method},
            {"n_observations" : results.nobs},
            {"aic" : results.aic},
            {"bic" : results.bic},
            {"hqic" : results.hqic}
        ],    
        "predictions": forecast_list,  
        "params": pd.DataFrame(df).to_dict(orient="records")
    }


if __name__ == "__main__":
    arima(sys.argv[1])