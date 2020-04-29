# Created by lixingxing at 2019/3/21

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File LocationL: # Enter

"""
# import sys

# sys.path.append('/home/dev/workspaces/auto-pcb-ii')
# sys.path.append('/Users/lixingxing/IBM/auto-pcb-ii')
from datetime import datetime

import cv2
import os
import time
import numpy as np
from image_handlers import read_table
from constants.path_manager import IMAGE_TEXT_DATA_PATH
from image_handlers.image_utilities import get_binary, find_table, find_text_region, intersection_lines_detection, \
    get_dominant_color, get_file_type, tencent_ocr, youdao_pure_text_ocr, yidao_pure_text_ocr, text_dict2text_list, \
    create_blank, find_min_max_points_group, group_gerber_ocr_text, tencent_pure_text_ocr
from tokenization.gerber_tokenization.get_checkbox_and_img import generate_selected_check_boxes, read_s8tp_file
from utilities.file_utilities import get_file_name, get_extension


class GM2Reader:
    def __init__(self, gm2_gerber_path):
        self.gm_path = gm2_gerber_path
        self.image_path = read_s8tp_file(gm2_gerber_path)
        self.image = cv2.imread(self.image_path)
        self.image_original_coo = list(self.image.shape[:2])
        self.image_height = self.image_original_coo[0]
        self.image_width = self.image_original_coo[1]
        self.blank_image = np.zeros(list(self.image.shape), self.image.dtype)
        self.covered_text_image = create_blank(self.image_width, self.image_height, rgb_color=(255, 255, 255))
        self.soft_margin = 10
        self.gerber_boxes = generate_selected_check_boxes(gm2_gerber_path, self.image_original_coo)

    @staticmethod
    def get_pure_table_region(table_coo, table_num):
        represent_point = table_coo[table_num][:2]
        width = abs(table_coo[table_num][0] - table_coo[table_num][2])
        height = abs(table_coo[table_num][1] - table_coo[table_num][3])
        represent_point.append(width)
        represent_point.append(height)
        return represent_point

    @staticmethod
    def ocr_detector(_image_path, _blank_image, _soft_margin, _min_point, ocr_type='yi_dao'):
        if ocr_type is 'yi_dao':
            return yidao_pure_text_ocr(_image_path, _blank_image, _soft_margin, _min_point)
        if ocr_type is 'you_dao':
            return youdao_pure_text_ocr(_image_path, _blank_image, _soft_margin, _min_point)
        if ocr_type is 'tencent':
            return tencent_pure_text_ocr(_image_path, _blank_image, _soft_margin, _min_point)

    def get_table_text_dict(self, highlight_readable_paras=True):
        """
        save table text dict in a list

        """
        print('I am working on extracting GM2 information dictionary')

        def _draw_rectangle(_image, color):
            cv2.rectangle(_image, (table_locate_info[0], table_locate_info[1]),
                          (table_locate_info[0] + table_locate_info[2],
                           table_locate_info[1] + table_locate_info[3]),
                          color, thickness=-1)

        table_num = 0
        table_dicts_group = []
        image_save_path = ''
        contrast_img = cv2.addWeighted(self.image, 1.3, self.blank_image, 1 - 1.3, 5)
        imgs, table_coo = read_table.extract_table_from_img(self.image_path)
        pure_table_image = np.zeros([self.image_height + self.soft_margin, self.image_width + self.soft_margin, 3],
                                    self.image.dtype)
        os.remove(self.image_path)
        for table in imgs:
            if not intersection_lines_detection(table):
                table_locate_info = self.get_pure_table_region(table_coo, table_num)

                # filling small table region prepare big table contours detector
                _draw_rectangle(pure_table_image, color=(0, 0, 255))
                _draw_rectangle(self.covered_text_image, color=(0, 0, 0))

                table_num += 1
            else:
                table_num += 1
                continue

        dilate_kernel = cv2.getStructuringElement(cv2.MORPH_OPEN, (7, 7))
        dilate_image = cv2.dilate(pure_table_image, dilate_kernel, iterations=2)
        binary_table_region = get_binary(dilate_image, my_threshold=[45, 255])
        cv2.imwrite('binary_table_region.png', binary_table_region)
        table_edge_condition, table_region_contours = find_text_region(binary_table_region, cv2.RETR_EXTERNAL)
        print('I am working on tables OCR')
        covered_text_image = cv2.subtract(self.covered_text_image, self.image)
        for edge_condition in table_edge_condition:
            sorted_edge_condition = sorted(edge_condition.tolist())
            min_point = sorted_edge_condition[0]
            max_point = sorted_edge_condition[-1]
            cut_table = self.image[min_point[1]:max_point[1], min_point[0]:max_point[0]]
            covered_text_table = covered_text_image[min_point[1]:max_point[1], min_point[0]:max_point[0]]
            c_x, c_y, c_z = cut_table.shape
            if c_x and c_y and c_z:
                table_ram = 'table_RAM.png'
                cv2.imwrite(table_ram, cut_table)
                min_max_points_group = find_min_max_points_group(covered_text_table, min_point)
                iso_table_dict = self.ocr_detector(table_ram, self.blank_image, self.soft_margin, min_point)
                if iso_table_dict:
                    grouped_small_tables = group_gerber_ocr_text(min_max_points_group, iso_table_dict,
                                                                 self.gerber_boxes)
                    table_dicts_group.append(list(grouped_small_tables.values()))
                os.remove(table_ram)
        if highlight_readable_paras:
            print('highlight step 1')
            highlight_step_1 = cv2.addWeighted(contrast_img, 0.8, self.blank_image, 0.2, 3)
            f_name = get_file_name(self.gm_path)
            file_name = f_name.split('/')[-1]
            f_extension = get_extension(self.image_path)
            tmp_file_path = '/data/fastprint/tmp-files'
            current_time = datetime.now().strftime('%Y%m%d%H%M%S')
            save_path = "{tmp_file_path}/{current_time}".format(tmp_file_path=tmp_file_path,
                                                                current_time=current_time)
            # 如果文件夹不存在，创建文件夹
            if not os.path.exists(save_path):
                os.mkdir(save_path)

            # 图片保存的路径
            image_save_path = "{save_path}/{file_name}_Marked_{f_extension}".format(
                save_path=save_path,
                file_name=file_name,
                f_extension=f_extension)
            cv2.imwrite(image_save_path, highlight_step_1)
        return table_dicts_group, image_save_path


def gm2_reader_start(s8tp_file_path):
    _table_reader = GM2Reader(s8tp_file_path)
    _text_dict_list, image_save_path = _table_reader.get_table_text_dict()
    # 返回gerber图像保存路径
    return _text_dict_list, image_save_path


def get_all_gm2_into_pickle(input_folder):
    def _get_all_files(_path):
        """"Gets all files in a directory"""
        if os.path.isfile(_path):
            return [_path]
        return [f for d in os.listdir(_path)
                for f in _get_all_files(os.path.join(_path, d))]

    all_files = _get_all_files(input_folder)
    i = 0
    for f in all_files:
        if f.endswith('.GM2'):
            print('file {}'.format(f))
            print('{}'.format(i))
            f_name = get_file_name(f)
            f_name = f_name + '_READ.pkl'
            if os.path.exists(f_name):
                continue
            try:
                _text_dict_list, _ = gm2_reader_start(f)
                print(_text_dict_list)
            except Exception as e:
                print(e)
                continue
            gm_pkl_file = open(f_name, 'wb')
            pickle.dump(_text_dict_list, gm_pkl_file)
            gm_pkl_file.close()
            i += 1


