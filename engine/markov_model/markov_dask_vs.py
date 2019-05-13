from dask.distributed import Client
from tabulate import tabulate
import matplotlib.pyplot as plt
import gzip
from collections import defaultdict, Counter
from datetime import datetime
import os

import pickle
import pandas as pd
import numpy as np

SCHEME_LAST = 1
SCHEME_RAND = 2
SCHEME_MEAN = 3
SCHEME_MEDIAN = 4

scheme_names = {
    SCHEME_LAST: 'LAST',
    SCHEME_RAND: 'RAND',
    SCHEME_MEAN: 'MEAN',
    SCHEME_MEDIAN: 'MEDIAN'
}


class MarkovModel:
    def __init__(self, order=3, missing_scheme=SCHEME_LAST, learn_split_at=-1):
        self.order = order
        self.states = defaultdict(Counter)
        self.missing_scheme = missing_scheme
        self.missing_count = 0
        self.missing_count_during_learning = 0
        self.learn_split_at = learn_split_at

    def gen(self, history):
        """
        Based on a history, generate a prediction for next step
        :param history:
        :return:
        """
        node = self.states[history]
        keys = np.array(list(node.keys()))
        counts = np.array(list(node.values()))
        ps = counts / counts.sum()
        return np.random.choice(keys, p=ps)

    def learn(self, vals):
        for i in range(len(vals) - self.order):
            history, flow = tuple(vals[i:i + self.order]), vals[i + self.order]
            try:
                x = self.gen(history)
            except Exception as e:
                self.missing_count += 1
                if i >= self.learn_split_at:
                    self.missing_count_during_learning += 1
                if self.missing_scheme == SCHEME_LAST:
                    x = history[-1]
                elif self.missing_scheme == SCHEME_RAND:
                    x = np.random.choice(history)
                elif self.missing_scheme == SCHEME_MEAN:
                    x = np.mean(history)
                elif self.missing_scheme == SCHEME_MEDIAN:
                    x = np.median(history)
            yield x
            self.states[history][flow] += 1


def do_model(args):
    fname, bins, order, scheme = args
    with gzip.open(os.path.expanduser(fname),
                   'rb') as infile:
        data_vs = pickle.load(infile)

    vs_df = pd.DataFrame(data_vs)
    vs_df.set_index('datetime', inplace=True)

    start = datetime.now()
    vs_df['binned_flow'] = [round(r.mid, 4) for r in pd.cut(vs_df.flow, bins=bins)]
    tail_idx = int(len(vs_df) * 0.4)
    vs_model = MarkovModel(order=order, missing_scheme=scheme, learn_split_at=len(vs_df) - tail_idx)
    preds = [None] + [p for p in vs_model.learn(vs_df.binned_flow.values)] + ([None] * (vs_model.order - 1))
    vs_df['markov_pred'] = preds
    vs_df = vs_df.tail(tail_idx)  # only evaluate last 40% of predictions
    vs_df.dropna(subset=['markov_pred'], inplace=True)

    return bins, order, (datetime.now() - start).total_seconds(), len(
        vs_df), vs_model.missing_count_during_learning, round(
        float(vs_model.missing_count_during_learning) / len(vs_df) * 100, 3), scheme_names[scheme], (
                   (vs_df['markov_pred'] - vs_df['flow']) ** 2).mean() ** .5, vs_df


if __name__ == "__main__":

    # client = Client('10.27.41.41:8786')
    #
    fname = '~/Dropbox/PhD/htm_models_adelaide/engine/vs_model/swarm_data/115_2_1_2_3_4_swarm.pkl.gz'
    args = []
    bins = 200
    order = 3
    fallback = SCHEME_MEAN
    res = (do_model((fname, bins, order, fallback)))
    df = res[-1]
    ax = df.drop(columns=['binned_flow']).plot(title=f'Markov Model (order {order}, {bins} bins, {fallback} fallback) Predictions on VS Data')
    ax.set_xlabel('Datetime')
    ax.set_ylabel('Flow')
    plt.show()
    # for scheme in scheme_names:
    #     for b in range(10, 200, 5):
    #         for order in [1, 2, 3, 4, 5, 6, 7]:
    #             args.append((fname, b, order, scheme))

    # futures = client.map(do_model, args, retries=5)
    #
    # results = client.gather(futures)
    # results.sort(key=lambda x: x[-1])
    # print(tabulate(results, headers=['Bins', 'Order', 'Time', 'Rows', 'Missing', 'Missing %', 'Scheme', 'RMSE']))
