#!/usr/bin/env python2.7
from Queue import Empty
from collections import Counter, deque
from datetime import timedelta, datetime
from multiprocessing import Pool
import multiprocessing.pool
import multiprocessing
import sys
import argparse
import importlib
import os
import time
import numpy
from pluck import pluck
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


def get_sensor_encoder(name, maxval=False, buckets=20):
    if maxval:
        max_vehicles = maxval

    resolution = max(0.001, (max_vehicles-1)/buckets)
    return {
        'fieldname': name,
        'name': name,
        # 'clipInput': True,
        'resolution': resolution,
        # 'numBuckets': 130.0,
        # 'minval': 0.0,
        # 'maxval': 250,
        # 'n': 600,
        'w': 21,
        'type': 'RandomDistributedScalarEncoder'
    }


def get_time_encoders():
    return [{
        'fieldname': 'timestamp',
        'name': 'timestamp_weekend',
        'weekend': (51, 9),
        'type': 'DateEncoder'
    }, {
        'fieldname': 'timestamp',
        'name': 'timestamp_timeOfDay',
        'type': 'DateEncoder',
        'timeOfDay': (101, 9.49)
    }, {
        'fieldname': 'timestamp',
        'name': 'timestamp_dayOfWeek',
        'type': 'DateEncoder',
        'timeOfDay': (51, 9.49)
    }
  #  , {
  #      'fieldname': 'weekOfYear',
  #      'name': 'weekOfYear',
  #      'minval': 0,
  #      'maxval': 53,
   #     'periodic': True,
    #    'type': 'ScalarEncoder',
     #   'n': 400,
      #  'w': 21
    #}
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
        location = locations_collection.find_one({'intersection_number': intersection})

        for k in location['sensors']:
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
                             {'$set': {'sensors': [i[0] for i in counts if i[1] != 0]}})


def getMax():
    readings = readings_collection.find()
    print "Max vehicle count:", max([max(
        filter(lambda x: x < max_vehicles, i.values())) for i in readings])

def getModelParamsFromName(intersection, clear=True):
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
    if clear:
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
        locations_collection.find_one_and_update({'intersection_number': self.intersection}, {'$set':{'running':True}})
        anomaly_likelihood_helper = anomaly_likelihood.AnomalyLikelihood(200, 200, reestimationPeriod=10)
        model = create_single_sensor_model(self.sensor, self.intersection)
        while not self.done:
            try:
                val = self.queue_in.get(True, 1)
            except Empty:
                continue

            result = model.run(val)
            prediction = result.inferences["multiStepBestPredictions"][1]

            if val[self.sensor] is None:
                anomaly_score = None
                likelihood = None
            else:
                anomaly_score = result.inferences["anomalyScore"]
                likelihood = anomaly_likelihood_helper.anomalyProbability(
                    val[self.sensor], anomaly_score, val['timestamp'])
            self.queue_out.put((self.sensor, prediction, anomaly_score, likelihood))
        # could probably serialize the model here

    def finish(self):
        self.done = True


def process_readings(readings, intersection, write_anomaly, progress=True, multi_model=False, smoothing=0):
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
    _smoothing = smoothing >= 1
    if _smoothing:
        previous = deque(maxlen=smoothing)
    for i in readings:
        counter += 1
        if progress:
            progBar.update()
        timestamp = i['datetime']
        if multi_model:
            predictions, anomalies = {}, {}
            for sensor, proc in models.iteritems():
                vc = i['readings'][sensor]
                if vc > max_vehicles:
                    vc = None
                elif _smoothing and len(previous):
                    vc = (vc + sum(pluck(sensor, previous)))/float(len(previous) + 1)
                fields = {"timestamp": timestamp, sensor: vc}
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
        if _smoothing:
            previous.append(i['readings'])
    locations_collection.find_one_and_update({'intersection_number': intersection}, {'$unset': {'running': ''}})
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
    intersection, write_anomaly, incomplete, \
     show_progress, multi_model, smooth = args[0], args[1],\
                     args[2], args[3],\
                     args[4], args[5]
    start_time = time.time()

    query = {'site_no': intersection}
    if incomplete:
        query['anomaly'] = {'$exists': False}
    readings = readings_collection.find(query, {'anomalies': False, 'predictions': False}, no_cursor_timeout=True).\
        sort('datetime', pymongo.ASCENDING)
    if readings.count(True) == 0:
        print "No readings for intersection {}".format(intersection)
        return
    process_readings(readings, intersection, write_anomaly, show_progress, multi_model)

    print("Intersection %s complete: --- %s seconds ---" % (intersection, time.time() - start_time))


