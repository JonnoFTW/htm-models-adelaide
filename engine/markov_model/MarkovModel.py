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
    def __init__(self, order=3, missing_scheme=SCHEME_LAST):
        self.order = order
        self.states = defaultdict(Counter)
        self.missing_scheme = missing_scheme
        self.missing_count = 0

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
                yield self.gen(history)
            except:
                self.missing_count += 1
                if self.missing_scheme == SCHEME_LAST:
                    yield history[-1]
                elif self.missing_scheme == SCHEME_RAND:
                    yield np.random.choice(history)
                elif self.missing_scheme == SCHEME_MEAN:
                    yield np.mean(history)
                elif self.missing_scheme == SCHEME_MEDIAN:
                    yield np.median(history)
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

    vs_model = MarkovModel(order=order, missing_scheme=scheme)

    preds = [None] + [p for p in vs_model.learn(vs_df.binned_flow.values)] + ([None] * (vs_model.order - 1))
    vs_df['markov_pred'] = preds
    vs_df.dropna(subset=['markov_pred'], inplace=True)
    vs_df = vs_df.tail(int(len(vs_df) * 0.4))  # only evaluate last 40% of predictions

    return bins, order, (datetime.now() - start).total_seconds(), len(vs_df), vs_model.missing_count, float(
        vs_model.missing_count) / len(vs_df), scheme_names[scheme], (
                   (vs_df['markov_pred'] - vs_df['flow']) ** 2).mean() ** .5
