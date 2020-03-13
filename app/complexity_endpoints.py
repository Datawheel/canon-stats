import json
import numpy as np
import pandas as pd
import requests
import sys

from complexity.complexity import complexity
from complexity.opportunity_gain import opportunity_gain
from complexity.proximity import proximity
from complexity.rca import rca
from complexity.relatedness import relatedness

API = str(sys.argv[2])
params = json.loads(sys.argv[1])
headers = sys.argv[4]


def _load_params():
    """
    Returns params for using
    """
    dd1, dd2, measure = params["rca"].split(",")
    # if "alias" in params:
    #     dd1, dd2 = params["alias"].split(",")

    dd1_id = "{} ID".format(dd1)
    dd2_id = "{} ID".format(dd2)

    return dd1, dd2, dd1_id, dd2_id, measure


def _load_alias_params():
    dd1, dd2, dd1_id, dd2_id, measure = _load_params()
    if "alias" in params:
        dd1, dd2 = params["alias"].split(",")
        dd1_id = "{} ID".format(dd1)
        dd2_id = "{} ID".format(dd2)

    return dd1, dd2, dd1_id, dd2_id

def _filter(df, dds):
    for dd in dds:
        filter_var = "filter_{}".format(dd)
        if filter_var in params and "{} ID".format(dd) in list(df):
            df = df[df["{} ID".format(dd)].astype(str) == str(params[filter_var])]

    return df


def _load_data():
    """
    Requests data from tesseract endpoint, and calculates RCA index
    """
    dd1, dd2, dd1_id, dd2_id, measure = _load_params()
    _params = params.copy()
    _params["drilldowns"] = "{},{}".format(dd1, dd2)
    _params["measures"] = measure

    # Removes rca as param
    _params.pop("rca", None)

    # Gets data and converts request into dataframe
    r = requests.get(API, params=_params, headers=json.loads(headers))
    if (r.status_code != 200):
        raise Exception(r.text)

    df = pd.DataFrame(r.json()["data"])

    dd1, dd2, dd1_id, dd2_id = _load_alias_params()

    # Gets labels for drilldowns
    df_labels_1 = df[[dd1, dd1_id]].drop_duplicates()
    df_labels_2 = df[[dd2, dd2_id]].drop_duplicates()

    # Using threshold_* param, filter rows into the dataframe
    for dd in [dd1, dd2]:
        filter_var = "threshold_{}".format(dd)
        dd_id = "{} ID".format(dd)
        if filter_var in _params and dd_id in list(df):
            df_temp = df[[dd_id, measure]].groupby([dd_id]).sum().reset_index()
            list_temp = df_temp[df_temp[measure] >= float(params[filter_var])][dd_id].unique()
            df = df[df[dd_id].isin(list_temp)]

    # Copies original dataframe
    df_final = df.copy()

    # Calculates RCA index
    df = df.pivot(index=dd1_id, columns=dd2_id, values=measure)
    output = rca(df).reset_index().melt(id_vars=dd1_id, value_name="{} RCA".format(measure))
    output = df_labels_1.merge(output, on=dd1_id)
    output = df_labels_2.merge(output, on=dd2_id)
    output = _threshold(output)

    # Includes parent and measure data
    output = output.merge(df_final, on=[dd1_id, dd2_id], how="inner")
    output = output.drop(columns=["{}_x".format(dd1), "{}_y".format(dd2)])
    output = output.rename(columns={"{}_x".format(dd2): dd2, "{}_y".format(dd1): dd1})

    return output


def _output(df):
    print(json.dumps({
      "data": json.loads(df.to_json(orient="records"))
    }))


def _threshold(df): 
    dd1, dd2, measure = params["rca"].split(",")
    if "threshold" in params:
        df["pivot"] = df[df[measure] > int(params["threshold"])]
        df = df[df["pivot"] == True].copy()
        df = df.drop(columns=["pivot"])

    return df


def _eci():
    dd1, dd2, dd1_id, dd2_id, measure = _load_params()
    df = _load_data()
    df_copy = df.copy()
    dd1, dd2, dd1_id, dd2_id = _load_alias_params()

    df_labels = df[[dd1, dd1_id]].drop_duplicates()

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
    dd1, dd2, dd1_id, dd2_id, measure = _load_params()
    df = _load_data()
    dd1, dd2, dd1_id, dd2_id = _load_alias_params()

    df_copy = df.copy()

    df = df.pivot(
        index=dd1_id, columns=dd2_id, values="{} RCA".format(measure)
    ).reset_index().set_index(dd1_id).dropna(axis=1, how="all").fillna(0)
    rcas = df.astype(float)

    iterations = int(params["iterations"]) if "iterations" in params else 21
    eci, pci = complexity(rcas, iterations)

    output = opportunity_gain(rcas, proximity(rcas), pci)
    output = pd.melt(
        output.reset_index(), 
        id_vars=[dd1_id], 
        value_name="{} Opportunity Gain".format(measure)
    )

    output = output.merge(df_copy, on=[dd1_id, dd2_id], how="inner")
    output = _filter(output, [dd1, dd2])

    _output(output)


def _proximity():
    dd1, dd2, dd1_id, dd2_id, measure = _load_params()
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
    dd1, dd2, dd1_id, dd2_id, measure = _load_params()

    df = _load_data()

    dd1, dd2, dd1_id, dd2_id = _load_alias_params()

    df = _filter(df, [dd1, dd2])

    _output(df)


def _relatedness():
    df = _load_data()
    dd1, dd2, dd1_id, dd2_id, measure = _load_params()
    dd1, dd2, dd1_id, dd2_id = _load_alias_params()

    relatedness_measure = "{} Relatedness".format(measure)

    df_copy = df.copy()

    df = df.pivot(
        index=dd1_id, columns=dd2_id, values="{} RCA".format(measure)
    ).reset_index().set_index(dd1_id).dropna(axis=1, how="all").fillna(0)
    df = df.astype(float)

    output = relatedness(df, proximity(df))
    output = pd.melt(output.reset_index(), id_vars=[dd1_id], value_name=relatedness_measure)

    output = _filter(output, [dd1, dd2])

    if "top_relatedness" in params:
        top = int(params["top_relatedness"])
        output = output.sort_values(by=relatedness_measure, ascending=False).head(top)

    output = output.merge(df_copy, on=[dd1_id, dd2_id], how="inner")

    _output(output)


if __name__ == "__main__":
    name = str(sys.argv[3])
    getattr(sys.modules[__name__], "_%s" % name)()
