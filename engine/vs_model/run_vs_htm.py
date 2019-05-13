#!/usr/bin/env python
from __future__ import print_function
import matplotlib
from nupic.algorithms import anomaly_likelihood

matplotlib.rcParams['date.autoformatter.day'] = '%A %b %d %Y'
matplotlib.use('QT4agg')
from nupic.frameworks.opf.model_factory import ModelFactory
from tqdm import tqdm
from datetime import datetime, timedelta
import cPickle as pickle
import gzip
import json
import numpy as np
import matplotlib.pyplot as plt
import logging
import yaml
from pymongo import MongoClient
import os
import subprocess
import io

logging.basicConfig()

with open('../../connection.yaml', 'r') as infile:
    conf = yaml.load(infile)
    mongo_uri = conf['mongo_uri']


def get_rows_sp(fname):
    p = subprocess.Popen(['zcat', fname], stdout=subprocess.PIPE)
    return pickle.load(p.stdout)



def data():
    cdir = os.path.dirname(os.path.realpath(__file__))
    pkl_fname = (cdir + '/swarm_data/115_2_1_2_3_4_swarm.pkl.gz')
    print("Starting unpickle data", end='...')
    start = datetime.now()
    rows = get_rows_sp(pkl_fname)
    print("Took {}".format(datetime.now() - start))
    return rows


