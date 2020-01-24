import json
import pandas as pd
import requests
import statsmodels.api as sm
import sys

from functools import reduce


def ols(API, params):

    r = requests.get(API, params=params)

    df = pd.DataFrame(r.json()["data"])
    measures = params["measures"].split(",")

    y = df[[measures[0]]].astype(float)
    X = pd.DataFrame(df, columns=measures[1:]).astype(float)
    X = sm.add_constant(X)

    model = sm.OLS(y, X)
    results = model.fit()

    results_as_html = results.summary().tables[1].as_html()
    df_1 = pd.read_html(results_as_html, header=0, index_col=0)
    df_2 = df_1[0].reset_index().rename(columns={"index": "id"})


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
            columns={"index": "id", 0: item["name"], 1: item["name"]})
        df_list.append(df)

    df = reduce(lambda x, y: pd.merge(x, y, on="id", how="inner"), df_list)

    return {
        "Model" : results.model.__class__.__name__,
        "Rsquared": results.rsquared,
        "Adj. squared": results.rsquared_adj,
        "F-stadistic": results.fvalue,
        "Prob F-statistic": results.fvalue,
        "Log-likelihood": results.llf,
        "AIC": results.aic,
        "BIC": results.bic,
        "No. Observations": results.nobs,
        "Measures": pd.DataFrame(df).to_dict(orient="records")
    }


if __name__ == "__main__":
    ols(sys.argv[1])