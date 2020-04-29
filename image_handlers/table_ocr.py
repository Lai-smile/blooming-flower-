# Created by lixingxing at 2018/11/13

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File LocationL: # Enter

"""
import hashlib
import json
import os
import time
import random
from urllib import parse, request
import base64
import requests

from path_manager import IMAGE_OUTPUT_PATH, IMAGE_TEXT_DATA_PATH


def get_nonce_str():
    """
    获得API所需的Nonce_str参数
    :return:Nonce_str 请求参数
    """
    eg = "fa577ce340859f9fe"
    seed_ = "abcdefghijklmnopqrstuvwxyz0123456789"
    nonce_str = ""
    for i in range(len(eg)):
        nonce_str += seed_[random.randint(0, len(seed_) - 1)]
    return nonce_str


def get_time_stamp():
    """
    返回秒级时间戳
    """
    t = time.time()
    return int(t)


def get_md5(strings):
    """

    :param strings:
    :return:
    """
    my_md5 = hashlib.md5()
    my_md5.update(strings.encode("utf-8"))
    secure = my_md5.hexdigest()
    # print (secure)
    return secure


def parser(req_dic):
    params = sorted(req_dic.items())
    data = parse.urlencode(params).encode("utf-8")
    return data


def img_processing(img_path):
    """
    :param img_path:图片路径
    :return: 图片base64编码
    """

    f = open(img_path, 'rb')
    ls_f = base64.b64encode(f.read())
    # ls_f = base64.b64encode(img)

    ls_f = str(ls_f, encoding="utf-8")
    # f.close()
    return ls_f


def get_req_sign(params_dic, app_Key):
    """
    签名有效期5分钟
    :param params_dic: 参数字典
    :param app_Key: APPKey
    :return:
    """
    params = sorted(params_dic.items())
    url_data = parse.urlencode(params)
    # print(url_data)
    url_data = url_data + "&" + "app_key" + "=" + app_Key
    url_data = get_md5(url_data).upper()
    return url_data


def explain_tencent_jason(item, min_point):
    item_string = item['itemstring']
    coo_dict = item['itemcoord'][0]
    x = coo_dict['x'] + min_point[0]
    y = coo_dict['y'] + min_point[1]
    width = coo_dict['width']
    height = coo_dict['height']
    item_locate = (x, y, width, height)
    return item_locate, item_string


def start_table_ocr(table_path):
    global info
    info = {
        "ID": "2111649024",
        "KEY": "BXeTQhYT3pSw1ggo"
    }
    url = r"https://api.ai.qq.com/fcgi-bin/ocr/ocr_generalocr"
    img_code = img_processing(table_path)
    if img_code:
        table_text_list = []
        has_value = False
        # print(img_code)
        req_dic = {
            "app_id": int(info["ID"]),
            "image": img_processing(table_path),
            "nonce_str": get_nonce_str(),
            "time_stamp": int(get_time_stamp()),
        }

        req_dic["sign"] = get_req_sign(req_dic, info["KEY"])
        reqData = sorted(req_dic.items())
        # print(reqData)
        # reqDatas = parse.urlencode(reqData)
        # print(reqDatas)
        # data = parse.urlencode(reqData).encode('utf-8')
        # req = request.Request('http://openapi.youdao.com/ocrapi', data)
        #
        # # response是HTTPResponse对象
        # response = request.urlopen(req).read().decode()
        # read_res_json = json.loads(response)

        r = requests.post(url, reqData)
        if r.status_code == 200:
            read_res_json = r.json()
        else:
            raise ValueError(' the ocr htrp returned an error: {}'.format(r.status_code))
        # read_res_json = requests.post(url, reqData).json()
        request_accept = False
        request_time = 0
        while not request_accept and request_time < 3:
            if read_res_json is not None:
                table_text_list = read_res_json["data"]["item_list"]
                request_accept = True
                if table_text_list:
                    has_value = True
            else:
                time.sleep(5)
                read_res_json = requests.post(url, reqData).json()
                request_time += 1
        return table_text_list, has_value


if __name__ == '__main__':
    import cv2

    path = IMAGE_TEXT_DATA_PATH  # GERBER_IMG_DATAPATH
    # file_name = 'middle_black.pdf-output-0.png'  # '(0.24平米) 04-28 20 4S7HQ08GA0/drill_drawing.pho.png'
    file_name = 'Remark2.png'
    input_file = os.path.join(path, file_name)
    # table_img = cv2.imread(input_file)
    # cv2.imshow('.', table_img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    # print(table_img)
    # a = bytearray(table_img)
    start_time = time.time()
    locate, string = start_table_ocr(input_file)
    print(locate)
    print(string)
    # for item in table_list:
    #     value = item['itemstring']
    #     coo_dict = item['itemcoord'][0]
    #     x = coo_dict['x']
    #     y = coo_dict['y']
    #     width = coo_dict['width']
    #     height = coo_dict['height']
    #     key = (x, y, width, height)
    #     print(key)
    print("--- %s seconds ---" % (time.time() - start_time))

    # info = {
    #     "ID": "2109792875",
    #     "KEY": "7O99Zd5a7DxUvTAk"
    # }
    #
    # url = r"https://api.ai.qq.com/fcgi-bin/ocr/ocr_generalocr"
    #
    # reqDic = {
    #     "app_id": int(info["ID"]),
    #     "image": img_processing("gdd_table_cut0.png"),
    #     "nonce_str": get_nonce_str(),
    #     "time_stamp": int(get_time_stamp()),
    # }
    #
    # reqDic["sign"] = get_req_sign(reqDic, info["KEY"])
    # reqData = sorted(reqDic.items())
    # reqDatas = parse.urlencode(reqData)
    # # print(reqDatas)
    # req = requests.post(url, reqData)
    # res = req.text
    # # print(req.status_code)
    # # print(res)
    # print(res)
    # # read_json = json.loads(res)
    # # print(len(read_json['data']['item_list']))
    # # print(read_json['data']['item_list'][1]['itemstring'])