def create_model():
    def rmse(y_true, y_pred, axis=0):
        return np.sqrt(((y_pred - y_true) ** 2).mean(axis=axis))

    def geh(y_true, y_pred, axis=0):
        return np.sqrt(2 * np.power(y_pred - y_true, 2) / (y_pred + y_true)).mean(axis=axis)

    conn = MongoClient(mongo_uri)
    # best = conn['jobs']['jobs'].find_one({
    #         'exp_key': 'htm_115_2_redo',
    #         'result.status': 'ok',
    #         'result.loss': {'$lte': 11.0},
    #         'result.model.modelParams.spParams.columnCount': 2048,
    #     },
    #     sort=[('result.model.modelParams.clParams.alpha', 1)])
    # best = conn['jobs']['jobs'].find_one({'tid': 3991})
    # best = conn['jobs']['jobs'].find_one({'tid':2178})
    with open('model_0/fast_model.json') as infile:
        best = json.load(infile)
    params = best['result']['model']
    params['modelParams']['inferenceType'] = 'TemporalAnomaly'
    # params['modelParams']['sensorParams']['encoders']['datetime_dayOfWeek']['dayOfWeek'] = [81, 9]
    # params['modelParams']['sensorParams']['encoders']['datetime_timeOfDay']['timeOfDay'] = [161, 9]
    # params['modelParams']['sensorParams']['encoders']['datetime_weekend']['weekend'] = [91, 9]
    # del params['modelParams']['sensorParams']['encoders']['datetime_weekend']
    print(json.dumps(params, indent=4))
    result_fname = 'result_data/htm_{}_115_2_anomaly.pkl'.format(best['tid'])
    if not os.path.exists(result_fname):
        print("Making and evaluating model ", best['tid'])
        rows = data()
        start = datetime.now()
        model = ModelFactory.create(params)
        model.enableInference({'predictedField': 'flow'})
        model.enableLearning()
        anomaly_likelihood_helper = anomaly_likelihood.AnomalyLikelihood(learningPeriod=200, estimationSamples=200, reestimationPeriod=10)
        actualDict = {}
        predictionsDict = {}
        anomalyScores = {}
        for row in tqdm(rows, desc='HTM '):
            dt = row['datetime']
            actualDict[dt] = row['flow']
            future_time = dt + timedelta(minutes=5)
            model_out = model.run(row).inferences
            predictionsDict[future_time] = model_out['multiStepBestPredictions'][1]
            anomaly_score = model_out['anomalyScore']
            anomalyScores[dt] = {
                'score': float(anomaly_score),
                'likelihood': float(anomaly_likelihood_helper.anomalyProbability(row['flow'], anomaly_score,
                                                                           timestamp=row['datetime']))
            }

        actual_x = []
        actual_y = []
        pred_y = []
        pred_x = []
        anomaly_score_y = []
        anomaly_likelihood_y = []
        # now make a good set to evaluate

        for x, y in sorted(actualDict.items()):
            if x in predictionsDict:
                actual_y.append(y)
                actual_x.append(x)
                pred_x.append(x)
                pred_y.append(predictionsDict[x])
                anomaly_score_y.append(anomalyScores[x]['score'])
                anomaly_likelihood_y.append(anomalyScores[x]['likelihood'])

        with open(result_fname, 'wb') as result:
            pickle.dump({
                'model_tid': best['tid'],
                'actual_x': actual_x,
                'actual_y': actual_y,
                'pred_y': pred_y,
                'pred_x': pred_x,
                'anomaly_score': anomaly_score_y,
                'anomaly_likelihood': anomaly_likelihood_y
            }, result)
        pred_rows = []
        for idx, i in enumerate(pred_x):
            pred_rows.append({
                'tid': best['tid'],
                'site_no': '115',
                'strategic_input': '2',
                'datetime': i,
                'actual': int(actualDict[i]),
                'prediction': float(predictionsDict[i]),
                'anomaly': anomalyScores[i]
            })
        # conn['mack0242']['scats_readings_predictions'].delete_many({'site_no': '115', 'strategic_input': '2'})
        # conn['mack0242']['scats_readings_predictions'].insert_many(pred_rows)
    else:
        print("Using cached results")

        with open(result_fname, 'rb') as result:
            obj = pickle.load(result)

        actual_x = obj['actual_x']
        actual_y = obj['actual_y']
        pred_x = obj['pred_x']
        pred_y = obj['pred_y']
        anomaly_score_y = obj['anomaly_score']
        anomaly_likelihood_y = obj['anomaly_likelihood']
    # calculate a running error score on the last 500 predictions
    lb = 50
    error_scores = []
    error_scores_x = []
    for idx, i in enumerate(actual_y):
        run_actual = np.array(actual_y[max(0, idx - lb):idx + 1])
        run_pred = np.array(pred_y[max(0, idx - lb):idx + 1])
        error_scores.append(rmse(run_actual, run_pred))
        error_scores_x.append(actual_x[idx])

    # make a plot
    def npa(l):
        return np.array(l)

    split_idx = int(len(actual_y) * 0.6)
    npactual_y = npa(actual_y[split_idx:])
    nppred_y = npa(pred_y[split_idx:])
    metric_results = {
        'rmse': rmse(npactual_y, nppred_y),
        'mgeh': geh(npactual_y, nppred_y),

    }

    import matplotlib.gridspec as gridspec
    gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1])
    fig = plt.figure()
    main_plot = fig.add_subplot(gs[0, 0])

    plt.plot(actual_x, actual_y, color='b', label='Actual')
    plt.plot(pred_x, pred_y, color='r', label='Predictions')
    plt.plot(error_scores_x, error_scores, color='g', label='Error')
    plt.xticks(rotation=20)
    plt.legend()
    main_plot.axes.set_ylim(0, 360)
    main_plot.axes.set_xlim(actual_x[0], actual_x[-1])
    plt.title("HTM Predictions at 115, SI 2".format(metric_results['rmse']))
    plt.xlabel('Time')
    plt.ylabel('Flow')

    anomaly_plot = fig.add_subplot(gs[1])
    plt.xlabel('Percentage')
    plt.ylabel('Date')
    anomalyRange = (0.0, 1.0)
    anomaly_plot.axes.set_ylim(anomalyRange)
    anomaly_plot.plot(actual_x, anomaly_likelihood_y, color='m', label='Anomaly Likelihood')
    anomaly_plot.plot(actual_x, anomaly_score_y, color='c', label='Anomaly Score')
    anomaly_plot.axes.set_xlim(actual_x[0], actual_x[-1])
    plt.legend()
    print("RMSE: {} GEH:{}".format(*metric_results.values()))
    plt.show()
    return model



if __name__ == '__main__':
    create_model()
