# Created by lixingxing at 2019/1/24

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File LocationL: # Enter

"""

import hashlib
from urllib import parse, request
import random
import json
import base64
# from aip import AipOcr
from path import root

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.ocr.v20181119 import ocr_client, models


class YoudaoOCR(object):

    def __init__(self, image_path, min_point):
        self.appKey = '6acb4e287f36ccf9'
        self.secretKey = 'b4flsTACE2Gmt5WF2UIK1XuSp1gvbRc9'
        self.httpClient = None
        self.image_path = image_path
        self.min_point = min_point
        self.loc_idx = []
        self.text_idx = []
        self.idx = 0
        self.loc_idx.append(1)

    def json_analyze(self, json_dict, content_list):

        if isinstance(json_dict, dict):
            for (label, value) in json_dict.items():
                # print(label, ':', value)
                if label == 'boundingBox':
                    self.idx += 1
                    content_list.append(value)
                elif label == 'text':
                    self.loc_idx.append(self.idx + 1)
                    self.text_idx.append(self.idx)
                    content_list.append(value)
                    self.idx += 1
                YoudaoOCR.json_analyze(self, value, content_list)
        elif isinstance(json_dict, list):
            for ie in json_dict:
                YoudaoOCR.json_analyze(self, ie, content_list)
        return content_list

    def save_as_standard(self, content_list):
        output_list = []
        output_dict = {}
        for item_idx in range(len(self.text_idx)):
            loc_i = self.loc_idx[item_idx]
            text_i = self.text_idx[item_idx]
            x1, y1, x2, y2, x3, y3, x4, y4 = map(int, content_list[loc_i].split(','))
            text = content_list[text_i]
            output_list.append((None, x1, y1, x3, y3, text))
            output_dict[(x1 + self.min_point[0], y1 + self.min_point[1], (x3 - x1), (y3 - y1))] = text

        return output_list, output_dict

    @staticmethod
    def get_md5(strings):
        my_md5 = hashlib.md5()
        my_md5.update(strings.encode('utf-8'))
        strings = my_md5.hexdigest()
        # print (secure)
        return strings

    def main_ocr(self):
        try:
            f = open(self.image_path, 'rb')  # 二进制方式打开图文件
            img = base64.b64encode(f.read())  # 读取文件内容，转换为base64编码
            img = str(img, encoding='utf-8')
            f.close()

            detectType = '10012'
            imageType = '1'
            langType = 'zh-en'
            salt = random.randint(1, 65536)

            sign = self.appKey + img + str(salt) + self.secretKey
            sign = self.get_md5(sign).upper()
            data = {'appKey': self.appKey, 'img': img, 'detectType': detectType, 'imageType': imageType,
                    'langType': langType,
                    'salt': str(salt), 'sign': sign}
            data = parse.urlencode(data).encode('utf-8')
            req = request.Request('http://openapi.youdao.com/ocrapi', data)

            # response是HTTPResponse对象
            response = request.urlopen(req).read().decode()
            response_dict = json.loads(response)

            empty_content_list = []
            content = self.json_analyze(response_dict, empty_content_list)
            processed_list, processed_dict = self.save_as_standard(content)
            return processed_list, processed_dict
        except Exception as e:
            print(e)
        finally:
            if self.httpClient:
                self.httpClient.close()


class BaiduOCR(object):
    def __init__(self, image_path):
        self.config = {
            'appId': '15482136',
            'apiKey': 'efqG2DZz5Ov82vxCs5WpSRbG',
            'secretKey': 'frEFlILO4WSRXf3ZeCrPHDqgvqepdx6D'
        }
        self.client = AipOcr(**self.config)
        self.image_path = image_path

    def main_ocr(self):
        f = open(self.image_path, 'rb')  # 二进制方式打开图文件
        # img = base64.b64encode(f.read())  # 读取文件内容，转换为base64编码
        image = f.read()
        # img = str(img, encoding='utf-8')
        f.close()
        result = self.client.basicGeneral(image)
        return_dict = {}
        random_value = 0
        if 'words_result' in result:
            for w in result['words_result']:
                return_dict[(random_value, random_value, random_value, random_value)] = w['words']
                random_value += 1
        return return_dict


class YidaoOCR(object):
    def __init__(self, image_path, min_point):
        self.image_path = image_path
        self.min_point = min_point

    def main_ocr(self):
        f = open(self.image_path, 'rb')  # 二进制方式打开图文件
        img = base64.b64encode(f.read())  # 读取文件内容，转换为base64编码
        img = str(img, encoding='utf-8')
        f.close()
        params = {'image_base64': img}
        data = parse.urlencode(params).encode('utf-8')
        req = request.Request('http://test.exocr.com:5000/ocr/v1/general', data)
        try:
            response = request.urlopen(req).read().decode()
            response_dict = json.loads(response)
            result = response_dict['result']
            # print(response_dict['result'])
            item_num = len(response_dict['result'])
            # print(len(response_dict['result']))
            location_dict = {}
            global height, left, top, width
            for idx in range(item_num):
                for key, value in result[idx].items():
                    if key == 'position':
                        height = value['height']
                        left = value['left']
                        top = value['top']
                        width = value['width']
                    elif key == 'words':
                        location_dict[(left + self.min_point[0], top + self.min_point[1], width, height)] = value
            return location_dict
        except OSError:
            print('网络无连接！')
            # print(location_dict)
            return {}


class TencentOCR:
    def __init__(self, image_path, min_point):
        self.image_path = image_path
        self.min_point = min_point

    def _preprocess(self):
        f = open(self.image_path, 'rb')  # 二进制方式打开图文件
        img = base64.b64encode(f.read())  # 读取文件内容，转换为base64编码
        img = str(img, encoding='utf-8')
        f.close()
        return img

    def main_ocr(self):
        print('loading Tencent ocr')
        img = self._preprocess()
        formatted_output = {}
        try:

            cred = credential.Credential("AKID0nLdgTSHadQxFJgi1JL7evxjFVhdxjtn", "oMgz2pMdfRwCPM3UgdKlx71f4D7k8GME")
            http_profile = HttpProfile()
            http_profile.endpoint = "ocr.tencentcloudapi.com"

            client_profile = ClientProfile()
            client_profile.httpProfile = http_profile
            client = ocr_client.OcrClient(cred, "ap-guangzhou", client_profile)

            req = models.GeneralAccurateOCRRequest()
            # req.ImageUrl = "https://mc.qcloudimg.com/static/img/6d4f1676deba26377d4303a462ca5074/image.png"
            req.ImageBase64 = img
            resp = client.GeneralAccurateOCR(req)
            resp_json = resp.to_json_string()
            resp_dict = json.loads(resp_json)
            print(resp_dict)
            for ocr_dict in resp_dict['TextDetections']:
                ocr_text = ocr_dict['DetectedText']
                print(ocr_text)
                ocr_polygon = ocr_dict['Polygon']  # four conner points
                point1, point2, point3, point4 = ocr_polygon[:]
                formatted_output[(point2['X'] + self.min_point[0],
                                  point2['Y'] + self.min_point[1],
                                 point4['X'] - point2['X'],
                                 point4['Y'] - point2['Y'])] = ocr_text
            # print(resp_json)
            # print(resp_dict['TextDetections'])
            # print(formatted_output)
            return formatted_output

        except TencentCloudSDKException as err:
            print(err)


if __name__ == '__main__':
    import os

    # import pickle
    # import cv2
    #
    #
    # def preprocessed(input_image_path):
    #     img = cv2.imread(input_image_path)
    #     h, w = img.shape[:2]
    #     new_img = cv2.resize(img, (2 * w, 2 * h))
    #     cv2.imwrite(input_image_path, new_img)
    #
    #
    # input_image_file = os.path.join(root, 'image_handlers', 'data', 'image_RAM', 'ram_Marked_.png')
    input_image_file = '/Users/lxy/中国银行青岛/invoice/0.png'

    # t_ocr = TencentOCR(input_image_file).main_ocr()
    print(YidaoOCR(input_image_file, [0, 0]).main_ocr())
