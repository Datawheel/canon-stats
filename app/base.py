import pandas as pd
import requests
import simplejson as json

class BaseClass:
    def __init__(self, API, headers={}):
        self.API = API
        self.headers = headers

    def get_data(self, params={}):
        r = requests.get(self.API, params=params, headers=self.headers)
        json_data = r.json()
        if (r.status_code != 200):
            raise Exception(r.text)
        df = pd.DataFrame(json_data["data"]) if "data" in json_data else pd.DataFrame([])
        return df

    def to_output(self, df):
        print(json.dumps({
            "data": json.loads(df.to_json(orient="records"))
        }))
