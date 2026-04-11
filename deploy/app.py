from flask import Flask, jsonify, render_template, request
import os
import time
from datetime import datetime

from carpark_service import (
    fetch_carpark_data,
    parse_carpark_xml,
    calculate_distance_km,
    MACAO_TZ,
    reverse_geocode,
    fetch_total_capacity_data,
    merge_carpark_data,
    merge_ev_data,
)
from carpark_locations import get_carpark_location

app = Flask(__name__, template_folder="templates")

DSAT_API_URL = "https://dsat.apigateway.data.gov.mo/car_park_maintance"
DSAT_API_CODE = os.getenv("DSAT_API_CODE")

# 緩存配置（5 分鐘）
_carpark_cache = None
_carpark_cache_time = None
EV_CACHE_DURATION = 300


def get_carpark_data_cached():
    """取得停車場數據（帶 5 分鐘緩存）"""
    global _carpark_cache, _carpark_cache_time
    
    now = time.time()
    if _carpark_cache is None or (_carpark_cache_time and now - _carpark_cache_time > EV_CACHE_DURATION):
        xml_data = fetch_carpark_data()
        carparks = parse_carpark_xml(xml_data)
        
        # 合併總車位數據
        total_capacity = fetch_total_capacity_data()
        carparks = merge_carpark_data(carparks, total_capacity)
        
        # 合併 EV 數據
        carparks = merge_ev_data(carparks)
        
        _carpark_cache = carparks
        _carpark_cache_time = now
    
    return _carpark_cache


@app.route("/")
def index():
    return render_template("index.html")


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    return response


@app.route("/api/carparks")
def api_carparks():
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    ev_only = request.args.get("ev_only", "false").lower() == "true"

    if lat is None or lng is None:
        return jsonify({"error": "需要提供 lat 和 lng 參數"}), 400

    try:
        # 使用 5 分鐘緩存的數據
        carparks = get_carpark_data_cached()
        
        if ev_only:
            carparks = [cp for cp in carparks if cp.get("ev_charging", 0) > 0]
            
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
        "carparks": result[:20],
    })


# Vercel 入口
app.api = app
wsgi_app = app


if __name__ == "__main__":
    app.run(debug=True, port=5000)