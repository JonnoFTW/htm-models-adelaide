#!/usr/bin/env python2.7
from collections import Counter
from datetime import timedelta
from multiprocessing import Pool
import sys
import argparse
import importlib
import os
import pprint
import time
import pymongo
import numpy as np

from nupic.frameworks.opf.modelfactory import ModelFactory
from nupic.data.inference_shifter import InferenceShifter
from nupic.swarming import permutations_runner
import pyprind

import nupic_anomaly_output
import yaml


def getEngineDir():
    return os.path.dirname(os.path.realpath(__file__))


try:
    path = os.path.join(os.path.dirname(getEngineDir()), 'connection.yaml')
    with open(path, 'r') as f:
        conf = yaml.load(f)
        mongo_uri = conf['mongo_uri']
        mongo_database = conf['mongo_database']
        mongo_collection = conf['mongo_collection']
        POOL_SIZE = conf['pool_size']
except:
    raise Exception('No connection.yaml with mongo_uri defined! please make one with a mongo_uri variable')

DESCRIPTION = """
Makes and runs a NuPIC model for an intersection in Adelaide and
determines its anomaly score based on historical traffic flow
"""
MODEL_PARAMS_DIR = "model_params"
MODEL_CACHE_DIR = "model_store"
SWARM_CONFIGS_DIR = "swarm_configs"
MIN_COUNT = 0
MAX_COUNT = 192  # a reasonable assumption based on TS3001


def setupFolders():
    for i in [MODEL_CACHE_DIR, MODEL_PARAMS_DIR, SWARM_CONFIGS_DIR]:
        directory = os.path.join(getEngineDir(), i)
        if not os.path.isdir(directory):
            print "Creating directory:", directory
            os.makedirs(directory)
            open(os.path.join(directory, '__init__.py'), 'wa').close()


def getModelDir(intersection):
    return os.path.join(getEngineDir(), MODEL_CACHE_DIR, intersection)


def get_most_used_sensors(intersection):
    with pymongo.MongoClient(mongo_uri) as client:
        collection = client[mongo_database][mongo_collection]
        records = collection.find({'site_no': intersection})
        counter = Counter()
        for i in records:
            for s, c in i['readings'].items():
                if c < 2040:
                    counter[s] += c
        return counter


def createModel(modelParams, intersection):
    modelDir = getModelDir(intersection)
    if False and os.path.isdir(modelDir):
        # Read in the cached model
        print "Loading cached model for {} from {}...".format(intersection, modelDir)
        return ModelFactory.loadFromCheckpoint(modelDir)
    else:
        # redo the modelParams to use the actual sensor names
        modelParams['modelParams']['sensorParams']['encoders'].clear()
        sensor_counts = get_most_used_sensors(intersection)
        # try:
        #     pField = getSwarmConfig(intersection)['inferenceArgs']['predictedField']
        # except:
        #     print "Determining most used sensor for ", intersection
        try:
            counts = sensor_counts.most_common(1)
            if counts[0][1] == 0:
                return None
            else:
                pField = counts[0][0]
        except:
            return None
        print "Using", pField, "as predictedField for", intersection
        with pymongo.MongoClient(mongo_uri) as client:
            collection = client[mongo_database][mongo_collection]
            doc = collection.find_one({'site_no': intersection})

            for k, v in doc['readings'].items():
                # don't model unused sensors
                # could run into errors when the sensor
                # was damaged for more than the sample period though
                if sensor_counts[k] == 0:
                    continue
                modelParams['modelParams']['sensorParams']['encoders'][k] = {
                    'clipInput': True,
                    'fieldname': k,
                    'maxval': 200,
                    'minval': 0,
                    'n': 100,
                    'name': k,
                    'type': 'ScalarEncoder',
                    'w': 21
                }
            modelParams['modelParams']['sensorParams']['encoders']['timestamp_dayOfWeek'] = {'fieldname': 'timestamp',
                                                                                  'name': 'timestamp_dayOfWeek',
                                                                                  'type': 'DateEncoder',
                                                                                  'dayOfWeek': (21, 1)}
            modelParams['modelParams']['sensorParams']['encoders']['timestamp_timeOfDay'] = {
                                                                                  'fieldname': 'timestamp',
                                                                                  'name': 'timestamp_timeOfDay',
                                                                                  'type': 'DateEncoder',
                                                                                  'timeOfDay': (21, 6)}
            modelParams['modelParams']['sensorParams']['encoders']['timestamp_weekend'] = {'fieldname': 'timestamp',
                                                                                  'name': 'timestamp_weekend',
                                                                                  'type': 'DateEncoder',
                                                                                  'weekend': (21, 1)}

        print "Creating model for {}...".format(intersection)
        model = ModelFactory.create(modelParams)
        model.site_no = intersection
        model.encoders = modelParams['modelParams']['sensorParams']['encoders'].keys()
        model.enableInference({'predictedField': pField})
        return model


