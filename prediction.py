import numpy as np
from PIL import Image
from tensorflow.keras.models import load_model
from cea import convert_to_cea_image   # ✅ CEA import

# -------- CONFIG --------
MODEL_PATH = "train_model.h5"   # trained CNN model
IMAGE_SIZE = (128, 128)
THRESHOLD = 0.5                 # standard threshold

# Load trained model
model = load_model(MODEL_PATH)

def prepare_image(image_path):
    """
    Apply CEA + resize + normalization
    """
    # Generate CEA image
    cea_image = convert_to_cea_image(image_path)

    # Resize
    cea_image = cea_image.resize(IMAGE_SIZE)

    # Normalize
    cea_image = np.array(cea_image) / 255.0

    # Reshape for CNN
    cea_image = cea_image.reshape(1, 128, 128, 3)

    return cea_image

def predict_image(image_path):
    """
    Predict whether image is Forged or Authentic
    """
    image = prepare_image(image_path)
    prediction = model.predict(image)[0][0]

    if prediction >= THRESHOLD:
        label = "Authentic"
        confidence = prediction * 100
    else:
        label = "Forged"
        confidence = (1 - prediction) * 100

    return label, confidence

# -------- TESTING --------
if __name__ == "__main__":
    test_image_path = "dataset/forged/Tp_D_CNN_M_N_ani00057_ani00055_11149.jpg"

    label, confidence = predict_image(test_image_path)

    print("Prediction :", label)
    print(f"Confidence : {confidence:.2f}%")
