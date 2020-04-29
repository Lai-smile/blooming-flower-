# Created by mqgao at 2018/12/26

"""
Get text from files. Supported file types contains: doc, docx, xls, xlsx, pdf
"""
from image_handlers.get_texts_from_pure_images import get_image_texts
from tokenization.gm2_tokenization.get_token_from_gm2 import gm2_reader_start
from tokenization.pdf_tokenization.get_text_from_pdf import get_texts_from_pdf
from tokenization.get_text_from_xml import get_xml_texts
from path import get_all_files
from tokenization.txt_tokenization.get_text_from_file import get_texts
from tokenization.pdf_tokenization.get_table_from_pdf import get_pdf_table

import ast
import requests
import uuid
import shutil
import os
import json
import bottle

from constants import API

from file_utilities import get_tmp_file_path
import time
import filecmp
from config.config import config
from log.logger import logger


def get_tokens_texts(filename):
    filepath, tmpfilename = os.path.split(filename)
    if tmpfilename.find('.') == -1:
        ext = 'gm2'
    elif 'fab' in tmpfilename or 'gd1' in tmpfilename:
        ext = 'gm2'
    else:
        ext = filename.split('.')[-1].lower()

    function_mapper = {
        'doc': get_word_tokens,
        'docx': get_word_tokens,
        'xls': get_excel_tokens,
        'xlsx': get_excel_tokens,
        'xlsm': get_excel_tokens,
        'xlsb': get_excel_tokens,
        # 'pdf': get_texts_from_pdf,
        'pdf': get_pdf_table,
        'txt': get_texts,
        'xml': get_xml_texts,
        'png': get_image_texts,
        'jpg': get_image_texts,
        'jpeg': get_image_texts,
        'gm2': gm2_reader_start,
    }

    image_save_path = ''
    if ext in function_mapper:
        if ext == 'gm2':
            text, image_save_path = function_mapper[ext](filename)
        else:
            text = function_mapper[ext](filename)

        if text and not isinstance(text, str):
            return text, image_save_path
        else:
            return [], image_save_path
    else:
        return [], image_save_path


def get_word_tokens(file_path):
    env = bottle.default_app().config.get('env')
    conf = config(env)
    win_server = conf.get('WIN_SERVER')
    url = win_server + API.ROOT + API.VERSION + "/parse_word"

    # _, ext = os.path.splitext(file_path)
    # tmp_file_name = str(uuid.uuid1()) + ext
    #
    # print(tmp_file_name)
    # shutil.copy(file_path, tmp_file_name)
    # with open(tmp_file_name, 'rb') as f:
    #     result = requests.post(url, files={'file': f})
    # # print(result.text)
    # result_dict = ast.literal_eval(result.text)
    # os.remove(tmp_file_name)

    return _get_token_(url, file_path)

def get_excel_tokens(file_path):
    env = bottle.default_app().config.get('env')
    conf = config(env)
    win_server = conf.get('WIN_SERVER')
    url = win_server + API.ROOT + API.VERSION + "/parse_excel"

    # print(file_path)
    # _, ext = os.path.splitext(file_path)
    # tmp_file_name = str(uuid.uuid1()) + ext
    # print(tmp_file_name)
    # shutil.copy(file_path, tmp_file_name)
    #
    # with open(tmp_file_name, 'rb') as f:
    #     print(f.name)
    #     result = requests.post(url, files={'file': f})
    # # result_dict = ast.literal_eval(result.text)
    # # print(result_dict)
    # result_dict = json.loads(result.text)
    # os.remove(tmp_file_name)
    # return result_dict['text_tokens']

    return _get_token_(url, file_path)


def _get_token_(url, file_path):
    _, ext = os.path.splitext(file_path)
    tmp_file_name = get_tmp_file_path(str(uuid.uuid1()) + ext.lower())

    shutil.copy(file_path, tmp_file_name)

    assert filecmp.cmp(file_path, tmp_file_name) is True

    token = []
    with open(tmp_file_name, 'rb') as f:
        logger.info(
            f"call get tokens from document service started. url is {url} ")
        response = requests.post(url, files={'file': f})

        logger.info(
            f"call get tokens from document service ended. result status code is {response.status_code}")

        if response.status_code == 200:
            result = json.loads(response.text)
            token = result['text_tokens']
            if isinstance(result, str):
                logger.exception(f"{tmp_file_name}文件可能损坏，请将订单文件另存为正确的格式后，重新上传。")
        else:
            logger.warning(response.status_code)
            logger.info(f"get tokens from windows server error. {response.content}")
            # os.remove(tmp_file_name)

    # os.remove(tmp_file_name)

    return token


if __name__ == '__main__':
    import zipfile

    for f in get_all_files('/Users/mqgao/Documents/Documents-IBM-MacPro/IBM工作文档/兴森快捷/ten-tests/解压包'):
        ext = f.split('.')

        try:
            text, _ = get_tokens_texts(f)
            print('file name: {}'.format(f))
            print('file content : {}'.format(text))
        except TypeError:
            print('parse file: {} error'.format(f))
        except zipfile.BadZipFile:
            print('ERROR {}'.format(f))