def getMax():
    with pymongo.MongoClient(mongo_uri) as client:
        collection = client[mongo_database][mongo_collection]
        readings = collection.find()
        print "Max vehicle count:", max([max(
            filter(lambda x: x < 2040, i.values())) for i in readings])


def getSwarmConfig(intersection):
    importName = "%s.swarm_config_%s" % (SWARM_CONFIGS_DIR, intersection)
    print "Importing swarm config from %s" % importName
    try:
        importedSwarmConfig = importlib.import_module(importName)
    except ImportError:
        sys.exit("No swarm config exist for '{0}'. Please run create_swarm_config.py {0}".format(intersection))
    return importedSwarmConfig.SWARM_DESCRIPTION


def getModelParamsFromName(intersection, swarm):
    """
    Given an intersection name, assumes a matching model params python module exists within
    the model_params directory and attempts to import it.
    :param intersection: intersection name, used to guess the model params module name.
    :param: swarm: run a swarm if the model params don't exist
    :return: OPF Model params dictionary
    """
    importName = "%s.model_params_%s" % (MODEL_PARAMS_DIR, intersection)
    print "Importing model params from %s" % importName
    try:
        importedModelParams = importlib.import_module(importName).MODEL_PARAMS
    except ImportError:
        if swarm:
            print "No model params exist for %s... swarming now!" % intersection
            swarmParams(getSwarmConfig(intersection), intersection)
            sys.exit("Swarming complete! Run again to run to run the model")
        else:
            raise sys.exit("No model params exist for '%s'. Run swarm first!" % intersection)
    return importedModelParams


def writeModelParams(params, intersection):
    paramsName = "model_params_%s.py" % intersection
    outPath = os.path.join(getEngineDir(), MODEL_PARAMS_DIR, paramsName)
    with open(outPath, 'wb') as outfile:
        outfile.write("MODEL_PARAMS = \\\n%s" % pprint.pformat(params, indent=2))
    return outPath


def swarmParams(swarmConfig, intersection):
    outputLabel = intersection
    permWorkDir = os.path.abspath('swarm')
    if not os.path.exists(permWorkDir):
        os.mkdir(permWorkDir)
    import multiprocessing as mp
    # use 3/4 of your CPUs
    maxWorkers = 3 * mp.cpu_count() / 2
    print "Running swarm!"
    modelParams = permutations_runner.runWithConfig(
        swarmConfig,
        {"maxWorkers": maxWorkers, "overwrite": True},
        outputLabel=outputLabel,
        outDir=permWorkDir,
        permWorkDir=permWorkDir,
        verbosity=2
    )
    modelParamsFile = writeModelParams(modelParams, intersection)
    return modelParamsFile


def runIoThroughNupic(readings, model, intersection, output, write_anomaly, collection):
    shifter = InferenceShifter()
    pfield = model.getInferenceArgs()['predictedField']
    if output == 'plot':
        output = nupic_anomaly_output.NuPICPlotOutput(intersection, pfield)
    elif output == 'csv':
        output = nupic_anomaly_output.NuPICFileOutput(intersection, pfield)
    counter = 0
    total = readings.count()
    num_readings = len(readings[0]['readings'])
    flows = np.empty(num_readings, dtype=np.uint16)
    progBar = pyprind.ProgBar(total, width=60)
    for i in readings:
        counter += 1
        progBar.update()
        timestamp = i['datetime']
        fields = {
            "timestamp": timestamp
        }
        for p, j in enumerate(i['readings'].items()):
            if j[0] not in model.encoders:
                continue
            vc = j[1]
            if vc > 2040:
                vc = None
            fields[j[0]] = vc
            if output:
                flows[p] = vc
        result = model.run(fields)
        if output == 'plot':
            result = shifter.shift(result)
        prediction = result.inferences["multiStepBestPredictions"][1]
        anomalyScore = result.inferences["anomalyScore"]
        if write_anomaly:
            write_anomaly_out(i, anomalyScore, pfield, prediction, collection)
        if output:
            output.write(timestamp, flows, prediction, anomalyScore)
        flows = np.empty(num_readings, dtype=np.uint16)
    print "\nRead", counter, "lines"
    if output:
        output.close()


