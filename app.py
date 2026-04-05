from flask import Flask, jsonify, render_template
import os
from carpark_service import fetch_carpark_data, parse_carpark_xml

app = Flask(__name__)

DSAT_API_URL = "https://dsat.apigateway.data.gov.mo/car_park_maintance"
DSAT_API_CODE = os.getenv("DSAT_API_CODE")


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
