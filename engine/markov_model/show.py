import numpy as np

from collections import defaultdict, Counter


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
    vals = [1, 2, 3, 1, 2, 2, 1, 2, 3]

    m = MarkovModel(2)
    print(m.learn(vals))
