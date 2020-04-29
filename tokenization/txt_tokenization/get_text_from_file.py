# Created by mqgao at 2018/12/26

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File Location: # Enter

"""

import chardet


def get_file_encoding(filename):
    raw_data = open(filename, 'rb').read()
    return chardet.detect(raw_data)['encoding']


def get_texts(filename):
    encoding = get_file_encoding(filename)
    lines = []
    with open(filename, encoding=encoding, errors='ignore') as f:
        for y, line in enumerate(f):
            lines.append((0, 0, y, 0, 0, line))

    return lines


if __name__ == '__main__':
    for line in get_texts('/Users/mqgao/Downloads/hikvision.txt'):
        print(line)
