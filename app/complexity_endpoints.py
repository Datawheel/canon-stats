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
from base import BaseClass

API = str(sys.argv[2])
params = json.loads(sys.argv[1])
headers = sys.argv[4]


def pivot_data(df, index, columns, values):
    return pd.pivot_table(df, index=[index], columns=[columns], values=[values]).reset_index().set_index(index).dropna(axis=1, how="all").fillna(0).astype(float)

def get_dd_id(dd):
    return "{} ID".format(dd)

def _load_params():
    """
    Returns params for using
    """
    dd1, dd2, measure = params["rca"].split(",")

    dd1_id = get_dd_id(dd1)
    dd2_id = get_dd_id(dd2)

    return dd1, dd2, dd1_id, dd2_id, measure


def _load_alias_params():
    dd1, dd2, dd1_id, dd2_id, measure = _load_params()
    if "alias" in params:
        dd1, dd2 = params["alias"].split(",")
        dd1_id = get_dd_id(dd1)
        dd2_id = get_dd_id(dd2)

    return dd1, dd2, dd1_id, dd2_id


def _threshold(df): 
    dd1, dd2, measure = params["rca"].split(",")
    if "threshold" in params:
        df["pivot"] = df[df[measure] > int(params["threshold"])]
        df = df[df["pivot"] == True].copy()
        df = df.drop(columns=["pivot"])

    return df


