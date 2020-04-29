# Created by lynn at 2019/01/11

"""
Get text from xml
"""
import re


def get_xml_texts(filename):
    pattern = re.compile(r'<(.*)>([\w|\s|\d]+)</(.*)>')
    for line in open(filename):
        if pattern.findall(line):
            print(pattern.findall(line))


if __name__ == '__main__':
    filename = "62364651.xml"
    get_xml_texts(filename)
