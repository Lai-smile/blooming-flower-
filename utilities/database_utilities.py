# Created by hudiibm at 2018/12/26
"""
Feature: #Enter feature name here
# Enter feature description here
Scenario: #Enter scenario name here
# Enter steps here
Test File Location: # Enter]
"""
import pandas as pd
import os
import re
from db_server.parmeter.Parameter import get_parameter_id
from db_server.utils import db_connect

os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'

# host = db_connect.host
# port = db_connect.port
# sid = db_connect.sid
# dsn = cx_Oracle.makedsn(host, port, sid)
#
# username = db_connect.username
# password = db_connect.password


def query(sql):
    """
    sql = 'select * from '+ table
    :param sql:
    """
    print(f"db utils query sql is {sql}", )

    conn = db_connect.oracle_connect()

    results = pd.read_sql(sql, conn)
    # conn.close
    return results

#
# def update(update_sql):
#     """
#     update_sql = "update GCZDH_PARAMETER_ADD_ALIAS " \
#                  "set PARAMETER_ALIAS='%s' " \
#                  "where PARAMETER_NAME = '%s'" % (alias, param_name)
#     :param update_sql
#     """
#     env_ = bottle.default_app().config.get('env')
#     conf = config(env_)
#     host = conf.get('host')
#     port = conf.get('port')
#     sid = conf.get('sid')
#
#     dsn = cx_Oracle.makedsn(host, port, sid)
#     username = conf.get('username')
#     password = conf.get('password')
#     conn = cx_Oracle.connect(username, password, dsn)
#
#     cr = conn.cursor()
#     cr.execute(update_sql)
#
#     cr.close()
#     conn.commit()


try:
    param_df = query('select * from PCB_PARAMETER')
    option_df = query('select * from PCB_PARAMETER_OPTION')
    value_df = query('select * from GCZDH_VALUE_OPTION_LIST')
except:
    import constants.path_manager as path

    param_df = pd.read_csv(path.FAKE_DB_PARAMETER)
    option_df = pd.read_csv(path.FAKE_DB_OPTION_LIST)
    value_df = pd.read_csv(path.FAKE_DB_OPTION_LIST)


def get_param_info(parameter_name):
    param_type, param_units, param_options = None, [], []
    try:
        row = param_df[param_df['PARAMETER_NAME'] == parameter_name]

        param_type = row['PARAMETER_TYPE'].iloc[0]

        unit = str(row['PARAMETER_UNIT'].iloc[0])
        if unit == 'None':
            unit = ''
        units_add = str(row['PARAMETER_UNIT_ETC'].iloc[0])
        if units_add == 'None':
            units_add = ''
        if unit:
            if units_add:
                param_units = [unit] + units_add.split('|')
            else:
                param_units = [unit]
        else:
            param_units = []

        param_options = option_df[option_df['PARAMETER_NAME'] == parameter_name]['OPTION_NAME'].tolist()
        options_add = option_df[option_df['PARAMETER_NAME'] == parameter_name]['OPTION_NAME_ALIAS'].tolist()
        for option in options_add:
            if option:
                option = str(option)
                for o_a in option.split('|'):
                    param_options.append(o_a)
    except:
        return param_type, param_units, param_options
    # print(param_type, param_units, param_options)
    return param_type, param_units, param_options


def get_options_by_parameter_name(parameter_name):
    # [['黄色', 'YELLOW SOLDERMASK'], ['红色', 'RED SOLDERMASK']]
    result = []
    # ['黄色', 'YELLOW SOLDERMASK']

    option_rows = option_df[option_df['PARAMETER_NAME'] == parameter_name]
    row_count = option_rows.shape[0]
    for i in range(row_count):
        row = []
        row.append(option_rows['OPTION_NAME'].iloc[i])
        row.append(option_rows['OPTION_NAME_EN'].iloc[i])
        result.append(row)
    return result


def get_param_val_by_en_val(st_param_nm, en_val):
    supper_en_val = en_val.strip().upper()
    options = get_options_by_parameter_name(st_param_nm)
    st_param_val = ''
    for option in options:
        if option[1]:
            sub_vals = re.split('\|', option[1])
            for val in sub_vals:
                if val.strip().upper() == supper_en_val:
                    st_param_val = option[0]
                    break
    if st_param_val:
        return st_param_val
    else:
        return en_val


def get_eng_candidate_value(parameter_name):
    candidate_value_dict = value_df[value_df['PARAMETER_NAME'] == parameter_name][
        ['PARAMETER_LIST_CONTENT', 'PARAMETER_LIST_CONTENT_EN']].set_index('PARAMETER_LIST_CONTENT').T.to_dict('list')
    candidate_value_dict = {k: v[0].lower().split('|') for k, v in candidate_value_dict.items() if v[0] is not None}
    return candidate_value_dict


def get_ch_candidate_value(parameter_name):
    candidate_value_dict = value_df[value_df['PARAMETER_NAME'] == parameter_name][
        ['PARAMETER_LIST_CONTENT', 'PARAMETER_LIST_CONTENT_ALIAS']].set_index('PARAMETER_LIST_CONTENT').T.to_dict(
        'list')
    candidate_value_dict = {k: v[0].lower().split('|') for k, v in candidate_value_dict.items() if v[0] is not None}
    return candidate_value_dict


def get_candidate_values_from_db(parameter_name):
    candidate_value_dict = value_df[value_df['PARAMETER_NAME'] == parameter_name][
        ['PARAMETER_LIST_CONTENT', 'PARAMETER_LIST_CONTENT_EN']].set_index('PARAMETER_LIST_CONTENT').T.to_dict('list')
    candidate_values = [v[0].lower().split('|') for k, v in candidate_value_dict.items() if v[0] is not None]

    candidate_value_dict = value_df[value_df['PARAMETER_NAME'] == parameter_name][
        ['PARAMETER_LIST_CONTENT', 'PARAMETER_LIST_CONTENT_ALIAS']].set_index('PARAMETER_LIST_CONTENT').T.to_dict(
        'list')
    candidate_values += [v[0].lower().split('|') for k, v in candidate_value_dict.items() if v[0] is not None]

    candidate_values = sum(candidate_values, [])
    return candidate_values


def get_copper_value_from_db(parameter_name):
    """
    :param parameter_name: 基铜厚度
    :return:    {0.33: [min_value, max_value],  ...}
    """
    candidate_values_dict = value_df[value_df["PARAMETER_NAME"] == parameter_name]
    corper_values = candidate_values_dict['PARAMETER_LIST_CONTENT']

    return corper_values


if __name__ == '__main__':
    print(get_parameter_id('外层基铜厚度'))
