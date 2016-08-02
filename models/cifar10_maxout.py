'''
This will attempt to reimplement the CIFAR-10 maxout network
as described by Goodfellow et al. (2013)

Ref: GitHub: lisa-lab/pylearn2/pylearn2/scripts/papers/maxout/cifar10.yaml
'''

from __future__ import print_function
from keras.preprocessing.image import ImageDataGenerator
from keras.models import Model
from keras.layers import Input, Dense, Activation, Flatten, Dropout, merge, MaxoutDense
from keras.layers import Convolution2D, MaxPooling2D, ZeroPadding2D
from keras.optimizers import Adam
from keras.utils.visualize_util import plot
from utils.preprocess import get_cifar

batch_size = 128
nb_classes = 10
nb_epoch = 474
data_augmentation = True

# plot the model?
plot_model = True
show_shapes = True
plot_file = 'cifar10_maxout.png'

# show the summary?
show_summary = True

# the data, shuffled and split between train and test sets
(X_train, Y_train), (X_test, Y_test) = get_cifar(p=1.0, append_test=False, use_c10=True)
print('X_train shape:', X_train.shape)
print(X_train.shape[0], 'train samples')
print(X_test.shape[0], 'test samples')

X_train = X_train.astype('float32')
X_test = X_test.astype('float32')
X_train /= 255
X_test /= 255

inputYUV = Input(shape=(3, 32, 32))

input_drop = Dropout(0.2)(inputYUV)

# This model combines many components within a single Maxout-Conv layer.
# This is layer 1: {pad: 4, num_channels: 96, num_pieces: 2, 
# kernel: [8, 8], pool: [4, 4], pool_stride: [2, 2]}
h0_pad = ZeroPadding2D((4, 4))(input_drop)
h0_conv_a = Convolution2D(96, 8, 8, border_mode='valid')(h0_pad)
h0_conv_b = Convolution2D(96, 8, 8, border_mode='valid')(h0_pad)
h0_conv = merge([h0_conv_a, h0_conv_b], mode='max', concat_axis=1)
h0_pool = MaxPooling2D(pool_size=(4, 4), strides=(2, 2))(h0_conv)
h0_drop = Dropout(0.5)(h0_pool)

# This is layer 2: {pad: 3, num_channels: 192, num_pieces: 2,
# kernel: [8, 8], pool: [4, 4], pool_stride: [2, 2]}
h1_pad = ZeroPadding2D((3, 3))(h0_drop)
h1_conv_a = Convolution2D(192, 8, 8, border_mode='valid')(h1_pad)
h1_conv_b = Convolution2D(192, 8, 8, border_mode='valid')(h1_pad)
h1_conv = merge([h1_conv_a, h1_conv_b], mode='max', concat_axis=1)
h1_pool = MaxPooling2D(pool_size=(4, 4), strides=(2, 2))(h1_conv)
h1_drop = Dropout(0.5)(h1_pool)

# This is layer 3: {pad: 3, num_channels: 192, num_pieces: 2,
# kernel: [5, 5], pool: [2, 2], pool_stride: [2, 2]}
h2_pad = ZeroPadding2D((3, 3))(h1_drop)
h2_conv_a = Convolution2D(192, 5, 5, border_mode='valid')(h2_pad)
h2_conv_b = Convolution2D(192, 5, 5, border_mode='valid')(h2_pad)
h2_conv = merge([h2_conv_a, h2_conv_b], mode='max', concat_axis=1)
h2_pool = MaxPooling2D(pool_size=(2, 2), strides=(2, 2))(h2_conv)
h2_drop = Dropout(0.5)(h2_pool)
h2_flat = Flatten()(h2_drop)

# Now the more conventional layers...
h3 = MaxoutDense(500, nb_feature=5)(h2_flat)
h3_drop = Dropout(0.5)(h3)
out = Dense(nb_classes)(h3_drop)
y = Activation('softmax')(out) 

model = Model(input=inputYUV, output=y)

model.compile(loss='categorical_crossentropy',
              optimizer=Adam(lr=0.0005),
              metrics=['accuracy'])

if show_summary:
    print(model.summary())

if plot_model:
    plot(model, show_shapes=show_shapes, to_file=plot_file)

if not data_augmentation:
    print('Not using data augmentation.')
    model.fit(X_train, Y_train,
              batch_size=batch_size,
              nb_epoch=nb_epoch,
              validation_data=(X_test, Y_test),
              shuffle=True,
              verbose=2)
else:
    print('Using real-time data augmentation.')

    # this will do preprocessing and realtime data augmentation
    datagen = ImageDataGenerator(
        featurewise_center=False,  # set input mean to 0 over the dataset
        samplewise_center=False,  # set each sample mean to 0
        featurewise_std_normalization=False,  # divide inputs by std of the dataset
        samplewise_std_normalization=False,  # divide each input by its std
        zca_whitening=False,  # apply ZCA whitening
        rotation_range=0,  # randomly rotate images in the range (degrees, 0 to 180)
        width_shift_range=0.1,  # randomly shift images horizontally (fraction of total width)
        height_shift_range=0.1,  # randomly shift images vertically (fraction of total height)
        horizontal_flip=True,  # randomly flip images
        vertical_flip=False)  # randomly flip images

    # compute quantities required for featurewise normalization
    # (std, mean, and principal components if ZCA whitening is applied)
    datagen.fit(X_train)

    # fit the model on the batches generated by datagen.flow()
    model.fit_generator(datagen.flow(X_train, Y_train,
                        batch_size=batch_size),
                        samples_per_epoch=X_train.shape[0],
                        nb_epoch=nb_epoch,
                        validation_data=(X_test, Y_test),
                        verbose=2)
