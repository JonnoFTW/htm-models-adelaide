import os
import sys
import argparse
import pymongo
import pluck
import csv
import yaml
from index import SWARM_CONFIGS_DIR, MAX_COUNT, getEngineDir
import pprint
import operator
from collections import Counter
__author__ = 'Jonathan Mackenzie'

try:
    path = os.path.join(os.path.dirname(getEngineDir()), 'connection.yaml')
    with open(path, 'r') as f:
        mongo_uri = yaml.load(f)['mongo_uri']
except:
    raise Exception('No connection.yaml with mongo_uri defined! please make one with a mongo_uri variable')



SWARM_DATA_CACHE = 'swarm_data_cache'
DESCRIPTION = "Create a swarm config for a given intersection if it doesn't already exist"

parser = argparse.ArgumentParser(description=DESCRIPTION)
parser.add_argument('--max', dest='max', type=int, help="Max number of cars to use in the input fields",
                    default=MAX_COUNT)
parser.add_argument('--overwrite', help="Overwrite any old config with this name", action='store_true')
parser.add_argument('intersection', type=str, help="Name of the intersection")

def getSwarmCache(intersection, overwrite=False):
    """
    :param intersection:
    :return: the csv file where cache data is stored for
    this intersection to be used in swarming
    """
    cache_file = os.path.join(getEngineDir(), SWARM_DATA_CACHE, intersection+'.csv')
    if os.path.exists(cache_file) and not overwrite:
        print "Using existing data cache file:", cache_file
    else:
        if overwrite:
            print "Overwriting cache file for", intersection, " in ", cache_file
        else:
            print "No cache file exists for", intersection, ".... creating new one in", cache_file
        with open(cache_file, 'wb') as csv_out, pymongo.MongoClient(mongo_uri) as client:
            db = client.mack0242
            collection = db['ACC_201306_20130819113933']
            readings = collection.find({'site_no': intersection})
            sensors = getSensors(intersection)
            fieldnames = ['timestamp'] + sensors
            writer = csv.DictWriter(csv_out, fieldnames=fieldnames)
            writer.writeheader()
            headerRow2 = {f: 'int' for f in sensors}
            headerRow2['timestamp'] = 'datetime'

            headerRow3 = {'timestamp': 'T'}
            writer.writerow(headerRow2)
            writer.writerow(headerRow3)
            if readings.count() == 0:
                raise Exception("No such intersection with site_no '%s' exists" % intersection)
            else:
                for i in readings:
                    # nupic model data format expects this format
                    row = {'timestamp': i['datetime'].strftime('%Y-%m-%d %H:%M')}
                    for j in i['readings']:
                        if j['vehicle_count'] > 2040:
                            row[j['sensor']] = None
                        else:
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


def getPopularLane(fname):
    counter = Counter()
    with open(fname[7:], 'rb') as cache_file:
        reader = csv.DictReader(cache_file)
        # skip the header rows
        reader.next()
        reader.next()
        for row in reader:
            del row['timestamp']
            for k, v in row.iteritems():
                try:
                    counter[k] += int(v)
                except:
                    pass
    return counter.most_common(1)[0][0]


if __name__ == "__main__":
    args = parser.parse_args()
    confdir = os.path.join(getEngineDir(), SWARM_CONFIGS_DIR)
    cachedir = os.path.join(getEngineDir(), SWARM_DATA_CACHE)
    dirs = [confdir, cachedir]
    for i in dirs:
        if not os.path.isdir(i):
            print "Making directory:", i
            os.makedirs(i)
            open(os.path.join(i, '__init__.py'), 'wa').close()
    out_name = os.path.join(getEngineDir(), SWARM_CONFIGS_DIR, 'swarm_config_%s.py' % args.intersection)
    if os.path.exists(out_name) and not args.overwrite:
        sys.exit("Swarm configuration already exists! Use `overwrite` flag to remake")
    else:
        with open(out_name, 'wb') as out_file:
            includedFields = [{
                        "fieldName": "timestamp",
                        "fieldType": "datetime"
                    }]
            swarmCache = getSwarmCache(args.intersection, args.overwrite)
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
                            "source": swarmCache,
                            "columns": [
                                "*"
                            ]
                        }
                    ]
                },
                "inferenceType": "TemporalAnomaly",
                "inferenceArgs": {
                    "predictionSteps": [
                        1
                    ],
                    "predictedField": getPopularLane(swarmCache)
                },
                "iterationCount": -1,
                "swarmSize": "medium"
            }
            print "Writing swarm config to", out_name
            out_file.write("SWARM_DESCRIPTION = {}".format(
                pprint.pformat(swarmConfig, indent=2)))
