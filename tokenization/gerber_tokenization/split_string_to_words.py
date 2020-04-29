# Created by mqgao at 2019/1/23

"""
Split the string into single tokens:

such as:
    split("thisisatest") => 'this is a tests'
"""

from utilities.path import root
import os
from math import log

# Build a cost dictionary, assuming Zipf's law and cost = -math.log(probability).
words_by_frequency = os.path.join(root, 'tokenization', 'gerber_tokenization', 'data', '125k_sort_with_fre.txt')
words = open(words_by_frequency).read().split()
wordcost = dict((k, log((i + 1) * log(len(words)))) for i, k in enumerate(words))
maxword = max(len(x) for x in words)


def infer_spaces(s):
    """Uses dynamic programming to infer the location of spaces in a string
    without spaces."""

    # Find the best match for the i first characters, assuming cost has
    # been built for the i-1 first characters.
    # Returns a pair (match_cost, match_length).
    def best_match(i):
        candidates = enumerate(reversed(cost[max(0, i - maxword):i]))
        return min((c + wordcost.get(s[i - k - 1:i], 9e999), k + 1) for k, c in candidates)

    # Build the cost array.
    cost = [0]
    for i in range(1, len(s) + 1):
        c, k = best_match(i)
        cost.append(c)

    # Backtrack to recover the minimal-cost string.
    out = []
    i = len(s)
    while i > 0:
        c, k = best_match(i)
        assert c == cost[i]
        out.append(s[i - k:i])
        i -= k

    return " ".join(reversed(out))


if __name__ == '__main__':
    print(infer_spaces('5ohesoltholetoleranceisassameastheelliticalhole'))
