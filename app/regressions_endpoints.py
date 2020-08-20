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

auth_level = int(sys.argv[4]) or 0 # Auth level
headers = json.loads(sys.argv[3]) # Headers
params = json.loads(sys.argv[1]) # Query params
cubes_cache = InternalCache(CUBES_API, headers).cubes


class Regressions:
    def __init__(self, name):
        base_class = BaseClass(API, headers, auth_level, cubes_cache)
        self.base = base_class
        self.data = base_class.get_data(params)
        self.name = name


    def get(self):
        def func_not_found():
            print('No Function ' + self.name + ' Found!')
        func_name = "_{}".format(self.name)
        func = getattr(self, func_name, func_not_found) 
        func()

    def _ols(self):
        data = ols(API, params, headers)
        self.base.to_json(data)

    def _logit(self):
        data = logit(API, params, headers)
        self.base.to_json(data)

    def _arima(self):
        data = arima(API, params, headers)
        self.base.to_json(data)

    def _probit(self):
        data = probit(API, params, headers)
        self.base.to_json(data)

    def _prophet(self):
        df = self.data.copy()
        data = prophet(df, params)
        self.base.to_json(data)

if __name__ == "__main__":
    name = str(sys.argv[2])
    Regressions(name).get()
