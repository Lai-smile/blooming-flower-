# Created by mqgao at 2018/10/22

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File Location: # Enter

"""

import sys; sys.setrecursionlimit(10000)
import importlib.util
import platform


def flatten(iterables, outter_type=list):
    if not isinstance(iterables, outter_type):
        return [iterables]
    elif len(iterables) < 1:
        return []
    else:
        return flatten(iterables[0], outter_type) + flatten(iterables[1:], outter_type)


def arg_first(iterables, pred):
    for index, element in enumerate(iterables):
        if pred(element):
            return index, element
    return None, None


def mapper_arg_first(mapper, arg):
    # the mapper is the map rules of a [(predicate, result)]
    for index, (predicate, result) in enumerate(mapper):
        if predicate(arg):
            return index, (predicate, result)
    return None, (None, None)


def split_by_nonalpha(string):
    if len(string) < 1:
        return []
    index, value = arg_first(string, lambda x: x.isalpha() != string[0].isalpha())

    if index:
        return [string[:index]] + split_by_nonalpha(string[index:])
    else:
        return [string]


def get_running_system():
    if platform.system() == 'Linux':
        return 'Linux'
    if platform.system() == 'Windows':
        return 'Windows'
    if platform.system() == 'Darwin':
        return 'Darwin'


def is_linux():
    return get_running_system() == 'Linux'


assert split_by_nonalpha('ab.ab..') == ['ab', '.', 'ab', '..']
assert split_by_nonalpha('ababa**jklX。我真是。生气。。') == \
        ['ababa', '**', 'jklX', '。', '我真是', '。', '生气', '。。']
