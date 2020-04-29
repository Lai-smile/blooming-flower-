# Created by lixingxing at 2019/3/1

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File LocationL: # Enter

"""
import os

import pandas as pd

from utilities.path import root
import pickle


shape_dict_path = '/Users/lixingxing/IBM/reference/PCB_standard/cn_sm_words.txt'
shape_dict_save_path = os.path.join(root, 'image_handlers', 'ocr_correction')
sm_words = pd.read_csv(shape_dict_path, sep='\t', header=None)
sm_word_dict = {}
# for i in sm_words.values.tolist():
for sm_word in sm_words.values.tolist():
    item = sm_word[0].split(' ')
    sm_word_dict[item[0]] = item[1]
# print(sm_word_dict)
with open('shape_sm_dict.pkl', 'wb') as f:
    pickle.dump(sm_word_dict, f)
