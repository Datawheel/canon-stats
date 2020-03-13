import json
import pandas as pd
import requests
import statsmodels.api as sm

import sys

from functools import reduce

def probit(API, params, headers):

    r = requests.get(API, params=params, headers=json.loads(headers))

    df = pd.DataFrame(r.json()["data"])
    measures = params["measures"].split(",")
    y = df[[measures[0]]] > df[[measures[0]]].mean()
    X = pd.DataFrame(df, columns=measures[1:])
    X = sm.add_constant(X)

    model = sm.Probit(y, X)
    results = model.fit(disp=0)

    data = {
        "model":[
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
    "model_info":[ 
        {"model_info" : results.model.__class__.__name__},
        #{"method" : model.method},
        {"n. observations" : results.nobs},
        {"pseudo_r_squared": results.prsquared},
        {"df_residuals" : results.df_resid},
        #{"df_model" : results.df_model},
        {"llr" : results.llf},
        {"llr_p_value" : results.llr},
        {"llr_pvalue" : results.llr_pvalue}

    ],    
    "params": pd.DataFrame(df).to_dict(orient="records")
    }

if __name__ == "__main__":
    probit("https://api.oec.world/tesseract/data", {"drilldowns": "HS4", "measures": "Trade Value,Quantity", "cube": "trade_s_can_m_hs"})