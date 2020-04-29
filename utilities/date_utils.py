import time
import re


def compare_time(time1,time2):
    date_separator = '/|-'
    time1 = re.sub(date_separator, '', time1)
    time2 = re.sub(date_separator, '', time2)
    s_time = time.mktime(time.strptime(time1, '%Y%m%d'))
    e_time = time.mktime(time.strptime(time2, '%Y%m%d'))

    return int(s_time) - int(e_time)