def run_all_intersections(write_anomaly, incomplete, intersections, multi_model, smooth):
    print "Running all on", os.getpid()
    start_time = time.time()

    if incomplete:
        key = '_id'
        query = [
            {'$match': {'anomaly': {'$exists': False}}},
            {'$group': {'_id': '$site_no'}}
        ]
        if intersections != '':
            query[0]['$match']['site_no'] = {'$in': intersections.split(',')}
        locations = list(readings_collection.aggregate(query))

    else:
        key = 'intersection_number'
        if intersections != '':
            query = {key: {'$in': intersections.split(',')}}
        else:
            query = {key:  {'$regex': '3\d\d\d'}}
        locations = list(locations_collection.find(query))
    gen = [(str(l[key]), write_anomaly, incomplete, False, multi_model, smooth) for l in locations]
    pool = Pool(8, maxtasksperchild=1)
    pool.map(run_single_intersection, gen)
    print("TOTAL TIME: --- %s seconds ---" % (time.time() - start_time))


def get_data():
    readings = readings_collection.find({'site_no': '3083'},
                                        {'datetime': True, 'readings': True}).sort('datetime', pymongo.ASCENDING)
    data = numpy.empty((readings.count(), 2), dtype=numpy.uint64)
    c = 0
    for i in readings:
        data[c][0] = i['datetime'].strftime("%s")
        data[c][1] = i['readings']['56']
        c += 1

    numpy.savetxt('3083_56.csv', data, fmt='%d', delimiter=',')


def create_upstream_model(max_input, steps=None):
    """
    A model where the link has its downstream readings summed
    :return:
    """
    model_params = getModelParamsFromName('3104_3044', clear=True)
    # model_params['modelParams']['sensorParams']['encoders']['upstream'] = get_sensor_encoder('upstream', 150)
    model_params['modelParams']['sensorParams']['encoders']['downstream'] = get_sensor_encoder('downstream', max_input)
    for i in get_time_encoders():
        model_params['modelParams']['sensorParams']['encoders'][i['name']] = i
    if steps is not None:
        model_params['modelParams']['clParams']['steps'] = ','.join(map(str, steps))
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(model_params)
    model = ModelFactory.create(model_params)
    model.enableInference({'predictedField': 'downstream'})

    return model

def create_downstream_model(intersections):
    """
    Just model those downstream sensors as separate inputs
    :param intersection:
    :return:
    """
    model_params = getModelParamsFromName('3104_3044', clear=True)
    intersection = locations_collection.find_one({'intersection_number': intersections[0],
                                                  'neighbours_sensors': {'$exists': True}})
    if intersection is None:
        sys.exit('No such intersection exists or it has no neighbours_sensors')

    multi_encoder = {
        'type': 'MultiEncoder',
        'fieldname': 'lanes',
        'encoderDescriptions': {}
    }
    for i in intersection['neighbours_sensors'][intersections[1]]['to']:
        i = str(i)
        multi_encoder['encoderDescriptions'][i] = get_sensor_encoder(i, 250)
    for i in get_time_encoders():
        model_params['modelParams']['sensorParams']['encoders'][i['name']] = i
    import json
    model_params['modelParams']['sensorParams']['encoders']['lanes'] = multi_encoder
    print json.dumps(model_params['modelParams']['sensorParams'], indent=4)
    # return None, intersection
    model = ModelFactory.create(model_params)
    model.enableInference({'predictedField': 'lanes'})
    return model, intersection


