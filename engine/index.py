#!/usr/bin/env python2.7
from Queue import Empty
from collections import Counter
from datetime import timedelta
from multiprocessing import Pool
import multiprocessing
import sys
import argparse
import importlib
import os
import time
import pymongo
import pyprind
import yaml

from nupic.frameworks.opf.modelfactory import ModelFactory
from nupic.algorithms import anomaly_likelihood

global CACHE_MODELS


def getEngineDir():
    return os.path.dirname(os.path.realpath(__file__))


try:
    path = os.path.join(os.path.dirname(getEngineDir()), 'connection.yaml')
    with open(path, 'r') as f:
        conf = yaml.load(f)
        mongo_uri = conf['mongo_uri']
        mongo_database = conf['mongo_database']
        mongo_collection = conf['mongo_collection']
        MODEL_PARAMS_DIR = conf['MODEL_PARAMS_DIR']
        MODEL_CACHE_DIR = conf['MODEL_CACHE_DIR']
        SWARM_CONFIGS_DIR = conf['SWARM_CONFIGS_DIR']
        max_vehicles = conf['max_vehicles']
except:
    raise Exception('No connection.yaml with mongo_uri defined! please make one with a mongo_uri variable')

DESCRIPTION = """
Makes and runs a NuPIC model for an intersection in Adelaide and
determines its anomaly score based on historical traffic flow
"""


def setupFolders():
    for i in [MODEL_CACHE_DIR, MODEL_PARAMS_DIR, SWARM_CONFIGS_DIR]:
        directory = os.path.join(getEngineDir(), i)
        if not os.path.isdir(directory):
            print "Creating directory:", directory
            os.makedirs(directory)
            open(os.path.join(directory, '__init__.py'), 'wa').close()


def getModelDir(intersection):
    return os.path.join(getEngineDir(), MODEL_CACHE_DIR, intersection)


client = pymongo.MongoClient(mongo_uri, w=0)
readings_collection = client[mongo_database][mongo_collection]
locations_collection = client[mongo_database]['locations']

def get_most_used_sensors(intersection):
    records = readings_collection.find({'site_no': intersection})
    counter = Counter()
    for i in records:
        for s, c in i['readings'].items():
            if c < max_vehicles:
                counter[s] += c
    return counter


def get_sensor_encoder(name):
    return {'fieldname': name,
            'resolution': 1,
            'n': 400,
            'name': name,
           # 'minval': 0,
           # 'maxval': max_vehicles,
            'type': 'DeltaEncoder',
            'w': 21
    }


def get_time_encoders():
    return [{
      'fieldname': 'timestamp',
      'name': 'timestamp_timeOfDay',
      'type': 'DateEncoder',
      'timeOfDay': (21, 6)},
      {
      'fieldname': 'timestamp',
      'name': 'timestamp_weekend',
      'type': 'DateEncoder',
      'weekend': (21, 1)},
      {'fieldname': 'timestamp',
       'name': 'timestamp_dayOfWeek',
       'type': 'DateEncoder',
       'dayOfWeek': (21, 1)}
    ]


def createModel(intersection):
    modelDir = getModelDir(intersection)
    if CACHE_MODELS and os.path.isdir(modelDir):
        # Read in the cached model
        print "Loading cached model for {} from {}...".format(intersection, modelDir)
        return ModelFactory.loadFromCheckpoint(modelDir)
    else:
        start = time.time()
        # redo the modelParams to use the actual sensor names
        modelParams = getModelParamsFromName('3001')

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
        doc = readings_collection.find_one({'site_no': intersection})

        for k in doc['readings']:
            # don't model unused sensors
            # could run into errors when the sensor
            # was damaged for more than the sample period though
            if sensor_counts[k] == 0 or k != pField:
                continue
            modelParams['modelParams']['sensorParams']['encoders'][k] = get_sensor_encoder(k)

        for i in get_time_encoders():
            modelParams['modelParams']['sensorParams']['encoders'][i['name']] = i


        model = ModelFactory.create(modelParams)
        model.enableInference({'predictedField': pField})
        print "Creating model for {}, in {}s".format(intersection, time.time() - start)
        return model


