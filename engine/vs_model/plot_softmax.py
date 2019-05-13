import matplotlib.pyplot as plt
import numpy as np
from sklearn.utils.extmath import softmax

if __name__ == "__main__":
    x = np.linspace(-6, 6, 100)
    e = np.exp(x - x.max())

    y = e / e.sum()
    plt.scatter(x,y, label='softmax')

    plt.scatter(x,np.tanh(x), label='tanh')
    plt.legend()
    plt.show()