def process_upstream_model(model, sensors):
    """

    :param intersections: a dict of {'upstream':{'id':3043,'query':
                            3084(1+2+3+4+5)-3032(1+2+3+4)+3084(10+11)+3044(5+6+7+8+9+10+11)-3084(1+2+3+4+5)+3032(1+2+3+4)-3084(10+11)},
                                     'downstream':{'id':'3084','sensors':[1,2,3,4}}
    :return:

    """
    import re
    # from collections import defaultdict
    # # upstream_sensors = set(re.findall(r"(-?\d+\(.*?\))", sensors['upstream']['query']))
    # queries = []
    # for i in upstream_sensors:
    #     if i[0] == '-':
    #         if i[1:] not in upstream_sensors:
    #             queries.append(i)
    #     else:
    #         if '-' + i not in upstream_sensors:
    #             queries.append(i)
    # # make a dict of intersections and the sensors we need to read from them
    # upstream_intersections = defaultdict(defaultdict)
    # for query in queries:
    #     split = query.split('(')
    #     intersection, isensors = split[0], split[1][:-1].split('+')
    #     upstream_intersections[intersection]['sensors'] = map(lambda x: str(int(x)*8), isensors)
    #     upstream_intersections[intersection]['subtract'] = query[0] == '-'

    # sensors_to_fetch = [sensors['downstream']['id']] + upstream_intersections.keys()
    # readings = readings_collection.find({'site_no': sensors['downstream']['id']},
    #                                     {'anomalies': False, 'predictions': False}, no_cursor_timeout=True). \
    #     sort('datetime', pymongo.ASCENDING)


    import nupic_anomaly_output

    output = nupic_anomaly_output.NuPICPlotOutput("Traffic Volume from " + sensors['upstream']['id'] + " to " + sensors['downstream']['id'])
    # print "Upstream:", sensors['upstream']
    # print "Downstream:", sensors['downstream']

    # input()


    # with open('readings.csv', 'w') as out:
    #   import csv
    #   writer = csv.DictWriter(out, fieldnames=['timestamp', 'downstream'])
    #   writer.writeheader()
    with open('readings.csv', 'r') as infile:
        import csv
        readings = csv.DictReader(infile)
        readings.next()
        readings.next()

        for reading in readings:
            # current_readings = {i['site_no']: i for i in [next(readings) for _ in range(len(sensors_to_fetch))]+[x]}

            # times = pluck(current_readings.values(), 'datetime')
            # if not times.count(times[0]) == len(times):
            #     print "Datetime mismatch"
            #     continue

            # downstream_reading = current_readings[sensors['downstream']['id']]
            timestamp = reading['timestamp']


            timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M')
            # print timestamp
            # upstream_total = 0
            #
            # for intersection_id, v in upstream_intersections.items():
            #     if intersection_id != downstream_reading['site_no']:
            #         total = sum([current_readings[intersection_id]['readings'][sensor] for sensor in v['sensors']])
            #         if v['subtract']:
            #             upstream_total -= total
            #         else:
            #             upstream_total += total
            # downstream_total = sum((reading['readings'][s] for s in sensors['downstream']['sensors']))
            downstream_total = float(reading['downstream'])

            fields = {
                "timestamp": timestamp,
                'downstream': downstream_total,
                # 'upstream': upstream_total
            }
            # writer.writerow(fields)
            result = model.run(fields)
            # print result

            anomaly_score = result.inferences["anomalyScore"]
            prediction = result.inferences["multiStepBestPredictions"][1]

            # likelihood = anomaly_likelihood_helper.anomalyProbability(downstream_total, anomaly_score, timestamp)
            # print "input", downstream_total, "Pred", prediction, "anomaly_score", anomaly_score
            output.write(timestamp, downstream_total, prediction, anomaly_score)


