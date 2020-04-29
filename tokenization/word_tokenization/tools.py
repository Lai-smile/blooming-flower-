# Created by mqgao at 2018/12/26

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File Location: # Enter

"""
import os
import time
from utilities.path import root, get_file_absolute_path


def get_output_dir():
    tmp_dir = os.path.join(root, 'tokenization', 'word_tokenization', 'tmp')
    assert os.path.exists(tmp_dir), 'output dir: {} is not exist'.format(tmp_dir)
    return os.path.abspath(tmp_dir)


def get_output_filename(filename):
    filename = filename.split('/')[-1]
    assert filename.endswith('.doc'), 'this is not a word 2003 file'
    filename = filename[:-len('.doc')] + '.docx'
    return os.path.join(get_output_dir(), filename)


def convert_doc_to_docx(filename):
    cmd = "soffice --headless --convert-to docx --outdir {} {}".format(get_output_dir(),
                                                                       get_file_absolute_path(filename))
    os.popen(cmd)

    new_file_name = get_output_filename(filename)

    for i in range(15):  # max waiting time is 15 * 0.2 = 3 seconds
        if os.path.exists(new_file_name):
            break
        else:
            time.sleep(0.0001)
    else:
        return None

    return new_file_name


if __name__ == '__main__':
    file_name = convert_doc_to_docx(
        '/Users/mqgao/Documents/Documents-IBM-MacPro/IBM工作文档/兴森快捷/ten-tests/解压包/(0.575平米) 06-16 15 6S0060U7A0 (1)/M_INT00150 VA_Õ‚–≠º”π§µ•.doc')

    assert os.path.exists(file_name)
