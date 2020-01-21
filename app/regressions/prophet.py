import json
import numpy as np
import pandas as pd
import requests
import sys
import warnings
from fbprophet import Prophet
import os 

class suppress_stdout_stderr(object):
    '''
    A context manager for doing a "deep suppression" of stdout and stderr in
    Python, i.e. will suppress all print, even if the print originates in a
    compiled C/Fortran sub-function.
       This will not suppress raised exceptions, since exceptions are printed
    to stderr just before a script exits, and after the context manager has
    exited (at least, I think that is why it lets exceptions through).

    '''
    def __init__(self):
        # Open a pair of null files
        self.null_fds = [os.open(os.devnull, os.O_RDWR) for x in range(2)]
        # Save the actual stdout (1) and stderr (2) file descriptors.
        self.save_fds = [os.dup(1), os.dup(2)]

    def __enter__(self):
        # Assign the null pointers to stdout and stderr.
        os.dup2(self.null_fds[0], 1)
        os.dup2(self.null_fds[1], 2)

    def __exit__(self, *_):
        # Re-assign the real stdout/stderr back to (1) and (2)
        os.dup2(self.save_fds[0], 1)
        os.dup2(self.save_fds[1], 2)
        # Close the null files
        for fd in self.null_fds + self.save_fds:
            os.close(fd)

def prophet(API, params):

    r = requests.get(API, params=params)
    df = pd.DataFrame(r.json()["data"])
    measures = params["measures"].split(",")
 
 
    default_params = {
        "seasonality_mode" : "multiplicative",
        "changepoint_prior_scale" : 0.05,
        "changepoint_range" : 0.95
    }


    if "seasonality_mode" in params:
        default_params["seasonality_mode"] = params["seasonality_mode"]
    
    if "changepoint_prior_scale" in params:
        default_params["changepoint_prior_scale"] = float(params["changepoint_prior_scale"])
    
    if "changepoint_range" in params:
        default_params["changepoint_range"] = float(params["changepoint_range"])
    

    seasonality_mode = default_params.get("seasonality_mode")
    changepoint_prior_scale = default_params.get("changepoint_prior_scale")
    changepoint_range = default_params.get("changepoint_range")

    if "Month" in df.columns:
        X = pd.to_datetime(df['Year'].astype(str) + df['Month'].astype(str), format='%Y%B')
        time_param = "%Y-%m"
        periods = 120
        
    else: 
        X = pd.to_datetime(df['Year'].astype(str), format='%Y')
        time_param = "%Y"
        periods = 10
    
    freq = params["drilldowns"][0]
    X_df = pd.DataFrame(X)

    for item in [0, "Year", "Month", "Days"]:
        X_df = pd.DataFrame(X_df).rename(columns={item: "Date"})

    df2 = pd.DataFrame(df[params["measures"]])
    merged = X_df.merge(df2, left_index=True, right_index=True)

    train_dataset = pd.DataFrame()
    train_dataset["ds"] = merged["Date"]
    train_dataset["y"] = merged[params["measures"]]
    
    
    with suppress_stdout_stderr():
        
        m = Prophet(seasonality_mode=seasonality_mode, changepoint_prior_scale=changepoint_prior_scale, changepoint_range=changepoint_range)
        m.fit(train_dataset)
        future = m.make_future_dataframe(periods=periods, freq=freq)
        forecast = m.predict(future)
        forecast["ds"] = forecast["ds"].dt.strftime(time_param)
        train_dataset["ds"] = train_dataset["ds"].dt.strftime(time_param)
        values = forecast[["ds", "yhat", "yhat_lower", "yhat_upper", "trend", "trend_lower", "trend_upper"]]

        names = {
            "ds": params["drilldowns"],
            "y" : params["measures"],
            "yhat": params["measures"] + " Prediction",
            "yhat_upper": params["measures"] + " Upper Bound",
            "yhat_lower": params["measures"] + " Lower Bound",
            "trend": params["measures"] + " Trend",
            "trend_lower": params["measures"] + " Lower Trend",
            "trend_upper": params["measures"] + " upper Trend"    
        }

        values["group"] = "chl"
    
        df_pred = pd.DataFrame(values)
        df_final = pd.merge(train_dataset,df_pred, on='ds', how='outer').fillna("null").rename(columns=names)
        

    return {
        "predictions" : df_final.to_dict(orient = "records"),      
        "prophet_args" : [
            {"seasonality_mode" : seasonality_mode},
            {"changepoint_prior_scale" : changepoint_prior_scale},
            {"changepoint_range" : changepoint_range}
        ]
    }

if __name__ == "__main__":
    #prophet(sys.argv[1])
    prophet("https://api.oec.world/tesseract/data", {"drilldowns":"Year","measures":"Trade Value","cube":"trade_i_baci_a_92"})