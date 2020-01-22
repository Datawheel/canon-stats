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


def pred(df, drilldowns, measures):

    default_params = {
        "changepoint_prior_scale" : 0.05,
        "changepoint_range" : 0.95,
        "periods" : 10,
        "seasonality_mode" : "multiplicative"
    }

    changepoint_prior_scale = float(default_params.get("changepoint_prior_scale"))
    changepoint_range = float(default_params.get("changepoint_range"))
    periods = int(default_params.get("periods"))
    seasonality_mode = default_params.get("seasonality_mode")

    #Change format for date
    if "Month" in drilldowns[0]:
        X = pd.to_datetime(df[["Year", "Month"]], format="%Y%B")
        time_param = "%Y-%m"
    
    elif "Year" in drilldowns[0]: 
        X = pd.to_datetime(df["Year"], format="%Y")
        time_param = "%Y"
    
    freq = drilldowns[0][0]
    df_temp = pd.DataFrame(X)
    
    # Rename time column to "Date", in case it bugs
    for item in [0, "Year", "Month", "Days"]:
            df_temp = pd.DataFrame(df_temp).rename(columns={item: "Date"})
    
    
    # Prepares dataset for prophet
    df2 = pd.DataFrame(df[measures[0]])
    merged = df_temp.merge(df2, left_index=True, right_index=True)
    train_dataset = pd.DataFrame(merged[["Date", measures[0]]]).rename(columns={"Date": "ds", measures[0]: "y"})
  
    
    with suppress_stdout_stderr():
        
        model = Prophet(seasonality_mode=seasonality_mode, changepoint_prior_scale=changepoint_prior_scale, changepoint_range=changepoint_range)
        model.fit(train_dataset)

        # Makes future predictions
        future = model.make_future_dataframe(periods=periods, freq=freq)
        forecast = model.predict(future)
        forecast["ds"] = forecast["ds"].dt.strftime(time_param)
        train_dataset["ds"] = train_dataset["ds"].dt.strftime(time_param)
        values = forecast[["ds", "yhat", "yhat_lower", "yhat_upper", "trend", "trend_lower", "trend_upper"]]

        #Changes values forecasted names into parameter name used for regression
        names = {
            "ds": drilldowns[0],
            "y" : measures[0],
            "yhat": measures[0] + " Prediction",
            "yhat_upper": measures[0] + " Upper Bound",
            "yhat_lower": measures[0] + " Lower Bound",
            "trend": measures[0] + " Trend",
            "trend_lower": measures[0] + " Lower Trend",
            "trend_upper": measures[0] + " upper Trend"    
        }

    return (values, train_dataset, names)


def prophet(API, params):

    r = requests.get(API, params=params)
    df = pd.DataFrame(r.json()["data"])
    measures = params["measures"].split(",")
    df[measures] = df[measures].astype(float)  
    drilldowns = params["drilldowns"].split(",")
    
    data = pd.DataFrame()
    if len(drilldowns) > 1:
        items = df[drilldowns[1]].unique()
        filters = params[drilldowns[1]].split(",")
        for item in items:
            df_temp = df.loc[df[drilldowns[1]] == item]
            values, train_dataset, names = pred(df_temp, drilldowns, measures)
            values[drilldowns[1]] = item
            values[drilldowns[1] + " "+ "ID"] = filters[list(df["Section"].unique()).index(item)]
            #creates a dataframe with predicted data
            df_pred = pd.DataFrame(values)
            #adds real values into dataframe
            df_final = pd.merge(train_dataset, df_pred, on="ds", how="outer").fillna("null").rename(columns=names)
            data = pd.concat([data, df_final], ignore_index=True, sort =False)
    else: 
        values, train_dataset, names = pred(df, drilldowns, measures)
        df_pred = pd.DataFrame(values)
        df_final = pd.merge(train_dataset, df_pred, on="ds", how="outer").fillna("null").rename(columns=names)
        data = pd.concat([data, df_final], ignore_index=True, sort=False)

    return {
        "predictions" : data.to_dict(orient = "records"),
    }

if __name__ == "__main__":
    #prophet(sys.argv[1])
    prophet("https://api.oec.world/tesseract/data", {"drilldowns":"Year","measures":"Trade Value","cube":"trade_i_baci_a_92"})