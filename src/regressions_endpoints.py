import simplejson as json
import sys
import os

from regressions.ols import ols
from regressions.logit import logit
from regressions.arima import arima
from regressions.probit import probit
from regressions.prophet import prophet

from base import BaseClass, API, CUBES_API
from cache import InternalCache

params = json.loads(sys.argv[1])
headers = sys.argv[2]
auth_level = int(sys.argv[4]) or 0
server_headers = sys.argv[5]
cubes_cache = InternalCache(CUBES_API, json.loads(headers)).cubes


class Regressions:
    def __init__(self, name):
        self.base = BaseClass(API, json.loads(headers), auth_level, cubes_cache)
        self.name = name


    def get(self):
        def func_not_found():
            print('No Function ' + self.name + ' Found!')
        func_name = "_{}".format(self.name)
        func = getattr(self, func_name, func_not_found) 
        func()

    def _ols(self):
        data = ols(API, params, headers)
        print(json.dumps(data, ignore_nan=True))

    def _logit(self):
        data = logit(API, params, headers)
        print(json.dumps(data, ignore_nan=True))

    def _arima(self):
        data = arima(API, params, headers)
        print(json.dumps(data, ignore_nan=True))

    def _probit(self):
        data = probit(API, params, headers)
        print(json.dumps(data))

    def _prophet(self):
        df = self.base.get_data(params)
        data = prophet(df, params)
        print(json.dumps(data, ignore_nan=True))

if __name__ == "__main__":
    name = str(sys.argv[3])
    Regressions(name).get()
