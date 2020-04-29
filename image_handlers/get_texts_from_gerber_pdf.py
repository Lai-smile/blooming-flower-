# Created by lixingxing at 2019/3/5

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File LocationL: # Enter

"""
import os
import pickle
import shutil
from pdf2image import convert_from_path
from image_handlers.image_utilities import convert_pdf
from image_handlers.read_text import TableTextReader
from utilities.path import root
import pickle


def choose_target_pdf(pdf_path):
    pdf_files = os.listdir(pdf_path)
    for pdf_file in pdf_files:
        if pdf_file.endswith(('pdf', 'PDF')) and '(' in pdf_file:
            for name in pdf_file.split('>'):
                if '(' in name:
                    shutil.move(os.path.join(input_pdf_path, pdf_file),
                                os.path.join(pdf2img_output_path, str(name) + '.png'))


def get_diff_pickle(input_pdf, pixel=400):
    pdf_image_name = convert_pdf(input_pdf, pdf2img_output_path, resolution=pixel) # os.path.join(test_pdf_path, 'g1.pdf')
    if pdf_image_name:
        table_reader = TableTextReader(str(pdf_image_name[0]))
        _text_dict_list, h = table_reader.get_table_text_dict(test_gerber=False, save_dict=False, highlight_readable_paras=False)
        return _text_dict_list
    else:
        print('pdf have not been transferred to image')


if __name__ == '__main__':

    input_pdf_path = os.path.join(root, 'image_handlers', 'data', 'Extraction_pdf-from-orders')
    test_pdf_path = os.path.join(root, 'image_handlers', 'data', 'image4experiment')
    pdf2img_output_path = os.path.join(root, 'image_handlers', 'data', 'gerber_pdf_images')
    pdf_name = 'cn_yaoqiu.pdf'
    test_pdf_path_file = os.path.join(test_pdf_path, pdf_name)

    input_file = os.path.join(root, 'image_handlers', 'data', 'gerber_pdf_images', 'cn_yaoqiu-0.png')
    text_dict_list = get_diff_pickle(test_pdf_path_file)
    # pkl_file = open(os.path.join(pdf2img_output_path, 'g1-0.png.pkl'), 'rb')
    # text_dict_list = pickle.load(pkl_file)

    # print(text_dict_list)
    for item in text_dict_list:
        print(item)

    #
    # correction = defaultdict(set)
    # print('total tokens: ')
    # print(sum(len(s) for s in text_dict_list))
    #
    # for segment in text_dict_list:
    #     for key, text in segment.items():
    #         print('*'*8 + ' :', text)
    #
    #         #text_with_index = list(enumerate(text.split()))
    #
    #         #print(' '.join(text_with_index))
    #
    #         with_wrong = input('is any wrong with this? (1/0), default is 0')
    #
    #         if str(with_wrong) == '1':
    #             wrong = input('please input wrong part')
    #             right = input('please input right value')
    #             correction[wrong].add(right)
    #
    # # print("--- %s seconds ---" % (time.time() - start_time))
    #
    # # with open('correction.pickle', 'wb') as f:
    # #     pickle.dump(correction, f)
