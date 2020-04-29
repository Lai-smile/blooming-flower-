
from enum import Enum


ROOT = "/auto-pcb/api/"
ROOT_GERBER = "/auto-pcb-gerber/api/"
VERSION = '1.0'


RULE_OLD_SERVER = "http://192.168.230.52/DecisionService/rest/ProductStandard/1.0/Prequalification/1.0"

RULE_SERVER = "http://192.168.230.52/DecisionService/rest/EngineerRuleApp/1.0/EngineerRuleSet/1.1"


# HTTP request rtn code, msg
SUCCESS = {'code': 200, 'msg': 'SUCCESS'}
ERR_PARAM = {'code': 400, 'msg':  '参数校验异常'}
ERR_AUTH = {'code': 401, 'msg': '用户没有权限'}
ERR_FORBIDDEN = {'code': 403, 'msg': '访问是被禁止'}
ERR_NOT_FOUND = {'code': 404, 'msg': '资源不存在'}
ERR_REQUEST_FORBIDDEN = {'code': 429, 'msg': '请求过多，超过访问速率限制'}

ERR_SYS_SERVER = {'code': 500, 'msg': '服务端非业务异常'}
ERR_SYS_FILE_SERVER = {'code': 501, 'msg': '订单文件参数提取失败'}
ERR_SYS_ORDER_STATUS = {'code': 551, 'msg': '更新订单状态失败， 请稍后再试'}

ERR_DB_SERVER = {'code': 550, 'msg': '数据库服务异常'}
