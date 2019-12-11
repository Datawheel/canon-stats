import sys
import numpy as np
import json
import pandas as pd
import requests

from complexity.complexity import complexity
from complexity.opportunity_gain import opportunity_gain
from complexity.proximity import proximity
from complexity.relatedness import relatedness


API = str(sys.argv[2])
params = json.loads(sys.argv[1])


def _filter(df, dds):
    for dd in dds:
        filter_var = "filter_{}".format(dd)
        if filter_var in params and "{} ID".format(dd) in list(df):
            df = df[df["{} ID".format(dd)].astype(str) == str(params[filter_var])]
    return df


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

    results = _filter(results, [dd1, dd2])

    if "ranking" in params and params["ranking"] == "true":
        results = results.sort_values("{} ECI".format(measure), ascending=False)
        results["{} Ranking".format(measure)] = range(1, results.shape[0] + 1)

    _output(results)


def _opportunity_gain():

    dd1, dd2, measure = params["rca"].split(",")

    dd1_id = "{} ID".format(dd1)
    dd2_id = "{} ID".format(dd2)

    df = _load_data()

    df_labels_1 = df[["{}".format(dd1), dd1_id]].drop_duplicates()
    df_labels_2 = df[["{}".format(dd2), dd2_id]].drop_duplicates()

    if "threshold" in params:
        df["pivot"] = df[df[measure] > int(params["threshold"])]
        df = df[df["pivot"] == True].copy()
        df = df.drop(columns=["pivot"])

    df = df.pivot(
        index=dd1_id, columns=dd2_id, values="{} RCA".format(measure)
    ).reset_index().set_index(dd1_id).dropna(axis=1, how="all").fillna(0)
    rcas = df.astype(float)

    iterations = int(params["iterations"]) if "iterations" in params else 20
    eci, pci = complexity(rcas, iterations)

    results = opportunity_gain(rcas, proximity(rcas), pci)
    results = pd.melt(results.reset_index(), id_vars=[dd1_id], value_name="{} Opportunity Gain".format(measure))
    results = df_labels_1.merge(results, on=dd1_id)
    results = df_labels_2.merge(results, on=dd2_id)

    results = _filter(results, [dd1, dd2])

    _output(results)


def rca():
    dd1, dd2, measure = params["rca"].split(",")

    df = _load_data()
    df = _filter(df, [dd1, dd2])

    _output(df)


def _relatedness():
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

    densities = relatedness(df, proximity(df))
    densities = pd.melt(densities.reset_index(), id_vars=[dd1_id], value_name="{} Relatedness".format(measure))

    densities["pivot"] = densities[dd1_id].astype(str) + "_" + densities[dd2_id].astype(str)

    densities = densities.merge(dd1_df, on=dd1_id)
    densities = densities.merge(dd2_df, on=dd2_id)
    densities = densities.merge(df_rca, on="pivot")
    densities = densities.drop(columns=["pivot"])

    densities = _filter(densities, [dd1, dd2])

    _output(densities)


if __name__ == "__main__":
    function_name = str(sys.argv[3])
    if (function_name == "eci"):
        eci()
    elif function_name == "opportunity_gain":
        _opportunity_gain()
    elif function_name == "relatedness":
        _relatedness()
    elif function_name == "rca":
        rca()
