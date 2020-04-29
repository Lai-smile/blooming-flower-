# Created by Wenhao at 2019-04-02
"""
Feature: #Enter feature name here
# Enter feature description here
Scenario: #Enter scenario name here
# Enter steps here
Test File Location: # Enter]
"""

import unicodedata
import re

CN_NUM_DIC = {
    '〇': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '零': 0,
    '壹': 1, '贰': 2, '叁': 3, '肆': 4, '伍': 5, '陆': 6, '柒': 7, '捌': 8, '玖': 9, '貮': 2, '两': 2,
}

CN_NUM = ['〇', '一', '二', '三', '四', '五', '六', '七', '八', '九', '零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖', '貮', '两', '单面', '双']

CN_UNIT = {
    '十': 10,
    '拾': 10,
    '百': 100,
    '佰': 100,
    '千': 1000,
    '仟': 1000,
    '万': 10000,
    '萬': 10000,
    '亿': 100000000,
    '億': 100000000,
    '兆': 1000000000000,
}


def is_number(content):
    return all(48 <= ord(c) <= 57 for c in content)


def is_num(num):
    pattern = re.compile(r'^[-+]?[-0-9]\d*\.\d*|[-+]?\.?[0-9]\d*$')
    result = pattern.match(num)
    if result:
        return True
    else:
        return False


def has_number(i_str):
    return bool(re.search(r'\d', i_str))


def adjust_wrong_number(content):
    new_text = [content[0]]
    for i, val in enumerate(content[1:-1]):
        if val == ',':
            previous = content[i]
            next_ = content[i + 2]
            if is_number(previous) and is_number(next_):
                val = '.'
        new_text.append(val)
    new_text.append(content[-1])
    return ''.join(new_text)


def get_numb_str(string):
    nums = re.findall(r"\d+\.?\d*", string)
    if len(nums) > 0:
        return nums[0]
    else:
        return string


def format_float(num):
    # 去掉浮点数尾部无效的0和无效的‘.’号
    return '{:g}'.format(num)


def chinese_to_arabic(cn: str) -> int:
    unit = 0  # current
    ldig = []  # digest
    for cndig in reversed(cn):
        if cndig in CN_UNIT:
            unit = CN_UNIT.get(cndig)
            if unit == 10000 or unit == 100000000:
                ldig.append(unit)
                unit = 1
        else:
            dig = CN_NUM_DIC.get(cndig)
            if unit:
                dig *= unit
                unit = 0
            ldig.append(dig)
    if unit == 10:
        ldig.append(10)
    val, tmp = 0, 0
    for x in reversed(ldig):
        if x == 10000 or x == 100000000:
            val += tmp * x
            tmp = 0
        else:
            tmp += x
    val += tmp
    return val


def extract_numb(text):
    str_numb = ''
    for char in text:
        if char.isnumeric():
            str_numb += char
    return str_numb


def is_decimal(s):
    """判断字符串是否为小数"""
    s = str(s)
    if s.count('.') == 1:
        left = s.split('.')[0]
        right = s.split('.')[1]
        if right.isdigit():
            if left.count('-') == 1 and left.startswith('-'):
                num = left.split('-')[-1]
                if num.isdigit():
                    return True
            elif left.isdigit():
                return True
    return False


def convert_to_percent(val):
    """将小数转换为百分数"""
    if is_decimal(val):
        if eval(val) < 1:
            val = format_float(eval(val) * 100)
            return str(val) + '%'
        else:
            val = format_float(eval(val))
            return str(val)


if __name__ == '__main__':
    print(chinese_to_arabic(extract_numb('十二层')))
