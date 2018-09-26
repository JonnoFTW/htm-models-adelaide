#!/usr/bin/env python
from __future__ import print_function
from time import time
import base64
from hyperopt import Trials, STATUS_OK, tpe, mongoexp
from nupic.frameworks.opf.model_factory import ModelFactory
from hyperas import optim
from hyperas.distributions import uniform, quniform
from tqdm import tqdm
from datetime import datetime, timedelta, date
import pickle
from bson import json_util
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import logging

logging.basicConfig()
import os
import subprocess

def data():
    cdir = os.path.dirname(os.path.realpath(__file__))
    pkl_fname = (cdir+'/swarm_data/115_2_1_2_3_4_swarm.pkl.gz')
    p = subprocess.Popen(['zcat', pkl_fname], stdout=subprocess.PIPE)
    rows = pickle.load(p.stdout)
    steps = 1
    # rows = rows[:10000]
    from pluck import ipluck
    _max_flow = float(max(ipluck(rows, 'flow')))
    print("MAX FLOW:", _max_flow)
    return rows, _max_flow


def create_model(rows, _max_flow):
    def rmse(y_true, y_pred, axis=0):
        return np.sqrt(((y_pred - y_true) ** 2).mean(axis=axis))

    def geh(y_true, y_pred, axis=0):
        return np.sqrt(2 * np.power(y_pred - y_true, 2) / (y_pred + y_true)).mean(axis=axis)

    null = None
    true = True
    false = False
    holidays = {date(2015, 1, 1),
                date(2015, 1, 26),
                date(2015, 3, 9),
                date(2015, 4, 3),
                date(2015, 4, 4),
                date(2015, 4, 6),
                date(2015, 4, 25),
                date(2015, 6, 8),
                date(2015, 10, 5),
                date(2015, 12, 24),
                date(2015, 12, 25),
                date(2015, 12, 28),
                date(2015, 12, 31),
                date(2016, 1, 1),
                date(2016, 1, 26),
                date(2016, 3, 14),
                date(2016, 3, 25),
                date(2016, 3, 26),
                date(2016, 3, 28),
                date(2016, 4, 25),
                date(2016, 6, 13),
                date(2016, 10, 3),
                date(2016, 12, 24),
                date(2016, 12, 26),
                date(2016, 12, 27),
                date(2016, 12, 31),
                date(2017, 1, 1),
                date(2017, 1, 2),
                date(2017, 1, 26),
                date(2017, 3, 13),
                date(2017, 4, 14),
                date(2017, 4, 15),
                date(2017, 4, 17),
                date(2017, 4, 25),
                date(2017, 6, 12),
                date(2017, 10, 2),
                date(2017, 12, 24),
                date(2017, 12, 25),
                date(2017, 12, 26),
                date(2017, 12, 31)}
    columnCount = 2048
    max_flow = _max_flow
    flow_buckets = {{quniform(1, 40, 1)}}
    synPermConnected = {{uniform(0.05, 0.25)}}
    activeColumns = {{quniform(20, 64, 1)}}
    synPermInactiveDec = {{uniform(0.0003, 0.1)}}
    synPermActiveInc = {{uniform(0.001, 0.1)}}
    potentialPct = {{uniform(0.2, 0.85)}}
    activationThreshold = {{quniform(5, 20, 1)}}
    pamLength = {{quniform(1, 10, 1)}}
    cellsPerColumn = {{quniform(8, 32, 2)}}
    minThreshold = {{quniform(4, 32, 1)}}
    alpha = {{uniform(0.0001, 0.2)}}
    boost = {{uniform(0.0, 0.1)}}
    tmPermanenceInc = {{uniform(0.05, 0.2)}}
    maxSynapsesPerSegment = {{quniform(28, 72, 2)}}
    newSynapseRatio = {{uniform(0.4, 0.8)}}
    newSynapseCount = maxSynapsesPerSegment * newSynapseRatio
    initialPerm = {{uniform(0.1, 0.33)}}
    maxSegmentsPerCell = {{quniform(32, 66, 2)}}
    permanenceDec = {{uniform(0.01, 0.2)}}
    weekend_width = {{quniform(30, 150, 2)}}
    weekend_width = int(1+weekend_width)
    timeOfDay_width = {{quniform(16, 201, 2)}}
    timeOfDay_width = int(1 + timeOfDay_width)
    dayOfWeek_width = {{quniform(20, 201, 2)}}
    dayOfWeek_width = int(1 + dayOfWeek_width)
    # must always be odd
    holiday_width = {{quniform(16,201,2)}}
    holiday_width = int(1 + holiday_width)
    dayOfWeek_radius = {{uniform(6, 15)}}
    timeOfDay_radius = {{uniform(6, 15)}}
    weekend_radius = {{uniform(6, 15)}}
    params = {
        "aggregationInfo": {
            "hours": 0,
            "microseconds": 0,
            "seconds": 0,
            "fields": [],
            "weeks": 0,
            "months": 0,
            "minutes": 0,
            "days": 0,
            "milliseconds": 0,
            "years": 0
        },
        "model": "HTMPrediction",
        "version": 1,
        "predictAheadTime": null,
        "modelParams": {
            "sensorParams": {
                "verbosity": 0,
                "encoders": {
                    "datetime_weekend": {
                        'fieldname': 'datetime',
                        'name': 'datetime_weekend',
                        'weekend': (weekend_width, weekend_radius),
                        'type': 'DateEncoder'
                    },
                    "datetime_timeOfDay": {
                        'fieldname': 'datetime',
                        'name': 'datetime_timeOfDay',
                        'type': 'DateEncoder',
                        'timeOfDay': (timeOfDay_width, timeOfDay_radius)
                    },
                    "datetime_dayOfWeek": {
                        'fieldname': 'datetime',
                        'name': 'datetime_dayOfWeek',
                        'type': 'DateEncoder',
                        'dayOfWeek': (dayOfWeek_width, dayOfWeek_radius)
                    },
                    "datetime_holiday": {
                        'fieldname': 'datetime',
                        'name': 'datetime_holiday',
                        'type': 'DateEncoder',
                        'holiday': holiday_width,
                        'holidays': [d.timetuple()[:3] for d in holidays]
                    },
                    "flow": {
                        'fieldname': "flow",
                        'name': 'flow',
                        'type': 'RandomDistributedScalarEncoder',
                        'resolution': max(0.001, (max_flow - 1) / flow_buckets)
                    }
                },

                "sensorAutoReset": null
            },
            "anomalyParams": {
                "anomalyCacheRecords": null,
                "autoDetectThreshold": null,
                "autoDetectWaitRecords": null
            },
            "spParams": {
                "columnCount": columnCount,
                "spVerbosity": 0,
                "spatialImp": "cpp",
                "synPermConnected": synPermConnected,
                "seed": 1956,
                "numActiveColumnsPerInhArea": int(activeColumns),
                "globalInhibition": 1,
                "inputWidth": 0,
                "synPermInactiveDec": synPermInactiveDec,
                "synPermActiveInc": synPermActiveInc,
                "potentialPct": potentialPct,
                "boostStrength": boost
            },
            "spEnable": true,
            "clEnable": true,
            "clParams": {
                "alpha": alpha,
                "verbosity": 0,
                "steps": "1",
                "regionName": "SDRClassifierRegion"
            },
            "inferenceType": "TemporalMultiStep",
            "trainSPNetOnlyIfRequested": false,
            "tmParams": {
                "columnCount": columnCount,
                "activationThreshold": int(activationThreshold),
                "pamLength": int(pamLength),
                "cellsPerColumn": int(cellsPerColumn),
                "permanenceInc": tmPermanenceInc,
                "minThreshold": int(minThreshold),
                "verbosity": 0,
                "maxSynapsesPerSegment": int(maxSynapsesPerSegment),
                "outputType": "normal",
                "initialPerm": initialPerm,
                "globalDecay": 0.0,
                "maxAge": 0,
                "permanenceDec": permanenceDec,
                "seed": 1960,
                "newSynapseCount": int(newSynapseCount),
                "maxSegmentsPerCell": int(maxSegmentsPerCell),
                "temporalImp": "cpp",
                "inputWidth": columnCount
            },
            "tmEnable": true
        }
    }
    #    print(json.dumps(params, indent=4))
    start = datetime.now()
    model = ModelFactory.create(params)
    model.enableInference({'predictedField': 'flow'})
    model.enableLearning()

    actualDict = {}
    predictionsDict = {}
    for row in tqdm(rows, desc='HTM '):
        actualDict[row['datetime']] = row['flow']
        future_time = row['datetime'] + timedelta(minutes=5)
        predictionsDict[future_time] = model.run(row).inferences['multiStepBestPredictions'][1]

    actual_x = []
    actual_y = []
    pred_y = []
    pred_x = []
    error_scores = []
    error_scores_x = []
    # now make a good set to evaluate

    for x,y in sorted(actualDict.items()):
        if x in predictionsDict:
            actual_y.append(y)
            actual_x.append(x)
            pred_x.append(x)
            pred_y.append(predictionsDict[x])


    # make a plot
    def npa(l):
        return np.array(l)
    split_idx = int(len(actual_y) * 0.6)
    npactual_y = npa(actual_y[split_idx:])
    nppred_y = npa(pred_y[split_idx:])


    # calculate a running error score on the last 500 predictions
    lb = 100
    for idx, i in enumerate(actual_y):
        run_actual = np.array(actual_y[max(0, idx-lb):idx+1])
        run_pred = np.array(pred_y[max(0, idx-lb):idx+1])
        error_scores.append(rmse(run_actual, run_pred))
        error_scores_x.append(actual_x[idx])

    metric_results = {
        'rmse': rmse(npactual_y, nppred_y),
        'mgeh': geh(npactual_y, nppred_y),
        'duration': (datetime.now() - start).total_seconds()
    }
    dpi = 80
    width = 1920 / dpi
    height = 1080 / dpi
    plt.figure(figsize=(width, height), dpi=dpi)
    plt.plot(actual_x, actual_y, color='b', label='Actual')
    plt.plot(pred_x, pred_y, color='r', label='Predictions')
    plt.plot(error_scores_x, error_scores, color='g', label='Error')
    plt.legend()
    plt.title("HTM Predictions at 115, SI 2: {}".format(metric_results['rmse']))
    plt.xlabel('Time')
    plt.ylabel('Flow')
    fig_name = 'model_{}.png'.format(time())
    plt.savefig(fig_name)
    plt.show()
    with open(fig_name, 'rb') as img_file:
        fig_b64 = base64.b64encode(img_file.read()).decode('ascii')

    print("RMSE: {} GEH:{} in {}s".format(*metric_results.values()))

    return {
        'loss': metric_results['rmse'],
        'status': STATUS_OK,
        'model': params,
        'metrics': metric_results,
        'figure': fig_b64
    }


if __name__ == '__main__':
    # trials = Trials()
    import sys

    trials = mongoexp.MongoTrials(sys.argv[1], exp_key='htm_115_2_rmse_loss_holidays')
    # data()
    import json

    # try:
    best_run, best_model = optim.minimize(model=create_model,
                                          data=data,
                                          algo=tpe.suggest,
                                          max_evals=200,
                                          trials=trials)
    print("Best performing model chosen hyper-parameters:")

    print(best_run)
    print(json_util.dumps(best_model, indent=4))
    # except Exception as e:
    #     print("Error", e.message)
    #     print(json_util.dumps(list(trials), indent=4))

    # for i in trials:
    #     print(json.dumps(i, indent=4))
