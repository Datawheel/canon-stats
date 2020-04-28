import functools
import requests 


def hash_dict(func):
    """Transform mutable dictionnary
    Into immutable
    Useful to be compatible with cache
    """
    class HDict(dict):
        def __hash__(self):
            return hash(frozenset(self.items()))

    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        args = tuple([HDict(arg) if isinstance(arg, dict) else arg for arg in args])
        kwargs = {k: HDict(v) if isinstance(v, dict) else v for k, v in kwargs.items()}
        return func(*args, **kwargs)
    return wrapped


class InternalCache:
    @hash_dict
    @functools.lru_cache(maxsize=None)
    def __init__(self, API, headers):
        r = requests.get(API, headers=headers)
        if (r.status_code != 200):
            raise Exception(r.text)
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