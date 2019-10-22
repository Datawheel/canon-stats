import sys
import numpy as np
import json
import pandas as pd
import requests

from complexity.complexity import complexity
from complexity.density import density
from complexity.proximity import proximity


API = str(sys.argv[2])
params = json.loads(sys.argv[1])


def _load_data():
    r = requests.get(API, params=params)
    return pd.DataFrame(r.json()["data"])


def _output(df):
    print(json.dumps({
      "data": json.loads(df.to_json(orient="records"))
      }))


def eci():
    dd1, dd2, measure = params["rca"].split(",")

    dd1_id = "{} ID".format(dd1)
    dd2_id = "{} ID".format(dd2)

    df = _load_data()

    df_labels = df[["{}".format(dd1), dd1_id]].drop_duplicates()

    if "threshold" in params:
        df["pivot"] = df[df[measure] > int(params["threshold"])]
        df = df[df["pivot"] == True].copy()
        df = df.drop(columns=["pivot"])

    df = df.pivot(
        index=dd1_id, columns=dd2_id, values="{} RCA".format(measure)
    ).reset_index().set_index(dd1_id).dropna(axis=1, how="all").fillna(0)
    df = df.astype(float)

    iterations = int(params["iterations"]) if "iterations" in params else 20
    eci, pci = complexity(df, iterations)

    results = pd.DataFrame(eci).rename(columns={0: "{} ECI".format(measure)}).reset_index()
    results = df_labels.merge(results, on=dd1_id)

    _output(results)


def rca():
    dd1, dd2, measure = params["rca"].split(",")

    df = _load_data()

    for dd in [dd1, dd2]:
        filter_var = "filter_{}".format(dd)
        if filter_var in params:
            df = df[df["{} ID".format(dd)] == int(params[filter_var])]

    _output(df)


def relatedness():
    df = _load_data()

    dd1, dd2, measure = params["rca"].split(",")

    dd1_id = "{} ID".format(dd1)
    dd2_id = "{} ID".format(dd2)

    dd1_df = df[["{}".format(dd1), dd1_id]].drop_duplicates()
    dd2_df = df[["{}".format(dd2), dd2_id]].drop_duplicates()

    df_rca = df.copy()
    df_rca["pivot"] = df_rca[dd1_id].astype(str) + "_" + df_rca[dd2_id].astype(str)
    df_rca = df_rca[["pivot", "{} RCA".format(measure)]]

    df = df.pivot(
        index=dd1_id, columns=dd2_id, values="{} RCA".format(measure)
    ).reset_index().set_index(dd1_id).dropna(axis=1, how="all").fillna(0)
    df = df.astype(float)

    densities = density(df, proximity(df))
    densities = pd.melt(densities.reset_index(), id_vars=[dd1_id], value_name="{} Relatedness".format(measure))

    densities["pivot"] = densities[dd1_id].astype(str) + "_" + densities[dd2_id].astype(str)

    densities = densities.merge(dd1_df, on=dd1_id)
    densities = densities.merge(dd2_df, on=dd2_id)
    densities = densities.merge(df_rca, on="pivot")
    densities = densities.drop(columns=["pivot"])

    for dd in [dd1, dd2]:
        filter_var = "filter_{}".format(dd)
        if filter_var in params:
            filter_param = params[filter_var]
            densities["{} ID".format(dd)] = densities["{} ID".format(dd)].astype(str)
            densities = densities[densities["{} ID".format(dd)] == filter_param]

    _output(densities)


if __name__ == "__main__":
    function_name = str(sys.argv[3])
    if (function_name == "eci"):
        eci()
    elif function_name == "relatedness":
        relatedness()
    elif function_name == "rca":
        rca()
