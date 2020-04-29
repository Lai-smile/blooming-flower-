# Created by mqgao at 2018/12/26

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File Location: # Enter

"""

import jieba
import string
from tokenization.token import Token
import re

from utilities.file_utilities import is_excel_file


def all_is_english(line):
    chinese_words = re.findall(r'[\u4e00-\u9fff]+', line)

    return len(chinese_words) == 0


def convert_text_tokens_to_standard_token(text_tokens):
    token = {}

    for t in text_tokens:
        x, y, content = t
        token[(x, y, -1, -1)] = content

    return token


def convert_to_standard_token(text_tokens):
    token = {}

    for t in text_tokens:
        i, x1, y1, x2, y2, content = t
        token[(i, x1, y1, x2, y2)] = content

    return token