def write_anomaly_out(doc, anomalyScore, pfield, prediction, collection):
    collection.update_one({"_id": doc["_id"]},
                          {"$set": {"anomaly_score": anomalyScore}})
    next_doc = collection.find_one({'site_no': doc['site_no'],
                                   'datetime': doc['datetime'] + timedelta(minutes=5)})
    if next_doc is not None:
        collection.update_one({'_id': next_doc['_id']},
                              {"$set": {"prediction": {
                                'sensor': pfield,
                                'prediction': prediction,
                                'error': abs(next_doc['readings'][pfield] - prediction)
                              }}})


def save_model(model):
    if model is None:
        print "Not saving model"
        return
    out_dir = getModelDir(model.site_no)
    print "Caching model to", out_dir
    model.save(out_dir)


def run_single_intersection(args):
    intersection, modelParams, write_anomaly = args[0], args[1], args[2]
    print "Running intersection", intersection
    start_time = time.time()
    model = createModel(modelParams, intersection)
    if model is None:
        return
    with pymongo.MongoClient(mongo_uri) as client:
        collection = client[mongo_database][mongo_collection]
        readings = collection.find({'site_no': intersection}).sort('datetime', pymongo.ASCENDING).limit(500)

        pfield = model.getInferenceArgs()['predictedField']
        for i in readings:
            timestamp = i['datetime']
            fields = {
                "timestamp": timestamp
            }
            for p, j in enumerate(i['readings'].items()):
                if j[0] not in model.encoders:
                    continue
                vc = j[1]
                if vc > 2040:
                    vc = None
                fields[j[0]] = vc
            result = model.run(fields)
            prediction = result.inferences["multiStepBestPredictions"][1]
            anomaly_score = result.inferences["anomalyScore"]
            if write_anomaly:
                write_anomaly_out(i, anomaly_score, pfield, prediction, collection)
    print("Intersection %s: --- %s seconds ---" % (intersection, time.time() - start_time))
    #save_model(model)


def run_all(locations, write_anomaly, key='intersection_number'):
    model_params = getModelParamsFromName('3001', False)
    pool = Pool(processes=POOL_SIZE)
    pool.map(run_single_intersection, ((i[key], model_params, write_anomaly) for i in locations))




def runModel(intersection, output, swarm, write_anomaly):
    #this is a hack, not every intersection needs these particular params
    modelParams = getModelParamsFromName('3001', swarm)
    with pymongo.MongoClient(mongo_uri) as client:
        db = client[mongo_database]
        collection = db[mongo_collection]
        readings = collection.find({'site_no': intersection}).sort('datetime', pymongo.ASCENDING)
        if readings.count() == 0:
            sys.exit("No such intersection '%s' exists or it has no readings saved!" % intersection)
        model = createModel(modelParams, intersection)
        if model is None:
            print "No data for", intersection
            return
        try:
            runIoThroughNupic(readings, model, intersection, output, write_anomaly, collection)
        except KeyboardInterrupt:
            pass
        finally:
            save_model(model)


def runAllModels(write_anomaly, incomplete):
    with pymongo.MongoClient(mongo_uri) as client:
        collection = client[mongo_database]['locations']
        start_time = time.time()

        if incomplete:
            locations, key = client[mongo_database][mongo_collection].aggregate([
                {'$match': {'prediction.sensor': {'$eq': '152'}}},
                {'$group': {'_id': '$site_no'}}
            ]), '_id'

        else:
            query = {'intersection_number': {'$regex': '3\d\d\d'}}
            locations, key = collection.find(query), 'intersection_number'
        run_all(locations, write_anomaly, key)
        print("TOTAL TIME: --- %s seconds ---" % (time.time() - start_time))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('--output', type=str, help="Output anomaly scores to :", choices=['csv', 'plot'])
    parser.add_argument('--swarm', help="Create model params via swarming", action='store_true')
    parser.add_argument('--write-anomaly', help="Write the anomaly score back into the document", action='store_true')
    parser.add_argument('--all', help="Run all readings through model", action="store_true")
    parser.add_argument('--intersection', type=str, help="Name of the intersection")
    parser.add_argument('--incomplete', help="Analyse those intersections not done yet", action='store_true')
    parser.add_argument('--popular', help="Show the most popular sensor for an intersection", action='store_true')
    args = parser.parse_args()
    setupFolders()
    if args.all and args.intersection:
        parser.error("You can't specify an intersection when running all intersections")
    elif args.all:
        runAllModels(args.write_anomaly, args.incomplete)
    elif args.popular:
        print "Lane usage for ", args.intersection, "is:  "
        for i, j in get_most_used_sensors(args.intersection).most_common():
            print '\t', i, j
    else:
        runModel(args.intersection, args.output, args.swarm, args.write_anomaly)
