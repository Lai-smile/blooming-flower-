# Created by lixingxing at 2018/11/28

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File LocationL: # Enter

"""
import csv
import os
import pickle
import time

import cv2
import numpy as np
import pytesseract

from image_handlers import read_table
from image_handlers.image_utilities import get_binary, find_table, find_text_region, intersection_lines_detection, \
    get_dominant_color, get_file_type, youdao_pure_text_ocr, yidao_pure_text_ocr, text_dict2text_list, \
    create_blank, tencent_pure_text_ocr
from image_handlers.split_image_text import pure_text_region
from image_handlers.v_cut_detect import v_cut_detector
from file_utilities import get_file_name, get_extension
from path import root


def ocr_preprocessed(input_image_path):
    img = cv2.imread(input_image_path)
    h, w = img.shape[:2]
    new_img = cv2.resize(img, (2 * w, 2 * h))
    cv2.imwrite(input_image_path, new_img)
    return input_image_path


class TableTextReader:
    def __init__(self, image_path):
        self.image_path = image_path
        self.image = cv2.imread(image_path)
        self.image_original_coo = list(self.image.shape[:2])
        self.image_height = self.image_original_coo[0]
        self.image_width = self.image_original_coo[1]
        self.blank_image = np.zeros(list(self.image.shape), self.image.dtype)
        self.covered_text_image = create_blank(self.image_width, self.image_height, rgb_color=(255, 255, 255))
        self.soft_margin = 10

    def intersection_tables_ocr(self, table_coo, table_num, highlight_readable_paras):
        print('I am working on intersection table OCR')
        bin_table = get_binary(self.image, my_threshold=[45, 255])
        table_lines = find_table(bin_table)
        region = find_text_region(table_lines, cv2.RETR_TREE)
        # read text of table into dictionary
        text_dict = {}
        for table in region[1:]:
            # get the coordinate order
            # use the minimum coordination as the represent point of each small table
            represent_point = sorted(table.tolist())[0]
            width = abs(table[1] - table[2])[0]
            height = abs(table[0] - table[1])[1]
            table_region = self.image[represent_point[1]:(represent_point[1] + height),
                           represent_point[0]:(represent_point[0] + width)]
            # relative_coo_point is [relative_x_value, relative_y_value, relative_rec_width, relative_rec_height]
            relative_width = width / self.image_width
            relative_height = height / self.image_height
            o_coo_point = (np.add(represent_point, table_coo[table_num][:2])).tolist()
            relative_coo_point = (np.divide(o_coo_point, self.image_original_coo)).tolist()
            relative_coo_point.append(relative_width)
            relative_coo_point.append(relative_height)
            # get text from table
            small_table_height, small_table_width, dim = table_region.shape
            if small_table_height == 0 and small_table_width == 0:
                continue
            elif 2 * width * height > self.image_height * self.image_width:
                continue
            elif height + self.soft_margin > self.image_height or width + self.soft_margin > self.image_width:
                continue
            text = pytesseract.image_to_string(table_region)
            text_dict[tuple(relative_coo_point)] = text
            if text and highlight_readable_paras:
                # highlight img
                cv2.rectangle(self.blank_image, (o_coo_point[0] + self.soft_margin, o_coo_point[1] + self.soft_margin),
                              (o_coo_point[0] + width - self.soft_margin, o_coo_point[1] + height - self.soft_margin),
                              (0, 0, 255), thickness=-1)
        table_num += 1
        return text_dict

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

    def get_table_text_dict(self, test_gerber=False, save_dict=False, highlight_readable_paras=None,
                            v_cut_save_path=None):
        """
        save table text dict in a list

        """
        print('I am working on extracting table information dictionary')
        table_num = 0
        table_loc = []
        table_dicts_group = []
        pure_text_dict_group = []
        # adjust contrast
        contrast_img = cv2.addWeighted(self.image, 1.3, self.blank_image, 1 - 1.3, 5)
        highlight_step_1 = self.blank_image.copy()
        gerber_file = get_file_type(self.image_path, test_gerber)
        if gerber_file:
            imgs, table_coo = read_table.extract_table_from_img(self.image_path)
            pure_table_image = np.zeros([self.image_height + self.soft_margin, self.image_width + self.soft_margin, 3],
                                        self.image.dtype)
            for table in imgs:
                if not intersection_lines_detection(table):
                    table_locate_info = self.get_pure_table_region(table_coo, table_num)
                    # filling small table region prepare big table contours detector
                    cv2.rectangle(pure_table_image, (table_locate_info[0], table_locate_info[1]),
                                  (table_locate_info[0] + table_locate_info[2],
                                   table_locate_info[1] + table_locate_info[3]),
                                  (0, 0, 255), thickness=-1)
                    table_loc.append(table_locate_info)
                    # cv2.rectangle(self.covered_text_image, (table_locate_info[0], table_locate_info[1]),
                    #               (table_locate_info[0] + table_locate_info[2],
                    #                table_locate_info[1] + table_locate_info[3]),
                    #               (0, 0, 0), thickness=-1)
                    table_num += 1
                else:
                    table_num += 1
                    continue
            # print(self.covered_text_image.shape)
            # f = open('4S7MD161A0_table_loc.pkl', 'wb')
            # pickle.dump(table_loc, f)
            # f.close()
            # cv2.imwrite('pure_pure_table.png', pure_table_image)

            dilate_kernel = cv2.getStructuringElement(cv2.MORPH_OPEN, (7, 7))
            dilate_image = cv2.dilate(pure_table_image, dilate_kernel, iterations=2)
            binary_table_region = get_binary(dilate_image, my_threshold=[45, 255])
            table_edge_condition, table_region_contours = find_text_region(binary_table_region, cv2.RETR_EXTERNAL)
            print('I am working on pure text OCR')
            o_img = self.image.copy()
            background_color = get_dominant_color(o_img)
            for edge_num in range(len(table_edge_condition)):
                # draw big table contours
                cv2.drawContours(o_img, table_edge_condition, edge_num, background_color, thickness=3)

            pure_text_dict_group = pure_text_region(o_img, background_color, self.blank_image)
            # cv2.imwrite('pure_table.png', binary_table_region)
            print('I am working on tables OCR')
            i = 0

            for edge_condition in table_edge_condition:
                sorted_edge_condition = sorted(edge_condition.tolist())
                min_point = sorted_edge_condition[0]
                max_point = sorted_edge_condition[-1]
                cut_table = self.image[min_point[1]:max_point[1], min_point[0]:max_point[0]]
                c_x, c_y, c_z = cut_table.shape
                if c_x and c_y and c_z:
                    table_ram = 'table_RAM' + str(i) + '.png'
                    # table_ram = 'table_RAM.png'
                    # print(table_ram)
                    cv2.imwrite(table_ram, cut_table)
                    i += 1
                    table_ram = ocr_preprocessed(table_ram)
                    iso_table_dict = self.ocr_detector(table_ram, self.blank_image, self.soft_margin, min_point)
                    if iso_table_dict:
                        table_dicts_group.append(iso_table_dict)
                    # os.remove(table_ram)
            if not table_dicts_group:
                print('not text')
                v_cut_detector(self.image, v_cut_save_path)
        elif not gerber_file:
            print('I am not gerber file using ocr')
            self.soft_margin = 0
            try:
                iso_table_dict = self.ocr_detector(self.image_path, self.blank_image, self.soft_margin, [0, 0])
            except Exception as e:
                print('OCR sever failed: {} Use backup solution'.format(e))
                iso_table_dict = self.ocr_detector(self.image_path, self.blank_image, self.soft_margin, [0, 0],
                                                   ocr_type='you_dao')

            if iso_table_dict:
                table_dicts_group.append(iso_table_dict)
        table_dicts_group.extend(pure_text_dict_group)

        if save_dict:
            # save table dictionary in pkl file
            print('save dictionary into pickle file')
            f_name = get_file_name(self.image_path)
            f_extension = get_extension(self.image_path)
            file = open(f_name + f_extension + '.pkl', 'wb')
            print('save path is:{}'.format(f_name + f_extension + '.pkl'))
            table_save_as_list = text_dict2text_list(table_dicts_group)
            print(table_save_as_list)
            pickle.dump(table_save_as_list, file)
            file.close()
        if highlight_readable_paras:
            print('highlight step 1')
            highlight_step_1 = cv2.addWeighted(contrast_img, 0.8, self.blank_image, 0.2, 3)
            f_name = get_file_name(self.image_path)
            f_extension = get_extension(self.image_path)
            cv2.imwrite(f_name + '_Marked_' + f_extension, highlight_step_1)
        return table_dicts_group, highlight_step_1


# def save_as_csv(ocr_path):
#     ocr_file = os.listdir(ocr_path)
#     for file in ocr_file:
#         _input_file = os.path.join(ocr_path, file)
#         if file.endswith(('png', 'PNG', 'jpg', 'jpeg')):
#             print(file)
#             out_ocr_file = os.path.join(ocr_path, file.split('.')[0])
#             out_ocr_file += '.csv'
#             save_file_name = open(out_ocr_file, 'w', newline='', encoding='utf-8-sig')
#             saver = csv.writer(save_file_name)
#             file_format = ['X坐标', 'Y坐标', '提取的文本']
#             saver.writerow(file_format)
#
#             ocr_preprocessed(_input_file)
#             _table_reader = TableTextReader(_input_file)
#             _text_dict_list, _highlight = _table_reader.get_table_text_dict(test_gerber=False, save_dict=False,
#                                                                             highlight_readable_paras=False)
#             print(len(_text_dict_list))
#             for l in _text_dict_list:
#                 print(l)
#                 _loc_info = [[key[0], key[1]] for key in l.keys()]
#                 _text_info = [text for text in l.values()]
#                 _new_info = []
#                 for index in range(len(_loc_info)):
#                     x, y = _loc_info[index]
#                     text = _text_info[index]
#                     info = [x, y, text]
#                     print(info)
#                     _new_info.append(info)
#                     saver.writerow(info)
#                 print(_new_info)
#             save_file_name.close()


# if __name__ == '__main__':
#     start_time = time.time()
#     # path = IMAGE_TEXT_DATA_PATH  # GERBER_IMG_DATAPATH
#     ocr_path = os.path.join(root, 'image_handlers', 'data', 'image4experiment', 'gd1_all.png')
#     print(ocr_path)
#     table_reader = TableTextReader(ocr_path)
#     text_dict_list, highlight = table_reader.get_table_text_dict(test_gerber=True, save_dict=False,
#                                                                  highlight_readable_paras=False)
#     print(text_dict_list)
#     # # with open(input_file + '.pkl')
#     # #     pickle.dump()
#     #
#     # print(text_dict_list)
#     # for d in text_dict_list:
#     #     for item in d.items():
#     #         print(item)
#     #     # print(d)
#
#     # # print(input_file)
#     # out_file = os.path.join(ocr_path, ocr_file_name)
#     # dict_path = os.path.join(IMAGE_OUTPUT_PATH, 'remark2.pkl')
#     # save_as_csv(ocr_path)
#
#     # #############################
#     # #  pdf table location extraction
#     # pdf_test_path = os.path.join(root, 'image_handlers', 'data', 'image4experiment')
#     # pdf_output_path = os.path.join(root, 'image_handlers', 'data', 'output4experiment')
#     # file_name = 'pdf_image.png'
#     # input_file = os.path.join(pdf_test_path, file_name)
#     # # output_file = os.path.join(pdf_output_path, file_name)
#     #
#     # # # print(input_file)
#     # # # out_file = os.path.join(ocr_path, ocr_file_name)
#     # # # # dict_path = os.path.join(IMAGE_OUTPUT_PATH, 'remark2.pkl')
#     # # # save_as_csv(ocr_path)
#     #
#     # # #############################
#     # # #  pdf table location extraction
#     # # pdf_test_path = os.path.join(root, 'image_handlers', 'data', 'image4experiment')
#     # # pdf_output_path = os.path.join(root, 'image_handlers', 'data', 'output4experiment')
#     # # file_name = 'pdf_image.png'
#     # # input_file = os.path.join(pdf_test_path, file_name)
#     # # # output_file = os.path.join(pdf_output_path, file_name)
#     # #
#
#     # save_as_csv('/Users/lixingxing/IBM/auto-pcb-ii/image_handlers/data/OCR23S_YI')
#     print('time cost is {} s'.format(time.time() - start_time))
