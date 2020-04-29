import h5py
from keras.models import Model
from keras.layers import Flatten, Dense, Input
from keras.optimizers import Adam
import os
from tqdm import tqdm
import numpy as np
from image_handlers.images_from_gerber.prepare_data import load_train_test_data
from image_handlers.images_from_gerber.deep_tools import get_resnet50_output, resnet50_last_layer_prediction

x_train, y_train, x_test, y_test = load_train_test_data()
# training
num_classes = 66
my_resnet50_output = get_resnet50_output()
file_name = 'resnet50_train_output1.h5'
if os.path.exists(file_name):
    print('{} is exist'.format(file_name))
    f = h5py.File(file_name, 'r')
    resnet50_train_output = f['resnet50_train_output1'][:]
    f.close()
else:
    print('{} is not exist'.format(file_name))
    resnet50_train_output = []
    delta = 10
    for i in tqdm(range(0, len(x_train), delta)):
        #         print(i)
        one_resnet50_train_output = my_resnet50_output([x_train[i:i + delta], 0])[0]
        resnet50_train_output.append(one_resnet50_train_output)
    resnet50_train_output = np.concatenate(resnet50_train_output, axis=0)
    f = h5py.File(file_name, 'w')
    f.create_dataset('resnet50_train_output1', data=resnet50_train_output)
    f.close()
input_tensor = Input(shape=(1, 1, 2048))
predictions = resnet50_last_layer_prediction(input_tensor, num_classes=66)
model = Model(inputs=input_tensor, outputs=predictions)
model.compile(optimizer=Adam(), loss='categorical_crossentropy', metrics=['accuracy'])

print('\nTraining ------------')
cm = 3
cm_str = '' if cm == 0 else str(cm)
cm2_str = '' if (cm + 1) == 0 else str(cm + 1)
if cm >= 1:
    model.load_weights('cnn_model_Caltech66_resnet50_' + cm_str + '.h5')
model.fit(resnet50_train_output, y_train, epochs=10, batch_size=128, )
model.save_weights('cnn_model_Caltech66_resnet50_' + cm2_str + '.h5')
