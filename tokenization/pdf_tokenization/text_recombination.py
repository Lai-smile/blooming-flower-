# Created by yuwenhao at 18/01/2019
# coding =utf-8

from tokenization.token import get_token_obj
import math


def get_partial_text(text, n=0): return text.split('\n')[n]


def get_enter_count(input_str): return input_str.count('\n')


def get_len(x1, y1, x2, y2):
    return float('%.2f' % math.sqrt(((x2 - x1) ** 2) + ((y2 - y1) ** 2)))


def get_sort_key(elem, position):
    return elem[1] if position == 1 else elem[2] if position == 2 else elem[0]


def is_overlap(tuple_1, tuple_2):
    rec_1, rec_2 = get_token_obj(tuple_1), get_token_obj(tuple_2)
    return True if (rec_2.x1 < rec_1.x2) and (rec_1.x1 < rec_2.x2) \
        and (rec_2.y1 < rec_1.y2) and (rec_1.y1 < rec_2.y2) else False


def is_redundant(input_list, input_str):
    return any((input_str in item and input_str != item) for item in input_list)


def drop_redundant(input_str):
    input_list = input_str.split('\n')
    map_list = [is_redundant(input_list, item) for item in input_list]
    return [i for i, j in zip(input_list, map_list) if j is False]


def overlap_recombination(i):
    enter_count = (get_enter_count(i.content))
    height = (i.x2 - i.x1) / enter_count

    output_list = []
    for j in range(enter_count):
        output_list += [(i.x0, round(i.x1 + height * j, 2), round(i.y1, 2),
                         round(i.x1 + height * (j + 1), 2), round(i.y2, 2), get_partial_text(i.content, j))]

    return output_list


def text_recombination(input_list):

    output_list = []

    for item in input_list:
        i = get_token_obj(item)
        content = '\n'.join(drop_redundant(i.content)) + '\n'

        if len(content) == 2 * get_enter_count(content):
            output_list += [(i.x0, i.x1, i.y1, i.x2, i.y2, ''.join(content.split('\n')))]
            continue

        if get_enter_count(content) <= 1:
            output_list += [(i.x0, i.x1, i.y1, i.x2, i.y2, get_partial_text(content))]

        elif get_enter_count(content) > 1:
            output_list += overlap_recombination(i)

    output_list.sort(key=lambda x: (get_sort_key(x, 0), get_sort_key(x, 1), -get_sort_key(x, 2)))

    return output_list



