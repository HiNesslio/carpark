from flask import Flask, jsonify, render_template, request
import os
from datetime import datetime

from carpark_service import (
    fetch_carpark_data,
    parse_carpark_xml,
    calculate_distance_km,
    MACAO_TZ,
    reverse_geocode,
    fetch_total_capacity_data,
    merge_carpark_data,
)
from carpark_locations import get_carpark_location

app = Flask(__name__, template_folder="templates")

DSAT_API_URL = "https://dsat.apigateway.data.gov.mo/car_park_maintance"
DSAT_API_CODE = os.getenv("DSAT_API_CODE")

_total_capacity_cache = None


def get_total_capacity():
    """取得總車位數據（帶緩存）"""
    global _total_capacity_cache
    if _total_capacity_cache is None:
        _total_capacity_cache = fetch_total_capacity_data()
    return _total_capacity_cache


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/carparks")
def api_carparks():
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    ev_only = request.args.get("ev_only", "false").lower() == "true"

    if lat is None or lng is None:
        return jsonify({"error": "需要提供 lat 和 lng 參數"}), 400

    try:
        xml_data = fetch_carpark_data()
        carparks = parse_carpark_xml(xml_data)
        
        total_capacity = get_total_capacity()
        carparks = merge_carpark_data(carparks, total_capacity)
        
    except ValueError as e:
        return jsonify({"error": f"數據格式錯誤: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"數據獲取失敗: {str(e)}"}), 500

    result = []
    for cp in carparks:
        loc = get_carpark_location(cp["name"])
        if loc:
            cp["distance_km"] = calculate_distance_km(lat, lng, loc["lat"], loc["lng"])
            result.append(cp)

    result.sort(key=lambda x: x["distance_km"])

    user_address = reverse_geocode(lat, lng)

    return jsonify({
        "updated_at": datetime.now(MACAO_TZ).isoformat(),
        "user_lat": lat,
        "user_lng": lng,
        "user_address": user_address,
        "ev_mode": ev_only,
        "carparks": result,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)