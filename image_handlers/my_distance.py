# Created by lixingxing at 2018/11/29

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File LocationL: # Enter

"""


def manhattan_distance(x, y):
    return abs(x[0] - y[0]) + abs(x[1] - y[1])


def hamming_distance(x, y):
    return bin(x ^ y).count('1')
