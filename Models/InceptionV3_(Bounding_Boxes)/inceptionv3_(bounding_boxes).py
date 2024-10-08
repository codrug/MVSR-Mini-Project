# -*- coding: utf-8 -*-
"""InceptionV3_(Bounding_Boxes).ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1EyJX7R6bW7cr0W4LDi468-TcdNUaVWpk
"""

# Setting up Environment
import os
import json
import numpy as np
from PIL import Image
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import VGG16
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, Flatten, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.optimizers import Adam
from sklearn.model_selection import train_test_split

# Paths to the dataset
img_dir = '/content/drive/MyDrive/Datasets/BOUNDING_BOXES_ALLINONE/agri_data/data'
classes_file = '/content/drive/MyDrive/Datasets/BOUNDING_BOXES_ALLINONE/classes.txt'

# Loading class names
with open(classes_file, 'r') as f:
    classes = f.read().splitlines()
    classes = {i: cls for i, cls in enumerate(classes)}

# Loading images and annotations
def load_data(img_dir):
    images = []
    labels = []
    n = 0
    for img_name in os.listdir(img_dir):
        if img_name.endswith('.jpeg') or img_name.endswith('.png'):
            img_path = os.path.join(img_dir, img_name)
            ann_path = os.path.join(img_dir, os.path.splitext(img_name)[0] + '.txt')

            # Load image
            img = Image.open(img_path)
            img = img.resize((100,100))
            images.append(np.array(img) / 255.0)  # Normalize to [0, 1]
            n += 1

            # Load annotation and set label (1 for weed, 0 for crop)
            with open(ann_path, 'r') as f:
                anns = f.read().strip().split('\n')
                is_weed = False
                for ann in anns:
                    cls_id = int(ann.split(' ')[0])
                    if classes[cls_id] == 'weed':
                        is_weed = True
                        break
                labels.append(1 if is_weed else 0)
    print(n, "images found")
    return np.array(images), np.array(labels)

# Loading the dataset
images, labels = load_data(img_dir)

X_train, X_val, y_train, y_val = train_test_split(images, labels, test_size=0.2, random_state=42)

# Step 3: Data Augmentation
train_datagen = ImageDataGenerator(
    rotation_range=40,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    fill_mode='nearest'
)

val_datagen = ImageDataGenerator()

train_generator = train_datagen.flow(X_train, y_train, batch_size=32)
val_generator = val_datagen.flow(X_val, y_val, batch_size=32)

# Step 4: Model Setup
base_model = InceptionV3(weights='imagenet', include_top=False, input_shape=(100, 100, 3))
x = base_model.output
x = GlobalAveragePooling2D()(x)
x = Dense(1024, activation='relu')(x)
predictions = Dense(1, activation='sigmoid')(x)

model = Model(inputs=base_model.input, outputs=predictions)

for layer in base_model.layers:
    layer.trainable = False
model.summary()

# Step 5: Training
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

history = model.fit(
    train_generator,
    epochs=10,
    validation_data=val_generator
)

# Step 6: Evaluation
y_val_pred = (model.predict(X_val) > 0.5).astype("int32")

print(classification_report(y_val, y_val_pred, target_names=['crop', 'weed']))

conf_mat = confusion_matrix(y_val, y_val_pred)
sns.heatmap(conf_mat, annot=True, fmt='d', cmap='Blues', xticklabels=['crop', 'weed'], yticklabels=['crop', 'weed'])
plt.xlabel('Predicted')
plt.ylabel('True')
plt.show()

# Plot training & validation accuracy values
plt.figure(figsize=(12, 4))
plt.subplot(1, 2, 1)
plt.plot(history.history['accuracy'])
plt.plot(history.history['val_accuracy'])
plt.title('Model accuracy')
plt.ylabel('Accuracy')
plt.xlabel('Epoch')
plt.legend(['Train', 'Validation'], loc='upper left')

# Plot training & validation loss values
plt.subplot(1, 2, 2)
plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('Model loss')
plt.ylabel('Loss')
plt.xlabel('Epoch')
plt.legend(['Train', 'Validation'], loc='upper left')
plt.show()