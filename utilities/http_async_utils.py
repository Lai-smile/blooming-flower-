import time
import asyncio
import chardet
from aiohttp import ClientSession
from aiohttp.client_exceptions import ContentTypeError

from log.logger import logger


def hello():
    time.sleep(1)


def run():
    for i in range(5):
        hello()
        print('Hello World:%s' % time.time())


# 定义异步函数
async def async_hello():
    asyncio.sleep(1)
    print('Hello World:%s' % time.time())


def async_run():
    loop = asyncio.get_event_loop()
    for i in range(5):
        loop.run_until_complete(async_hello())


async def get_url_content(url, index):
    async with ClientSession() as session:
        async with session.get(url) as response:
            # response = await response.read()
            # print(response)
            print('Hello World:%s' % index)

            return await response.read()


async def get_url_content_with_max_concurrent_num(url, concurrent_num, index):
    async with concurrent_num:
        async with ClientSession() as session:
            async with session.get(url) as response:
                print('Hello World:%s' % index)
                return await response.text("utf-8", "ignore")


async def post_json(url, params, semaphore_num=500):
    logger.info(f"async_post_json url is {url} params are {params}")
    semaphore = asyncio.Semaphore(semaphore_num)
    async with semaphore:
        async with ClientSession() as session:
            try:
                async with session.post(url, json=params) as resp:
                    try:
                        return await resp.json()
                    except ContentTypeError as e:
                        logger.exception(f'Result is not json formatted, {e}')
                        return  # await resp.text()
            except asyncio.TimeoutError as e:
                logger.exception(f'current request timeout. params is {params}')


if __name__ == '__main__':
    async_run()

    url = "https://www.baidu.com/{}"

    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(get_url_content(url))
    #
    # print('test result')

    # 批量请求
    loop = asyncio.get_event_loop()

    tasks = []

    concurrent_num = asyncio.Semaphore(100)

    for i in range(2):
        task = asyncio.ensure_future(get_url_content_with_max_concurrent_num(url.format(i), concurrent_num, i))
        tasks.append(task)
    loop.run_until_complete(asyncio.wait(tasks))

    # to_get = [hello(url.format(), concurrent_num, index) for index in range(200)]

    result = loop.run_until_complete(asyncio.gather(*tasks))

    print(result)

    loop.close()

    a = "\u6210\u54c1\u5b54\u5f84"
    print(a)

    b = bytes(b"\u6210\u54c1\u5b54\u5f84")

    print(b.decode(encoding='ascii'))

    print("\\u6210\\u54c1\\u5b54\\u5f84")
    print("\\u6210\\u54c1\\u5b54\\u5f84".encode('ascii').decode('utf-8'))
    print("\\u6210\\u54c1\\u5b54\\u5f84".encode('utf-8').decode())
