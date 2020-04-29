# Created by lixingxing at 2018/11/29

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File LocationL: # Enter

"""
from pybktree import BKTree

# def manhattan_distance(x, y):
#     return abs(x[0] - y[0]) + abs(x[1] - y[1])
#
#
# class MyBKTree(BKTree):
#     def __init__(self, distance_function):
#         super().__init__(self, distance_function)
from image_handlers.my_distance import manhattan_distance

if __name__ == '__main__':
    a = [(1, 1), (2, 2), (3, 3)]
    my_bk = BKTree(manhattan_distance, a)
    c = my_bk.find((0, 0), 3)
    print(c)
