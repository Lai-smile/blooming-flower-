# Created by hudiibm at 2018/12/27
"""
Feature: #Enter feature name here
# Enter feature description here
Scenario: #Enter scenario name here
# Enter steps here
Test File Location: # Enter]
"""
import numpy as np
import os
from gensim.models import KeyedVectors
from constants import path_manager as P
from constants.constants import model_name, en_model_name
from utilities.txt_utilities import have_chinese_, stemmer

model_path = os.path.join(P.WV_MODELS_PATH, model_name, 'model.vec')
model = KeyedVectors.load_word2vec_format(model_path)

en_model_path = os.path.join(P.WV_MODELS_PATH, en_model_name, 'model.vec')
en_model = KeyedVectors.load_word2vec_format(en_model_path)

import jieba


# jieba.load_userdict(P.JIEBA_USER_DICT)


def normalization(array):
    return array / sum(array ** 2) ** (1 / 2)


def param2vect(param, analysis=False):
    assert type(param) == str

    def add_words_vict_up(word_list, model):
        vector = np.zeros(300)
        for i in [word for word in word_list if word]:
            try:
                vector += model[i]
                if analysis: print('get the word：', i)
            except KeyError:
                np.random.seed(ord(i[0]))
                vector += normalization(np.random.rand(300) - 0.5)
                if analysis: print('dont know word：', i)
        if sum(vector) == 0:
            return vector
        else:
            return normalization(vector)

    if have_chinese_(param):
        if analysis: print('Use Chinese model')
        words = jieba.cut(param)
        return add_words_vict_up(words, model)

    else:
        if analysis: print('Use English model')
        param = stemmer(param)
        words = param.split(' ')
        return add_words_vict_up(words, en_model)


def similarity(v1, v2):
    return sum(v1 * v2)
