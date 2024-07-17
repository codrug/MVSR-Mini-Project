import numpy as np
import os
import time
import matplotlib.pyplot as plt
import tensorflow as tf
from PIL import Image
from sklearn.metrics import classification_report
from tensorflow.keras.applications import InceptionV3
from tensorflow.keras.callbacks import LearningRateScheduler, EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from tensorflow.keras.layers import GlobalAveragePooling2D, Dense, Dropout, BatchNormalization
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.utils import to_categorical


# Define directories
train_dir = r'/content/drive/MyDrive/Mini-Project-Sem-4/WeedCrop.v1i.yolov5pytorch/train'
valid_dir = r'/content/drive/MyDrive/Mini-Project-Sem-4/WeedCrop.v1i.yolov5pytorch/valid'
test_dir = r'/content/drive/MyDrive/Mini-Project-Sem-4/WeedCrop.v1i.yolov5pytorch/test'
image_dir = os.path.join(train_dir, 'images')


# Print directory contents
contents = os.listdir(train_dir)
num_of_dirs = len([name for name in contents if os.path.isdir(os.path.join(train_dir, name))])
print("Contents of the directory:")
for item in contents:
    print(item)
print(f"\nNumber of directories: {num_of_dirs}")




# Load images from the directory
images = []
for file_name in os.listdir(image_dir):
    if file_name.endswith(('.png', '.jpg', '.jpeg')):
        image_path = os.path.join(image_dir, file_name)
        image = Image.open(image_path)
        images.append(image)

if images:
    print(f"{len(images)} images found")
    images[0].show()
else:
    print("No images found in the directory.")




# Define model parameters
batch_size = 128
num_epochs = 30
image_size = (139, 139)
num_classes = 2




# Load the InceptionV3 model
base_model = InceptionV3(weights='imagenet', include_top=False, input_shape=(*image_size, 3))



# Freeze the layers of the base model
for layer in base_model.layers:
    layer.trainable = False




# Add custom classification layers
x = base_model.output
x = GlobalAveragePooling2D()(x)
x = Dense(256, activation='relu')(x)
x = BatchNormalization()(x)
x = Dropout(0.5)(x)
class_outputs = Dense(num_classes, activation='softmax')(x)




# Create the model
model = Model(inputs=base_model.input, outputs=class_outputs)

# Compile the model
model.compile(loss='categorical_crossentropy', optimizer=Adam(learning_rate=0.001), metrics=['accuracy'])




# Data generators with augmentation
train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=45,
    width_shift_range=0.3,
    height_shift_range=0.3,
    shear_range=0.3,
    zoom_range=0.3,
    horizontal_flip=True,
    fill_mode='nearest'
)

train_dataset = train_datagen.flow_from_directory(
    train_dir,
    target_size=image_size,
    batch_size=batch_size,
    class_mode='categorical'
)


valid_dir = r'/content/drive/MyDrive/Mini-Project-Sem-4/WeedCrop.v1i.yolov5pytorch/valid'
val_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=20,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    fill_mode='nearest'
)

val_dataset = val_datagen.flow_from_directory(
    valid_dir,
    target_size=image_size,
    batch_size=batch_size,
    class_mode='categorical'
)




# Define learning rate scheduler
def lr_scheduler(epoch):
    if epoch < 10:
        return 0.001
    elif 10 <= epoch < 20:
        return 0.0001
    else:
        return 0.00001

lr_schedule = LearningRateScheduler(lr_scheduler)



# Define early stopping
early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)

# Define model checkpoint to save the best model
checkpoint = ModelCheckpoint('best_model.keras', monitor='val_accuracy', save_best_only=True, mode='max', verbose=1)

# Define ReduceLROnPlateau callback
reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=3, min_lr=1e-6)




# Train the model
history = model.fit(
    train_dataset,
    epochs=num_epochs,
    validation_data=val_dataset,
    callbacks=[lr_schedule, early_stop, checkpoint, reduce_lr]
)




# Convert the model to TensorFlow Lite
model = tf.keras.models.load_model('best_model.keras')
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

with open('model.tflite', 'wb') as f:
    f.write(tflite_model)




# Save the model in Keras format
model.save('plant_disease_model_inception.keras')




# Evaluate the model on the test data
test_datagen = ImageDataGenerator(rescale=1./255)
test_dataset = test_datagen.flow_from_directory(
    test_dir,
    target_size=image_size,
    batch_size=batch_size,
    class_mode='categorical'
)

test_labels = to_categorical(test_dataset.classes, num_classes=num_classes)
start_time = time.time()
y_pred = model.predict(test_dataset)
y_pred_bool = np.argmax(y_pred, axis=1)
rounded_labels = np.argmax(test_labels, axis=1)

print(classification_report(rounded_labels, y_pred_bool, digits=4))
print(f"Time taken to predict the model: {time.time() - start_time}")




# Save the model in HDF5 format
model.save('plant_disease_model_inception.h5')




# Visualize a specific image and prediction
img_path = r'/kaggle/input/weed-detection/test/ridderzuring_3126_jpg.rf.8980b3ae3ec4ecd023aab5bc54c26089.jpg'
img = tf.keras.preprocessing.image.load_img(img_path, target_size=image_size)
img_array = tf.keras.preprocessing.image.img_to_array(img)
img_array = tf.image.resize(img_array, image_size)
img_array = tf.expand_dims(img_array, axis=0)

predictions = model.predict(img_array)
predicted_class = np.argmax(predictions[0])




# Generate the heatmap
last_conv_layer = model.get_layer('mixed10')
heatmap_model = tf.keras.models.Model([model.inputs], [last_conv_layer.output, model.output])

with tf.GradientTape() as tape:
    conv_outputs, predictions = heatmap_model(img_array)
    loss = predictions[:, predicted_class]

grads = tape.gradient(loss, conv_outputs)
pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
heatmap = tf.reduce_mean(tf.multiply(pooled_grads, conv_outputs), axis=-1)
heatmap = np.maximum(heatmap, 0)

heatmap_resized = cv2.resize(heatmap.numpy(), (img_array.shape[2], img_array.shape[1]))




# Overlay the heatmap on the original image
img_array_uint8 = (img_array[0].numpy() * 255).astype(np.uint8)
heatmap_resized_uint8 = (heatmap_resized * 255).astype(np.uint8)
heatmap_resized_uint8 = cv2.applyColorMap(heatmap_resized_uint8, cv2.COLORMAP_JET)
superimposed_img = cv2.addWeighted(img_array_uint8, 0.6, heatmap_resized_uint8, 0.4, 0)




# Display the original image, heatmap, and overlay
plt.figure(figsize=(12, 6))
plt.subplot(131)
plt.imshow(img)
plt.title('Original Image')

plt.subplot(132)
plt.imshow(heatmap_resized_uint8)
plt.title('Heatmap')

plt.subplot(133)
plt.imshow(superimposed_img)
plt.title('Overlay')

plt.tight_layout()
plt.show()