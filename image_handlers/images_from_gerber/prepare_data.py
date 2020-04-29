# Created by lixingxing at 2019/3/28

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File LocationL: # Enter

"""
import pandas as pd
import os
import cv2
from sklearn.model_selection import train_test_split
import pickle

DATA_SAVE_PATH = 'data/gerber_image_data.pkl'


def load_label_target():
    global LABEL_PATH, TARGET_PATH, IMAGE_DATA_PATH, DATA_SAVE_PATH
    LABEL_PATH = '/Users/lixingxing/IBM/gerbel_label/data/label.xlsx'
    TARGET_PATH = '/Users/lixingxing/IBM/gerbel_label/data/target.txt'
    IMAGE_DATA_PATH = '/Users/lixingxing/IBM/gerbel_label/data/待标注图像'
    my_label = pd.read_excel(LABEL_PATH)
    my_target = pd.read_csv(TARGET_PATH, sep='/t', engine='python')
    return my_label, my_target


def standard_data():
    my_label, my_target = load_label_target()

    len(set([item[0] for item in my_target.values.tolist()]))
    target = set([item[0] for item in my_target.values.tolist()])
    my_label['图片名称'] = my_label['图片名称'].apply(lambda x: str(x).strip())

    label_name = [str(name).split('.')[0] for name in my_label['图片名称'].values.tolist()]
    label_dict = {}
    for i, label in enumerate(my_label['标签'].values.tolist()):
        label_dict[label_name[i] + '.png'] = str(label)

    try:
        file_names = os.listdir(IMAGE_DATA_PATH)
        image_names = []
        image_path = []
        image_label = []
        for file in file_names:
            sub_path = os.path.join(IMAGE_DATA_PATH, file)
            if os.path.isdir(sub_path):
                sub_files = os.listdir(sub_path)
                for file in sub_files:
                    if file.endswith('png'):
                        file_label = label_dict[file]
                        if file_label in target:
                            image_names.append(file)
                            image_path.append(os.path.join(sub_path, file))
                            image_label.append(str(file_label))
        data = {'ImageName': image_names, 'ImagePath': image_path, 'ImageLabel': image_label}
        new_data = pd.DataFrame(data, columns=['ImageName', 'ImagePath', 'ImageLabel'])
        return new_data
    except KeyError as e:
        print('{} is not a key'.format(e))


def image_preprocess(img_path, resize_w=300, resize_h=300):
    img = cv2.imread(img_path)
    img = cv2.resize(img, (resize_w, resize_h))
    #  img = img.reshape(-1, resize_w, resize_h, 3)
    return img


def split_save_data():
    pkl_file_name = open(DATA_SAVE_PATH, 'wb')
    new_data = standard_data()
    x = []
    y = pd.get_dummies(new_data.ImageLabel).as_matrix()
    for path in new_data['ImagePath'].values.tolist():
        processed_img = image_preprocess(path)
        x.append(processed_img)
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=0)
    pickle.dump(x_train, pkl_file_name)
    pickle.dump(y_train, pkl_file_name)
    pickle.dump(x_test, pkl_file_name)
    pickle.dump(y_test, pkl_file_name)
    pkl_file_name.close()


def load_train_test_data():
    print('load data')
    image_data = open(DATA_SAVE_PATH, 'rb')
    x_train = pickle.load(image_data)
    y_train = pickle.load(image_data)
    x_test = pickle.load(image_data)
    y_test = pickle.load(image_data)
    image_data.close()
    return x_train, y_train, x_test, y_test


def prepare_unlabeled_data(images_path):
    files = os.listdir(images_path)
    _unlabeled_x = []
    _unlabeled_name = []
    for file in files:
        if file.endswith('.png'):
            file_path = os.path.join(images_path, file)
            unlabeled_img = image_preprocess(file_path)
            _unlabeled_name.append(file)
            _unlabeled_x.append(unlabeled_img.tolist())
    return _unlabeled_x, _unlabeled_name


if __name__ == '__main__':
    unlabeled_x, unlabeled_name = prepare_unlabeled_data(
        '/Users/lixingxing/IBM/gerbel_label/data/待标注图像/group-connected-0000000009_DRILL')
    print(type(unlabeled_x[0]))
