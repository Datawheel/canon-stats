import json
import pandas as pd
import requests
import statsmodels.api as sm

import sys

from functools import reduce

def logit(API, params):

    r = requests.get(API, params=params)

    df = pd.DataFrame(r.json()["data"])
    measures = params["measures"].split(",")
    y = df[[measures[0]]] > df[[measures[0]]].mean()
    X = pd.DataFrame(df, columns=measures[1:])
    X = sm.add_constant(X)

    model = sm.Logit(y, X)
    results = model.fit(disp=0)
    print(results.llr)
    return {
        "model_info":[
            {"model_info" : results.model.__class__.__name__},
            {"n. observations" : results.nobs},
            {"pseudo_r_squared": results.prsquared},
            {"df_residuals" : results.df_resid},
            {"df_model" : results.df_model},
            {"llr" : results.llf},
            #{"llr_p_value" : results.llr_pvalue}
        ]
    }


if __name__ == "__main__":
    logit("https://api.oec.world/tesseract/data", {"drilldowns": "HS4", "measures": "Trade Value,Quantity", "cube": "trade_s_can_m_hs"})
