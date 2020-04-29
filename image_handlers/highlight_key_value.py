# Created by lixingxing at 2018/10/23

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File LocationL: # Enter

"""
import time
import cv2
from text_handlers.pair_match_main import pari_match_for_all_tables
from my_constants.path_manager import IMAGE_OUTPUT_PATH, IMAGE_TEXT_DATA_PATH
import numpy as np
import os


def highlight(param_locate, color):
    soft_margin = 10
    # param_coo_x = int(param_locate[0] * img_width)
    # param_coo_y = int(param_locate[1] * img_height)
    # width = int(param_locate[2] * img_width)
    # height = int(param_locate[3] * img_height)
    cv2.rectangle(blank, (param_locate[0] - soft_margin, param_locate[1] - soft_margin),
                  (param_locate[0] + param_locate[2] + soft_margin, param_locate[1] + param_locate[3] + soft_margin), color,
                  thickness=-1)


def highlight_image(highlight_step_1, text_dict, output_path=None, save_highlight=True):
    # main function
    global blank
    print('highlight step 2')
    green = (0, 255, 0)
    yellow = (0, 255, 255)
    img_height, img_width, img_dim = highlight_step_1.shape
    blank = np.zeros([img_height, img_width, img_dim], highlight_step_1.dtype)
    contrast_img = cv2.addWeighted(highlight_step_1, 1.3, blank, 1 - 1.3, 5)
    table_type, table_info = pari_match_for_all_tables(text_dict)
    table_num = 0
    for label in table_type:
        if label == 'param_table':
            # print('mark param_table')
            useful_dicts_list = table_info[table_num]
            dict_num = len(useful_dicts_list)
            # print(dict_num)
            for num in range(dict_num):
                # print('num dict{}'.format(num))
                param_dict = useful_dicts_list[num]
                key_param_locate = param_dict['key_locate']
                value_param_locate = param_dict['value_locate']
                highlight(key_param_locate, green)
                highlight(value_param_locate, yellow)
        table_num += 1
    highlight_step_2 = cv2.addWeighted(contrast_img, 0.8, blank, 0.2, 3)
    if save_highlight:
        cv2.imwrite(output_path, highlight_step_2)
    return table_info


if __name__ == '__main__':
    from image_handlers.read_text import TableTextReader
    # from utilities.visualization_utilities import prview_table_extract

    path = IMAGE_TEXT_DATA_PATH  # GERBER_IMG_DATAPATH
    # file_name = 'middle_black.pdf-output-0.png'  # '(0.24平米) 04-28 20 4S7HQ08GA0/drill_drawing.pho.png'
    file_name = 'gdd.png'
    input_file = os.path.join(path, file_name)
    out_file = os.path.join(IMAGE_OUTPUT_PATH, file_name)
    dict_path = os.path.join(IMAGE_OUTPUT_PATH, 'text_dic.pkl')
    start_time = time.time()
    table_reader = TableTextReader(input_file)
    text_dict_list, highlight_step1 = table_reader.get_table_text_dict(save_dict=dict_path, highlight_readable_paras=True)

    # for i in text_dict_list:
    #     prview_table_extract(i)

    print(text_dict_list)
    table_information = highlight_image(highlight_step1, text_dict_list, output_path='tests——highlighted.png')
    print("--- %s seconds ---" % (time.time() - start_time))

