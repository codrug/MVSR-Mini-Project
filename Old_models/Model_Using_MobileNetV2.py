from tensorflow.keras.callbacks import EarlyStopping
import os
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam

#Preprocessing
datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=20,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    fill_mode='nearest'
)

train_directory = r"C:\Users\dhruv\Model_dev\train_folder"
train_data = datagen.flow_from_directory(
    train_directory,
    class_mode='binary', #binary or categorical
    target_size=(128, 128),
    batch_size=32
)

test_directory = r"C:\Users\dhruv\Model_dev\test_folder"
test_data = datagen.flow_from_directory(
    test_directory,
    class_mode='binary',
    target_size=(128, 128),
    batch_size=32
)

# Visualizing
directory_path = r"C:\Users\dhruv\Model_dev\train_folder\train"
allowed_extensions = ('.jpeg', '.jpg')
try:
    file_list = [
        file_name for file_name in os.listdir(directory_path)
        if os.path.splitext(file_name)[-1].lower() in allowed_extensions
    ]

    for file_name in file_list[:5]:
        img_path = os.path.join(directory_path, file_name)
        img = mpimg.imread(img_path)
        plt.imshow(img)
        #plt.axis('off')
        plt.show()
except Exception as e:
    print(f"An error occurred: {e}")

from tensorflow.keras.applications import MobileNetV2

conv_base = MobileNetV2(
    weights='imagenet',
    include_top=False,
    input_shape=(128, 128, 3),
    pooling='avg'
)
conv_base.trainable = False
conv_base.summary()

import tensorflow as tf
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping

early_stopping = EarlyStopping(monitor='val_loss', patience=5)

model = Sequential()
model.add(conv_base)
model.add(BatchNormalization())
model.add(Dense(128, activation='relu'))
model.add(Dropout(0.35))
model.add(BatchNormalization())
model.add(Dense(60, activation='relu'))
model.add(Dense(1, activation='sigmoid'))

model.summary()

# Compile the model
model.compile(
    optimizer=Adam(learning_rate=0.0001),
    loss='binary_crossentropy',
    metrics=['accuracy']
)

# Define EarlyStopping callback
early_stopping = EarlyStopping(monitor='val_loss', patience=5)

history = model.fit(
    train_data,
    epochs=10,
    validation_data=test_data,
    callbacks=[early_stopping]
)

model.save('weed_detection_model.h5')

evaluation = model.evaluate(test_data)
print("Validation Loss:", evaluation[0])
print("Validation Accuracy:", evaluation[1])

def plot_metrics(history):
    # Plot training & validation accuracy values
    plt.plot(history.history['accuracy'])
    plt.plot(history.history['val_accuracy'])
    plt.title('Model accuracy')
    plt.ylabel('Accuracy')
    plt.xlabel('Epoch')
    plt.legend(['Train', 'Validation'], loc='upper left')
    plt.show()

    # Plot training & validation loss values
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.title('Model loss')
    plt.ylabel('Loss')
    plt.xlabel('Epoch')
    plt.legend(['Train', 'Validation'], loc='upper left')
    plt.show()
    
plot_metrics(history)

#CONVERSION
import tensorflow as tf

# Load your trained Keras model
model = tf.keras.models.load_model('weed_detection_model.h5')

# Save the model in the SavedModel format using export
saved_model_dir = r'C:\Users\dhruv\Model_dev'
tf.saved_model.save(model, saved_model_dir)

# Convert the model to TensorFlow Lite format
converter = tf.lite.TFLiteConverter.from_saved_model(saved_model_dir)
converter.optimizations = [tf.lite.Optimize.DEFAULT]  # Apply optimizations

# Convert the model
tflite_model = converter.convert()

# Save the converted TensorFlow Lite model
with open('converted_model.tflite', 'wb') as f:
    f.write(tflite_model)

print("Model converted and saved successfully as 'converted_model.tflite'")