import os
import patoolib

base_url = "F:\B074"
unzip_high_url = "F:\B074_originalI_file"
#列出压缩包内的文件
# patoolib.list_archive("package.deb")
def decompress_file(filename):
    #先判断文件类型
    if filename.endswith('zip') or filename.endswith('ZIP') or filename.endswith('rar'):
        # 获取文件名的绝对路径
        file_abs_path = os.path.abspath(filename)
        try:
            child_file = patoolib.extract_archive(file_abs_path,unzip_high_url)
            decompress_file(child_file)
        except Exception:
            print('文件格式不正确，无法解压！')