def create_single_sensor_model(sensor, intersection):
    start = time.time()
    model_params = getModelParamsFromName('3001')
    model_params['modelParams']['sensorParams']['encoders'][sensor] = get_sensor_encoder(sensor)
    for i in get_time_encoders():
        model_params['modelParams']['sensorParams']['encoders'][i['name']] = i
    model = ModelFactory.create(model_params)
    model.enableInference({'predictedField': sensor})
  #  print "Creating model for {}:{} in {}s on pid {}".format(intersection, sensor, time.time() - start, os.getpid())
    return model


def setup_location_sensors(intersection):
    if not intersection:
        query = {}
    else:
        query = {'intersection_number': {'$in': intersection.split(',')}}
    for i in locations_collection.find(query):
        counts = get_most_used_sensors(i['intersection_number']).most_common()
        if len(counts) == 0:
            continue
        locations_collection.update_one({'_id': i['_id']},
                             {'$set': {'sensors':
                                           [i[0] for i in counts if i[1] != 0]
                                  }})


def getMax():
    readings = readings_collection.find()
    print "Max vehicle count:", max([max(
        filter(lambda x: x < max_vehicles, i.values())) for i in readings])

def getModelParamsFromName(intersection):
    """
    Given an intersection name, assumes a matching model params python module exists within
    the model_params directory and attempts to import it.
    :param intersection: intersection name, used to guess the model params module name.
    :return: OPF Model params dictionary
    """
    importName = "%s.model_params_%s" % (MODEL_PARAMS_DIR, intersection)
    # print "Importing model params from %s" % importName
    try:
        importedModelParams = importlib.import_module(importName).MODEL_PARAMS
    except ImportError:
       raise sys.exit("No model params exist for '%s'. Run swarm first!" % intersection)
    importedModelParams['modelParams']['sensorParams']['encoders'].clear()
    return importedModelParams


def get_encoders(model):
    return set([i.name for i in model._getSensorRegion().getSelf().encoder.getEncoderList()])


class Worker(multiprocessing.Process):
    def __init__(self, sensor, intersection):
        super(Worker, self).__init__()
        self.queue_in = multiprocessing.Queue()
        self.queue_out = multiprocessing.Queue()
        self.done = False
        self.sensor = sensor
        self.intersection = intersection

    def run(self):
        anomaly_likelihood_helper = anomaly_likelihood.AnomalyLikelihood(50, 50)
        model = create_single_sensor_model(self.sensor, self.intersection)
        while not self.done:
            try:
                val = self.queue_in.get(True, 1)
            except Empty:
                continue
            result = model.run(val)
            prediction = result.inferences["multiStepBestPredictions"][1]
            anomaly_score = result.inferences["anomalyScore"]
            likelihood = anomaly_likelihood_helper.anomalyProbability(
                val[self.sensor], anomaly_score, val['timestamp'])
            self.queue_out.put((self.sensor, prediction, anomaly_score, likelihood))
        # could probably serialize the model here

    def finish(self):
        self.done = True


def process_readings(readings, intersection, write_anomaly, progress=True, multi_model=False):
    counter = 0
    total = readings.count(True)

    if multi_model:

        loc = locations_collection.find_one({'intersection_number': intersection})
        models = {}
        for sensor in loc['sensors']:
            models[sensor] = Worker(sensor, intersection)
            models[sensor].start()
    else:
        model = createModel(intersection)
        anomaly_likelihood_helper = anomaly_likelihood.AnomalyLikelihood(1000, 200)
        if model is None:
            print "No model could be made for intersection", intersection
            return
        pfield = model.getInferenceArgs()['predictedField']
        encoders = get_encoders(model)
    if progress:
        progBar = pyprind.ProgBar(total, width=50)

    for i in readings:
        counter += 1
        if progress:
            progBar.update()
        timestamp = i['datetime']

        if multi_model:
            predictions, anomalies = {}, {}
            for sensor, proc in models.iteritems():
                fields = {"timestamp": timestamp, sensor: i['readings'][sensor]}
                proc.queue_in.put(fields)
            for sensor, proc in models.iteritems():
                result = proc.queue_out.get()
                # (self.sensor, prediction, anomaly_score, likelihood)
                anomalies[result[0]] = {'score': result[2], 'likelihood': result[3]}
                predictions[result[0]] = result[1]
        else:
            fields = {"timestamp": timestamp}
            for p, j in enumerate(i['readings'].items()):
                if j[0] not in encoders:
                    continue
                vc = j[1]
                if vc > max_vehicles:
                    vc = None
                fields[j[0]] = vc
            result = model.run(fields)
            prediction = result.inferences["multiStepBestPredictions"][1]
            anomaly_score = result.inferences["anomalyScore"]
            predictions = {pfield: prediction}
            likelihood = anomaly_likelihood_helper.anomalyProbability(
                i['readings'][pfield], anomaly_score, timestamp)
            anomalies = {pfield: {'score': anomaly_score, 'likelihood': likelihood}}
        if write_anomaly:
            write_anomaly_out(i, anomalies, predictions)
    if multi_model:
        for proc in models.values():
            proc.terminate()
    else:
        save_model(model, intersection)
    if progress:
        print
    print "Read", counter, "lines"



