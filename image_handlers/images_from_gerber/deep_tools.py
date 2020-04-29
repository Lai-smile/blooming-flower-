# Created by lixingxing at 2019/3/28

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File LocationL: # Enter

"""
from keras import Input
from keras.applications.resnet50 import ResNet50
import keras.backend as K
from keras.layers import Flatten, Dense


def get_resnet50_output():
    input_tensor = Input(shape=(300, 300, 3))
    base_model = ResNet50(input_tensor=input_tensor, include_top=False, weights='imagenet')
    # base_model = ResNet50(input_tensor=input_tensor,include_top=False,weights=None)

    resnet50_output = K.function([base_model.layers[0].input, K.learning_phase()], [base_model.layers[-1].output])
    return resnet50_output


def resnet50_last_layer_prediction(input_tensor, num_classes):
    x = Flatten()(input_tensor)
    x = Dense(1024, activation='relu')(x)
    predictions = Dense(num_classes, activation='softmax')(x)
    return predictions
