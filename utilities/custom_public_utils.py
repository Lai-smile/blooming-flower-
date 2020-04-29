from decimal import Decimal

from log.logger import logger
from utilities.txt_utilities import any_item_be_contain, repair_num_str
from utilities.number_utilities import get_numb_str, is_num


COPPER_FOIL_VALUE_LIST = list(range(1, 50))


def convert_standard_value(param_name, param_value, source_param_value=None):
    """
    值转换

    :param param_name: 参数名
    :param param_value: 参数值
    :param source_param_value: 原始参数值
    :return:
    """
    # 铜厚值转换
    standard_value = convert_copper_standard_value(param_name, param_value, source_param_value)
    return standard_value


def convert_copper_standard_value(param_name, param_value, source_param_value=None):
    """
    铜厚值转换
    :param param_name: 参数名
    :param param_value: 参数值
    :param source_param_value: 原始参数值
    :return:
    """
    convert_complete_copper_param_list = ['完成铜厚度']
    convert_base_copper_param_list = ['基铜厚度']
    not_need_convert = {'最小孔铜厚度': ['um']}
    standard_parameter_value = param_value
    if param_name and param_value:
        if param_name in not_need_convert and any_item_be_contain(not_need_convert[param_name], source_param_value):
            return get_numb_str(standard_parameter_value)
        if any_item_be_contain(convert_complete_copper_param_list, param_name):
            num_str = get_numb_str(param_value)
            if is_num(num_str):
                try:
                    num_tmp = repair_num_str(float(num_str))
                    num = eval(num_tmp)
                    # 确认铜厚度单位为um不可能小于12
                    if num < 12:
                        return round(num * 35, 2)
                    else:
                        return num
                except Exception as error:
                    logger.error({f'不能转换成数字，错误信息为:{error}'})
        elif any_item_be_contain(convert_base_copper_param_list, param_name):
            num_str = get_numb_str(param_value)
            if is_num(num_str):
                try:
                    num_tmp = repair_num_str(float(num_str))
                    num = eval(num_tmp)
                    # 确认铜厚度单位为um不可能小于12
                    if num < 12:
                        return num
                    if num == 12:
                        standard_parameter_value = 0.33
                    elif num == 18:
                        standard_parameter_value = 0.5
                    elif num == 50:
                        standard_parameter_value = 1.43
                    else:
                        standard_parameter_value = copper_foil_standard_value_conversion(round(num / 35, 2))
                except Exception as error:
                    logger.error({f'不能转换成数字，错误信息为:{error}'})

    return str(standard_parameter_value)


def copper_foil_standard_value_conversion(need_convert_value):
    """
    铜箔，单位为oz的标准参数值转换
    正确的换算是1OZ=35.4um。也可以按35um计算。换算后按上面就近取值。
    eg: 0.54-->0.5, 1.25-->1.33 , 1.12-->1
    :param need_convert_value: 需要转换的参数值
    :return: 标准参数值
    """
    # 把三个标准小数值加到标准参数值列表中
    standard_float_value = [0.33, 0.5, 1.43]
    # 铜箔标准参数值列表,标准参数值列表
    standard_float_value.extend(COPPER_FOIL_VALUE_LIST)
    copper_foil_value_list = sorted(standard_float_value)
    select = Decimal(str(need_convert_value)) - Decimal(str(copper_foil_value_list[0]))
    index = 0
    for i in range(1, len(copper_foil_value_list) - 1):
        select2 = Decimal(str(need_convert_value)) - Decimal(str(copper_foil_value_list[i]))
        if abs(select) > abs(select2):
            select = select2
            index = i
    return copper_foil_value_list[index]


if __name__ == '__main__':
    result = convert_standard_value('外层完成铜厚度', '35um')
    print('----------' + str(result))
    result = convert_standard_value('外层基铜厚度', '30um')
    print('----------' + str(result))
