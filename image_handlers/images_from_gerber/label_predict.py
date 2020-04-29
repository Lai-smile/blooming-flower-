# Created by lixingxing at 2019/3/28

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File LocationL: # Enter

"""
import sys

sys.path.append('/home/ibmdev/workspace/auto-pcb-ii/image_handlers/images_from_gerber')

import h5py
import os
import numpy as np
from keras import Input, Model
import pandas as pd
from tqdm import tqdm

from image_handlers.images_from_gerber.prepare_data import load_train_test_data, standard_data, prepare_unlabeled_data
from image_handlers.images_from_gerber.deep_tools import get_resnet50_output, resnet50_last_layer_prediction

CM2_STR = 4
NUM_CLASSES = 66
MAX_NUM = 1


# input_tensor = Input(shape=(300, 300, 3))

def get_resnet50_format_output(images_path):
    """

    :param images_path: the input path must be image characters dir
    :return: output of resnet50 from the input data
    """
    x, name = prepare_unlabeled_data(images_path)
    print(type(x))
    _resnet50_output = []
    delta = 10
    save_path = os.path.join(images_path, 'resnet50_unlabeled_output.h5')
    if os.path.exists(save_path):
        f = h5py.File(save_path, 'r')
        _resnet50_output = f['resnet50_unlabeled_output'][:]
        f.close()
    else:
        for i in tqdm(range(0, len(x), delta)):
            #         print(i)
            my_resnet50_output = get_resnet50_output()
            one_resnet50_test_output = my_resnet50_output([x[i:i + delta], 0])[0]
            _resnet50_output.append(one_resnet50_test_output)
        _resnet50_output = np.concatenate(_resnet50_output, axis=0)
        f = h5py.File(save_path, 'w')
        f.create_dataset('resnet50_unlabeled_output', data=_resnet50_output)
        f.close()
    return _resnet50_output, name


def get_resnet50_test_output():
    x_train, y_train, x_test, y_test = load_train_test_data()
    print(type(x_test))
    file_name = 'data/resnet50_test_output.h5'
    if os.path.exists(file_name):
        f = h5py.File(file_name, 'r')
        resnet50_test_output = f['resnet50_test_output'][:]
        f.close()
    else:
        resnet50_test_output = []
        delta = 10
        for i in tqdm(range(0, len(x_test), delta)):
            #         print(i)
            my_resnet50_output = get_resnet50_output()
            one_resnet50_test_output = my_resnet50_output([x_test[i:i + delta], 0])[0]
            resnet50_test_output.append(one_resnet50_test_output)
        resnet50_test_output = np.concatenate(resnet50_test_output, axis=0)
        f = h5py.File(file_name, 'w')
        f.create_dataset('resnet50_test_output', data=resnet50_test_output)
        f.close()
    return resnet50_test_output, y_test


def evaluation(y_predict, y_label):
    pred_array = np.array(y_predict)
    test_arg = np.argmax(y_label, axis=1)
    print(test_arg)
    class_count = [0 for _ in range(NUM_CLASSES)]
    class_acc = [0 for _ in range(NUM_CLASSES)]

    new_data = standard_data()
    class_name_list = pd.get_dummies(new_data.ImageLabel).columns.values.tolist()

    for i in range(len(test_arg)):
        class_count[test_arg[i]] += 1
        if test_arg[i] in pred_array[i]:
            class_acc[test_arg[i]] += 1
        else:
            print('{} was recognized as {}'.format(class_name_list[int(test_arg[i])],
                                                   class_name_list[int(pred_array[i])]))
    print('top-' + str(MAX_NUM) + ' all acc:', str(sum(class_acc)) + '/' + str(len(test_arg)),
          sum(class_acc) / float(len(test_arg)))

    for i in range(NUM_CLASSES):
        print(i, class_name_list[i], 'acc: ' + str(class_acc[i]) + '/' + str(class_count[i]))


def prediction(resnet50_output, output_name, save_result=False):
    pred_y = []
    pred_chars = {}

    print('\nPredicting ------------')
    input_tensor = Input(shape=(1, 1, 2048))
    predictions = resnet50_last_layer_prediction(input_tensor, num_classes=NUM_CLASSES)
    model = Model(inputs=input_tensor, outputs=predictions)
    model.load_weights(os.path.join('data', 'cnn_model_Caltech66_resnet50_' + str(CM2_STR) + '.h5'))
    pred = model.predict(resnet50_output, batch_size=32)
    if save_result:
        f = h5py.File(os.path.join('data', 'pred_' + str(CM2_STR) + '.h5'), 'w')
        f.create_dataset('pred', data=pred)
        f.close()

    for row in pred:
        pred_y.append(row.argsort()[-MAX_NUM:][::-1])  # 获取最大的N个值的下标
    # print(pred_list)
    pred_array = np.array(pred_y)
    # test_arg = np.argmax(y_test, axis=1)
    # print(test_arg)
    # class_count = [0 for _ in range(NUM_CLASSES)]
    # class_acc = [0 for _ in range(NUM_CLASSES)]

    new_data = standard_data()
    class_name_list = pd.get_dummies(new_data.ImageLabel).columns.values.tolist()
    if output_name:
        for i in range(len(pred_array)):
            # class_count[test_arg[i]] += 1
            pred_chars[output_name[i]] = class_name_list[int(pred_array[i])]
    return pred_y, pred_chars
    #     if test_arg[i] in pred_array[i]:
    #         class_acc[test_arg[i]] += 1
    #     else:
    #         print('{} was recognized as {}'.format(class_name_list[int(test_arg[i])],
    #                                                class_name_list[int(pred_array[i])]))
    # print('top-' + str(max_num) + ' all acc:', str(sum(class_acc)) + '/' + str(len(test_arg)),
    #       sum(class_acc) / float(len(test_arg)))
    #
    # for i in range(NUM_CLASSES):
    #     print(i, class_name_list[i], 'acc: ' + str(class_acc[i]) + '/' + str(class_count[i]))


if __name__ == '__main__':
    # resnet50_output, name = get_resnet50_format_output('/Users/lixingxing/IBM/gerbel_label/data/待标注图像/group-connected-0000000009_DRILL')
    # y, chars = prediction(resnet50_output, name)
    # print(y)
    # print(chars)
    resnet50_output, _ = get_resnet50_test_output()
    p1, p2 = prediction(resnet50_output, None)
    print(p1)
    print(p2)
