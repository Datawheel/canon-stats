import requests
import pandas as pd
import statsmodels.api as sm
import json
from functools import reduce
from urllib import parse
import sys
from statsmodels.tsa.arima_model import ARIMA
from sklearn.metrics import mean_squared_error
import warnings
from pandas.plotting import autocorrelation_plot
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as pyplot
import matplotlib.pyplot as plt
import numpy as np
from pandas import Series

import requests
import pandas as pd
import statsmodels.api as sm
import json
from functools import reduce
from urllib import parse
import sys
from statsmodels.tsa.arima_model import ARIMA
from sklearn.metrics import mean_squared_error
import warnings
from pandas.plotting import autocorrelation_plot
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as pyplot
import matplotlib.pyplot as plt
import numpy as np
import warnings
from pandas import Series
from statsmodels.tsa.arima_model import ARIMA
from sklearn.metrics import mean_squared_error


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
                    print('ARIMA%s MSE=%.3f' % (order,mse))
                except:
                    continue
    return best_cfg


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
		print('predicted=%f, expected=%f' % (yhat, obs))
	error = mean_squared_error(test, predictions)
	plt.show()
	return predictions

def arima(API, params):

    #Recolección de datos
    r = requests.get(API, params=params)

    df = pd.DataFrame(r.json()["data"])
    measures = params["measures"].split(",")

    X = pd.DataFrame(df, columns=measures[:]).set_index(df["Year"])

    p_values = [0, 1, 2, 4, 6, 8, 10]
    d_values = range(0, 3)
    q_values = range(0, 3)
    warnings.filterwarnings("ignore")
    best_cfg = evaluate_models(X.values, p_values, d_values, q_values)
    model = ARIMA(X.values, order=best_cfg)
    results = model.fit()

    results_as_html = results.summary().tables[1].as_html()
    df_1 = pd.read_html(results_as_html, header=0, index_col=0)
    df_2 = df_1[0].reset_index().rename(columns={"index": "id"})

    return {
    
        "Measures": pd.DataFrame(df_2).to_dict(orient="records")
    }

if __name__ == "__main__":
    arima(sys.argv[1])