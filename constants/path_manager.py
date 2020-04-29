# Created by hudiibm at 2018/12/26
"""
Feature: #Enter feature name here
# Enter feature description here
Scenario: #Enter scenario name here
# Enter steps here
Test File Location: # Enter]
"""
import os
from utilities.path import root

WV_MODELS_PATH = os.path.join(root, 'nlp_synonym', 'wv_models')
TRAIN_SOURCES_PATH = os.path.join(root.parent, 'metadata', 'train_source')

TEST_PICKLES_PATH = os.path.join(root, 'nlp_synonym', 'data', 'pickles')
JIEBA_USER_DICT = os.path.join(root, 'nlp_synonym', 'data', 'Jieba_dict.txt')
TEST_PICKLES_VIEW_PATH = os.path.join(root, 'nlp_synonym', 'data', 'pickles_view')
FAKE_DB_TEST_ALIAS = os.path.join(root, 'nlp_synonym', 'data', 'GCZDH_TEST_ALIAS.csv')
FAKE_DB_PARAMETER = os.path.join(root, 'nlp_synonym', 'data', 'GCZDH_GCZDH_PARAMETER.csv')
FAKE_DB_OPTION_LIST = os.path.join(root, 'nlp_synonym', 'data', 'GCZDH_GCZDH_PARAMETER_OPTION_LIST.csv')
PNG_TEXT_DATA_PATH = os.path.join(root, 'image_handlers', 'data', 'png')
PNG_TEXT_DATA_RAM_PATH = os.path.join(root, 'image_handlers', 'data', 'image_RAM')
IMAGE_TEXT_DATA_PATH = os.path.join(root, 'image_handlers', 'data', 'image4experiment')
OCR_TEST_PATH = os.path.join(root, 'image_handlers', 'data', 'OCR23S_YI')
IMAGE_OUTPUT_PATH = os.path.join(root, 'image_handlers', 'data', 'output4experiment')
OCR_OUTPUT_PATH = os.path.join(root, 'image_handlers', 'ocr_output')
TEST_GERBER_PATH = os.path.join(root, 'tests', 'test_image_handlers', 'test_input_images', 'gdd_gerber.png')
TEST_TEXT_PATH = os.path.join(root, 'tests', 'test_image_handlers', 'test_input_images', 'text.jpg')

# 常量参数配置路径
CONSTANTS_PATH = os.path.join(root, 'get_paramter_by_config', 'constants')

FONT_PATH = os.path.join(root, 'utilities', 'data', 'PingFang-SC-Semibold-2.ttf')

# 自动化系统文件保存根目录
FILE_ROOT_PATH = '/data/fastprint/'


