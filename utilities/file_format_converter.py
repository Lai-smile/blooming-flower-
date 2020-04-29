# created by lynn at 01/23/2019

import win32com.client
import os
from win32com.client import constants
from utilities.path import get_file_absolute_path


def convert2pdf(file, in_type, out_type="pdf"):
    file = get_file_absolute_path(file)
    print(file)

    pdf_path = file + ".pdf"
    if in_type == "excel":
        app = win32com.client.gencache.EnsureDispatch('Excel.Application')
        app.Visible = 0
        app.DisplayAlerts = 0
        f = app.Workbooks.Open(os.path.abspath(file))
    elif in_type == "word":
        app = win32com.client.gencache.EnsureDispatch('Word.Application')
        app.Visible = 0
        app.DisplayAlerts = 0
        f = app.Documents.Open(os.path.abspath(file))

    if out_type == "pdf" and in_type == "excel":
        f.ExportAsFixedFormat(0, pdf_path)
        # f.PrintOut()
    elif out_type == "pdf" and in_type == "word":
        f.SaveAs(pdf_path, FileFormat=constants.wdFormatPDF)
    elif out_type == "html":
        f.SaveAs(file + ".html", 44)

    f.Close()
    app.Quit()

    return pdf_path


if __name__ == '__main__':

    path = r"C:\Users\LYN\Desktop\data_extraction\all_sheets\\"

    for file in os.listdir(path):
        convert2pdf(os.path.join(path, file), "excel", "pdf")
    # convert_format(file,"excel","html")
