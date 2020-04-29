from constants.path_manager import IMAGE_TEXT_DATA_PATH

import pytesseract
import cv2
import os
import time


LANGUAGE = 'chi_sim+eng'


def text_extract(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray, lang=LANGUAGE)
    return text


def main():
    INPUT_IMG = 'chinese1.png'

    input_img_path = os.path.join(IMAGE_TEXT_DATA_PATH, INPUT_IMG)
    image = cv2.imread(input_img_path)

    start_time = time.time()
    print(text_extract(image))
    print("--- %s seconds ---" % (time.time() - start_time))


if __name__ == '__main__':
    main()
