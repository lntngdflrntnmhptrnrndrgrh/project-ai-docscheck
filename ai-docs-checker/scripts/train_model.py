import os
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping

# Tentukan base folder (root proyek)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATASET_DIR = os.path.join(BASE_DIR, "dataset_ttd")

# Parameter
IMG_SIZE = (224, 224)
BATCH_SIZE = 16
EPOCHS = 15

# Data generator dengan augmentasi
data_gen = ImageDataGenerator(
    rescale=1./255,
    validation_split=0.1,
    rotation_range=5,
    zoom_range=0.1,
    horizontal_flip=False
)

train_ds = data_gen.flow_from_directory(
    DATASET_DIR,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode="categorical",
    subset="training"
)

val_ds = data_gen.flow_from_directory(
    DATASET_DIR,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode="categorical",
    subset="validation"
)

# Jumlah kelas dari folder
num_classes = len(train_ds.class_indices)
print(f"Detected classes: {train_ds.class_indices}")

# Bangun model
base_model = MobileNetV2(weights="imagenet", include_top=False, input_shape=(224, 224, 3))
base_model.trainable = False

model = Sequential([
    base_model,
    GlobalAveragePooling2D(),
    Dense(128, activation='relu'),
    Dense(num_classes, activation='softmax')
])

model.compile(
    optimizer=Adam(),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

# Training
model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS,
    callbacks=[EarlyStopping(patience=3, restore_best_weights=True)]
)

# Simpan model
model.save(os.path.join(BASE_DIR, "model_ttd.h5"))
print("✅ Model saved as model_ttd.h5")
