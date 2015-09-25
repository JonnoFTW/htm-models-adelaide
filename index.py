#!/usr/bin/env python2.7
import pymongo
from connection import mongo_uri
from pluck import pluck
import sys, argparse
import importlib
import os, pprint
import numpy as np

import nupic_anomaly_output
from nupic.frameworks.opf.modelfactory import ModelFactory
from nupic.data.inference_shifter import InferenceShifter

from nupic.swarming import permutations_runner

DESCRIPTION = """
Makes and runs a NuPIC model for an intersection in Adelaide and
determines its anomaly score based on historical traffic flow
"""
MODEL_PARAMS_DIR = "model_params"
MODEL_CACHE_DIR = "model_store"
SWARM_CONFIGS_DIR = "swarm_configs"
MIN_COUNT = 0
MAX_COUNT = 192 # a reasonable assumption based on TS3001


def setupFolders():
    for i in [MODEL_CACHE_DIR, MODEL_PARAMS_DIR, SWARM_CONFIGS_DIR]:
        directory = os.path.join(os.getcwd(), i)
        if not os.path.isdir(directory):
            print "Creating directory:", directory
            os.makedirs(directory)
            open(os.path.join(directory, '__init__.py'), 'wa').close()


def getModelDir(intersection):
    return os.path.join(os.getcwd(), MODEL_CACHE_DIR, intersection)


def createModel(modelParams, intersection):
    modelDir = getModelDir(intersection)
    if os.path.isdir(modelDir):
        # Read in the cached model
        print "Loading cached model for %s..." % intersection
        model = ModelFactory.loadFromCheckpoint(modelDir)
    else:
        print "Creating model for %s..." % intersection
        model = ModelFactory.create(modelParams)
        model.enableInterface({'predictedField': "vehicle_count"})
        return model


def getMax():
     with pymongo.MongoClient(mongo_uri) as client:
        db = client.mack0242
        collection = db['ACC_201306_20130819113933']
        readings = collection.find()
        print "Max vehicle count:", max([max(
            filter(lambda x:x < 2040, pluck(i['readings'], 'vehicle_count'))) for i in readings])


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
    outPath = os.path.join(os.getcwd(), MODEL_PARAMS_DIR, paramsName)
    with open(outPath, 'wb') as outfile:
        outfile.write("MODEL_PARAMS = \\\n%s" % pprint.PrettyPrint(indent=2).pformat(params))
    return outPath


def swarmParams(swarmConfig, intersection):
    outputLabel = intersection
    permWorkDir = os.path.abspath('swarm')
    if not os.path.exists(permWorkDir):
        os.mkdir(permWorkDir)
    import multiprocessing as mp
    # use 3/4 of your CPUs
    maxWorkers = 3 * mp.cpu_count()/2
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


def runIoThroughNupic(readings, model, intersection, plot):
    shifter = InferenceShifter()
    pfield = model.getInferenceArgs()['predictedField']
    if plot:
        output = nupic_anomaly_output.NuPICPlotOutput(intersection, pfield)
    else:
        output = nupic_anomaly_output.NuPICFileOutput(intersection, pfield)
    counter = 0
    num_readings = len(readings[0]['readings'])
    flows = np.empty(num_readings, dtype=np.uint16)
    # should probably use a message queue here or something
    # running a data through a model could take a while
    # and will block, if we multithread or multiprocess it could
    # be good. Have a pool of processes, each assigned to process
    # data for a particular set of models


    # also investigate re analysing data near the start
    for i in readings:
        counter += 1
        if counter % 100 == 0:
            print "Read %i lines..." % counter
        timestamp = i['datetime']
        fields = {
            "timestamp": timestamp
        }
        for p, j in enumerate(i['readings']):
            vc = j['vehicle_count']
            if vc > 2040:
                vc = None
            fields[j['sensor']] = vc
            flows[p] = vc
        result = model.run(fields)
        if plot:
          result = shifter.shift(result)

        prediction = result.inferences["multiStepBestPredictions"][1]
        anomalyScore = result.inferences["anomalyScore"]
        output.write(timestamp, flows, prediction, anomalyScore)
        flows = np.empty(num_readings, dtype=np.uint16)
    output.close()


def runModel(intersection, plot, swarm):
    modelParams = getModelParamsFromName(intersection, swarm)
    with pymongo.MongoClient(mongo_uri) as client:
        db = client.mack0242
        collection = db['ACC_201306_20130819113933']
        readings = collection.find({'intersection_number': intersection})
        if readings.count() == 0:
            sys.exit("No such intersection '%s' exists!" % intersection)
        model = createModel(modelParams)
        try:
            runIoThroughNupic(readings, model, intersection, plot)
        except KeyboardInterrupt:
            model.save(getModelDir(intersection))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('--plot', help="Plot the anomaly scores", action='store_true')
    parser.add_argument('--swarm', help="Create model params via swarming", action='store_true')
    parser.add_argument('intersection', type=str, help="Name of the intersection", default=3001)

    args = parser.parse_args()
    setupFolders()
    runModel(args.intersection, args.plot, args.swarm)

