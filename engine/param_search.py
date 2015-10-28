import numpy
import pymongo
import yaml
import os
"""
Perform a series of models over the data of intersection 3083, sensor 56 until it actually detects the incidents
"""


def get_engine_dir():
    return os.path.dirname(os.path.realpath(__file__))



try:
    path = os.path.join(os.path.dirname(get_engine_dir()), 'connection.yaml')
    with open(path, 'r') as f:
        conf = yaml.load(f)
        mongo_uri = conf['mongo_uri']
        mongo_database = conf['mongo_database']
        mongo_collection = conf['mongo_collection']
        max_vehicles = conf['max_vehicles']
except:
    raise Exception('No connection.yaml with mongo_uri defined! please make one with a mongo_uri variable')


client = pymongo.MongoClient(mongo_uri, w=0)
readings_collection = client[mongo_database][mongo_collection]

