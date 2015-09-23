import os
import sys
import argparse
import pymongo
import pluck
from connection import mongo_uri
import csv
from index import SWARM_CONFIGS_DIR, MAX_COUNT
import pprint
__author__ = 'Jonathan Mackenzie'

SWARM_DATA_CACHE = 'swarm_data_cache'
DESCRIPTION = "Create a swarm config for a given intersection if it doesn't already exist"

parser = argparse.ArgumentParser(description=DESCRIPTION)
parser.add_argument('intersection', type=str, help="Name of the intersection")
parser.add_argument('max', type=int, help="Max number of cars to use in the input fields", default=MAX_COUNT)
parser.add_argument('overwrite', type=bool, help="Overwrite any old config with this name", default=False)

def getSwarmCache(intersection):
    """
    :param intersection:
    :return: the csv file where cache data is stored for
    this intersection to be used in swarming
    """
    cache_file = os.path.join(os.getcwd(), SWARM_DATA_CACHE, intersection+'.csv')
    if os.path.exists(cache_file):
        print "Using existing data cache file:", cache_file
    else:
        print "No cache file exists for", intersection, ".... creating new one in", cache_file
        with open(cache_file, 'wb') as csv_out, pymongo.MongoClient(mongo_uri) as client:
            db = client.mack0242
            collection = db['ACC_201306_20130819113933']
            readings = collection.find({'site_no': intersection}) # probably do some filtering here
            fieldnames = ['datetime'] + getSensors(intersection)
            writer = csv.DictWriter(csv_out, fieldnames=fieldnames)
            writer.writeheader()
            if readings.count() == 0:
                raise Exception("No such intersection with site_no '%s' exists" % intersection)
            else:
                for i in readings:
                    row = {'datetime': i['datetime']}
                    for j in i['readings']:
                        if j['vehicle_count'] < 2040:
                            row[j['sensor']] = j['vehicle_count']
                    writer.writerow(row)
    return "file://"+cache_file

def getSensors(intersection):
    with pymongo.MongoClient(mongo_uri) as client:
        db = client.mack0242
        collection = db['ACC_201306_20130819113933']
        reading = collection.find_one({'site_no': intersection})
        if reading is None:
            raise Exception("No such intersection with site_no '%s' exists" % intersection)
        return pluck.pluck(reading['readings'], 'sensor')
if __name__ == "__main__":
    args = parser.parse_args()
    out_name = os.join(os.getcwd(), SWARM_CONFIGS_DIR, args.intersection + '_swarm_config')
    if os.path.exists(out_name) and args.overwrite:
        sys.exit("Swarm configuration already exists! Use `overwrite` flag to remake")
    else:
        with open(out_name, 'wb') as out_file:
            includedFields = [ {
                        "fieldName": "timestamp",
                        "fieldType": "datetime"
                    }]
            includedFields.extend([{
                               'fieldName': i,
                               'fieldType': "int",
                               "maxValue": args.max,
                               "minValue": 0}
                                   for i in getSensors(args.intersection)])
            swarmConfig = {

                "includedFields": includedFields,
                "streamDef": {
                    "info": "Traffic Volumes on a per sensor basis",
                    "version": 1,
                    "streams": [
                        {
                            "info": "Traffic Volumes for "+args.intersection,
                            "source": getSwarmCache(args.intersection),
                            "columns": [
                                "*"
                            ]
                        }
                    ]
                },
                "inferenceType": "TemporalAnomaly",
                "iterationCount": -1,
                "swarmSize": "medium"
            }
            out_file.write("SWARM DESCRIPTION = \n{}".format(
                pprint.pformat(swarmConfig, indent=2)))
