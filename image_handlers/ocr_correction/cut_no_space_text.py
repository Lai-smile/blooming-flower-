# Created by lixingxing at 2019/2/19

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File LocationL: # Enter

"""

import numpy as np
from image_handlers.ocr_correction.correct_eng_words import clean_words_in_dict, correction


def best_match(i, text):
    candidates = enumerate(reversed(cost[max(0, i - max_word):i]))
    _pick_me = []
    for k, cost_pr in candidates:
        _pick_me.append((cost_pr + word_cost.get(correction(text[i - k - 1:i]), 9e999), k + 1))
    cost_pr, k = min(tuple(_pick_me))
    return cost_pr, k


def segment_correct_text(text):
    global word_cost
    global max_word
    global cost

    cleaned_text = clean_words_in_dict()
    word_cost = dict((k, np.log((i + 1) * np.log(len(cleaned_text)))) for i, k in enumerate(cleaned_text))
    max_word = max(len(x) for x in cleaned_text)
    cost = [0]

    for i in range(1, len(text) + 1):
        c, k = best_match(i, text)
        cost.append(c)

    out = []
    i = len(text)
    while i > 0:
        c, k = best_match(i, text)
        assert c == cost[i]
        out.append(correction(text[i - k:i]))
        i -= k

    final = " ".join(reversed(out))
    return final


if __name__ == '__main__':
    import time
    start_time = time.time()
    sg = segment_correct_text('dataorprodurtion')
    time_cost = time.time() - start_time
    print(sg)
    print('_______time_cost: {}s______'.format(time_cost))
