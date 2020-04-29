# Created by mqgao at 2018/12/26

"""
Get each cell of office excel sheet.

Reference:
1. https://openpyxl.readthedocs.io/en/stable/usage.html#read-an-existing-workbook
2. https://blogs.harvard.edu/rprasad/2014/06/16/reading-excel-with-python-xlrd/

"""

import xlrd
from tokenization.excel_tokenization.get_content_except_image import get_content_web

from utilities.http_utils import postJSON


def get_excel_text_location(filename):
    book = xlrd.open_workbook(filename)
    for sheet in book.sheet_names():
        xl_sheet = book.sheet_by_name(sheet)
        for y in range(xl_sheet.nrows):
            for x in range(xl_sheet.ncols):
                cell_obj = xl_sheet.cell(y, x)
                if cell_obj.value:
                    yield x, y, cell_obj.value


# parse excel old implements by minquan
# def get_excel_texts(filename):
#     return [(x, y, t) for x, y, t in get_excel_text_location(filename)]


# (1, 9, 8, 9, 8):['制板说明', 'Text', '挠性板']
def get_excel_texts(file_name):
    return [(sheet_index, x1, y1, x2, y2, t) for sheet_index, x1, y1, x2, y2, t in get_content_web(file_name)]


def get_excel_texts_remote(file_path):

    # url = "http://192.168.0.108:8888/auto-pcb/api/1.0/parse/excel/text"

    url = "http://0.0.0.0:8888/auto-pcb/api/1.0/parse/excel/text"

    params = {'file_path': file_path}

    result = postJSON(url, params)

    print("get_excel_texts_remote result is {}".format(result))

    return result.text

