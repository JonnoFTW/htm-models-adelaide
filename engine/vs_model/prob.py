import sys
import numba
from datetime import datetime
from fractions import Fraction
import numpy as np


@numba.jit
def prime_factors(n):
    """
    Returns the set of prime factors of n using trial division
    :param n:
    :return:
    """
    s = set()
    i = n
    d = 2
    while i != 1:
        quot, rem = divmod(i, d)
        if rem == 0:
            s.add(d)
            i = quot
        else:
            d += 1
    return s


def totient(n):
    """
    Calculate the number of numbers < d that are coprime to d
    :param n:
    :return:
    """
    total = n
    for p in prime_factors(n):
        total *= 1 - (1./ p)
    return total

import tqdm
def solve2(d):
    total = 0
    for i in tqdm.tqdm(range(2, d + 1)):
        total += totient(i)
    return total


if __name__ == "__main__":
    d = 1000000
    # for i in [100, 76, 50, 48, 36, 20, 10]:
    #     print(i, prime_factors(i))
    start = datetime.now()
    print(solve2(d))
    print("Took {}".format(datetime.now() - start))
