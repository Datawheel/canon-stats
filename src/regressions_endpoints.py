import simplejson as json
import sys

from regressions.ols import ols
from regressions.logit import logit
from regressions.arima import arima
from regressions.probit import probit
from regressions.prophet import prophet

API = str(sys.argv[2]) 
params = json.loads(sys.argv[1])
headers = sys.argv[4]


default_params = {
  "cube": "trade_i_baci_a_92",
  "drilldowns": "Year",
  "measures": "Trade Value",
  "seasonality_mode": "multiplicative",
  "changepoint_prior_scale": 0.05,
  "changepoint_range": 0.80
}

def _ols():
    data = ols(API, params, headers)
    print(json.dumps({"data": data}))

def _logit():
    data = logit(API, params, headers)
    print(json.dumps({"data": data}))

def _arima():
    data = arima(API, params, headers)
    print(json.dumps({"data": data}, ignore_nan=True))

def _probit():
    data = probit(API, params, headers)
    print(json.dumps({"data": data}))

def _prophet():
    data = prophet(API, params, headers)
    print(json.dumps({"data": data}, ignore_nan=True))

if __name__ == "__main__":
    function_name = str(sys.argv[3])
    if (function_name == "ols"):
        _ols()
    elif (function_name == "logit"):
        _logit()
    elif (function_name == "arima"):
        _arima()
    elif (function_name == "probit"):
        _probit()
    elif (function_name == "prophet"):
        _prophet()
