import pandas as pd
import matplotlib.pyplot as plt
import os
from collections import Counter, defaultdict
import numpy as np

class MarkovModel:
    def __init__(self, order=3):
        self.order = order
        self.states = defaultdict(Counter)

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
        """
        Learn the probability distribution from a sequence
        """
        for i in range(len(vals) - self.order):
            history, flow = tuple(vals[i:i + self.order]), vals[i + self.order]
            # print(history, "\\rightarrow", flow, '\\\\')
            self.states[history][flow] += 1
if __name__ == "__main__":
    sm_fname = '~/Dropbox/PhD/htm_models_adelaide/engine/markov_model/115_2_sm_flow.pkl'
    sm = pd.read_pickle(os.path.expanduser(sm_fname))
    print(Counter(sm))
    plot = sm.hist(bins=range(35), align='left')
    plot.set_xticks(range(35))
    plot.set_title('Histogram of per phase Flow Counts at TS115')
    plot.set_xlabel('Flow')
    plot.set_ylabel('Count')
    plt.show()
    m = MarkovModel(order=2)
    m.learn(sm.values)
