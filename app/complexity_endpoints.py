import json
import numpy as np
import os
import pandas as pd
import re
import requests
import sys

from base import BaseClass, API, CUBES_API
from cache import get_hash_id, InternalCache, RedisCache
from complexity.complexity import complexity
from complexity.opportunity_gain import opportunity_gain
from complexity.proximity import proximity
from complexity.rca import rca
from complexity.relatedness import relatedness

def yn(x):
    value = x and x in ["true", "1", True]
    return value or False

auth_level = int(sys.argv[4]) or 0 # Auth level
headers = json.loads(sys.argv[3]) # Headers
params = json.loads(sys.argv[1]) # Query params
cubes_cache = InternalCache(CUBES_API, headers).cubes

is_cache = yn(os.environ["CANON_STATS_CACHE"])


def convert_dict(params):
    return dict([item.split(":") for item in params.split(",")]) if params else {}


def filtered_params(params):
    return {k:params[k] for k in params if re.match("(?!.*(debug|filter_|options|ranking)).*$", k)}


def filter_threshold(x, right=False):
    return right if "Right" in x[0] else not right


def get_dd_id(dd):
    """
    Includes ID in a drilldown name.
    """
    return f"{dd} ID"


def pivot_data(df, index, columns, values):
    """
    Pivots dataframe based on drilldowns.
    """
    return pd.pivot_table(df, index=[index], columns=[columns], values=values).reset_index().set_index(index).dropna(axis=1, how="all").fillna(0).astype(float)


def _load_params():
    """
    Split rca param into drilldowns and measure, and associates each drilldown with its ID.
    @returns: drilldown names (dd1, dd2), drilldown ids (dd1_id, dd2_id), and measure.
    """
    dd1, dd2, measure = params.get("rca").split(",")

    dd1_id = get_dd_id(dd1)
    dd2_id = get_dd_id(dd2)

    return dd1, dd2, dd1_id, dd2_id, measure


def _load_alias_params():
    """
    Updates drilldown names and ids, using alias param.
    @returns: drilldown names (dd1, dd2), drilldown ids (dd1_id, dd2_id), and measure.
    """
    dd1, dd2, dd1_id, dd2_id, measure = _load_params()
    if "alias" in params:
        dd1, dd2 = params.get("alias").split(",")
        dd1_id = get_dd_id(dd1)
        dd2_id = get_dd_id(dd2)

    return dd1, dd2, dd1_id, dd2_id


def _update_params(dd1, dd2, key="alias"):
    if params.get(key):
        dd1, dd2 = params.get(key).split(",")

    dd1_id = get_dd_id(dd1)
    dd2_id = get_dd_id(dd2)

    return dd1, dd2, dd1_id, dd2_id


