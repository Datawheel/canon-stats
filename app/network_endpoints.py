import sys
import networkx as nx
import numpy as np
import pandas as pd
import requests
import json
from base import BaseClass
from cache import InternalCache
from complexity.proximity import proximity


API = str(sys.argv[2]) + "/data"
params = json.loads(sys.argv[1])
headers = sys.argv[4]
auth_level = int(sys.argv[5]) or 0
CUBES_API = str(sys.argv[2]) + "/cubes"
cubes_cache = InternalCache(CUBES_API, json.loads(headers)).cubes


class Network:
    def __init__(self):
        self.base = BaseClass(API, json.loads(headers), auth_level, cubes_cache)

    def draw_network(self):
        dd1, dd2, measure = params["rca"].split(",")
        if "alias" in params:
            dd1, dd2 = params["alias"].split(",")

        dd1_id = "{} ID".format(dd1)
        dd2_id = "{} ID".format(dd2)
        df = self.base.get_data(params)

        df = df.pivot(
            index=dd1_id, columns=dd2_id, values="{} RCA".format(measure)
        ).reset_index().set_index(dd1_id).dropna(axis=1, how="all").fillna(0)
        df = df.astype(float)

        # Calculates proximity
        phi = proximity(df)
        keep = np.triu(np.ones(phi.shape)).astype(bool).reshape(phi.size)

        df_stacked = pd.DataFrame(phi.stack(dropna=False)[keep])
        df_stacked.index.names = ["{} Source".format(dd2_id), "{} Target".format(dd2_id)]
        df_stacked = df_stacked.reset_index().rename(columns={0: "value"})
        df_stacked = df_stacked.fillna(0)

        df_stacked["{} Source".format(dd2_id)] = df_stacked["{} Source".format(dd2_id)].astype(str)
        df_stacked["{} Target".format(dd2_id)] = df_stacked["{} Target".format(dd2_id)].astype(str)

        graph = nx.Graph()

        def nodes_add(col, prefix):
            for cell in col:
                graph.add_node("{}".format(prefix, str(col)))
                

        def edges_add(df):
            for s in df.itertuples():
                graph.add_edge(
                    "{}".format(s._1), 
                    "{}".format(s._2), 
                    weight=s.value
            )

        nodes_add(df_stacked["{} Source".format(dd2_id)].unique(), "")

        edges_add(df_stacked)

        graph = nx.maximum_spanning_tree(graph)
        # y = np.percentile(df_stacked.value, 95)
        y = 0.65

        edges_add(df_stacked[df_stacked.value >= y])

        layout = getattr(nx, "spring_layout")
        pos = layout(graph)

        network = {
            "edges": [{"source": edge[0], "target": edge[1]} for edge in list(graph.edges)],
            "nodes": [{"id": node, "x": float(pos[node][0]), "y": float(pos[node][1])} for node in df_stacked["{} Source".format(dd2_id)].unique()]
        }

        print(json.dumps({
        "data": network
        }))

if __name__ == "__main__":
    Network().draw_network()