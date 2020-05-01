import os
import pandas as pd
import requests
# import requests_cache
import simplejson as json

# expire_after_env_var = "CANON_STATS_CACHE_EXPIRE_AFTER" in os.environ
# expire_after = int(os.environ["CANON_STATS_CACHE_EXPIRE_AFTER"]) if expire_after_env_var else 60*60*24
# requests_cache.install_cache("canon_stats_cache", expire_after=expire_after, allowable_codes=(200, ))
# requests_cache.remove_expired_responses()

class BaseClass:
    def __init__(self, API, headers={}, auth_level=0, cubes_cache={}):
        self.API = API
        self.headers = headers
        self.auth_level = auth_level
        self.cubes_cache = cubes_cache

    def get_data(self, params={}):
        cube = params.get("cube")
        if self.auth_level >= self.cubes_cache[cube]["min_auth_level"]:
            r = requests.get(self.API, params=params, headers=self.headers)
            json_data = r.json()
            if (r.status_code != 200):
                raise Exception(r.text)
            df = pd.DataFrame(json_data["data"]) if "data" in json_data else pd.DataFrame([])
        else:
            raise Exception("This cube is not public")

        return df

    def to_output(self, df):
        print(json.dumps({
            "data": json.loads(df.to_json(orient="records"))
        }))