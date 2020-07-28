from sqlite3 import Error
import functools
import os
import requests 
import sqlite3

def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()

class InternalCache:
    def __init__(self, API, headers):
        r = requests.get(API, headers)
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
                "min_auth_level": cube["min_auth_level"],
                "parents": levels
            }

        self.cubes = item


import collections
import hashlib
import pyarrow as pa
import redis

def get_hash_id(x):
    def hash_id(x): 
        return hashlib.sha224(x.encode("utf-8")).hexdigest()[:10]
    return hash_id(get_str(x)) if isinstance(x, dict) else hash_id(x)

def get_str(x):
    return str(dict(collections.OrderedDict(sorted(x.items()))))

class RedisCache:
    def __init__(self):
        HOST = os.environ["CANON_STATS_CACHE_HOST"]
        PASSWORD = os.environ["CANON_STATS_CACHE_PASSWORD"]
        PORT = os.environ["CANON_STATS_CACHE_PORT"]

        self.context = pa.default_serialization_context()
        self.r = redis.Redis(host=HOST, password=PASSWORD, port=PORT, db=0)

    def set(self, key, df):
        return self.r.set(key, self.context.serialize(df).to_buffer().to_pybytes())

    def get(self, key):
        NoneType = type(None)
        data = self.r.get(key)
        return self.context.deserialize(data) if type(data) is not NoneType else False  