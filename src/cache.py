import functools
import os
import requests 
import requests_cache

class InternalCache:
    def __init__(self, API, headers):
        r = requests.get(API, headers=headers)
        cubes = r.json()["cubes"]
        item = {}

        for cube in cubes:
            levels = {}
            for dimension in cube["dimensions"]:
                for hierarchy in dimension["hierarchies"]:
                    level_names = []
                    for level in hierarchy["levels"]:
                        level_name = level["unique_name"] or level["name"]
                        level_names.append(level["name"])
                        levels[level_name] = level_names.copy()

            item[cube["name"]] = {
                "parents": levels
            }

        self.cubes = item