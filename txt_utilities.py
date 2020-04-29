# Created by hudiibm at 2019/1/7
"""
Feature: #Enter feature name here
# Enter feature description here
Scenario: #Enter scenario name here
# Enter steps here
Test File Location: # Enter]
"""
import re
from difflib import SequenceMatcher
from nltk.stem.snowball import SnowballStemmer

LONG_TEXT_IDENTIFIER = [',', '，', '。', ';', '；', '、']

COLON = [':', '：']

PARAM_UNIT = ['um', 'mm', 'V', 'inch²', '℃', 'Mohm', 'H', 'oz', 's', '个/mm²', '㎡', 'V/s', 'mil', 'ohm',
              'ugNaCl/cm²', 'inch', '°', '%', '小时', 'ASF', 'Hz', 'GHz', 'Kg/mm²', '分钟', '°C', 'mA', 'henry',
              'mm/inch', 'HV', 'm', 'MΩ', 'V-CUP', '层', '个']

SPECIAL_PARAM_LIST = ['数']


def split_by_colon(val):
    # 将包含冒号的token内容拆分成两个token
    return re.split(r'[：:]', val)


def required_to_split_by_colon(val):
    if val and isinstance(val, str) and any_item_be_contain(COLON, val):
        result_list = list(filter(None, split_by_colon(val.strip())))
        if len(result_list) == 2 and not any_item_be_contain(LONG_TEXT_IDENTIFIER, result_list[0]) \
                and not any_item_be_contain(LONG_TEXT_IDENTIFIER, result_list[1]) \
                and not contain_multi_right_bracket(result_list[0]) \
                and not contain_multi_right_bracket(result_list[1]) \
                and not (contain_left_bracket(result_list[0]) and contain_right_bracket(result_list[1])):
            return True
        else:
            return False
    else:
        return False


def contain_multi_right_bracket(str):
    right_bracket = [')', '）']
    if any_item_be_contain(right_bracket, str):
        if str.count(right_bracket[0]) > 1 or str.count(right_bracket[1]) > 1:
            return True
    return False


def contain_left_bracket(str):
    left_bracket = ['(', '（']
    if any_item_be_contain(left_bracket, str):
        return True
    return False


def contain_right_bracket(str):
    right_bracket = [')', '）']
    if any_item_be_contain(right_bracket, str):
        return True
    return False


def have_chinese_(input_string):
    pattern = u'[\u4e00-\u9fff]+'
    found_chinese = re.findall(pattern, input_string)
    return True if found_chinese else False


def find_chinese(input_string):
    pattern = u'[\u4e00-\u9fff]+'
    found_chinese = re.findall(pattern, input_string)
    return found_chinese


assert have_chinese_('alsdfj动力反馈')
assert have_chinese_('ajldfj') is False
assert have_chinese_('alsdfj。') is False


def remove_serial_num(s):
    # if re.findall(layscount_pattern, s):
    #     return s
    pattern = u'^\d+\.?[\d+]*([\u4e00-\u9fff\W\w]+|.{4,})'
    result = re.findall(pattern, s)
    if len(result) > 0:
        return result[0]
    return s


assert remove_serial_num('1.2你好') == '你好'
assert remove_serial_num('2你好') == '你好'
assert remove_serial_num('12.3你好') == '你好'
assert remove_serial_num('12.你好') == '你好'
assert remove_serial_num('1.23你好abc') == '你好abc'


def remove_before_num(s):
    if have_chinese_(s):
        ls = list(filter(None, re.split('\u3000| ', s, 1)))
        # 例：1.0  公司名称 ->符合条件
        # 例: 4 mil微孔电镀填铜 ->不符合条件
        # 例: 4 层 ->不符合条件
        # 例: 4.1 层数 ->符合条件
        # 例:15 .过孔是否覆盖阻焊 -> 不符合条件
        if len(ls) == 2 and is_number(ls[0]) \
                and (not any_item_start_with(PARAM_UNIT, ls[1].strip())
                     or any_item_start_with(SPECIAL_PARAM_LIST, replace_all(PARAM_UNIT, ls[1].strip()))) \
                and ls[1].find('.') == -1:
            return ls[1]
        ls = list(filter(None, re.split(r'[.、．]', s, 1)))
        # 例：1.一般信息 -> 符合条件
        # 例：14、是否加生产年周 -> 符合条件
        # 例：15 .过孔是否覆盖阻焊 -> 符合条件
        # 例：0.5（L11.L12按照1OZ处理） -> 不符合条件
        if len(ls) == 2 and is_number(ls[0]) and not is_number(ls[1][0:1]):
            return re.sub('[:：]', '', ls[1])
    return s


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False


def repair_num_str(s):
    if not isinstance(s, str):
        s = str(s)
    if s.strip().endswith('.0'):
        return s[0:s.find('.0')]
    else:
        return s


