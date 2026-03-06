import numpy as np
from PIL import Image
from tensorflow.keras.models import load_model
from cea import convert_to_cea_image   # CEA import

# -------- CONFIG --------
MODEL_PATH = "train_model.h5"
IMAGE_SIZE = (128, 128)
THRESHOLD = 0.5

# Load trained model
model = load_model(MODEL_PATH)


def prepare_image(image_path):
    """
    Apply CEA + resize + normalization
    """

    cea_image = convert_to_cea_image(image_path)

    cea_image = cea_image.resize(IMAGE_SIZE)

    cea_image = np.array(cea_image) / 255.0

    cea_image = cea_image.reshape(1, 128, 128, 3)

    return cea_image


# -------- FORGERY TYPE DETECTION --------
def detect_forgery_type(cea_image):

    gray = np.mean(cea_image, axis=2)

    threshold = np.mean(gray) + 2 * np.std(gray)
    mask = gray > threshold

    artifact_pixels = np.sum(mask)

    if artifact_pixels < 500:
        return "Possible Copy-Move"

    elif artifact_pixels < 2000:
        return "Possible Splicing"

    else:
        return "Complex Manipulation"


def predict_image(image_path):
    """
    Predict whether image is Forged or Authentic
    """

    image = prepare_image(image_path)

    prediction = model.predict(image)[0][0]

    if prediction >= THRESHOLD:
        label = "Authentic"
        confidence = prediction * 100
        forgery_type = "None"

    else:
        label = "Forged"
        confidence = (1 - prediction) * 100

        # Generate CEA for forgery type analysis
        cea_img = convert_to_cea_image(image_path)

        forgery_type = detect_forgery_type(np.array(cea_img))

    return label, confidence, forgery_type


# -------- TESTING --------
if __name__ == "__main__":

    test_image_path = "dataset/forged/Tp_D_CNN_M_N_ani00057_ani00055_11149.jpg"

    label, confidence, forgery_type = predict_image(test_image_path)

    print("Prediction :", label)
    print(f"Confidence : {confidence:.2f}%")

    if label == "Forged":
        print("Forgery Type :", forgery_type)
