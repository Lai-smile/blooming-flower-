# Created by lynn at 2019/01/11

"""
Get each cell of office excel sheet.

Reference:
1. https://docs.xlwings.org/en/stable/api.html
2. https://docs.microsoft.com/en-us/office/vba/api/overview/excel

"""

import os
import pickle
import re
import string
import time

import xlwings as xw


def col2num(col):
    num = 0
    for c in col:
        if c in string.ascii_letters:
            num = num * 26 + (ord(c.upper()) - ord('A')) + 1
    return num


def location(sht_name, top_left, bottom_right):
    loc = top_left + ":" + bottom_right
    loc_re = re.findall(r"[\w']+|[.,!?;]", loc)
    #     print(loc_re)
    return (sht_name, int(loc_re[1]), col2num(loc_re[0]), int(loc_re[3]), col2num(loc_re[2]))


def range2loc(sht_name, range):
    loc_re = re.findall(r"[\w']+|[.,!?;]", range)
    if len(loc_re) == 2:
        return (sht_name, int(loc_re[1]), col2num(loc_re[0]), int(loc_re[1]), col2num(loc_re[0]))
    else:
        return (sht_name, int(loc_re[1]), col2num(loc_re[0]), int(loc_re[3]), col2num(loc_re[2]))


class Content():
    def __init__(self, sheet, category, value=" ", caption=" "):
        self.sheet = sheet
        self.category = category
        self.value = value
        self.caption = caption


def get_content(filename):
    # print(xw.books)
    # wb = xw.Book(filename)
    app = xw.App(visible=False, add_book=False)
    app.display_alerts = False
    app.screen_updating = False
    wb = app.books.open(filename)
    res = {}

    for sheet in wb.sheets:

        if sheet.pictures:
            for obj in sheet.pictures:
                try:
                    if "Picture" not in obj.api.Name and "图片" not in obj.api.Name:
                        print("OLEObjects" + " " + obj.api.Name + " " + str(obj.api.Object.Caption) + " " + str(
                            obj.api.Object.Value) + " " + obj.api.Object.TopLeftCell.Address + " " + obj.api.Object.BottomRightCell.Address)
                        loc = location(sheet.index, obj.api.Object.TopLeftCell.Address,
                                       obj.api.Object.BottomRightCell.Address)
                        OLEObjects = Content(sheet.name, obj.api.Name, obj.api.Object.Caption, obj.api.Object.Value)
                        res[loc] = [OLEObjects.sheet, OLEObjects.category, OLEObjects.caption, OLEObjects.value]
                    else:
                        print(
                            "Picture " + obj.api.Name + " " + obj.api.TopLeftCell.Address + " " + obj.api.BottomRightCell.Address + " " + "path")
                        loc = location(sheet.index, obj.api.TopLeftCell.Address, obj.api.BottomRightCell.Address)
                        PicObjects = Content(sheet.name, obj.api.Name)
                        res[loc] = [PicObjects.sheet, PicObjects.category, False]

                        # obj.api.CopyPicture()
                        # for fmt in app.api.ClipboardFormats:
                        #     print(fmt)

                        # img = ImageGrab.grabclipboard()
                        # if isinstance(img, Image.Image):
                        #     print("yes")
                        #     img.save(sheet.name+"_"+obj.api.Name+".png")

                except:
                    continue
        #             ignore unknown pictures

        last_cell = sheet.range("A1").api.SpecialCells(11).Address

        for cell in sheet.range("A1", last_cell):
            # print(cell.api.Address)
            if cell.api.MergeCells:
                if cell.value is not None:
                    print(cell.api.MergeArea.Address + " " + str(cell.value))
                    addr = cell.api.MergeArea.Address
                    loc = location(sheet.index, addr.split(":")[0], addr.split(":")[1])
                    Merged = Content(sheet.name, "Merged", str(cell.value))
                    res[loc] = [Merged.sheet, Merged.category, Merged.value]
            elif cell.api.Value is not None:
                print(cell.api.Address + " " + str(cell.api.Value))
                loc = location(sheet.index, cell.api.Address, cell.api.Address)
                Single_text = Content(sheet.name, "Text", str(cell.api.Value))
                res[loc] = [Single_text.sheet, Single_text.category, Single_text.value]
            else:
                continue

        if sheet.api.Comments:
            for comment in sheet.api.Comments:
                # print(comment.parent.Address)
                loc = location(sheet.index, comment.parent.Address, comment.parent.Address)
                Comment = Content(sheet.name, "Comment", comment.Text())
                if loc in res:
                    res[loc].append([Comment.sheet, Comment.category, Comment.value])
                else:
                    res[loc] = [Comment.sheet, Comment.category, Comment.value]
                # comment.Delete()

        if sheet.api.Hyperlinks:
            for hl in sheet.api.Hyperlinks:
                loc = range2loc(sheet.index, hl.Range.Address)
                if hl.Address:
                    hl_value = hl.Address
                elif hl.SubAddress:
                    hl_value = hl.SubAddress
                Hyperlink = Content(sheet.name, "Hyperlink", hl_value, hl.TextToDisplay)
                if loc in res:
                    res[loc].append([Hyperlink.sheet, Hyperlink.category, Hyperlink.caption])
                else:
                    res[loc] = [Hyperlink.sheet, Hyperlink.category, Hyperlink.caption]

        # if sheet.shapes:
        #     cnt=sheet.shapes.api.Count
        #     print("count before ungroup:  ",cnt)
        #     for i in range(cnt):
        #         i+=1
        #         shp=sheet.shapes.api.Item(i)
        #         print(shp.Type)
        #         if shp.Type== 6:
        #             shp.Ungroup
        #             wb.save()

        if sheet.shapes:
            cnt_after_ungroup = sheet.shapes.api.Count
            print("count after ungroup:  ", cnt_after_ungroup)
            for i in range(cnt_after_ungroup):
                i += 1
                shp = sheet.shapes.api.Item(i)

                # print(shp.Name,shp.Type)
                if shp.Type == 8 and "Picture" not in shp.Name:

                    if "Check Box" in shp.Name or "Option Button" in shp.Name:
                        loc = location(sheet.index, shp.TopLeftCell.Address, shp.BottomRightCell.Address)
                        if shp.ControlFormat.Value:
                            Checkbox = Content(sheet.name, shp.Name, shp.AlternativeText)

                            if loc in res:
                                res[loc].append([Checkbox.sheet, Checkbox.category, Checkbox.value])
                            else:
                                res[loc] = [Checkbox.sheet, Checkbox.category, Checkbox.value]
                        print(loc, res[loc])
                    if "Drop Down" in shp.Name:
                        dropdown_range = shp.ControlFormat.ListFillRange
                        if "#REF!" in dropdown_range:
                            continue
                        if "!" in dropdown_range:
                            try:
                                dropdown_range_sht = dropdown_range.split("!")[0]
                                dropdown_range_cell = dropdown_range.split("!")[1]
                                dropdown_value_list = wb.sheets[dropdown_range_sht].range(dropdown_range_cell).value
                            except:
                                continue
                        else:
                            dropdown_value_list = sheet.range(dropdown_range).value
                        # print(shp.Name,shp.ControlFormat.ListFillRange)

                        dropdown_value_index = int(shp.ControlFormat.ListIndex) - 1
                        dropdown_value = dropdown_value_list[dropdown_value_index]
                        Dropdown = Content(sheet.name, shp.Name, dropdown_value)
                        loc = location(sheet.index, shp.TopLeftCell.Address, shp.BottomRightCell.Address)
                        res[loc] = [Dropdown.sheet, Dropdown.category, Dropdown.value]
                        print(loc, res[loc])

    wb.close()
    app.quit()
    time.sleep(3)
    return res


