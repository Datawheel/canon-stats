import json
import sys

from regressions.logit import logit

API = str(sys.argv[2])
params = json.loads(sys.argv[1])

def _logit():
    data = logit(API, params)
    print(json.dumps({"data": data}))

if __name__ == "__main__":
    _logit()