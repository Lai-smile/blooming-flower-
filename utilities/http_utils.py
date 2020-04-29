
import requests, ast

import logging


def postJSON(url, params):

    # url = 'http://0.0.0.0:8888/auto-pcb/api/1.0/parse/excel'

    # params = {'root_path' : 'http://0.0.0.0:8888/auto-pcb/', 'files_path' : 'a.xls,b.xls'}

    headers = {
              'content-type': 'application/json; charset=utf-8',
              'cache-control': "no-cache"
              }

    # result = requests.request("POST", url, data=params, headers=headers)

    logging.info(f"HttpUtils postJSON url is {url}, params are {params}")

    result = requests.request("POST", url, json=params, headers=headers)

    logging.info(f"HttpUtils postJSON result encoding is {result.encoding} result status is {result.status_code}, result are {result.text}, content is {result.content}")

    return result
