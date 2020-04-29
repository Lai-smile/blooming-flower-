# created by lynn at 01/23/2019


import zipfile, os
import win32com.client


def get_images(xlsfile, dest_path=""):
    app = win32com.client.gencache.EnsureDispatch('Excel.Application')
    app.Visible = 0
    app.DisplayAlerts = 0
    doc = app.Workbooks.Open(xlsfile)
    doc.SaveAs(xlsfile + ".xlsx", 51)
    # 51 for xlWorkbookDefault

    doc.Close()
    app.Quit()
    # xls to xlsx

    xlsxfile = xlsfile + ".xlsx"
    # xlsxfilepath = Path(xlsxfile)
    # xlsxfilepath.rename(xlsxfilepath.with_suffix('.zip'))
    zf = xlsfile + ".zip"
    if not os.path.exists(zf):
        os.rename(xlsxfile, os.path.splitext(xlsxfile)[0] + ".zip")
    # zip xlsx

    # filename=os.path.basename(xlsfile)
    extracted_path = os.path.splitext(xlsfile)[0] + "-extracted/"
    print(extracted_path)
    if not os.path.exists(extracted_path): os.makedirs(extracted_path)
    with zipfile.ZipFile(zf, "r") as zip:
        zip.extractall(extracted_path)
    #     unzip xlsx

    os.remove(zf)
    #     delete zip file

    img_path = os.path.join(extracted_path, "xl", "media")

    pic_path = dest_path + '_images_office'
    if not os.path.exists(pic_path):
        os.mkdir(pic_path)

    path_out = []
    i = 0

    for file in os.listdir(img_path):
        if file.endswith("png") or file.endswith("jpg") or file.endswith("jpeg"):
            extracted_pic = os.path.join(extracted_path, 'xl', 'media', file)
            saved_pic = os.path.join(pic_path, file)
            os.rename(extracted_pic, saved_pic)
            # move image from extracted path to destination path
            path_out.append(saved_pic)
            i += 1

    return {'img_count': i, 'paths': path_out}


if __name__ == '__main__':
    print(get_images(r"C:\Users\LYN\Desktop\data_extraction\all_sheets\ITKY.758748.489M3_04JL-00_SN_NP_Datasheet.xls"))
