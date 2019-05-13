from dask.distributed import Client
from tabulate import tabulate
from collections import defaultdict, Counter
from datetime import datetime
import os

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
                yield self.gen(history), None
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
                yield None, x
            self.states[history][flow] += 1


def do_model(args):
    fname, order, scheme = args
    vs_df = pd.read_pickle(os.path.expanduser(fname))
    start = datetime.now()
    tail_idx = int(len(vs_df) * 0.4)
    vs_model = MarkovModel(order=order, missing_scheme=scheme, learn_split_at=len(vs_df) - tail_idx)
    preds = pd.DataFrame([(None, None)] + [p for p in vs_model.learn(vs_df.measured_flow.values)] + (
            [(None, None)] * (vs_model.order - 1)), columns=['markov_pred_actual', 'markov_pred_miss'])
    vs_df['markov_pred'] = preds.markov_pred_actual.fillna(preds.markov_pred_miss)
    vs_df = vs_df.join(preds).drop(['phase_time'], axis=1).set_index('datetime')

    vs_df = vs_df.tail(tail_idx)  # only evaluate last 40% of predictions
    vs_df.dropna(subset=['markov_pred'], inplace=True)

    return order, (datetime.now() - start).total_seconds(), len(
        vs_df), vs_model.missing_count_during_learning, round(
        float(vs_model.missing_count_during_learning) / len(vs_df) * 100, 3), scheme_names[scheme], (
                   (vs_df['markov_pred'] - vs_df.measured_flow) ** 2).mean() ** .5, vs_df


if __name__ == "__main__":
    fname = '~/Dropbox/PhD/htm_models_adelaide/engine/markov_model/115_2_sm.pkl'
    args = []
    # res = do_model((fname, 6, SCHEME_MEAN))
    # res2 = do_model((fname, 3, SCHEME_MEDIAN))
    # print(res[:-1])
    # exit()
    client = Client('10.27.41.41:8786')
    for scheme in scheme_names:
        for order in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            args.append((fname, order, scheme))

    futures = client.map(do_model, args, retries=5)

    results = client.gather(futures)
    results.sort(key=lambda x: x[6])
    print(tabulate([x[:-1] for x in results], headers=['Order', 'Time', 'Rows', 'Missing', 'Missing %', 'Scheme', 'RMSE']))
