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
auth_level = int(sys.argv[5]) or 0
server_headers = sys.argv[6]
CUBES_API = str(sys.argv[2]) + "/cubes"
cubes_cache = InternalCache(CUBES_API, json.loads(headers)).cubes


def filter_threshold(x, right=False):
    if "Right" in x[0]:
        return right
    else:
        return not right

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


class Complexity:
    def __init__(self, name):
        dd1, dd2, dd1_id, dd2_id, measure = _load_params()
        ddi1_unique = dd1
        ddi2_unique = dd2
        dd1, dd2, dd1_id, dd2_id = _load_alias_params()

        # Keeps drilldowns used in cubes using method="subnational|relatedness"
        if params.get("rcaRight"):
            dd1_right, dd2_right, measure = params.get("rcaRight").split(",")
            if params.get("aliasRight"):
                dd1_right, dd2_right = params.get("aliasRight").split(",")
            dd1_right_id = get_dd_id(dd1_right)
            dd2_right_id = get_dd_id(dd2_right)
        else:
            dd1_right = dd1
            dd1_right_id = dd1_id
            dd2_right = dd2
            dd2_right_id = dd2_id

        options = params.get("options")
        threshold = params.get("threshold")
        eciThreshold = params.get("eciThreshold")

        self.base = BaseClass(API, json.loads(headers), auth_level, cubes_cache)
        self.cube_name = params.get("cube")
        self.cubes_cache = cubes_cache
        self.dd1 = dd1
        self.dd1_unique = ddi1_unique
        self.dd2_unique = ddi2_unique
        self.dd1_right = dd1_right
        self.dd2_right = dd2_right
        self.dd1_right_id = dd1_right_id
        self.dd2_right_id = dd2_right_id
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
        self.threshold = dict([item.split(":") for item in threshold.split(",")]) if threshold else {}
        self.eciThreshold = dict([item.split(":") for item in eciThreshold.split(",")]) if eciThreshold else {}


    def threshold_step(self, df, threshold = {}):
        dd1, dd2, dd1_id, dd2_id = _load_alias_params()
        df_copy = df.copy()
        threshold_items = threshold or self.threshold

        if threshold_items:
            for item in list(threshold_items.items()):
                is_right = "Right" in item[0]
                key = item[0].replace("Right", "")
                value = float(item[1])

                dd_id = get_dd_id(key)
                if key == "Population" and os.environ["CANON_STATS_POPULATION_BASE"]: 
                    # Get params for population api
                    POP_API = os.environ["CANON_STATS_POPULATION_BASE"]
                    env_params = os.environ["CANON_STATS_POPULATION_PARAMS"]

                    # Creates params dictionary
                    pop_params = {}
                    for row in env_params.split("|"):
                        [index, v] = row.split(":")
                        pop_params[index] = v

                    # Adds timespan to dictionary
                    if "YearPopulation" in params:
                        pop_params["Year"] = params.get("YearPopulation")
                    else:
                        pop_params["time"] = "year.latest"

                    # Calls population API
                    pop_df = BaseClass(POP_API, json.loads(headers), auth_level, cubes_cache).get_data(pop_params)

                    # Gets list of country_id's that has a value over the threshold
                    dd_geo_id = self.dd1_right_id if is_right else dd1_id
                    list_temp_id = pop_df[pop_df[pop_params["measures"]] >= int(value)][dd_geo_id].unique()
                    df_copy = df_copy[df_copy[dd_geo_id].isin(list_temp_id)]

                elif dd_id in list(df):
                    df_temp = df[[dd_id, self.measure]].groupby([dd_id]).sum().reset_index()
                    threshold_value = value
                    if (threshold_value < 1):
                        df_sum = df[self.measure].sum()
                        threshold_value *= df_sum
                    list_temp = df_temp[df_temp[self.measure] >= threshold_value][dd_id].unique()
                    df_copy = df_copy[df_copy[dd_id].isin(list_temp)]

        else:
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
                if "YearPopulation" in params:
                    pop_params["Year"] = params.get("YearPopulation")
                else:
                    pop_params["time"] = "year.latest"

                # Calls population API
                pop_df = BaseClass(POP_API, json.loads(headers), auth_level, cubes_cache).get_data(pop_params)

                # Gets list of country_id's that has a value over the threshold
                list_temp_id = pop_df[pop_df[pop_params["measures"]] >= int(params.get("threshold_Population"))][dd1_id].unique()
                df_copy = df_copy[df_copy[dd1_id].isin(list_temp_id)]


            for dd in [dd1, dd2]:
                filter_var = "threshold_{}".format(dd)
                dd_id = get_dd_id(dd)
                if filter_var in params and dd_id in list(df_copy):
                    df_temp = df[[dd_id, self.measure]].groupby([dd_id]).sum().reset_index()
                    list_temp = df_temp[df_temp[self.measure] >= float(params[filter_var])][dd_id].unique()
                    df_copy = df_copy[df_copy[dd_id].isin(list_temp)]

        return df_copy


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

            threshold_items = dict(filter(lambda x: filter_threshold(x), self.threshold.items()))
            df_subnat = self.threshold_step(df_subnat, threshold_items)

            p = pivot_data(df_subnat, dd1_id, dd2_id, measure)

            col_sums = p.sum(axis=1)
            col_sums = col_sums.values.reshape((len(col_sums), 1))
            subnat_rca_numerator = np.divide(p, col_sums)

            dd1_right, dd2_right, measure_right =  _params.get("rcaRight").split(",")

            # Calculates denominator
            params_right = {
                "cube": _params.get("cubeRight"),
                "drilldowns": "{},{}".format(dd1_right, dd2_right),
                "measures": measure_right,
                "Year": _params.get("YearRight")
            }

            df_right = self.base.get_data(params_right)
            threshold_items = dict(filter(lambda x: filter_threshold(x, True), self.threshold.items()))
            df_right = self.threshold_step(df_right, threshold_items)

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
            if "variable" in list(df_rca_subnat):
                df_rca_subnat = df_rca_subnat.rename(columns={"variable": dd2_id})

            self.labels = df_subnat

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
            df = self.threshold_step(df)

            # Copies original dataframe
            df_final = df.copy()
            self.labels = df_final

            # Calculates RCA index
            df = pivot_data(df, dd1_id, dd2_id, measure)
            output = rca(df)
            output = output.reset_index().melt(id_vars=dd1_id, value_name=self.rca_measure)

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

        if self.endpoint not in ["eci", "pci"]:
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
        else:
            dd = self.dd1 if self.endpoint == "eci" else self.dd2
            dd_id = dd1_id if self.endpoint == "eci" else dd2_id
            if self.parents:
                parents = self.cubes_cache[self.cube_name]["parents"]
                dd_unique = self.dd1_unique if self.endpoint == "eci" else self.dd2_unique
                dd_parents = parents[dd_unique]
                dd_parents += [get_dd_id(i) for i in dd_parents.copy()]
                a = self.labels[dd_parents].drop_duplicates()
            else:
                a = self.labels[[dd, dd_id]].drop_duplicates()

            df = df.merge(a, on=[dd_id])

        return df


    def transform_proximity_step(self, df):
        dd1 = self.dd2
        dd1_id = self.dd1_id
        dd2 = self.dd2
        dd2_id = self.dd2_id
        proximity_measure = self.proximity_measure

        filter_var = "filter_{}".format(dd2)

        if filter_var in params and "{} ID Source".format(dd2) in list(df):
            df = df.loc[np.in1d(df["{} ID Source".format(dd2)].astype(str), [str(params[filter_var])])]

        filter_val = "proximity_min"

        if filter_val in params:
            df = df[df[proximity_measure] >= float(params[filter_val])]

        if self.parents:
            parents = self.cubes_cache[self.cube_name]["parents"]
            dd2_parents = parents[self.dd2_unique]
            dd2_parents += [get_dd_id(i) for i in dd2_parents.copy()]

            temp = self.labels[dd2_parents].drop_duplicates().dropna()
            a = temp.copy().rename(columns={dd2_id: "{} Source".format(dd2_id)})
            b = temp.copy().rename(columns={dd2_id: "{} Target".format(dd2_id)})

            source_columns = {parent: "{} Source".format(parent) for parent in dd2_parents}
            target_columns = {parent: "{} Target".format(parent) for parent in dd2_parents}
                                       
            df = df.merge(a, on=["{} Source".format(dd2_id)], how="left").fillna(0).rename(columns=source_columns)
            df = df.merge(b, on=["{} Target".format(dd2_id)], how="left").fillna(0).rename(columns=target_columns)

        else:
            temp = self.labels[[self.dd2, dd2_id]].drop_duplicates().dropna()
            a = temp.copy().rename(columns={dd2_id: "{} Source".format(dd2_id)})
            b = temp.copy().rename(columns={dd2_id: "{} Target".format(dd2_id)})

            df = df.merge(a, on=["{} Source".format(dd2_id)], how="left").fillna(0).rename(columns={dd2: "{} Source".format(dd2)})
            df = df.merge(b, on=["{} Target".format(dd2_id)], how="left").fillna(0).rename(columns={dd2: "{} Target".format(dd2)})

        return df


    def _complexity(self):
        df = self.load_step()
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

        df_copy = df.copy()
        df = pivot_data(df, dd1_id, dd2_id, rca_measure)

        # Filters by ECI threshold
        if self.eciThreshold:
            rcas = df.copy()
            rcas[rcas >= 1] = 1
            rcas[rcas < 1] = 0
            if dd1 in self.eciThreshold:
                value = int(self.eciThreshold[dd1])
                cols = np.sum(rcas, axis=1)
                cols = list(cols[cols > value].index)
                df = df[df.index.isin(cols)]
                df_copy = df_copy[df_copy[dd1_id].isin(cols)]
            if dd2 in self.eciThreshold:
                value = int(self.eciThreshold[dd2])
                rows = np.sum(rcas, axis=0)
                rows = list(rows[rows > value].index)
                df = df[rows]
                df_copy = df_copy[df_copy[dd2_id].isin(cols)]

        iterations = self.iterations

        # Calculates ECI / PCI for subnational territories
        if self.method == "subnational":
            # If method="subnational", you need to defined a comparison cube
            dd1_right, dd2_right, measure_right =  params.get("rcaRight").split(",")

            # Calculates RCA matrix using a comparison cube
            params_right = {
                "cube": params.get("cubeRight"),
                "drilldowns": "{},{}".format(dd1_right, dd2_right),
                "measures": measure_right,
                "Year": params.get("YearRight")
            }
            df_right = self.base.get_data(params_right)
            threshold_items = dict(filter(lambda x: filter_threshold(x, True), self.threshold.items()))
            df_right = self.threshold_step(df_right, threshold_items)

            # Gets dd1/dd2 ids for comparison cube
            if params.get("aliasRight"):
                dd1_right, dd2_right = params.get("aliasRight").split(",")
            dd1_right_id = get_dd_id(dd1_right)
            dd2_right_id = get_dd_id(dd2_right)

            # Pivots dataframe
            df_right = pivot_data(df_right, dd1_right_id, dd2_right_id, measure_right)

            # Calculates ECI / PCI for comparison cube
            eci, pci = complexity(rca(df_right), iterations)
            df_pci = pd.DataFrame(pci).rename(columns={0: complexity_measure}).reset_index()
            df_pci = df_pci.merge(df_copy, on=dd2_id)
            dds = [complexity_dd_id]
            results = df_pci[df_pci[rca_measure] >= 1].groupby(dds).mean().reset_index()
            results = results[dds + [complexity_measure]]

        else:
            eci, pci = complexity(df, iterations)
            complexity_data = eci if self.endpoint == "eci" else pci
            results = pd.DataFrame(complexity_data).rename(columns={0: complexity_measure}).reset_index()
            # results = df_labels.merge(results, on=complexity_dd_id)

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

        output = self.transform_step(output, [dd1, dd2], self.opp_gain_measure)

        self.base.to_output(output)


    def _proximity(self):
        df = self.load_step()
        dd1 = self.dd1
        dd1_id = self.dd1_id
        dd2 = self.dd2
        dd2_id = self.dd2_id
        rca_measure = self.rca_measure

        if "filter_{}".format(dd1) in params:
            temp = df.loc[np.in1d(df[dd1_id].astype(str), [str(params["filter_{}".format(dd1)])])].copy()

        df_labels = df[[dd2_id]].drop_duplicates()

        rcas = pivot_data(df, dd1_id, dd2_id, rca_measure)

        df = proximity(rcas)

        df = df.reset_index()
        df = df.rename(columns={dd2_id: "{} Target".format(dd2_id)})
        df = pd.melt(df, id_vars="{} Target".format(dd2_id), value_name=self.proximity_measure)
        df = df.rename(columns={dd2_id: "{} Source".format(dd2_id)}).copy()
        
        if "filter_{}".format(dd1) not in params:
            df = df[df["{} Source".format(dd2_id)] != df["{} Target".format(dd2_id)]]

        for item in ["Source", "Target"]:
            df = df.merge(df_labels, left_on="{} {}".format(dd2_id, item), right_on=dd2_id)
            df = df.rename(columns={dd2: "{} {}".format(dd2, item)})
            df = df.drop(columns=[dd2_id])

        output = self.transform_proximity_step(df)

        if "filter_{}".format(dd1) in params:
            output = output.merge(temp, left_on="{} Target".format(dd2_id), right_on=dd2_id)

        self.base.to_output(output)


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
