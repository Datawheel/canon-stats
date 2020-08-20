import os
import pandas as pd
import requests
import simplejson as json

BASE_URL = str(os.environ["CANON_STATS_API"]).strip("/")

API = f"{BASE_URL}/data.jsonrecords"
CUBES_API = f"{BASE_URL}/cubes"


class BaseClass:
    def __init__(self, API, headers={}, auth_level=0, cubes_cache={}):
        self.API = API
        self.headers = headers
        self.auth_level = auth_level
        self.cubes_cache = cubes_cache

    def get_data(self, params={}):
        # cube = params.get("cube")
        # if self.auth_level >= self.cubes_cache[cube]["min_auth_level"]:
        r = requests.get(self.API, params=params, headers=self.headers)
        json_data = r.json()
        if (r.status_code != 200):
            raise Exception(r.text)
        df = pd.DataFrame(json_data["data"]) if "data" in json_data else pd.DataFrame([])
        #else:
        #    raise Exception("This cube is not public")

        return df

    def to_output(self, df):
        """
        Convert a DataFrame to a JSON file, that can be used as response by an API.
        @returns: JSON formatted string.
        """
        output = {
            "data": json.loads(df.to_json(orient="records"))
        }
        print(json.dumps(output))


    def to_json(self, data):
        print(json.dumps(data, ignore_nan=True))