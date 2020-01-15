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

    # Creo un dataframe
    df = pd.DataFrame(r.json()["data"])

    # Paso los valores de la primera columna a una provicional llamada endogena
    endog = df[[measures[0]]]

    # Creo una columna que contenga un booleano si supera el promedio
    endog["mu"] = endog > endog.mean()

    # Calculo del logit
    y = endog["mu"]
    X = pd.DataFrame(df, columns=measures[1:])
    X = sm.add_constant(X)

    model = sm.OLS(y, X)
    results = model.fit()

    data = [
        {"name": "coef", "value": results.params},
        {"name": "std err", "value": results.bse},
        {"name": "z", "value": results.tvalues},
        {"name": "P > |z|", "value": results.pvalues},
        {"name": "low_cof_int", "value": results.conf_int()[0]},
        {"name": "upp_cof_int", "value": results.conf_int()[1]}
    ]

    df_list = []

    for item in data:
        df = pd.DataFrame(item["value"]).reset_index().rename(
            columns={"index": "id", 0: item["name"], 1: item["name"]})
        df_list.append(df)

    df = reduce(lambda x, y: pd.merge(x, y, on="id", how="inner"), df_list)

    return {
        "rsquared": results.rsquared,
        "adj. rsquared": results.rsquared_adj,
        "F-stadistic": results.fvalue,
        "Prob F-stadistic": results.fvalue,
        "Log-likelihood": results.llf,
        "AIC": results.aic,
        "BIC": results.bic,
        "n_observations": results.nobs,
        "params": pd.DataFrame(df).to_dict(orient="records")
    }


if __name__ == "__main__":
    logit(sys.argv[1])