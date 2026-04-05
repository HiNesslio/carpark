from flask import Flask, jsonify, render_template
import os

app = Flask(__name__, static_folder="static", static_url_path="")

DSAT_API_URL = "https://dsat.apigateway.data.gov.mo/car_park_maintance"
DSAT_API_CODE = os.getenv("DSAT_API_CODE", "09d43a591fba407fb862412970667de4")


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
