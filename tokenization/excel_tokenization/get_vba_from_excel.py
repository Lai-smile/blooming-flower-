# Created by Wenhao at 2019/01/09
# Olevba, tool for extracting Macro in excel, shows source code
from oletools.olevba import VBA_Parser, TYPE_OLE, TYPE_OpenXML, TYPE_Word2003_XML, TYPE_MHTML


def get_vba_source_from_excel(filename):
    vbaparser = VBA_Parser(filename)

    if vbaparser.detect_vba_macros():
        print('VBA Macros found')
    else:
        print('No VBA Macros found')

    for (filename, stream_path, vba_filename, vba_code) in vbaparser.extract_macros():
        print('-' * 79)
        print('Filename    :', filename)
        print('OLE stream  :', stream_path)
        print('VBA filename:', vba_filename)
        print('- ' * 39)
        print(vba_code)


if __name__ == '__main__':
    # filename should be a path of file, not a directory
    filename = '/Users/yuwenhao/Desktop/Test.xls'
    get_vba_source_from_excel(filename)