def get_content_web(filename):
    for key, value in get_content(filename).items():
        sht_index = key[0]
        x1, y1, x2, y2 = key[1], key[2], key[3], key[4]
        content = value
        yield sht_index, x1, y1, x2, y2, content


def walk(in_path, output_folder):
    if not os.path.exists(in_path):
        return -1
    for root, dirs, names in os.walk(in_path):

        for name in names:
            filename = os.path.join(root, name)
            print(filename)
            pickle_to_dump = get_content(filename)

            # filename=pickle_to_dump[1]
            # for key,value in pickle_to_dump[0].items():
            #     yield key[0],key[1],key[2],key[3],key[4],value,filename

            file_basename = os.path.basename(filename)
            output_file_name = os.path.splitext(file_basename)[0] + ".pickle"
            output_file = os.path.join(output_folder, output_file_name)

            with open(output_file, 'wb') as f:
                pickle.dump(pickle_to_dump, f)

            # print(filename)
            with open(os.path.join(output_folder, "failed.txt"), "a+", encoding="utf-8") as f:
                f.write('\n'.join(filename))


if __name__ == '__main__':
    # tests single file
    # filename = r"C:\Users\LYN\Desktop\data_extraction\all_sheets\ITKY.758748.489M3_04JL-00_SN_NP_Datasheet.xls"
    #
    # res=[(sheet_index, x1, y1, x2, y2, t) for sheet_index, x1, y1, x2, y2, t in get_content_web(filename)]
    # print(res)
    # with open("C:/Users/LYN/Desktop/test_data_web\excel\HDMI SMA.xls.pickle", 'wb') as f:
    #     pickle.dump(pickle_to_dump, f)

    # tests all excel in a folder
    output_path = 'C:/Users/LYN/Desktop/failed_output/'
    file_path = 'C:/Users/LYN/Desktop/failed/'
    walk(file_path, output_path)

    # tests all files from server
    # filename = r'//192.168.224.8/工程自动化/工程自动化小组/01测试订单存入目录/第二阶段/前处理文件/2层/'
    # output_folder = r'C:/Users/LYN/Desktop/pickles_from_excel/'
    #
    # for i, file in enumerate(get_all_files(filename)):
    #     # if i % 50 == 0:
    #     print('*'*8)
    #     print('{}: {}'.format(i, file))
    #     if file.endswith('.zip'):
    #         unpack_zip_file_path = unpack_zip(file, os.path.join(root, 'extracted-data'))
    #         print(unpack_zip_file_path)
    #         for f in get_all_files(unpack_zip_file_path):
    #             if f.endswith(".xls"):
    #                 pickle_to_dump=get_content(f)
    #                 file_basename=os.path.basename(f)
    #                 output_file_name=os.path.splitext(file_basename)[0]+".pickle"
    #
    #                 output_file=os.path.join(output_folder,output_file_name)
    #
    #                 with open(output_file, 'wb') as f:
    #                     pickle.dump(pickle_to_dump, f)