def run_upstream_model(intersections, args):

    downstream = locations_collection.find_one({'intersection_number': intersections[0]})
    if args.aggregate:
        model = create_upstream_model()
    else:
        model = 5
    sensors = {
        'downstream': {
            'id': downstream['intersection_number'],
            'sensors': map(lambda x: str(x*8), downstream['neighbours_sensors'][intersections[1]]['to'])
        },
        'upstream': {
            'id': intersections[1],
            'query': downstream['neighbours_sensors'][intersections[1]]['from']
        }
    }
    process_upstream_model(model, sensors)


def process_downstream_model(intersections, model, intersection, args):
    readings = readings_collection.find({'site_no': intersections[0]})
    sensors = intersection['neighbours_sensors'][intersections[1]]['to']
    import csv
    with open('lane_data_{}_{}.csv'.format(intersections[0], intersections[1]), 'w') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=['timestamp']+[str(sensor) for sensor in sensors])
        writer.writeheader()
        print "Writing to " + outfile.name
        for r in readings:
            lanes = {str(sensor): r['readings'][str(sensor)] for sensor in sensors}

            lanes['timestamp'] = r['datetime']
            writer.writerow(lanes)
            # print fields

            # result = model.run(fields)
            # print result


def run_downstream_model(args):
    intersections = args.intersection.split(",")
    model, intersection = create_downstream_model(intersections)
    process_downstream_model(intersections, model, intersection, args)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('--search', help='Perform a parameter search', action='store_true')
    parser.add_argument('--write-anomaly', help="Write the anomaly score back into the document", action='store_true')
    parser.add_argument('--all', help="Run all readings through model", action="store_true")
    parser.add_argument('--intersection', type=str, help="Name of the intersection", default='')
    parser.add_argument('--incomplete', help="Analyse those intersections not done yet", action='store_true')
    parser.add_argument('--popular', help="Show the most popular sensor for an intersection", action='store_true')
    parser.add_argument('--cache-models', help="Cache models", action='store_true')
    parser.add_argument('--setup-sensors', help='store used sensors in locations. Use --intersection to specify '
                                                'many otherwise it will do all of them', action='store_true')
    parser.add_argument('--multi-model', help="Use a model per sensor", action='store_true')
    parser.add_argument('--smooth', type=int, help="Smooth the readings values using a mean filter with given size", default=0)
    parser.add_argument('--upstream-model', help="Make a model that analyses the traffic between two", default='')
    parser.add_argument('--downstream-model', help="Model each sensor of a link separately", action='store_true')
    parser.add_argument('--aggregate', help='aggregates',  default='store_true')
    args = parser.parse_args()
    if args.downstream_model:
        run_downstream_model(args)
        raw_input("exit")
        sys.exit()
    if args.upstream_model:
        intersections = args.upstream_model.split(',')
        run_upstream_model(intersections, args)
        raw_input("exit")
        sys.exit()
    if args.search:
        print "Searching for good encoder params"
        get_data()
        sys.exit()
    if args.setup_sensors:
        setup_location_sensors(args.intersection)
        sys.exit()
    CACHE_MODELS = args.cache_models
    setupFolders()
    if args.all:
        run_all_intersections(args.write_anomaly, args.incomplete, args.intersection, args.multi_model, args.smooth)
    elif args.popular:
        print "Lane usage for ", args.intersection, "is:  "
        for i, j in get_most_used_sensors(args.intersection).most_common():
            print '\t', i, j
    else:
        if args.intersection == '':
            parser.error("Please specify an intersection")
        run_single_intersection((args.intersection, args.write_anomaly, args.incomplete, True, args.multi_model, args.smooth))
