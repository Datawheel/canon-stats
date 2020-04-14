from fbprophet import Prophet
from pandas.tseries.offsets import Day, MonthEnd, YearEnd
import os 
import pandas as pd
import warnings


default_params = {
    "seasonality_mode" : "multiplicative",
    "changepoint_prior_scale" : 0.05,
    "changepoint_range" : 0.95,
    "periods" : 10
}

class suppress_stdout_stderr(object):
    """
    A context manager for doing a "deep suppression" of stdout and stderr in
    Python, i.e. will suppress all print, even if the print originates in a
    compiled C/Fortran sub-function.
       This will not suppress raised exceptions, since exceptions are printed
    to stderr just before a script exits, and after the context manager has
    exited (at least, I think that is why it lets exceptions through).
    """
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


def pred(df, drilldowns, measures, seasonality_mode, changepoint_prior_scale, changepoint_range, periods):
    months = {'January':1, 'February':2, 'March':3, 'April':4, 'May':5, 'June':6, 'July':7, 'August':8, 'September':9, 'October':10, 'November':11, 'December':12}
    quarters = {1:"03", 2:"06", 3:"09", 4:"12"}

    level = drilldowns[0]
    measure = measures[0]

    #Change format for date
    if "Month" in level:
        df["Month"] = df["Month"].map(months)
        df["Date"] = pd.to_datetime(df[["Year", "Month"]].assign(DAY=1))
        X = df["Date"] + pd.offsets.MonthEnd(0) 
        time_param = "%Y-%m"

    elif "Quarter" in level: 
        df["Quarter ID"] = df["Quarter ID"].map(quarters)
        X =  df["Year"].astype(str) + df["Quarter ID"].astype(str)
        X = pd.to_datetime(X, format="%Y%m")
        periods = periods + 1
        time_param = "%Y-%m"
    
    elif "Year" in level: 
        X = pd.to_datetime(df["Year"], format="%Y")
        X = X + pd.offsets.YearEnd(0) 
        time_param = "%Y"

    freq = level[0]
    df_temp = pd.DataFrame(X)

    # Renames time column to "Date", in case it bugs
    for item in [0, "Year", "Quarter", "Month", "Days"]:
        df_temp = pd.DataFrame(df_temp).rename(columns={item: "Date"})

    # Prepares dataset for prophet
    merged = df_temp.merge(pd.DataFrame(df[measure]), left_index=True, right_index=True)
    train_dataset = pd.DataFrame(merged[["Date", measure]]).rename(columns={"Date": "ds", measure: "y"})

    with suppress_stdout_stderr():
        model = Prophet(
            changepoint_prior_scale=changepoint_prior_scale, 
            changepoint_range=changepoint_range,
            seasonality_mode=seasonality_mode
        )
        model.fit(train_dataset)

        # Makes future predictions
        future = model.make_future_dataframe(periods=periods, freq=freq)
        forecast = model.predict(future)
        forecast["ds"] = forecast["ds"].dt.strftime(time_param)
        values = forecast[["ds", "yhat", "yhat_lower", "yhat_upper", "trend", "trend_lower", "trend_upper"]]

        # Changes values forecasted columns into parameter name used for regression
        columns = {
            "ds": "Date",
            "y" : measure,
            "yhat": measure + " Prediction",
            "yhat_upper": measure + " Upper Bound",
            "yhat_lower": measure + " Lower Bound",
            "trend": measure + " Trend",
            "trend_lower": measure + " Lower Trend",
            "trend_upper": measure + " Upper Trend"
        }

    return (values, columns)


def prophet(df, params):
    drilldowns = params["drilldowns"].split(",")
    measures = params["measures"].split(",")
    measures = [measures[0]]
    measure = measures[0]
    df = df.dropna()

    # Converts measure column to float
    df[measure] = df[measure].astype(float)  

    # Replaces default params by params given by the user
    for item in default_params.keys():
        if item in params:
            default_params[item] = params[item]

    seasonality_mode = default_params.get("seasonality_mode")
    changepoint_prior_scale = float(default_params.get("changepoint_prior_scale"))
    changepoint_range = float(default_params.get("changepoint_range"))
    periods = int(default_params.get("periods"))

    output = pd.DataFrame()

    if len(drilldowns) > 1:
        pred_level = drilldowns[1]
        pred_level_id = pred_level + " "+ "ID"

        items = df[pred_level].unique()

        for item in items:
            df_temp = df.loc[df[pred_level] == item]
            
            id_val = df_temp[pred_level_id].loc[df_temp[pred_level] == item]
            values, columns = pred(df_temp, drilldowns, measures, seasonality_mode, changepoint_prior_scale, changepoint_range, periods)
            
            values[pred_level] = item
            values[pred_level_id] = id_val.values[0]

            # Creates a dataframe with predicted data
            df_pred = pd.DataFrame(values).rename(columns=columns)
            true_values = df_temp[measures].reset_index()
            df_pred = pd.concat([df_pred, true_values[measures]], axis=1)

            # Adds real values into dataframe
            output = pd.concat([output, df_pred], ignore_index=True, sort=False)

    else: 
        values, columns = pred(df, drilldowns, measures, seasonality_mode, changepoint_prior_scale, changepoint_range, periods)
        true_values = df[measures].reset_index()

        df_pred = pd.DataFrame(values).rename(columns=columns)   
        df_pred = pd.concat([df_pred, true_values[measures]], axis=1)

        output = output.merge(df_pred, how="outer", left_index=True, right_index=True)

    output[(output[measures[0] + " Prediction"] < 0)] = 0
    output[(output[measures[0] + " Lower Bound"] < 0)] = 0
    output[(output[measures[0] + " Upper Bound"] < 0)] = 0
    output[(output[measures[0] + " Lower Trend"] < 0)] = 0
    output[(output[measures[0] + " Upper Trend"] < 0)] = 0

    output = output.drop(output[output["Date"] == 0].index)

    return { 
        "data" : output.to_dict(orient = "records"),
        "params" : {
            "changepoint_prior_scale" : changepoint_prior_scale,
            "changepoint_range" : changepoint_range,
            "periods" : periods,
            "seasonality_mode" : seasonality_mode
        }
    }

if __name__ == "__main__":
    #prophet(sys.argv[1])
    prophet("https://api.oec.world/tesseract/data", {"drilldowns":"Quarter","measures":"Trade Value","cube":"trade_i_comtrade_m_hs","parents":"true"},"{}")