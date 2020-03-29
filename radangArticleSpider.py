from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from lxml import html
import time
import os

from myGastritis.settings import BASE_DIR

if __name__ == "__main__":
    # 定义一个driver，模拟启动浏览器
    driver = webdriver.Chrome()
    url = "https://www.ncbi.nlm.nih.gov/books/?term=gastritis"
    driver.get(url)
    # 找到包含所有书本名称信息的id为maincontent的div标签
    # data=driver.find_elements_by_id('maincontent')
    # 生成当前页面快照并保存
    # driver.save_screenshot("booklist.png")
    # booklis=driver.get_screenshot_as_file('booklist.png')
    # print("*"*50)
    # print(booklis)
    # id=pageno是该页面页数搜索框，输入数字可以跳到相应页面
    # pages = driver.find_elements_by_id('pageno')
    # print("*"*50)
    # print(pages)
    # for single_page in pages:
    #     single_page.send_keys(u"1")
    #     driver.save_screenshot("page1.png")
    #     pag = driver.get_screenshot_as_file('page1.png')
    #     print("1" * 50)
    #     print(pag)
    # driver.find_elements_by_id('pageno').send_keys(Keys.RETURN)
    # driver.find_elements_by_id('pageno').submit()
    # 定义etree
    etree = html.etree
    html = driver.page_source
    page = etree.HTML(html)
    booklist = page.xpath("//div[@id='maincontent']//div[@class='rprt']//a//@href")
    print("1" * 50)
    print(booklist)
    for book in booklist:
        base_url = 'https://www.ncbi.nlm.nih.gov/'
        new_url = base_url + book
        driver.get(new_url)
        html2 = driver.page_source
        bookcontent = etree.HTML(html2)
        table_content = bookcontent.xpath("//div[@class='rsltcont']//p[2]/a/@href")
        print(table_content)
        newest_url = base_url + table_content
        driver.get(newest_url)
        html3 = driver.page_source
        discription_page = etree.HTML(html3)
        discription = discription_page.xpath("//div[@class='body-content whole_rhythm']//div[1]/p/text()").strip()
        book_name = discription_page.xpath("//div[@class='icnblk_cntnt']/h1[@id='_NBK487782_']/span/text()").strip()
        print(book_name)
        # 开始导入translate
        import translate

        # 指定翻译的语言
        tran = translate.Translator(to_lang='Chinese')
        # translate只能翻译250个字符，所以要把句子分割
        new_discription = discription.split(',')
        grap = ''
        for sentence in new_discription:
            content = tran.translate(new_discription)
            grap += content + ','
            graph = grap[:-1] + '。'
            with open(os.path.join(BASE_DIR, 'files/' + book_name + '.txt'), 'w', encoding="utf8")as f:
                f.write(graph)
