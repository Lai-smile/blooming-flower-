# Created by mqgao at 2018/12/26

"""
Get all content from office word.

Reference: https://github.com/ankushshah89/python-docx2txt

"""

import docx2txt
import os
from tokenization.word_tokenization.tools import convert_doc_to_docx
import zipfile


def get_office_word_text(filename, tried_time=0):
    if tried_time > 10:
        return 'Cannot Read this Doc'

    converted = False

    if filename.endswith('.doc'):
        filename = convert_doc_to_docx(filename)
        converted = True

    try:
        if filename:
            text = get_docx_text(filename)
            if converted:
                os.remove(filename)
            return text
        else:
            return None
    except zipfile.BadZipFile:
        print('cannot parse, try one more')
        get_office_word_text(filename, tried_time+1)


def get_docx_text(filename):
    text = docx2txt.process(filename, ".")
    lines = text.split('\n')

    lines = [(0, y, line) for y, line in enumerate(lines)]

    return lines


if __name__ == '__main__':
    file = '/Users/mqgao/PycharmProjects/ParameterExtractor/server_side/tmp/.doc/word1.doc'
    get_office_word_text(file)
