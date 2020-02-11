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


def pred(df, drilldowns, measures,seasonality_mode,changepoint_prior_scale,changepoint_range,periods):
    


    

    months = {'January':1, 'February':2, 'March':3, 'April':4, 'May':5, 'June':6, 'July':7, 'August':8, 'September':9, 'October':10, 'November':11, 'December':12}
    

    #Change format for date
    if "Month" in drilldowns[0]:
        df["Month"] = df["Month"].map(months)
        df['Date'] = pd.to_datetime(df[['Year', 'Month']].assign(DAY=1))
        X = df["Date"]
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
            "ds": "Date",
            "y" : measures[0],
            "yhat": measures[0] + " Prediction",
            "yhat_upper": measures[0] + " Upper Bound",
            "yhat_lower": measures[0] + " Lower Bound",
            "trend": measures[0] + " Trend",
            "trend_lower": measures[0] + " Lower Trend",
            "trend_upper": measures[0] + " Upper Trend"    
        }

    return (values, train_dataset, names)


def prophet(API, params):

    r = requests.get(API, params=params)
    measures = params["measures"].split(",")
    measures = [measures[0]]
    df = pd.DataFrame(r.json()["data"]).dropna()
    df[measures] = df[measures].astype(float)  
    drilldowns = params["drilldowns"].split(",")
    
    default_params = {
        "seasonality_mode" : "multiplicative",
        "changepoint_prior_scale" : 0.05,
        "changepoint_range" : 0.95,
        "periods" : 10
    }

    for item in default_params.keys():
        if item in params:
            default_params[item] = params[item]
    
    seasonality_mode = default_params.get("seasonality_mode")
    changepoint_prior_scale = float(default_params.get("changepoint_prior_scale"))
    changepoint_range = float(default_params.get("changepoint_range"))
    periods = int(default_params.get("periods"))

    
    data2 = pd.DataFrame()
 

    if len(drilldowns) > 1:
        items = df[drilldowns[1]].unique()
       
        for item in items:
            df_temp = df.loc[df[drilldowns[1]] == item]
            
            id_val = df_temp[drilldowns[1] + " "+ "ID"].loc[df_temp[drilldowns[1]]==item]
            
            values, train_dataset, names = pred(df_temp, drilldowns, measures,seasonality_mode,changepoint_prior_scale,changepoint_range,periods)
            
            values[drilldowns[1]] = item
            values[drilldowns[1] + " "+ "ID"] = id_val.values[0]
            #creates a dataframe with predicted data
            
            df_pred = pd.DataFrame(values).rename(columns=names)
            
            true_values = df_temp[measures].reset_index()

            df_pred = pd.concat([df_pred,true_values[measures]], axis=1)
            
            #adds real values into dataframe
            
            
            data2 = pd.concat([data2, df_pred], ignore_index=True, sort =False)
           
        
        #data2= data2.merge(data, how="outer", left_index=True, right_index=True)   
       
    
    else: 

        values, train_dataset, names = pred(df, drilldowns, measures,seasonality_mode,changepoint_prior_scale,changepoint_range,periods)
       
        true_values = df[measures].reset_index()
           
        df_pred = pd.DataFrame(values).rename(columns=names)   
        df_pred = pd.concat([df_pred,true_values[measures]], axis=1)

        
        
        data2= data2.merge(df_pred, how="outer", left_index=True, right_index=True)

   
    return {
        "predictions" : data2.to_dict(orient = "records"),
        "prophet_args" : [
            {"seasonality_mode" : seasonality_mode},
            {"changepoint_prior_scale" : changepoint_prior_scale},
            {"changepoint_range" : changepoint_range},
            {"periods" : periods}
        ]
    }

if __name__ == "__main__":
    #prophet(sys.argv[1])
    prophet("https://api.oec.world/tesseract/data", {"drilldowns":"Year,Section","measures":"Trade Value","cube":"trade_s_jpn_m_hs","parents":"true","Section":"1,2,3"})