import requests
import pandas as pd
import json
import sys
import numpy as np
from statsmodels.tsa.arima_model import ARIMA
import warnings
import matplotlib.pyplot as plt
import numpy as np
from pandas import Series
from sklearn.metrics import mean_squared_error
from functools import reduce

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
    dataset = dataset.astype('float32')
    best_score, best_cfg = float("inf"), None
    for p in p_values:
        for d in d_values:
            for q in q_values:
                order = (p,d,q)
                try:
                    mse = evaluate_arima_model(dataset, order)
                    if mse < best_score:
                        best_score, best_cfg = mse, order
                    #print('ARIMA%s MSE=%.3f' % (order,mse))
                except:
                    continue
    return (best_cfg)


## Predictions on ARIMA Model
def pred_func(X,order):
	size = int(len(X.values) * 0.66)
	train, test = X.values[0:size], X.values[size:len(X)]
	history = [x for x in train]
	predictions = list()
	for t in range(len(test)):
		model = ARIMA(history, order=order)
		model_fit = model.fit(disp=0)
		output = model_fit.forecast()
		yhat = output[0][0]
		predictions.append(yhat)
		obs = test[t]
		history.append(obs)
		#print('predicted=%f, expected=%f' % (yhat, obs))
	#plt.show()
	return predictions




def arima(API, params):

    r = requests.get(API, params=params)
    df = pd.DataFrame(r.json()["data"])
    measures = params["measures"].split(",")
    X = pd.DataFrame(df, columns=measures[:]).set_index(df["Year"])
    
    p_values = range(0, 3)
    d_values = range(0, 3)
    q_values = range(0, 3)
    warnings.filterwarnings("ignore")
    best_cfg = evaluate_models(X.values, p_values, d_values, q_values)
    model = ARIMA(X.values, order=(1,0,0))
    results = model.fit(disp=0)
    
    start_index = 0
    end_index = (len(X)+10)
    forecast = results.predict()
    forecast_list = forecast.tolist()

    data = {
        "model":[
            {"name": "exog_name", "value": model.exog_names},
            {"name": "params", "value": results.params},
            {"name": "bse", "value": results.bse},
            {"name": "t_values", "value": results.tvalues},
            {"name": "p_values", "value": results.pvalues},
            {"name": "low_cof_int", "value": results.conf_int()[0]},
            {"name": "upp_cof_int", "value": results.conf_int()[1]}
    ]
    }

    df_list = []

    for item in data["model"]:
        df = pd.DataFrame(item["value"]).reset_index().rename(
            columns={"index": "id", 0: item["name"]})
        df_list.append(df)

    df = reduce(lambda x, y: pd.merge(x, y, on="id", how="inner"), df_list)
    df = df.drop(["id"], axis=1)

    return {
    "Predictions": forecast_list,
    "Measures" : pd.DataFrame(df).to_dict(orient="records")
    }


if __name__ == "__main__":
    arima("https://api.oec.world/tesseract/data",
          {"drilldowns": "Year", "measures": "Trade Value", "cube": "trade_i_baci_a_92"})
