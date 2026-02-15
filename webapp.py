from flask import Flask, render_template, request
import cv2
import os
import numpy as np

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
RESULT_FOLDER = "static/results"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["RESULT_FOLDER"] = RESULT_FOLDER


def detect_microplastics(image_path, output_path):
    image = cv2.imread(image_path)
    original = image.copy()

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    thresh = cv2.adaptiveThreshold(
        blur, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11, 2
    )

    edges = cv2.Canny(thresh, 50, 150)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    count = 0

    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 80:
            count += 1
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(original, (x, y), (x+w, y+h), (0, 255, 0), 2)

    cv2.imwrite(output_path, original)

    return count


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["image"]

        if file:
            upload_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            result_path = os.path.join(app.config["RESULT_FOLDER"], file.filename)

            file.save(upload_path)

            count = detect_microplastics(upload_path, result_path)

            return render_template("index.html",
                                   uploaded_image=upload_path,
                                   result_image=result_path,
                                   count=count)

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
