
from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import json
import numpy as np
from PIL import Image
from tensorflow.keras.models import load_model
from cea import convert_to_cea_image

# -----------------------------
# APP SETUP
# -----------------------------
app = Flask(__name__)
app.secret_key = "forgexplorer_secret_key"

# -----------------------------
# CONFIG
# -----------------------------
UPLOAD_FOLDER = "static/uploads"
CEA_FOLDER = "static/cea"
MODEL_PATH = "train_model.h5"
IMAGE_SIZE = (128, 128)
THRESHOLD = 0.5
HISTORY_FILE = "history.json"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CEA_FOLDER, exist_ok=True)

model = load_model(MODEL_PATH)

# -----------------------------
# LOAD HISTORY
# -----------------------------
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r") as f:
        history_data = json.load(f)
else:
    history_data = []

# -----------------------------
# HOME
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")

# -----------------------------
# ABOUT
# -----------------------------
@app.route("/about")
def about():
    return render_template("about.html")

# -----------------------------
# LOGIN
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        users_file = "users.json"

        if os.path.exists(users_file):
            with open(users_file, "r") as f:
                users = json.load(f)
        else:
            users = []

        for user in users:
            if user["email"] == email and user["password"] == password:

                session["logged_in"] = True
                session["user_email"] = email

                flash("Login Successful!", "success")
                return redirect(url_for("home"))

        flash("Invalid Email or Password!", "error")

    return render_template("login.html")

# -----------------------------
# REGISTER
# -----------------------------
@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        users_file = "users.json"

        if os.path.exists(users_file):
            with open(users_file,"r") as f:
                users = json.load(f)
        else:
            users = []

        users.append({
            "email": email,
            "password": password
        })

        with open(users_file,"w") as f:
            json.dump(users,f,indent=4)

        flash("Registration Successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# -----------------------------
# ADMIN USER LIST
# -----------------------------
@app.route("/admin")
def users():

    users_file = "users.json"

    if os.path.exists(users_file):
        with open(users_file, "r") as f:
            users = json.load(f)
    else:
        users = []

    return render_template("admin.html", users=users)

# -----------------------------
# DELETE USER
# -----------------------------
@app.route("/delete_user/<email>")
def delete_user(email):

    users_file = "users.json"

    if os.path.exists(users_file):
        with open(users_file, "r") as f:
            users = json.load(f)
    else:
        users = []

    users = [user for user in users if user["email"] != email]

    with open(users_file, "w") as f:
        json.dump(users, f, indent=4)

    flash("User deleted successfully!", "success")

    return redirect(url_for("users"))

# -----------------------------
# UPLOAD IMAGE
# -----------------------------
@app.route("/upload", methods=["GET", "POST"])
def upload():

    if not session.get("logged_in"):
        return redirect(url_for("login"))

    image_filename = None

    if request.method == "POST":

        file = request.files.get("image")

        if file:

            base = os.path.splitext(file.filename)[0]
            image_filename = base + ".jpg"

            path = os.path.join(UPLOAD_FOLDER, image_filename)

            img = Image.open(file).convert("RGB")
            img.save(path, "JPEG")

    return render_template("upload.html", image_filename=image_filename)

# -----------------------------
# CEA IMAGE
# -----------------------------
@app.route("/cea/<filename>")
def cea_page(filename):

    if not session.get("logged_in"):
        return redirect(url_for("login"))

    image_path = os.path.join(UPLOAD_FOLDER, filename)

    cea_img = convert_to_cea_image(image_path)

    cea_name = os.path.splitext(filename)[0] + "_cea.jpg"
    cea_path = os.path.join(CEA_FOLDER, cea_name)

    cea_img.save(cea_path, "JPEG")

    return render_template(
        "cea.html",
        original_image=f"uploads/{filename}",
        cea_image=f"cea/{cea_name}",
        filename=filename
    )

# -----------------------------
# RESULT
# -----------------------------
@app.route("/result/<filename>")
def result(filename):

    if not session.get("logged_in"):
        return redirect(url_for("login"))

    cea_name = os.path.splitext(filename)[0] + "_cea.jpg"
    cea_path = os.path.join(CEA_FOLDER, cea_name)

    img = Image.open(cea_path).resize(IMAGE_SIZE)
    img = np.array(img) / 255.0
    img = img.reshape(1, 128, 128, 3)

    pred = model.predict(img)[0][0]

    if pred >= THRESHOLD:
        label = "Authentic"
        confidence = pred * 100
    else:
        label = "Forged"
        confidence = (1 - pred) * 100

    history_data.append({
        "email": session.get("user_email"),
        "image": filename,
        "result": label,
        "confidence": f"{confidence:.2f}%"
    })

    with open(HISTORY_FILE, "w") as f:
        json.dump(history_data, f, indent=4)

    return render_template(
        "result.html",
        prediction=label,
        confidence=f"{confidence:.2f}%",
        image=f"uploads/{filename}",
        cea_image=f"cea/{cea_name}"
    )

# -----------------------------
# HISTORY
# -----------------------------
@app.route("/history")
def history():
    return render_template("history.html", history=history_data)

# -----------------------------
# LOGOUT
# -----------------------------
@app.route("/logout")
def logout():

    session.clear()

    flash("Logged out successfully!", "success")

    return redirect(url_for("home"))

# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)