class Complexity:
    """
    This module allows to calculate Economic Complexity measures.
    """
    def __init__(self, name):
        """
        Custom query parameters own of canon-stats includes @param.
        Custom measures names used on the Class includes @measure.
        """
        dd1, dd2, dd1_id, dd2_id, measure = _load_params()
        dd1_unique = dd1
        dd2_unique = dd2
        dd1, dd2, dd1_id, dd2_id = _load_alias_params()

        # Defines default values for secondary drilldowns
        dd1_right = dd1
        dd1_right_id = dd1_id
        dd2_right = dd2
        dd2_right_id = dd2_id

        # If "rcaRight" param is defined, updates secondary drilldown values.
        if params.get("rcaRight"):
            dd1_right, dd2_right, measure = params.get("rcaRight").split(",")
            dd1_right, dd2_right, dd1_right_id, dd2_right_id = _update_params(dd1_right, dd2_right, "aliasRight")

        # Gets custom params.
        cube_name = params.get("cube")
        eci_threshold = params.get("eciThreshold")
        iterations = params.get("iterations")
        method = params.get("method")
        options = params.get("options")
        threshold = params.get("threshold")

        # Generates an empty dataframe used as default value.
        empty_df = pd.DataFrame([])

        self.base = BaseClass(API, headers, auth_level, cubes_cache)
        self.cache = RedisCache()
        self.cube_name = cube_name
        self.cubes_cache = cubes_cache
        self.dd1 = dd1
        self.dd1_id = dd1_id
        self.dd1_right = dd1_right
        self.dd1_right_id = dd1_right_id
        self.dd1_unique = dd1_unique
        self.dd2 = dd2
        self.dd2_id = dd2_id
        self.dd2_right = dd2_right
        self.dd2_right_id = dd2_right_id
        self.dd2_unique = dd2_unique
        self.df_cube_right = empty_df.copy()
        self.eci_threshold = convert_dict(eci_threshold) # @param
        self.eci_measure = f"{measure} ECI" # @measure
        self.endpoint = str(sys.argv[2])
        self.iterations = int(iterations) if iterations else 20 # @param
        self.labels = empty_df.copy()
        self.measure = measure
        self.method = method # @param
        self.name = name
        self.opp_gain_measure = f"{measure} Opportunity Gain" # @measure
        self.options = convert_dict(options) # @param
        self.parents = yn(params.get("parents"))
        self.pci_measure = f"{measure} PCI" # @measure
        self.proximity_measure = f"{measure} Proximity" # @measure
        self.ranking = yn(params.get("ranking")) # @param
        self.rca_measure = f"{measure} RCA" # @measure
        self.relatedness_measure = f"{measure} Relatedness" # @measure
        self.threshold = convert_dict(threshold) # @param


    def call(self):
        """
        Dynamically, call each endpoint of complexity.
        Internally, each function that is related to an endpoint must to start with "_".
        @returns: Complexity's function is invoked.
        """
        def func_not_found():
            print(f"No Function {self.name} Found!")
        func_name = f"_{self.name}"
        func = getattr(self, func_name, func_not_found) 
        func()


    def threshold_step(self, df, threshold = {}):
        """
        Generates cuts on data before to do calculations
        @returns: DataFrame filtered by thresholds defined.
        """
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
                    pop_df = BaseClass(POP_API, headers, auth_level, cubes_cache).get_data(pop_params)

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
                pop_df = BaseClass(POP_API, headers, auth_level, cubes_cache).get_data(pop_params)

                # Gets list of country_id's that has a value over the threshold
                list_temp_id = pop_df[pop_df[pop_params["measures"]] >= int(params.get("threshold_Population"))][dd1_id].unique()
                df_copy = df_copy[df_copy[dd1_id].isin(list_temp_id)]


            for dd in [dd1, dd2]:
                filter_var = f"threshold_{dd}"
                dd_id = get_dd_id(dd)
                if filter_var in params and dd_id in list(df_copy):
                    df_temp = df[[dd_id, self.measure]].groupby([dd_id]).sum().reset_index()
                    list_temp = df_temp[df_temp[self.measure] >= float(params[filter_var])][dd_id].unique()
                    df_copy = df_copy[df_copy[dd_id].isin(list_temp)]

        return df_copy


    def load_step(self):
        """
        Requests data from tesseract endpoint, and calculates RCA index.
        @returns: RCA matrix.
        """
        # Creates a dict with params
        dd1, dd2, dd1_id, dd2_id, measure = _load_params()
        drilldowns = f"{dd1},{dd2}"
        _params = {k:params[k] for k in params if re.match("(?!.*(debug|filter_|options|ranking|rca|threshold)).*$", k)}
        _params["drilldowns"] = drilldowns
        _params["measures"] = measure

        # Calculates RCA matrix for local units (subnational).
        # We compare the share of an activity in a local unit (e.g. region, province) with the share of that activity in the world. 
        # For further references: https://oec.world/en/resources/methods#uses
        # Methods accepted are "subnational" and "relatedness".
        if self.method in ["subnational", "relatedness"]:
            # Gets params related with "subnational" cube
            params_left = {k:_params[k] for k in _params if re.match("(?!.*(filter_|Right)).*$", k)}

            # Gets params related with "world" cube
            dd1_right, dd2_right, measure_right =  _params.get("rcaRight").split(",")
            params_right = {k.replace("Right", ""):_params[k] for k in _params if re.match("\w+Right", k) and re.match("(?!.*(alias|rca)).*$", k)}
            params_right["drilldowns"] = f"{dd1_right},{dd2_right}"
            params_right["measures"] = measure_right
            right_regex = "\w+Right"

            # Generates an unique dict based on "world" params
            params_right_key = {k:_params[k] for k in _params if re.match(right_regex, k) or re.match(right_regex, _params[k])}

            # Generates unique ids
            params_id = get_hash_id(filtered_params(params_left))
            params_right_id = get_hash_id(filtered_params(params_right_key))

            # Gets subnational/world data stored on Redis
            data = self.cache.get(params_id) if is_cache else None
            df_cube_right = self.cache.get(f"cube_right_{params_right_id}") if is_cache else None

            # Checks if there is world data stored on Redis
            is_cube_right = False
            if is_cache and isinstance(df_cube_right, pd.DataFrame):
                self.df_cube_right = df_cube_right
                is_cube_right = True

            # Checks if there is subnational data stored on Redis
            if is_cache and isinstance(data, pd.DataFrame):
                df_rca_subnat = data
                df_right = self.cache.get(f"subnational_{params_right_id}")
                self.labels = self.cache.get(f"labels_{params_id}")

                dd1_right, dd2_right, dd1_right_id, dd2_right_id = _update_params(dd1_right, dd2_right, "aliasRight")

            else:
                # Calculates numerator of the subnational RCA
                # This numerator is based on subnational data
                df_subnat = self.base.get_data(params_left)
                threshold_items = dict(filter(lambda x: filter_threshold(x), self.threshold.items()))
                df_subnat = self.threshold_step(df_subnat, threshold_items)
                self.labels = df_subnat
                p = pivot_data(df_subnat, dd1_id, dd2_id, measure)

                # Calculates numerator
                col_sums = p.sum(axis=1)
                col_sums = col_sums.values.reshape((len(col_sums), 1))
                subnat_rca_numerator = np.divide(p, col_sums)

                # Verifies if we have stored
                if ~is_cube_right:
                    # Calculates denominator of the subnational RCA
                    # This denominator is based on "World" data
                    df_right = self.base.get_data(params_right)
                    threshold_items = dict(filter(lambda x: filter_threshold(x, True), self.threshold.items()))
                    df_right = self.threshold_step(df_right, threshold_items)

                    # Updates drilldowns ids, in case to define aliasRight on URL
                    dd1_right, dd2_right, dd1_right_id, dd2_right_id = _update_params(dd1_right, dd2_right, "aliasRight")

                    # Pivots data related with cube right, and stores on df_cube_right
                    q = pivot_data(df_right, dd1_right_id, dd2_right_id, measure_right)
                    self.df_cube_right = q
                else:
                    q = df_cube_right

                # Calculates denominator
                row_sums = q.sum(axis=0)
                total_sum = q.sum().sum()
                rca_denominator = np.divide(row_sums, total_sum)

                # Calculates subnational RCA
                rca_subnat = subnat_rca_numerator / rca_denominator

                # Melts dataframe
                df_rca_subnat = rca_subnat.reset_index().set_index(dd1_id).dropna(axis=1, how="all").fillna(0)
                df_rca_subnat = pd.melt(df_rca_subnat.reset_index(), id_vars=[dd1_id], value_name=self.rca_measure)

                # If cache is activated, stores RCA subnational matrix, labels, cube right used
                if is_cache:
                    self.cache.set(f"subnational_{params_right_id}", df_right)
                    self.cache.set(f"labels_{params_id}", df_subnat)
                    self.cache.set(params_id, df_rca_subnat)
                    self.cache.set(f"cube_right_{params_right_id}", q)

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

        # Calculates RCA matrix
        else:
            # Generates an unique ID for the query
            params_id = get_hash_id(filtered_params(_params))
            labels_cache_id = f"labels_{params_id}"
            data = self.cache.get(params_id) if is_cache else None

            # Checks if you are using cache
            if is_cache and isinstance(data, pd.DataFrame):
                output = data
                self.labels = self.cache.get(labels_cache_id)

            # Calcules for the first time the RCA matrix
            else:
                # Gets data from OLAP cube
                df = self.base.get_data(_params)
                # Loads drilldowns
                dd1, dd2, dd1_id, dd2_id = _load_alias_params()
                # Implements thresholds on dataset before to calculate RCA
                df = self.threshold_step(df)
                # Generates a copy of the original dataframe
                df_copy = df.copy()
                self.labels = df_copy
                # Calculates RCA matrix
                df = pivot_data(df, dd1_id, dd2_id, measure)
                output = rca(df)
                # Converts RCA matrix into a list
                output = output.reset_index().melt(id_vars=dd1_id, value_name=self.rca_measure)
                # Stores the dataframe using Redis
                if is_cache:
                    self.cache.set(labels_cache_id, df_copy)
                    self.cache.set(params_id, output)

            return output


    def transform_step(self, df, dds, measure):
        """
        Transforms the dataframe after doing complexity calculations.
        @returns: DataFrame transformed.
        """
        # Includes Ranking.
        if self.ranking:
            df = df.sort_values(measure, ascending=False)
            df[f"{measure} Ranking"] = range(1, df.shape[0] + 1)

        # Filters dataframe by each drilldowns.
        for dd in dds:
            filter_var = f"filter_{dd}"
            filter_id = get_dd_id(dd)
            if filter_var in params and filter_id in list(df):
                column = df[filter_id].astype(str)
                param = params[filter_var].split(",")
                df = df.loc[np.in1d(column, param)]

        # Sorts dataframe. Options are "asc", "ascending", "descending", and "desc".
        sort = self.options.get("sort")
        if sort and sort in ["asc", "ascending", "desc", "descending"]:
            ascending = sort == "asc" or sort == "ascending"
            df = df.sort_values(by=measure, ascending=ascending)

        # Limits the maximum number of results to return.
        limit = self.options.get("limit")
        if limit and limit.isdigit():
            df = df.head(int(limit))

        # Assign labels for each ID on dataframe.
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
            is_eci = self.endpoint == "eci"
            dd = self.dd1 if is_eci else self.dd2
            dd_id = dd1_id if is_eci else dd2_id
            if self.parents:
                parents = self.cubes_cache[self.cube_name]["parents"]
                dd_unique = self.dd1_unique if is_eci else self.dd2_unique
                dd_parents = parents[dd_unique]
                dd_parents += [get_dd_id(i) for i in dd_parents.copy()]
                a = self.labels[dd_parents].drop_duplicates()
            else:
                a = self.labels[[dd, dd_id]].drop_duplicates()

            df = df.merge(a, on=[dd_id])

        return df


    def _complexity(self):
        """
        Calculates ECI / PCI
        """
        df = self.load_step()
        dd1 = self.dd1
        dd1_id = self.dd1_id
        dd2 = self.dd2
        dd2_id = self.dd2_id

        # Get variables from Class
        eci_measure = self.eci_measure
        iterations = self.iterations
        pci_measure = self.pci_measure
        rca_measure = self.rca_measure

        complexity_measure = eci_measure if self.endpoint == "eci" else pci_measure
        complexity_dd_id = dd1_id if self.endpoint == "eci" else dd2_id

        df_copy = df.copy()
        df = pivot_data(df, dd1_id, dd2_id, rca_measure)

        # Filters by ECI threshold
        if self.eci_threshold:
            rcas = df.copy()
            rcas[rcas >= 1] = 1
            rcas[rcas < 1] = 0
            # Removes small data related with drilldown1
            if dd1 in self.eci_threshold:
                value = int(self.eci_threshold[dd1])
                cols = np.sum(rcas, axis=1)
                cols = list(cols[cols > value].index)
                df = df[df.index.isin(cols)]
                df_copy = df_copy[df_copy[dd1_id].isin(cols)]

            # Removes small data related with drilldown2
            if dd2 in self.eci_threshold:
                value = int(self.eci_threshold[dd2])
                rows = np.sum(rcas, axis=0)
                rows = list(rows[rows > value].index)
                df = df[rows]
                df_copy = df_copy[df_copy[dd2_id].isin(cols)]

        # Calculates ECI / PCI for subnational territories
        if self.method == "subnational":
            df_right = self.df_cube_right
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

        iterations = self.iterations
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
        """
        Calculates RCA
        """
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
    # Based on API used, generates the internal function's name.
    name = str(sys.argv[2])
    full_name = "complexity" if name in ["eci", "pci"] else name
    # Executes the function according to its name.
    Complexity(full_name).call()
