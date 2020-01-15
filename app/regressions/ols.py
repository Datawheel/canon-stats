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

    y = df[[measures[0]]]
    X = pd.DataFrame(df, columns=measures[1:])
    X = sm.add_constant(X)

    model = sm.OLS(y, X)
    results = model.fit()

    results_as_html = results.summary().tables[1].as_html()
    df_1 = pd.read_html(results_as_html, header=0, index_col=0)
    df_2 = df_1[0].reset_index().rename(columns={"index": "id"})

    return {
        "Model" : results.model.__class__.__name__,
        "Rsquared": results.rsquared,
        "Adj. squared": results.rsquared_adj,
        "F-stadistic": results.fvalue,
        "Prob F-stadistic": results.fvalue,
        "Log-likelihood": results.llf,
        "AIC": results.aic,
        "BIC": results.bic,
        "No. Observations": results.nobs,
        "Measures": pd.DataFrame(df_2).to_dict(orient="records")
    }


if __name__ == "__main__":
    ols(sys.argv[1])