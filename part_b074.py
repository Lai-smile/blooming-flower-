import os
from threading import Thread
import numpy as np
import pandas as pd
from win32com import client as wc

base_url = "F:\B074"
unzip_url = r"F:\B074_unzip\\"  # 一次解压后的新文件保存的路径
unzip_high_url = "F:\B074_originalI_file"  # 二次解压后的新文件保存的路径
dirs = os.listdir(base_url) #原始订单名列表
basic_url=r'C:\Users\Administrator\Desktop\bo74-PART'
srcond_dirs = os.listdir(basic_url)
one_zip_path=[] #原始文件名列表
original_order_list=[] #要提取的文件名列表
customer_code_list = [] #客户代码
for filename in dirs:
    customer_code = filename.split('.')[0][2:5]
    customer_code_list.append(customer_code)

for second_dir in srcond_dirs:
    for dir in dirs:
        if second_dir.split(' ')[-1] ==dir:
             one_zip_path.append(second_dir+'.zip')

full_path=r''
for full_name in srcond_dirs:
    full_path=os.path.join(basic_url,full_name)
    if len(os.listdir(full_path))>1:
        for file_document in os.listdir(full_path):
            if file_document.endswith('doc'):
                original_order_list.append(file_document)

content_list=[] #提取项
for doc in original_order_list:
    if os.path.join(full_path,doc)==True:
        with open(os.path.join(full_path,doc)) as f:
            w = wc.Dispatch('Word.Application')
            document = w.Documents(unzip_high_url + str(doc))  # 读入文件
            tables = document.tables  # 获取文件中的表格集
            table = tables[0]  # 获取文件中的第一个表格
            if table.cell(5, 0).text=='工程要求' or table.cell(5, 0).text=='技术要求':
                WorksRequirements_0 = table.cell(5, 0).text  # 工程要求或技术要求,cell(5,0)表示第6行第1列数据，以此类推
                WorksRequirements_1 = table.cell(5, 1).text  # 工程要求或技术要求内容
                specialThings_0 = table.cell(6, 0).text  # 注意事项
                specialThings_1 = table.cell(6, 1).text  # 注意事项内容
                content = {WorksRequirements_0: WorksRequirements_1, specialThings_0: specialThings_1}
                content_dict = {doc: content}
                content_list.append(content_dict)

data_df = pd.DataFrame(
    np.arange(6315).reshape(1263, 5),
    # columns=[
    #     '客户代码',
    #     '原始订单名',
    #     '原始文件名',
    #     '要提取的文件名',
    #     '提取项',
    # ]
)
print(one_zip_path)
print(original_order_list)
print(content_list)
data_df.insert(0,'客户代码',customer_code_list)
data_df.insert(1,'原始订单名',dirs)
data_df.insert(2,'原始文件名',one_zip_path)
data_df.insert(3,'要提取的文件名',original_order_list)
data_df.insert(4,'提取项',content_list)
print(data_df)
writer = pd.ExcelWriter('BO74_data.xlsx')
data_df.to_excel(writer, float_format='%.5f')
writer.save()