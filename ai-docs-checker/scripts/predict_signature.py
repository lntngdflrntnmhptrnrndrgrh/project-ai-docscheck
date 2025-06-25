import tensorflow as tf
from keras.preprocessing import image
from keras.preprocessing.image import ImageDataGenerator
import numpy as np
import os

MODEL_PATH = "../model_ttd.h5"
IMG_SIZE = (224, 224)
CLASS_NAMES = ["lengkap", "sebagian", "tidak_ada"]

model = tf.keras.models.load_model(MODEL_PATH)

def predict_signature(img_path):
    img = image.load_img(img_path, target_size=IMG_SIZE)
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0) / 255.0

    pred = model.predict(x)[0]
    class_id = np.argmax(pred)
    return CLASS_NAMES[class_id], float(pred[class_id])