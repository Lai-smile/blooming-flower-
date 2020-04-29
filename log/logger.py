import logging
import config
import datetime
import os
import logging.handlers
import bottle
from config.config import config

logger = logging.getLogger("auto-pcb-ii")
logger.setLevel(logging.INFO)

log_path = config().get('log_path')

# added by zhoulong
# if not os.path.exists(log_path[:log_path.rfind(os.sep)+1]):
#     os.makedirs(log_path[:log_path.rfind(os.sep)+1])
#     with open(log_path, mode="w", encoding="utf-8") as f:  # 写文件,当文件不存在时,就直接创建此文件
#         pass

# 日志文件达到10M后，自动生成新文件
handler = logging.handlers.RotatingFileHandler(log_path, maxBytes=10*1024*1024, backupCount=10000)
# 设置文件达到10M后重命名的文件名
handler.namer = lambda x: x.split(".")[0] + '_' + datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S.%f') + '.' + x.split(".")[1]
handler.setLevel(logging.DEBUG)

# 设置日志格式
formatter = logging.Formatter(
    '%(asctime)s - %(processName)s - %(threadName)s - %(filename)s - %(funcName)s - %(levelname)s - %(message)s',
    datefmt='%Y/%m/%d %H:%M:%S')
handler.setFormatter(formatter)

# 将相应的handler添加在logger对象中
logger.addHandler(handler)
