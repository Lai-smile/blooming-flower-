"""
记录长文本所需常量配置信息

"""

LONG_MARK = 'LONG_MARK'
LONG_MARK_START_CONTENT = 'LONG_MARK_START_CONTENT'

LNG_TEXT_CN = '长文本'
LNG_TEXT_PARAMETER_ID = 1010

# 多句话合并为一段长文本做为特殊要求时，通过空格' '分割
LNG_TEXT_SPECIAL_REQUEST_SPLIT = ' '

# 句子之间的分割符
# \\$\\$ 当多行的句子合并时
# \n 当Excel一个单元格里出现多行时
# '    ' 解决当多句话出现在一个单元格中，用空格分开换行的问题
LNG_TEXT_DEFAULT_SENTENCE_SPLIT_SYMBOL = ['\\$\\$', '\n', '\t', '    ']


LNG_TEXT_RULE_MATCH_DIRECTION_RIGHT = 'R'
LNG_TEXT_RULE_MATCH_DIRECTION_LEFT = 'L'
