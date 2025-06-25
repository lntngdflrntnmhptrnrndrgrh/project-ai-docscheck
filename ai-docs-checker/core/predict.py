# core/predict.py
import os
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

# Load model
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODEL_PATH = os.path.join(BASE_DIR, "model_ttd.h5")
model = load_model(MODEL_PATH)

CLASS_NAMES = ["lengkap", "sebagian"]  # Tambah "tidak_ada" jika tersedia

def predict_signature(img_path):
    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    prediction = model.predict(img_array)
    class_index = np.argmax(prediction[0])
    class_label = CLASS_NAMES[class_index]
    confidence = float(np.max(prediction[0]))

    return class_label, confidence
