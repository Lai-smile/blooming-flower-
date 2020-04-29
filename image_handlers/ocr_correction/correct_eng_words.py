# Created by lixingxing at 2019/2/19

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File LocationL: # Enter

"""
import os
import re
from collections import Counter
from path import root

DICT_PATH = os.path.join(root, 'image_handlers', 'ocr_correction', 'data', 'big.txt')


def clean_words_in_dict():
    #     print(text.split(' '))
    file = open(DICT_PATH, encoding='utf-8')
    text = file.read()
    clean_text = re.findall(r'[a-zA-Z0-9/.]+', text.lower())
    file.close()
    return clean_text


WORDS = Counter(clean_words_in_dict())


def p_x(word, total_count=sum(WORDS.values())):
    return WORDS[word] / total_count


def checker(words):
    return set(w for w in words if w in WORDS)


def edits1(word):
    letters = 'abcdefghijklmnopqrstuvwxyz'
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    deletes = [L + R[1:] for L, R in splits if R]
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
    replaces = [L + c + R[1:] for L, R in splits if R for c in letters]
    inserts = [L + c + R for L, R in splits for c in letters]
    return set(deletes + transposes + replaces + inserts)


def edits2(word):
    return set(e2 for e1 in edits1(word) for e2 in edits1(e1))


def candidates(word):
    can = (checker([word]) or checker(edits1(word)) or checker(edits2(word)) or [word])
    return can


def correction(word):
    return max(candidates(word), key=p_x)
