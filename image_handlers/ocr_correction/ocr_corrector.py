# Created by lixingxing at 2019/2/20

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File LocationL: # Enter

"""
import csv
import os
import re
from collections import Counter

from image_handlers.image_ocr import YidaoOCR
from image_handlers.ocr_correction.connect_split_word import connect_split_word_main
from image_handlers.ocr_correction.correct_eng_words import correction, clean_words_in_dict
from image_handlers.ocr_correction.cut_no_space_text import segment_correct_text
from path import root

CLEAN_PATTEN = r'[a-zA-Z/[0-9/.]+'
WORDS = Counter(clean_words_in_dict())


def delete_rule(word):
    if word is not '':
        if word[-1] is '.':
            word = word[:-1]
        elif word[0] is '.':
            word = word[1:]
        elif word is '.':
            word = ''
    return word


def correct_text(text):
    return re.sub(CLEAN_PATTEN, correct_match, text)


def correct_match(match):
    # print(match)
    word = match.group()
    word = delete_rule(word)
    num_loc = [f.span() for f in re.finditer('[0-9]', word)]
    chr_loc = [f.span() for f in re.finditer('[a-zA-Z]', word)]
    if bool(num_loc) and len(word) < 5 and bool(chr_loc):
        letters = ''.join(re.findall('[a-zA-Z]', word))
        numbers = ''.join(re.findall('[0-9]', word))
        num_end_loc = num_loc[-1][1]
        if num_end_loc == len(word):
            new_word = letters + numbers
            return case_of(new_word)(correction(letters.lower()) + numbers)
        else:
            new_word = numbers + letters
            return case_of(new_word)(numbers + correction(letters.lower()))
    else:
        return case_of(word)(correction(word.lower()))


def case_of(text):
    return (str.upper if text.isupper() else
            str.lower if text.islower() else
            str.title if text.istitle() else
            str)


def target_reader(target_file_path):
    target = []
    with open(target_file_path) as f:
        csv_file = csv.reader(f)
        next(csv_file)
        for csv_f in csv_file:
            target.append(csv_f[-1].split(' '))
    return target


def include_numbers(s):
    num_re = re.findall(r'[0-9]+', s)
    dot_re = re.findall(r'\.', s)
    return bool(num_re and dot_re)


def correct_ocr_output(ocr_output_dict):
    ocr_output_original = [value.split(' ') for value in ocr_output_dict.values()]
    # print(ocr_output_original)
    ocr_correct = [correct_text(value).split(' ') for value in ocr_output_dict.values()]
    for line_num in range(len(ocr_correct)):
        correct_line = ocr_correct[line_num]
        ocr_original_line = ocr_output_original[line_num]
        for word_num in range(len(correct_line)):
            correct_word = correct_line[word_num]
            ocr_original_word = delete_rule(ocr_original_line[word_num])
            if not include_numbers(ocr_original_word):
                clean_correct = ' '.join(re.findall(CLEAN_PATTEN, correct_word)).lower()
                if WORDS[clean_correct]:
                    # print(WORDS[clean_correct])
                    ocr_output_original[line_num][word_num] = correct_word
                elif len(clean_correct) > 15:
                    print('I am working on splitting words')
                    segmented_words = segment_correct_text(clean_correct)
                    ocr_output_original[line_num][word_num] = segmented_words
            else:
                ocr_output_original[line_num][word_num] = ocr_original_word
    corrected_ocr_output = [' '.join(o) for o in ocr_output_original]
    # print(corrected_ocr_output[0])
    # print([connect_split_word_main(corrected_ocr_output[0])])
    return corrected_ocr_output


def corrector_main(ocr_output_dict):
    """

    :param ocr_output_dict:
    :return: new_output:corrected ocr result format is {(location): text}
    """
    new_output = {}
    i = 0

    corrected_texts = correct_ocr_output(ocr_output_dict)
    for k in ocr_output_dict.keys():
        new_output[k] = corrected_texts[i]
        i += 1
    return new_output


def evaluation(ocr_target_path, correct_output):
    ocr_target = target_reader(ocr_target_path)
    target = [delete_rule(j) for i in ocr_target for j in i]
    total_num = 0
    correct_num = 0

    for i_word in range(len(correct_output)):
        total_num += 1
        if correct_output[i_word] == target[i_word]:
            correct_num += 1
    acc = correct_num / total_num
    return acc


if __name__ == '__main__':
    # import pandas as pd
    import time

    start_time = time.time()
    # file_name = 'ocr_output.pkl'
    # ocr_output_path = os.path.join(root, 'image_handlers', 'ocr_correction', 'data', file_name)
    # ocr_target_path = os.path.join(root, 'image_handlers', 'ocr_correction', 'data', 'label', '7.txt')
    #
    # input_image_path = os.path.join(root, 'image_handlers', 'data', 'OCR23S_YI', '7.png')
    # # my_ocr = YidaoOCR(input_image_path, [0,0])
    # # ocr_output_dict = my_ocr.main_ocr()
    # ocr_output_dict = {(1, 2, 3, 4): 'DESCR IPT ION', (4, 5, 6, 7): 'Gol den Finger', (5, 6, 7, 8): 'Conft qurat ion'}
    # c = corrector_main(ocr_output_dict)
    ocr_o = {(161, 18, 676, 32): 'DataorProdurtion Approval of N w Orders'}
    print(corrector_main(ocr_o))

    # print(c)
    print('-----time cost(s): {}-----'.format(time.time() - start_time))
