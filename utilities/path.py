# Created by mqgao at 2018/12/26

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File Location: # Enter

"""
import os
import pathlib

root = pathlib.Path(os.path.abspath(__file__)).parent.parent
save_long_text_path = os.path.join(root, 'long_text_text.csv')


def get_all_files(path, verbose=False):
    """"Gets all files in a directory"""
    if verbose: print(path)

    if not os.path.exists(path): return []
    if os.path.isfile(path): return [path]

    return [f for d in os.listdir(path) for f in get_all_files(os.path.join(path, d), verbose)]


def get_file_absolute_path(filename):
    assert os.path.exists(filename), 'file: {} , not exist'.format(filename)
    return os.path.abspath(filename)
