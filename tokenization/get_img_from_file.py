import ast
import os
import shutil
import uuid

import requests
import bottle

from constants import API
from config.config import config
from log.logger import logger


def get_images_from_file(filename, dest_path):
    ext = filename.split('.')[-1].lower()

    function_mapper = {
        # 'xls': get_images_from_excel,
        # 'xlsx': get_images_from_excel,
        # 'xlsm': get_images_from_excel,
        # 'doc': get_images_from_word,
        # 'docx': get_images_from_word,
        # 'pdf': get_image_from_pdf
    }

    if ext in function_mapper:
        text = function_mapper[ext](filename, dest_path)
        if text:
            logger.info(f'get_images_from_file result is {text}')
            return text
        else:
            return {'img_count': 0, 'paths': []}
    else:
        logger.warning(f'get_images_from_file file type out of range. file_type is {ext}')
        return {'img_count': 0, 'paths': []}


def get_images_from_excel(file_path, dest_path=""):
    env = bottle.default_app().config.get('env')
    conf = config(env)
    win_server = conf.get('WIN_SERVER')

    url = win_server + API.ROOT + API.VERSION + "/get_images_from_excel"

    return _get_image_from_file_(url, file_path)


def get_images_from_word(file_path, dest_path=""):
    env = bottle.default_app().config.get('env')
    conf = config(env)
    win_server = conf.get('WIN_SERVER')
    url = win_server + API.ROOT + API.VERSION + '/get_images_from_word'

    return _get_image_from_file_(url, file_path)


def _get_image_from_file_(url, file_path):
    _, ext = os.path.splitext(file_path)
    tmp_file_name = str(uuid.uuid1()) + ext

    shutil.copy(file_path, tmp_file_name)

    img_count = 0
    with open(tmp_file_name, 'rb') as f:
        response = requests.post(url, files={'file': f})

        logger.info(
            f"get_images_from_word url is {url}, result status code is {response.status_code},  result is {response.text}")

        if response.status_code == 200:
            response_dict = ast.literal_eval(response.text)
            img_count = response_dict['img_count']
        else:
            logger.error("_get_image_from_file_ error, return def image info.")

    os.remove(tmp_file_name)

    return {"img_count": img_count, "paths": ''}
