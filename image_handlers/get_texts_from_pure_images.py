# Created by lixingxing at 2019/1/16

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File LocationL: # Enter

"""
import os
# import importlib
import cv2
from sklearn.cluster import KMeans
from collections import Counter
from path_manager import IMAGE_TEXT_DATA_PATH, OCR_TEST_PATH
from image_handlers.read_text import TableTextReader
import numpy as np
from path_manager import PNG_TEXT_DATA_RAM_PATH, PNG_TEXT_DATA_PATH
from log.logger import logger


def get_dominant_color(image):
    threshold = 127
    img_res = cv2.resize(image, (30, 30), interpolation=cv2.INTER_AREA)
    img_rgb = cv2.cvtColor(img_res, cv2.COLOR_BGR2RGB)
    image = img_rgb.reshape((img_rgb.shape[0] * img_rgb.shape[1], 3))
    clt = KMeans(2)
    clt.fit(image)
    center_colors = clt.cluster_centers_
    most_common_label = Counter(clt.labels_).most_common(1)
    background_label = most_common_label[0][0]
    background_color = center_colors[background_label][0]
    if background_color < threshold:
        dominant_color = (0, 0, 0)
    else:
        dominant_color = (255, 255, 255)
    return background_color


def draw_rect_on_image(img):
    x = 0
    y = 0
    x1 = 0
    y1 = 0
    rows, cols, dim = img.shape
    for row in range(rows):
        for col in range(cols):
            if (
                    not (img[row, col][0] > 254 and img[row, col][1] > 254 and img[row, col][
                        2] > 254)) and col > 1 and row > 1:
                if x == 0:
                    x = col
                    y = row
                    img[row, col] = [255, 255, 255]
                break
    for row in range(rows):
        for col in range(cols):
            if (not (img[rows - row - 1, cols - col - 1][0] > 254 and img[rows - row - 1, cols - col - 1][1] > 254 and
                     img[rows - row - 1, cols - col - 1][2] > 254)):
                if x1 == 0:
                    x1 = cols - col - 1
                    y1 = rows - row - 1
                break
    cv2.rectangle(img, (x - 7, y), (x1 - 3, y1), (0, 255, 0), 1)
    # if rows < 300 and cols < 300:
    #     img = cv2.copyMakeBorder(img, 381, 381, 856, 856, cv2.BORDER_CONSTANT, value=[255, 255, 255])
    return img


def top_hat_image(img):
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    res, binary_img = cv2.threshold(gray_img, 125, 255, cv2.THRESH_BINARY)
    element = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 21))
    binary_img = cv2.morphologyEx(binary_img, cv2.MORPH_BLACKHAT, element)
    return binary_img


def get_image_texts(image_name):
    ram_out_file = os.path.join(PNG_TEXT_DATA_RAM_PATH, 'ram.png')
    img = cv2.imread(image_name)
    background_color = get_dominant_color(img)
    threshold = 125
    print(background_color)
    if background_color < threshold:
        logger.error('not a pure text image')
    rect_img = draw_rect_on_image(img)
    dst_img = top_hat_image(rect_img)
    cv2.imwrite(ram_out_file, dst_img)

    try:
        table_reader = TableTextReader(ram_out_file)
        text_dict_list, highlight = table_reader.get_table_text_dict(test_gerber=False, save_dict=False,
                                                                     highlight_readable_paras=True)
        new_info = []
        if len(text_dict_list) == 1:
            loc_info = [key for key in text_dict_list[0].keys()]
            text_info = [text for text in text_dict_list[0].values()]
            for index in range(len(loc_info)):
                new_info.append((None, loc_info[index][0], loc_info[index][1], loc_info[index][0] + loc_info[index][2],
                                 loc_info[index][1] + loc_info[index][3], text_info[index]))
    except Exception as e:
        print('get image text failed:{}'.format(e))
        new_info = None
    os.remove(ram_out_file)
    return new_info


def get_binary(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    res, binary = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)
    return binary


def log(c, img):
    output_img = c * np.log(1.0 + img)
    output_img = np.uint8(output_img + 0.5)
    return output_img


def reverse(img):
    output = 255 - img
    return output


def gamma(img, c, v):
    lut = np.zeros(256, dtype=np.float32)
    for i in range(256):
        lut[i] = c * i ** v
    output_img = cv2.LUT(img, lut)
    output_img = np.uint8(output_img + 0.5)  # 这句一定要加上
    return output_img


def clear_edge(img, width):
    img[0:width - 1, :] = 1
    img[1 - width:-1, :] = 1
    img[:, 0:width - 1] = 1
    img[:, 1 - width:-1] = 1
    return img


if __name__ == '__main__':
    path = IMAGE_TEXT_DATA_PATH
    file_name = 's896-2.png'
    input_file = os.path.join(path, file_name)
    # info = get_image_texts(input_file)
    # if len(info) < 5:
    #     logger.error('not a pure text image')
    # print(info)
