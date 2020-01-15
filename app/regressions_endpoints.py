import json
import sys

from regressions.ols import ols
from regressions.logit import logit

API = str(sys.argv[2])
params = json.loads(sys.argv[1])


def _ols():
    data = ols(API, params)
    print(json.dumps({"data": data}))

def _logit():
    data = logit(API, params)
    print(json.dumps({"data": data}))


if __name__ == "__main__":
    function_name = str(sys.argv[3])
    if (function_name == "ols"):
        _ols()
    elif function_name == "logit":
        _logit()

