#!/usr/bin/env python
from __future__ import print_function
import matplotlib
from matplotlib import cm
from nupic.algorithms import anomaly_likelihood
from pluck import pluck

matplotlib.rcParams['date.autoformatter.day'] = '%A %b %d %Y'
matplotlib.use('QT4agg')
from nupic.frameworks.opf.model_factory import ModelFactory
from tqdm import tqdm
from datetime import datetime, timedelta
import cPickle as pickle
import json
import numpy as np
import matplotlib.pyplot as plt
import logging
import yaml
from pymongo import MongoClient
import os
from scipy import stats
import subprocess
import tabulate

logging.basicConfig()
eps = 1e-7
with open('../../connection.yaml', 'r') as infile:
    conf = yaml.load(infile)
    mongo_uri = conf['mongo_uri']


def get_rows_sp(fname):
    p = subprocess.Popen(['zcat', fname], stdout=subprocess.PIPE)
    return pickle.load(p.stdout)


def data():
    cdir = os.path.dirname(os.path.realpath(__file__))
    pkl_fname = cdir + '/swarm_data/115_2_1_2_3_4_swarm.pkl.gz'
    rows = get_rows_sp(pkl_fname)
    return rows


class Model:
    def __init__(self, lb, func):
        self.lb = lb
        self.func = func

    def __repr__(self):
        return "<Model lb={} func={}>".format(self.lb, self.func.__name__)

    def predict(self, row, dataDict):
        # try to get the previous 3 rows and take their average
        dt = row['datetime']
        data = [row['flow']]
        for i in range(1, self.lb + 1):
            val = dataDict.get(dt - timedelta(minutes=-5 * i), None)
            if val is not None:
                data.append(val)
        return self.func(data) + eps


def create_model():
    def rmse(y_true, y_pred, axis=0):
        return np.sqrt(((y_pred - y_true) ** 2).mean(axis=axis))

    def geh(y_true, y_pred, axis=0):
        return np.sqrt(2 * np.power(y_pred - y_true, 2) / (y_pred + y_true)).mean(axis=axis)
        # make a plot

    def npa(l):
        return np.array(l)

    rows = data()
    actualDict = {}
    actual_x = []
    actual_y = []
    # pred_x = []
    for r in rows:
        actualDict[r['datetime']] = r['flow']
        actual_x.append(r['datetime'])
        actual_y.append(r['flow'])
    predictionsDict = {}

    def lingress(rows):
        slope, intercept, rval, pval, err = stats.linregress(range(len(rows)), rows)
        return max(0, ((len(rows) + 1) * slope) + intercept)

    split_idx = int(len(actual_y) * 0.6)
    npactual_y = npa(actual_y[split_idx:]) + eps
    models = {Model(lb, func): {'px': [], 'py': []} for lb in range(1, 10) for func in [np.mean, np.median, lingress]}
    colors = cm.rainbow(np.linspace(0, 1, len(models)))
    it = iter(colors)
    for model, preds in models.items():
        for row in tqdm(rows, desc=repr(model)):
            dt = row['datetime']
            actualDict[dt] = row['flow']
            future_time = dt + timedelta(minutes=5)
            pred = model.predict(row, actualDict)
            predictionsDict[future_time] = pred
            preds['px'].append(future_time)
            preds['py'].append(pred)

        # calculate a running error score on the last 500 predictions
        lb = 50
        error_scores = []
        error_scores_x = []
        for idx, i in enumerate(actual_y):
            run_actual = np.array(actual_y[max(0, idx - lb):idx + 1])
            run_pred = np.array(preds['py'][max(0, idx - lb):idx + 1])
            error_scores.append(rmse(run_actual, run_pred))
            error_scores_x.append(actual_x[idx])
        c = next(it)
        # plt.plot(error_scores_x, error_scores, color=c, label='Error {}'.format(model))
        plt.plot(preds['px'], preds['py'], color=c, label='Pred {}'.format(model))
        nppred_y = npa(preds['py'][split_idx:]) + eps
        metric_results = {
            'model': repr(model),
            'rmse': rmse(npactual_y, nppred_y),
            'mgeh': geh(npactual_y, nppred_y),
        }
        models[model]['results'] = metric_results
        print("\n", model, ": ", metric_results)

    plt.plot(actual_x, actual_y, color='b', label='Actual')

    plt.xticks(rotation=20)
    plt.legend()

    plt.ylim(0, 360)
    plt.xlim(actual_x[0], actual_x[-1])
    plt.title("Dumb Predictions at 115, SI 2")
    plt.xlabel('Time')
    plt.ylabel('Flow')

    # print("RMSE: {} GEH:{}".format(*metric_results.values()))
    print(tabulate.tabulate(pluck(models.values(), 'results'), headers='keys'))
    plt.show()


if __name__ == '__main__':
    create_model()