class Complexity:
    def __init__(self, name):
        dd1, dd2, dd1_id, dd2_id, measure = _load_params()
        dd1, dd2, dd1_id, dd2_id = _load_alias_params()
        options = params.get("options")

        self.base = BaseClass(API, json.loads(headers))
        self.dd1 = dd1
        self.dd1_id = dd1_id
        self.dd2 = dd2
        self.dd2_id = dd2_id
        self.eci_measure = "{} ECI".format(measure)
        self.endpoint = str(sys.argv[3])
        self.iterations = int(params.get("iterations")) if "iterations" in params else 20
        self.measure = measure
        self.method = params.get("method")
        self.name = name
        self.opp_gain_measure = "{} Opportunity Gain".format(measure)
        self.options = dict([item.split(":") for item in options.split(",")]) if options else {}
        self.pci_measure = "{} PCI".format(measure)
        self.proximity_measure = "{} Proximity".format(measure)
        self.ranking = True if params.get("ranking") and params.get("ranking") == "true" else False
        self.rca_measure = "{} RCA".format(measure)
        self.relatedness_measure = "{} Relatedness".format(measure)


    def load_step(self):
        """
        Requests data from tesseract endpoint, and calculates RCA index
        """
        dd1, dd2, dd1_id, dd2_id, measure = _load_params()
        drilldowns = "{},{}".format(dd1, dd2)
        _params = params.copy()
        _params["drilldowns"] = drilldowns
        _params["measures"] = measure

        # Removes rca as param
        _params.pop("rca", None)

        # Gets data and converts request into dataframe
        method = _params.get("method")
        if method == "subnational":
            paramsLeft = {
                "cube": _params.get("cube"),
                "drilldowns": drilldowns,
                "measures": measure,
                "parents": "true",
                "Year": _params.get("Year")
            }
            df_subnat = self.base.get_data(paramsLeft)

            # return self.base.to_output(pd.DataFrame(df_subnat[dd1_id]).value_counts())
            p = pivot_data(df_subnat, dd1_id, dd2_id, measure)

            col_sums = p.sum(axis=1)
            col_sums = col_sums.values.reshape((len(col_sums), 1))
            subnat_rca_numerator = np.divide(p, col_sums)

            dd1_right, dd2_right, measure_right =  _params.get("rcaRight").split(",")

            # Calculates denominator
            paramsRight = {
                "cube": _params.get("cubeRight"),
                "drilldowns": "{},{}".format(dd1_right, dd2_right),
                "measures": measure_right,
                "Year": _params.get("YearRight")
            }

            df_right = self.base.get_data(paramsRight)

            if params.get("aliasRight"):
                dd1_right, dd2_right = params.get("aliasRight").split(",")

            dd1_right_id = get_dd_id(dd1_right)
            dd2_right_id = get_dd_id(dd2_right)

            q = pivot_data(df_right, dd1_right_id, dd2_right_id, measure_right)

            row_sums = q.sum(axis=0)
            total_sum = q.sum().sum()
            rca_denominator = np.divide(row_sums, total_sum)

            rca_subnat = subnat_rca_numerator / rca_denominator

            df_rca = rca_subnat.reset_index().set_index(dd1_id).dropna(axis=1, how="all").fillna(0)
            df_rca = pd.melt(df_rca.reset_index(), id_vars=[dd1_id], value_name=self.rca_measure)

            df_rca = df_rca.merge(df_subnat, on=[dd1_id, dd2_id])
            return df_rca
        else:
            df = self.base.get_data(_params)

            dd1, dd2, dd1_id, dd2_id = _load_alias_params()

            # Gets labels for drilldowns
            df_labels_1 = df[[dd1, dd1_id]].drop_duplicates()
            df_labels_2 = df[[dd2, dd2_id]].drop_duplicates()

            # Using threshold_* param, filter rows into the dataframe
            for dd in [dd1, dd2]:
                filter_var = "threshold_{}".format(dd)
                dd_id = get_dd_id(dd)
                if filter_var in _params and dd_id in list(df):
                    df_temp = df[[dd_id, measure]].groupby([dd_id]).sum().reset_index()
                    list_temp = df_temp[df_temp[measure] >= float(params[filter_var])][dd_id].unique()
                    df = df[df[dd_id].isin(list_temp)]

            # Copies original dataframe
            df_final = df.copy()

            # Calculates RCA index
            df = df.pivot(index=dd1_id, columns=dd2_id, values=measure)
            output = rca(df).reset_index().melt(id_vars=dd1_id, value_name=self.rca_measure)
            output = df_labels_1.merge(output, on=dd1_id)
            output = df_labels_2.merge(output, on=dd2_id)
            output = _threshold(output)

            # Includes parent and measure data
            output = output.merge(df_final, on=[dd1_id, dd2_id], how="inner")
            output = output.drop(columns=["{}_x".format(dd1), "{}_y".format(dd2)])
            output = output.rename(columns={"{}_x".format(dd2): dd2, "{}_y".format(dd1): dd1})

            return output

    def get(self):
        def func_not_found():
            print('No Function ' + self.name + ' Found!')
        func_name = "_{}".format(self.name)
        func = getattr(self, func_name, func_not_found) 
        func()


    def transform_step(self, df, dds, measure):
        if self.ranking:
            df = df.sort_values(measure, ascending=False)
            df["{} Ranking".format(measure)] = range(1, df.shape[0] + 1)

        for dd in dds:
            filter_var = "filter_{}".format(dd)
            filter_id = "{} ID".format(dd)
            if filter_var in params and filter_id in list(df):
                df = df[df[filter_id].astype(str) == str(params[filter_var])]

        limit = self.options.get("limit")
        sort = self.options.get("sort")
        if sort and sort in ["asc", "desc"]:
            ascending = sort == "asc"
            df = df.sort_values(by=measure, ascending=ascending)
        if limit and limit.isdigit():
            df = df.head(int(limit))

        return df


    def _complexity(self):
        df = self.load_step()
        df_copy = df.copy()
        dd1 = self.dd1
        dd1_id = self.dd1_id
        dd2 = self.dd2
        dd2_id = self.dd2_id

        rca_measure = self.rca_measure
        eci_measure = self.eci_measure
        pci_measure = self.pci_measure

        complexity_measure = eci_measure if self.endpoint == "eci" else pci_measure
        complexity_dd_id = dd1_id if self.endpoint == "eci" else dd2_id
        complexity_dd = dd1 if self.endpoint == "eci" else dd2

        df_labels = df[[complexity_dd, complexity_dd_id]].drop_duplicates()

        df = pivot_data(df, dd1_id, dd2_id, rca_measure)

        iterations = self.iterations

        if self.method == "subnational":
            dd1_right, dd2_right, measure_right =  params.get("rcaRight").split(",")

            # Calculates denominator
            paramsRight = {
                "cube": params.get("cubeRight"),
                "drilldowns": "{},{}".format(dd1_right, dd2_right),
                "measures": measure_right,
                "Year": params.get("YearRight")
            }

            df_right = self.base.get_data(paramsRight)

            if params.get("aliasRight"):
                dd1_right, dd2_right = params.get("aliasRight").split(",")

            dd1_right_id = get_dd_id(dd1_right)
            dd2_right_id = get_dd_id(dd2_right)

            df_right = pivot_data(df_right, dd1_right_id, dd2_right_id, measure_right)

            eci, pci = complexity(rca(df_right), iterations)
            df_pci = pd.DataFrame(pci).rename(columns={0: complexity_measure}).reset_index()
            df_pci = df_pci.merge(df_copy, on=dd2_id)
            dds = [complexity_dd_id, complexity_dd]
            results = df_pci[df_pci[rca_measure] >= 1].groupby(dds).mean().reset_index()
            results = results[dds + [complexity_measure]]

        else:
            eci, pci = complexity(df, iterations)
            complexity_data = eci if self.endpoint == "eci" else pci
            results = pd.DataFrame(complexity_data).rename(columns={0: complexity_measure}).reset_index()
            results = df_labels.merge(results, on=complexity_dd_id)

        results = self.transform_step(results, [dd1, dd2], complexity_measure)

        self.base.to_output(results)


    def _opportunity_gain(self):
        df = self.load_step()
        dd1 = self.dd1
        dd1_id = self.dd1_id
        dd2 = self.dd2
        dd2_id = self.dd2_id
        rca_measure = self.rca_measure

        df_copy = df.copy()
        df_copy = pivot_data(df_copy, dd1_id, dd2_id, rca_measure)

        iterations = int(params["iterations"]) if "iterations" in params else 21
        eci, pci = complexity(df_copy, iterations)

        output = opportunity_gain(df_copy, proximity(df_copy), pci)
        output = pd.melt(
            output.reset_index(), 
            id_vars=[dd1_id], 
            value_name=self.opp_gain_measure
        )

        output = output.merge(df_copy, on=[dd1_id, dd2_id], how="inner")
        output = self.transform_step(output, [dd1, dd2], self.opp_gain_measure)

        self.base.to_output(output)


    def _proximity(self):
        df = self.load_step()
        dd1_id = self.dd1_id
        dd2 = self.dd2
        dd2_id = self.dd2_id
        rca_measure = self.rca_measure

        df_labels = df[[dd2, dd2_id]].drop_duplicates()
        
        rcas = pivot_data(df, dd1_id, dd2_id, rca_measure)
        df = proximity(rcas)

        df = df.reset_index()
        df = df.rename(columns={dd2_id: "{} Target".format(dd2_id)})
        df = pd.melt(df, id_vars="{} Target".format(dd2_id), value_name=self.proximity_measure)
        df = df.rename(columns={dd2_id: "{} Source".format(dd2_id)})
        df = df[df["{} Source".format(dd2_id)] != df["{} Target".format(dd2_id)]]

        for item in ["Source", "Target"]:
            df = df.merge(df_labels, left_on="{} {}".format(dd2_id, item), right_on=dd2_id)
            df = df.rename(columns={dd2: "{} {}".format(dd2, item)})
            df = df.drop(columns=[dd2_id])

        filter_var = "filter_{}".format(dd2)
        if filter_var in params and "{} ID Source".format(dd2) in list(df):
            df = df[df["{} ID Source".format(dd2)].astype(str) == str(params[filter_var])]

        self.base.to_output(df)


    def _rca(self):
        df = self.load_step()
        df = self.transform_step(df, [self.dd1, self.dd2], self.rca_measure)
        self.base.to_output(df)


    def _relatedness(self):
        df = self.load_step()
        dd1 = self.dd1
        dd1_id = self.dd1_id
        dd2 = self.dd2
        dd2_id = self.dd2_id
        rca_measure = self.rca_measure
        relatedness_measure = self.relatedness_measure

        df_copy = df.copy()
        df_copy = pivot_data(df_copy, dd1_id, dd2_id, rca_measure)

        output = relatedness(df_copy, proximity(df_copy))
        output = pd.melt(output.reset_index(), id_vars=[dd1_id], value_name=relatedness_measure)

        output = self.transform_step(output, [dd1, dd2], relatedness_measure)

        output = output.merge(df, on=[dd1_id, dd2_id], how="inner")

        self.base.to_output(output)


if __name__ == "__main__":
    name = str(sys.argv[3])
    full_name = "complexity" if name in ["eci", "pci"] else name
    Complexity(full_name).get()
