from flask import Flask, render_template, request, redirect, url_for, session
import os
import numpy as np
from PIL import Image
from tensorflow.keras.models import load_model
from cea import convert_to_cea_image

app = Flask(__name__)
app.secret_key = "forgexplorer_secret_key"

# ---------------- CONFIG ----------------
UPLOAD_FOLDER = "static/uploads"
CEA_FOLDER = "static/cea"
MODEL_PATH = "train_model.h5"
IMAGE_SIZE = (128, 128)
THRESHOLD = 0.5

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CEA_FOLDER, exist_ok=True)

model = load_model(MODEL_PATH)

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["logged_in"] = True
        return redirect(url_for("upload"))
    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# ---------------- UPLOAD (TIFF SAFE) ----------------
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    if request.method == "POST":
        file = request.files.get("image")

        if file:
            # ALWAYS convert to JPG
            base_name = os.path.splitext(file.filename)[0]
            jpg_filename = base_name + ".jpg"
            image_path = os.path.join(UPLOAD_FOLDER, jpg_filename)

            img = Image.open(file)
            img = img.convert("RGB")        # CRITICAL for TIFF
            img.save(image_path, "JPEG")

            return redirect(url_for("cea_page", filename=jpg_filename))

    return render_template("upload.html")

# ---------------- CEA PAGE (JPG OUTPUT) ----------------
@app.route("/cea/<filename>")
def cea_page(filename):
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    image_path = os.path.join(UPLOAD_FOLDER, filename)

    # Generate CEA image
    cea_img = convert_to_cea_image(image_path)
    cea_img = cea_img.convert("RGB")

    cea_filename = os.path.splitext(filename)[0] + "_cea.jpg"
    cea_path = os.path.join(CEA_FOLDER, cea_filename)
    cea_img.save(cea_path, "JPEG")

    return render_template(
        "cea.html",
        original_image=f"uploads/{filename}",
        cea_image=f"cea/{cea_filename}",
        filename=filename
    )

# ---------------- RESULT PAGE ----------------
@app.route("/result/<filename>")
def result(filename):
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    cea_filename = os.path.splitext(filename)[0] + "_cea.jpg"
    cea_path = os.path.join(CEA_FOLDER, cea_filename)

    # CNN input
    cea_img = Image.open(cea_path).resize(IMAGE_SIZE)
    img = np.array(cea_img) / 255.0
    img = img.reshape(1, 128, 128, 3)

    pred = model.predict(img)[0][0]

    if pred >= THRESHOLD:
        label = "Authentic"
        confidence = pred * 100
    else:
        label = "Forged"
        confidence = (1 - pred) * 100

    return render_template(
        "result.html",
        prediction=label,
        confidence=f"{confidence:.2f}%",
        image=f"uploads/{filename}",
        cea_image=f"cea/{cea_filename}"
    )

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
