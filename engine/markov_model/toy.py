from collections import defaultdict, Counter

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
        print(vals, len(vals), len(vals) - self.order)
        for i in range(len(vals) - self.order):
            history, flow = tuple(vals[i:i + self.order]), vals[i + self.order]
            print(history, '\\rightarrow', flow,'\\\\')
            # yield self.gen(history)
            self.states[history][flow] += 1


if __name__ == "__main__":
    vals = [1, 2, 3, 1, 2, 1, 2, 3]
    m = MarkovModel(2)
    m.learn(vals)
    for s, t in m.states.items():
        probs = [(n,t[n]/sum(t.values())) for n in t]
        print(s,probs)