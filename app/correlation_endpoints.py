import json
import os
import pandas as pd
import sys

from base import BaseClass

API = str(sys.argv[2]) + "/data"
params = json.loads(sys.argv[1])
headers = sys.argv[4]
auth_level = int(sys.argv[5]) or 0
server_headers = sys.argv[6]
CUBES_API = str(sys.argv[2]) + "/cubes"

class Correlation:
    def __init__(self, name):

        if params.get("from"):
            product_from = params.get("from")
        if params.get("to"):
            product_to = params.get("to")
        if params.get("from_code"):
            product_code = params.get("from_code")

        self.base = BaseClass(API, json.loads(headers), auth_level)
        self.name = name
        self.product_code = product_code
        self.product_from = product_from
        self.product_to = product_to

    def get(self):
        def func_not_found():
            print('No Function ' + self.name + ' Found!')
        func_name = "_{}".format(self.name)
        func = getattr(self, func_name, func_not_found) 
        func()

    def _correlation(self):
        df = pd.read_csv('static/correlation_table.csv', dtype="str")

        output = df[df[self.product_from] == self.product_code][[self.product_from, self.product_to]].drop_duplicates()
        output.to_json(orient="records")
    
        self.base.to_output(output)

if __name__ == "__main__":
    name = "correlation"
    Correlation(name).get()