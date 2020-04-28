import json
import numpy as np
import os
import pandas as pd
import requests
import sys

from complexity.complexity import complexity
from complexity.opportunity_gain import opportunity_gain
from complexity.proximity import proximity
from complexity.rca import rca
from complexity.relatedness import relatedness
from base import BaseClass
from cache import InternalCache


API = str(sys.argv[2]) + "/data"
params = json.loads(sys.argv[1])
headers = sys.argv[4]


def pivot_data(df, index, columns, values):
    return pd.pivot_table(df, index=[index], columns=[columns], values=values).reset_index().set_index(index).dropna(axis=1, how="all").fillna(0).astype(float)

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
        ddi1_unique = dd1
        ddi2_unique = dd2
        dd1, dd2, dd1_id, dd2_id = _load_alias_params()
        options = params.get("options")

        CUBES_API = str(sys.argv[2]) + "/cubes"
        cubes_cache = InternalCache(CUBES_API, json.loads(headers)).cubes

        self.base = BaseClass(API, json.loads(headers))
        self.cube_name = params.get("cube")
        self.cubes_cache = cubes_cache
        self.dd1 = dd1
        self.dd1_unique = ddi1_unique
        self.dd2_unique = ddi2_unique
        self.dd1_id = dd1_id
        self.dd2 = dd2
        self.dd2_id = dd2_id
        self.eci_measure = "{} ECI".format(measure)
        self.endpoint = str(sys.argv[3])
        self.iterations = int(params.get("iterations")) if "iterations" in params else 20
        self.labels = pd.DataFrame([])
        self.measure = measure
        self.method = params.get("method")
        self.name = name
        self.opp_gain_measure = "{} Opportunity Gain".format(measure)
        self.options = dict([item.split(":") for item in options.split(",")]) if options else {}
        self.parents = True if params.get("parents") and params.get("parents") == "true" else False
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
        if self.method in ["subnational", "relatedness"]:
            paramsLeft = {}
            for key in _params.keys():
                param_key = _params.get(key)
                if "Right" not in key and "filter_" not in key:
                    paramsLeft[key] = param_key

            df_subnat = self.base.get_data(paramsLeft)

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

            df_rca_subnat = rca_subnat.reset_index().set_index(dd1_id).dropna(axis=1, how="all").fillna(0)
            df_rca_subnat = pd.melt(df_rca_subnat.reset_index(), id_vars=[dd1_id], value_name=self.rca_measure)

            df_rca_subnat = df_rca_subnat.merge(df_subnat, on=[dd1_id, dd2_id])
            if self.method == "subnational":
                return df_rca_subnat
            elif self.method == "relatedness":
                # Copies original dataframe
                df_final = df_right.copy()
                # Calculates RCA index
                df_final = pivot_data(df_final, dd1_right_id, dd2_right_id, measure)
                output = rca(df_final)
                return df_rca_subnat, output
            else:
                return pd.DataFrame([])
        else:
            df = self.base.get_data(_params)

            dd1, dd2, dd1_id, dd2_id = _load_alias_params()

            # Use of the population threshold 
            if "threshold_Population" in params:
                # Get params for population api
                POP_API = os.environ["CANON_STATS_POPULATION_BASE"]
                env_params = os.environ["CANON_STATS_POPULATION_PARAMS"]

                # Creates params dictionary
                pop_params = {}
                for row in env_params.split("|"):
                    [index, value] = row.split(":")
                    pop_params[index] = value

                # Adds timespan to dictionary
                if "YearPopulation" in _params:
                    pop_params["Year"] = _params.get("YearPopulation")
                else:
                    pop_params["time"] = "year.latest"
                
                # Calls population API
                pop_df = BaseClass(POP_API, json.loads(headers)).get_data(pop_params)

                # Gets list of country_id's that has a value over the threshold
                list_temp_id = pop_df[pop_df[pop_params["measures"]] >= int(_params.get("threshold_Population"))][dd1_id].unique()
                df = df[df[dd1_id].isin(list_temp_id)]

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
            self.labels = df_final

            # Calculates RCA index
            df = pivot_data(df, dd1_id, dd2_id, measure)
            output = rca(df).reset_index().melt(id_vars=dd1_id, value_name=self.rca_measure)
            # output = output.merge(df_final, on=[dd1_id, dd2_id], how="outer").fillna(0)

            output = _threshold(output)
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
            filter_id = get_dd_id(dd)
            if filter_var in params and filter_id in list(df):
                df = df[df[filter_id].astype(str) == str(params[filter_var])]

        limit = self.options.get("limit")
        sort = self.options.get("sort")
        if sort and sort in ["asc", "desc"]:
            ascending = sort == "asc"
            df = df.sort_values(by=measure, ascending=ascending)
        if limit and limit.isdigit():
            df = df.head(int(limit))

        dd1_id = self.dd1_id
        dd2_id = self.dd2_id

        if self.parents:
            parents = self.cubes_cache[self.cube_name]["parents"]
            dd1_parents = parents[self.dd1_unique]
            dd2_parents = parents[self.dd2_unique]
            dd1_parents += [get_dd_id(i) for i in dd1_parents.copy()]
            dd2_parents += [get_dd_id(i) for i in dd2_parents.copy()]

            a = self.labels[dd1_parents].drop_duplicates()
            b = self.labels[dd2_parents].drop_duplicates()

        else:
            a = self.labels[[self.dd1, dd1_id]].drop_duplicates()
            b = self.labels[[self.dd2, dd2_id]].drop_duplicates()

        df = df.merge(self.labels[[dd1_id, dd2_id, self.measure]].dropna(), on=[dd1_id, dd2_id], how="left").fillna(0)
        df = df.merge(a, on=[dd1_id])
        df = df.merge(b, on=[dd2_id])
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
        if self.method == "relatedness":
            df, df_country = self.load_step()
        else: 
            df = self.load_step()

        dd1 = self.dd1
        dd1_id = self.dd1_id
        dd2 = self.dd2
        dd2_id = self.dd2_id
        rca_measure = self.rca_measure
        relatedness_measure = self.relatedness_measure

        df_copy = df.copy()
        df_copy = pivot_data(df_copy, dd1_id, dd2_id, rca_measure)

        if self.method == "relatedness":
            phi = proximity(df_country)
            output = relatedness(df_copy.reindex(columns=list(phi)).fillna(0), phi)
        else: 
            output = relatedness(df_copy, proximity(df_copy))
        
        output = pd.melt(output.reset_index(), id_vars=[dd1_id], value_name=relatedness_measure)

        output = self.transform_step(output, [dd1, dd2], relatedness_measure)
        output = output.merge(df, on=[dd1_id, dd2_id], how="inner")

        self.base.to_output(output)


if __name__ == "__main__":
    name = str(sys.argv[3])
    full_name = "complexity" if name in ["eci", "pci"] else name
    Complexity(full_name).get()
