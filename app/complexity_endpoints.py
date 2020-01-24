import sys
import numpy as np
import json
import pandas as pd
import requests

from complexity.complexity import complexity
from complexity.opportunity_gain import opportunity_gain
from complexity.proximity import proximity
from complexity.rca import rca
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
    _params = params.copy()
    dd1, dd2, measure = _params["rca"].split(",")
    _params["drilldowns"] = "{},{}".format(dd1, dd2)
    _params["measures"] = measure
    _params.pop("rca", None)
    r = requests.get(API, params=_params)
    df = pd.DataFrame(r.json()["data"])

    if "alias" in _params:
        dd1, dd2 = _params["alias"].split(",")

    dd1_id = "{} ID".format(dd1)
    dd2_id = "{} ID".format(dd2)

    df_labels_1 = df[["{}".format(dd1), dd1_id]].drop_duplicates()
    df_labels_2 = df[["{}".format(dd2), dd2_id]].drop_duplicates()

    for dd in [dd1, dd2]:
        filter_var = "threshold_{}".format(dd)
        dd_id = "{} ID".format(dd)
        if filter_var in _params and dd_id in list(df):
            df_temp = df[[dd_id, measure]].groupby([dd_id]).sum().reset_index()
            list_temp = df_temp[df_temp[measure] >= float(params[filter_var])][dd_id].unique()
            df = df[df[dd_id].isin(list_temp)]


    df = df.pivot(index=dd1_id, columns=dd2_id, values=measure)

    output = rca(df).reset_index().melt(id_vars=dd1_id, value_name="{} RCA".format(measure))
    output = df_labels_1.merge(output, on=dd1_id)
    output = df_labels_2.merge(output, on=dd2_id)

    return output



def _output(df):
    print(json.dumps({
      "data": json.loads(df.to_json(orient="records"))
      }))

def _params():
    dd1, dd2, measure = params["rca"].split(",")
    if "alias" in params:
        dd1, dd2 = params["alias"].split(",")

    dd1_id = "{} ID".format(dd1)
    dd2_id = "{} ID".format(dd2)

    return dd1, dd2, measure, dd1_id, dd2_id


def eci():
    dd1, dd2, measure, dd1_id, dd2_id = _params()

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

    if "ranking" in params and params["ranking"] == "true":
        results = results.sort_values("{} ECI".format(measure), ascending=False)
        results["{} Ranking".format(measure)] = range(1, results.shape[0] + 1)

    results = _filter(results, [dd1, dd2])

    _output(results)


def _opportunity_gain():

    dd1, dd2, measure, dd1_id, dd2_id = _params()

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


def _proximity():
    dd1, dd2, measure, dd1_id, dd2_id = _params()

    df = _load_data()


    df_labels = df[["{}".format(dd2), dd2_id]].drop_duplicates()

    rcas = df.pivot(
        index=dd1_id, columns=dd2_id, values="{} RCA".format(measure)
    ).reset_index().set_index(dd1_id).dropna(axis=1, how="all").fillna(0)
    rcas = rcas.astype(float)
    df = proximity(rcas)

    df = df.reset_index()
    df = df.rename(columns={dd2_id: "{} Target".format(dd2_id)})
    df = pd.melt(df, id_vars="{} Target".format(dd2_id), value_name="{} Proximity".format(measure))
    df = df.rename(columns={dd2_id: "{} Source".format(dd2_id)})
    df = df[df["{} Source".format(dd2_id)] != df["{} Target".format(dd2_id)]]

    for item in ["Source", "Target"]:
        df = df.merge(df_labels, left_on="{} {}".format(dd2_id, item), right_on=dd2_id)
        df = df.rename(columns={dd2: "{} {}".format(dd2, item)})
        df = df.drop(columns=[dd2_id])

    filter_var = "filter_{}".format(dd2)
    if filter_var in params and "{} ID Source".format(dd2) in list(df):
        df = df[df["{} ID Source".format(dd2)].astype(str) == str(params[filter_var])]

    _output(df)

def _rca():
    dd1, dd2, measure, dd1_id, dd2_id = _params()

    df = _load_data()
    df = _filter(df, [dd1, dd2])

    _output(df)


def _relatedness():
    df = _load_data()

    dd1, dd2, measure, dd1_id, dd2_id = _params()
    relatedness_measure = "{} Relatedness".format(measure)

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
    densities = pd.melt(densities.reset_index(), id_vars=[dd1_id], value_name=relatedness_measure)

    densities["pivot"] = densities[dd1_id].astype(str) + "_" + densities[dd2_id].astype(str)

    densities = densities.merge(dd1_df, on=dd1_id)
    densities = densities.merge(dd2_df, on=dd2_id)
    densities = densities.merge(df_rca, on="pivot")
    densities = densities.drop(columns=["pivot"])

    densities = _filter(densities, [dd1, dd2])

    if "top_relatedness" in params:
        densities = densities.sort_values(by=relatedness_measure, ascending=False).head(int(params["top_relatedness"]))

    _output(densities)


if __name__ == "__main__":
    function_name = str(sys.argv[3])
    if (function_name == "eci"):
        eci()
    elif function_name == "opportunity_gain":
        _opportunity_gain()
    elif function_name == "proximity":
        _proximity()
    elif function_name == "relatedness":
        _relatedness()
    elif function_name == "rca":
        _rca()
