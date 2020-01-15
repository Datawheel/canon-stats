import json
import pandas as pd
import requests
import statsmodels.api as sm

import sys

from functools import reduce

def logit(API, params):

    r = requests.get(API, params=params)

    df = pd.DataFrame(r.json()["data"])
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors='coerce')
    measures = params["measures"].split(",")

    y = df[[measures[0]]] > df[[measures[0]]].mean()
    X = pd.DataFrame(df, columns=measures[1:])
    X = sm.add_constant(X)

    model = sm.Logit(y, X)
    results = model.fit(disp=0)
    results.summary()

    # results_as_html = results.summary().tables[1].as_html()
    # df_1 = pd.read_html(results_as_html, header=0, index_col=0)
    # df_2 = df_1[0].reset_index().rename(columns={"index": "id"})

    return {
        "hello": "goodbye"
        #"goodbye": X.to_dict(orient="records")
        #"Model" : results.model.__class__.__name__,
        #"Rsquared": results.rsquared,
        #"Adj. squared": results.rsquared_adj,
        #"F-stadistic": results.fvalue,
        #"Prob F-stadistic": results.fvalue,
       # "Log-likelihood": results.llf,
       # "AIC": results.aic,
       # "BIC": results.bic,
       # "No. Observations": results.nobs,
        #"Measures": pd.DataFrame(df_2).to_dict(orient="records"),
    }


if __name__ == "__main__":
    logit("https://api.oec.world/tesseract/data", {"drilldowns": "HS4", "measures": "Trade Value,Quantity", "cube": "trade_s_can_m_hs"})
