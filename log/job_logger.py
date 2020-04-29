import logging
import datetime
import logging.handlers


logger = logging.getLogger("scheduler")
logger.setLevel(logging.INFO)


# 日志文件达到10M后，自动生成新文件
handler = logging.handlers.RotatingFileHandler("/home/log/job.log", maxBytes=10*1024*1024, backupCount=10000)
# 设置文件达到10M后重命名的文件名
handler.namer = lambda x: x.split(".")[0] + '_' + datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S.%f') + '.' + \
                          x.split(".")[1]
handler.setLevel(logging.INFO)

# 设置日志格式
formatter = logging.Formatter(
    '%(asctime)s - %(processName)s - %(threadName)s - %(filename)s - %(funcName)s - %(levelname)s - %(message)s',
    datefmt='%Y/%m/%d %H:%M:%S')
handler.setFormatter(formatter)

# 将相应的handler添加在logger对象中
logger.addHandler(handler)
