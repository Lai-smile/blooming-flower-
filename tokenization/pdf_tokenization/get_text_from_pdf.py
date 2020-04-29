# Created by Wenhao at 2019-03-14
"""
Feature: #Enter feature name here
# Enter feature description here
Scenario: #Enter scenario name here
# Enter steps here
Test File Location: # Enter]
"""

import os
from binascii import b2a_hex

from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTFigure, LTImage
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

from tokenization.pdf_tokenization.text_recombination import text_recombination


def covert_to_byte_string(s, enc='utf-8'):

    return s if isinstance(s, str) else s.encode(enc)


def get_obj_locations(obj, page_media):

    x_min, y_min, x_max, y_max = page_media

    x0, y0 = round(y_max - obj.bbox[3], 2), round(obj.bbox[0], 2)
    x1, y1 = round(y_max - obj.bbox[1], 2), round(obj.bbox[2], 2)

    return x0, y0, x1, y1


def with_pdf(pdf_doc, fn, pdf_pwd='', *args):
    # Open the pdf document, and apply the function, returning the results

    fp = open(pdf_doc, 'rb')

    # Create a PDF parser object associated with the file object.
    parser = PDFParser(fp)

    # Create a PDF document object that stores the document structure.
    # Password for initialization as 2nd parameter
    document = PDFDocument(parser, pdf_pwd)
    parser.set_document(document)

    # Check if the document allows text extraction. If not, abort.
    if not document.is_extractable:
        print('the document does not allow text extraction')

    return fn(document, *args)


def determine_image_type(stream_first_4_bytes):
    # find out the image file type based on the magic number comparison of the first 4 (or 2) bytes

    file_type = None
    bytes_as_hex = str(b2a_hex(stream_first_4_bytes))
    if bytes_as_hex.startswith('ffd8'): file_type = '.jpeg'
    elif bytes_as_hex == '89504e47': file_type = '.png'
    elif bytes_as_hex == '47494638': file_type = '.gif'
    elif bytes_as_hex.startswith('424d'): file_type = '.bmp'

    return file_type


def write_file(folder, filename, file_data, flags='w'):
    # write the file data to the folder and filename combination
    # flags: 'w' for write text, 'wb' for write binary, use 'a' instead of 'w' for append

    result = False
    if os.path.isdir(folder):
        try:
            file_obj = open(os.path.join(folder, filename), flags)
            file_obj.write(file_data)
            file_obj.close()
            result = True
        except IOError:
            pass
    return result


def save_image(lt_image, page_number, images_folder):
    # save the image data from this LTImage object, and return the file name, if successful

    result = None
    if lt_image.stream:
        file_stream = lt_image.stream.get_rawdata()
        if file_stream:
            file_ext = '.jpeg'
            if file_ext:
                file_name = ''.join([str(page_number), '_', lt_image.name, file_ext])
                if write_file(images_folder, file_name, file_stream, flags='wb'):
                    result = file_name

    return result


def update_page_text_hash(page_number, h, lt_obj, page_media, pct=0):
    # Use the bbox x0, x1 values within pct% to produce lists of associated text within the hash

    x0, y0, x1, y1 = get_obj_locations(lt_obj, page_media)

    key_found = False
    for k, v in h.items():
        hash_x0, hash_x1 = k[1], k[3]

        if (hash_x0 * (1.0+pct)) > y0 > (hash_x0 * (1.0-pct)) \
                and (hash_x1 * (1.0+pct)) > y1 > (hash_x1 * (1.0-pct)):

            h[k] = v + [covert_to_byte_string(lt_obj.get_text())]
            key_found = True

    if not key_found:
        h[(page_number, x0, y0, x1, y1)] = covert_to_byte_string(lt_obj.get_text())

    return h


def parse_lt_objs(lt_objs, page_number, page_media, images_folder):
    # Iterate through the list of LT* objects and capture the text or image data contained in each

    text_content = []
    page_text = {}
    for lt_obj in lt_objs:

        if isinstance(lt_obj, LTTextBox) or isinstance(lt_obj, LTTextLine):
            # text, so arrange is logically based on its column width
            page_text = update_page_text_hash(page_number, page_text, lt_obj, page_media)

        elif isinstance(lt_obj, LTImage):
            x0, y0, x1, y1 = get_obj_locations(lt_obj, page_media)
            text_content += [(page_number, x0, y0, x1, y1,
                              '_#IMAGE#_')]

            # TODO get image from pdf page
            """
            Possible solutions
            1. unicode current results (hard)
            2. utilize locations into image detection in png files
            """
            # an image, so save it to the designated folder, and note its place in the text
            # saved_file = save_image(lt_obj, page_number, images_folder)
            # if saved_file:
            #     # use html style <img /> tag to mark the position of the image within the text
            #     text_content += ['<img src="' + os.path.join(images_folder, saved_file) + '" />']
            #     print('successfully saved images')
            # else:
            #     pass
            #     # print(sys.stderr, "error saving image on page")

        elif isinstance(lt_obj, LTFigure):

            text_content += parse_lt_objs(lt_obj, page_number, page_media, images_folder)

    text_content += [tuple([k for k in key] + [value]) for key, value in page_text.items()]

    return text_content


def _parse_pages(doc, images_folder):
    # open PDFDocument object, get the pages and parse each one
    # To be passed to with_pdf()

    rsrcmgr = PDFResourceManager()

    # TODO modify the parameter of extraction
    laparams = LAParams()

    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    all_tokens = []
    for index, page in enumerate(PDFPage.create_pages(doc)):

        print(index + 1, page.mediabox)

        interpreter.process_page(page)
        # receive the LTPage object for this page
        layout = device.get_result()
        # layout is an LTPage object which may contain child objects like LTTextBox, LTFigure, LTImage, etc.

        all_tokens += parse_lt_objs(layout, (index+1), page.mediabox, images_folder)

    return all_tokens


def get_token_text_from_pdf(pdf_doc_path, images_folder=None, pdf_pwd=''):

    # Process each of the pages in this pdf file and
    return with_pdf(pdf_doc_path, _parse_pages, pdf_pwd, *tuple([images_folder]))


def get_texts_from_pdf(file_name):

    ori_texts = get_token_text_from_pdf(file_name)
    return text_recombination(ori_texts)


if __name__ == '__main__':

    path = '/Users/yeleiyl/Downloads/wsdata/EG00A02AA0_7335PCB加工要求说明卡.pdf'
    opt = '/Users/wenhaoyu/Desktop'

    for i in get_texts_from_pdf(path): print(i)