def remove_num(s):
    # if re.findall(layscount_pattern, s):
    #     return s
    pattern = u'[\d+]?([\u4e00-\u9fff]+|.{4,})[\d+]?'
    result = re.findall(pattern, s)
    if len(result) > 0:
        return result[0]
    return s


# print(remove_num('1.2你好'))
# assert remove_num('1.2你好') == '.你好'
# assert remove_num('2你好') == '你好'
# assert remove_num('12.3你好') == '.你好'
# assert remove_num('12.你好') == '你好'


def remove_text_in_parenthesis(s):
    regex = re.compile(".*?\((.*?)\)")

    s = s.replace('（', '(')
    s = s.replace('）', ')')
    result = re.findall(regex, s)

    start = s.find('(')
    end = s.find(')')
    if start != -1 and end != -1:
        result = s[:start] + s[end + 1:]

    return result or s


def stemmer(en_text):
    stemmer = SnowballStemmer("english")
    return ' '.join([stemmer.stem(w) for w in en_text.split(' ')])


def pretreat_txt(text):
    text = str(text).strip()
    text = text.lower()
    if have_chinese_(text):
        text = text.replace(' ', '')
        text = text.replace('\n', '')
        text = text.replace(':', '')
        text = remove_serial_num(text)
        text = remove_num(text)
    else:
        text = text.replace('\n', ' ')
        text = text.replace(':', ' ')
        text = stemmer(text)
    text = remove_text_in_parenthesis(text)
    return text


assert pretreat_txt('新单工程要求(请分条分类填写,每个订单不能超过3条)') == '新单工程要求'


def pretreat_text_dict(text_dict):
    for key in text_dict.keys():
        text_dict[key] = pretreat_txt(text_dict[key])
    return text_dict


def unit_seperitors(text):
    text = str(text)
    text = text.replace('；', '|')
    text = text.replace(',', '|')
    text = text.replace('、', '|')
    text = text.replace('，', '|')
    text = text.replace('\r', '|')
    return text


def clean_nameinsys(text):
    text = str(text)
    text = text.replace(':', '')
    text = text.replace('/', '')
    return text


def clean_colon(text):
    text = str(text)
    text = text.replace(':', '')
    text = text.replace('：', '')
    text = remove_serial_num(text)
    text = remove_serial_num(text)
    return text.strip()


def clean_colon_only(text):
    text = str(text)
    text = text.replace(':', '')
    text = text.replace('：', '')
    return text.strip()


def clean_tail_colon(text):
    if any_item_end_with(COLON, text):
        str_list = list(text)
        return ''.join(str_list[0:-1])
    else:
        return text


def remove_space(val):
    if have_chinese_(val):  # 英文单不能去除单词间的空格
        val = val.replace(' ', '')
    else:
        val = val.strip()
    return val


def convert_none_to_empty(s):
    str = '' if (s is None or s == 'None') else s
    return str


def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


assert similarity('see', 'sea') > similarity('s', 'sea')
assert similarity('一根藤上七朵花', '一根藤上哒哒哒') > similarity('啦啦啦啦啦', '葫芦娃')


def jaccard_list(a, b):
    # a,b must be a list
    return len(list(set(a).intersection(set(b)))) / len(list(set(a).union(set(b))))


def similar_to_any_elements(input_string, elements):
    return any(similarity(input_string, l) > 0.6 for l in elements)


assert similar_to_any_elements('see', ['sea', 'd', 'gd'])


def any_item_be_contain(str_list, target_string):
    if isinstance(target_string, str):
        for i in str_list:
            if i in target_string:
                return True
            else:
                continue
    return False


def replace_all(str_list, target_string):
    for i in str_list:
        target_string = re.sub(i, '', target_string)
    return target_string


def get_match_str(str_list, target_string):
    if isinstance(target_string, str):
        for i in str_list:
            if i in target_string:
                return i
    return None


def any_item_start_with(str_list, target_string):
    for s in str_list:
        if target_string.startswith(s):
            return True
        else:
            continue
    return False


def any_item_end_with(str_list, target_string):
    for s in str_list:
        if target_string.endswith(s):
            return True
        else:
            continue
    return False


def any_item_be_equal(str_list, target_string):
    if isinstance(target_string, str):
        for i in str_list:
            if i == target_string:
                return True
            else:
                continue
    return False


def all_item_be_contain(str_list, target_string):
    for s in str_list:
        if s not in target_string:
            return False
        else:
            continue
    return True


assert any_item_be_contain(['字符', '丝印', 'silkscreen'], '字符')
assert any_item_be_contain(['字符', '丝印', 'silkscreen'], 'silkscreen')

if __name__ == '__main__':
    s2 = 'alsdfj动力反馈4 mil微孔电镀填铜'
    print(find_chinese(s2))