if __name__ == '__main__':
    import pickle

    # input_f = '/home/dev/workspaces/auto-pcb-ii/20190321S8TP测试文件'
    # get_all_gm2_into_pickle(input_f, start=100, end=200)
    path = IMAGE_TEXT_DATA_PATH
    input_files = os.path.join(path, 's8tp4')
    s8tp_path = '/Users/lixingxing/IBM/xingying1'
    debug = '/Users/lixingxing/IBM/auto-pcb-ii/image_handlers/data/image4experiment/debug'
    # get_all_gm2_into_pickle(debug)
    print(gm2_reader_start('/Users/yeleiyl/Downloads/wsdata/gerber/4s8tp0ata0/gd1'))
    gm2_text_string_list, _ = gm2_reader_start('/Users/yeleiyl/Downloads/wsdata/gerber/4s8tp0ata0/fab')
    print(gm2_text_string_list)
    y = 1
    gm2_text_string_table = []
    for table_list in gm2_text_string_list:
        for y_item in table_list:
            c_list = []
            for intdex, x_item in enumerate(y_item):
                c_list.append((y, intdex + 1, y, intdex + 1, x_item[1]))
            gm2_text_string_table.append(c_list)
            y += 1
    print(gm2_text_string_table)

    # gm_file = open('test_gm_s8tp.pkl', 'wb')
    # s8tp_files = os.listdir(s8tp_path)
    # text_dict_list_group = []
    # i = 0
    # for file in s8tp_files:
    #     if file.endswith('.GM2'):
    #         print('file {}'.format(i))
    #         table_reader = GM2Reader(os.path.join(s8tp_path, file))
    #         text_dict_list = table_reader.get_table_text_dict()
    #         print(text_dict_list)
    #         text_dict_list_group.extend(text_dict_list)
    #         i += 1
    # pickle.dump(text_dict_list_group, gm_file)
    # gm_file.close()
    #

    ##################
    # start_time = time.time()
    # path = IMAGE_TEXT_DATA_PATH  # GERBER_IMG_DATAPATH
    # input_file = os.path.join(path, 'test-gerber1.png')
    # gerber_file = os.path.join(path, 'TZ7.820.2449.GM2')
    # print(gerber_file)
    # gm_test_file = open(os.path.join(path, 'TZ7.820.2449.pkl'), 'wb')
    # table_reader = GM2Reader(gerber_file)
    # text_dict_list = table_reader.get_table_text_dict()
    # print(text_dict_list)
    # pickle.dump(text_dict_list, gm_test_file)
    # gm_test_file.close()
    # print('time cost is: {}'.format(time.time() - start_time))
    #