def write_anomaly_out(doc, anomalies, predictions):
    readings_collection.update_one({"_id": doc["_id"]},
                          {"$set": {"anomalies": anomalies}})
    next_doc = readings_collection.find_one({'site_no': doc['site_no'],
                                   'datetime': doc['datetime'] + timedelta(minutes=5)})
    if next_doc is not None:
        readings_collection.update_one({'_id': next_doc['_id']},
                              {"$set": {"predictions": predictions}})


def save_model(model, site_no):
    if not CACHE_MODELS:
        return
    if model is None:
        print "Not saving model for", site_no
        return
    start = time.time()
    out_dir = getModelDir(site_no)
    model.save(out_dir)
    print "Caching model to {} in {}s".format(out_dir, time.time() - start)


def run_single_intersection(args):
    intersection, write_anomaly, incomplete, show_progress, multi_model = args[0], args[1], args[2], args[3], args[4]
    start_time = time.time()

    query = {'site_no': intersection}
    if incomplete:
        query['anomaly'] = {'$exists': False}
    readings = readings_collection.find(query, no_cursor_timeout=True).sort('datetime', pymongo.ASCENDING)
    if readings.count(True) == 0:
        print "No readings for intersection {}".format(intersection)
        return
    process_readings(readings, intersection, write_anomaly, show_progress, multi_model)

    print("Intersection %s complete: --- %s seconds ---" % (intersection, time.time() - start_time))


def run_all_intersections(write_anomaly, incomplete, intersections, multi_model=True):
    print "Running all on", os.getpid()
    start_time = time.time()
    if incomplete:
        key = '_id'
        locations = list(readings_collection.aggregate([
            {'$match': {'anomaly': {'$exists': False}}},
            {'$group': {'_id': '$site_no'}}
        ]))

    else:
        key = 'intersection_number'
        if intersections != '':
            query = {key: {'$in': intersections.split(',')}}
        else:
            query = {key:  {'$regex': '3\d\d\d'}}
        locations = list(locations_collection.find(query))
    gen = [(str(l[key]), write_anomaly, incomplete, False) for l in locations]
    if multi_model:
        size = multiprocessing.cpu_count()/2
    else:
        size = 8
    pool = Pool(size)
    pool.map(run_single_intersection, gen)
    print("TOTAL TIME: --- %s seconds ---" % (time.time() - start_time))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('--write-anomaly', help="Write the anomaly score back into the document", action='store_true')
    parser.add_argument('--all', help="Run all readings through model", action="store_true")
    parser.add_argument('--intersection', type=str, help="Name of the intersection", default='')
    parser.add_argument('--incomplete', help="Analyse those intersections not done yet", action='store_true')
    parser.add_argument('--popular', help="Show the most popular sensor for an intersection", action='store_true')
    parser.add_argument('--cache-models', help="Cache models", action='store_true')
    parser.add_argument('--setup-sensors', help='store used sensors in locations. Use --intersection to specify many otherwise it will do all of them', action='store_true')
    parser.add_argument('--multi-model', help="Use a model per sensor", action='store_true')
    args = parser.parse_args()
    if args.setup_sensors:
        setup_location_sensors(args.intersection)
        sys.exit()
    CACHE_MODELS = args.cache_models
    setupFolders()
    if args.all:
        run_all_intersections(args.write_anomaly, args.incomplete, args.intersection)
    elif args.popular:
        print "Lane usage for ", args.intersection, "is:  "
        for i, j in get_most_used_sensors(args.intersection).most_common():
            print '\t', i, j
    else:
        if args.intersection == '':
            parser.error("Please specify an intersection")
        run_single_intersection((args.intersection, args.write_anomaly, args.incomplete, True, args.multi_model))
