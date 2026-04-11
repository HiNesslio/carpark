# Vercel 部署 - 澳門停車場實時資訊
# 單一日 api/index.py 文件

import os
import xml.etree.ElementTree as ET
import requests
import math
from datetime import datetime, timezone, timedelta
from flask import Flask, jsonify, render_template, request

app = Flask(__name__, template_folder="api/templates")

# ============ 配置 ============
MACAO_TZ = timezone(timedelta(hours=8))
DSAT_API_URL = "https://dsat.apigateway.data.gov.mo/car_park_maintance"
DSAT_API_CODE = os.getenv("DSAT_API_CODE") or "09d43a591fba407fb862412970667de4"
DSAT_INFO_URL = "https://www.dsat.gov.mo/dsat/carpark_info2.aspx"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"

# 停車場座標
CARPARK_LOCATIONS = {
    "栢力停車場": {"lat": 22.2025, "lng": 113.5430},
    "望信停車場": {"lat": 22.2080, "lng": 113.5490},
    "東啟大廈停車場": {"lat": 22.2050, "lng": 113.5510},
    "栢佳停車場": {"lat": 22.2010, "lng": 113.5420},
    "栢湖停車場": {"lat": 22.2000, "lng": 113.5440},
    "南灣湖景大馬路停車場": {"lat": 22.1920, "lng": 113.5380},
    "西灣湖景大馬路停車場": {"lat": 22.1890, "lng": 113.5350},
    "媽閣交通樞紐": {"lat": 22.1860, "lng": 113.5310},
    "氹仔奧林匹克體育中心停車場": {"lat": 22.1550, "lng": 113.5550},
    "氹仔市政街市停車場": {"lat": 22.1570, "lng": 113.5560},
    "路環市區停車場": {"lat": 22.1200, "lng": 113.5600},
    "栢蕙": {"lat": 22.202335, "lng": 113.5504998},
    "港珠澳大橋邊檢大樓東公共停車場": {"lat": 22.2590, "lng": 113.5320},
    "港珠澳大橋邊檢大樓西停車場": {"lat": 22.2570, "lng": 113.5290},
    "氹仔中央公園": {"lat": 22.1530, "lng": 113.5570},
    "何賢公園": {"lat": 22.1930, "lng": 113.5390},
    "快達樓": {"lat": 22.1948, "lng": 113.5355},
    "亞馬喇前地": {"lat": 22.1960, "lng": 113.5380},
    "馬六甲街": {"lat": 22.1970, "lng": 113.5410},
    "青怡大廈": {"lat": 22.1985, "lng": 113.5430},
    "華士古達嘉馬花園": {"lat": 22.1935, "lng": 113.5415},
    "湖畔大廈": {"lat": 22.1450, "lng": 113.5650},
    "業興大廈": {"lat": 22.1470, "lng": 113.5680},
    "交通事務局大樓": {"lat": 22.1860, "lng": 113.5320},
    "蓮花路": {"lat": 22.138667, "lng": 113.560005},
    "宋玉生廣場停車場": {"lat": 22.188348, "lng": 113.551009},
    "祐漢公園停車場": {"lat": 22.210877, "lng": 113.551882},
}

# EV 停車場數據（預設數據）
EV_CARPARK_DATA = {
    "港珠澳大橋邊檢大樓東公共停車場 ": 4,
    "港珠澳大橋邊檢大樓西停車場": 4,
    "氹仔中央公園": 6,
    "何賢公園": 4,
    "快達樓": 2,
    "亞馬喇前地": 4,
    "馬六甲街": 2,
    "青怡大廈": 2,
    "華士古達嘉馬花園": 4,
    "湖畔大廈": 4,
    "業興大廈": 2,
    "交通教育局大樓": 2,
}

# 額外總車位數據
EXTRA_CAPACITY = {
    "塔石廣場地下上落客區(重型客車)": {"light_vehicle": 0, "motorcycle": 0, "heavy_vehicle": 20},
    "交通事務局大樓": {"light_vehicle": 145, "motorcycle": 118, "heavy_vehicle": 0},
    "沙梨頭街市市政綜合大樓": {"light_vehicle": 116, "motorcycle": 194, "heavy_vehicle": 0},
    "旅遊塔": {"light_vehicle": 350, "motorcycle": 0, "heavy_vehicle": 0},
    "媽閣交通樞紐停車場": {"light_vehicle": 201, "motorcycle": 403, "heavy_vehicle": 27},
    "澳門新批發市場": {"light_vehicle": 230, "motorcycle": 198, "heavy_vehicle": 0},
    "蓮花路 (重型)": {"light_vehicle": 0, "motorcycle": 0, "heavy_vehicle": 240},
    "氹仔客運碼頭": {"light_vehicle": 740, "motorcycle": 196, "heavy_vehicle": 0},
    "氹仔柯維納馬路停車場": {"light_vehicle": 61, "motorcycle": 0, "heavy_vehicle": 10},
    "東亞運大馬路公共停車場": {"light_vehicle": 45, "motorcycle": 20, "heavy_vehicle": 0},
    "港珠澳大橋邊檢大樓東公共停車場 ": {"light_vehicle": 3000, "motorcycle": 0, "heavy_vehicle": 0},
    "港珠澳大橋邊檢大樓西停車場": {"light_vehicle": 3089, "motorcycle": 2054, "heavy_vehicle": 0},
}

# ============ 工具函數 ============

def calculate_distance_km(lat1, lng1, lat2, lng2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return round(R * c, 1)

def reverse_geocode(lat, lng):
    try:
        params = {"lat": lat, "lng": lng, "format": "json", "addressdetails": 1}
        r = requests.get(NOMINATIM_URL, params=params, timeout=5)
        data = r.json()
        addr = data.get("address", {})
        parts = []
        for key in ["neighbourhood", "suburb", "city", "municipality"]:
            if key in addr:
                parts.append(addr[key])
        return ", ".join(parts) if parts else data.get("display_name", "")[:50]
    except:
        return ""

# ============ API ============

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    return response

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
        # 獲取即時數據 - 使用與本地版本相同的 header
        headers = {
            "Authorization": f"APPCODE {DSAT_API_CODE}",
            "user-agent": "MacauCarpark/1.0",
            "Accept": "application/xml"
        }
        
        # 添加調試日誌
        print(f"[DEBUG] Calling DSAT API: {DSAT_API_URL}")
        print(f"[DEBUG] Using subscription key: {DSAT_API_CODE[:8]}...")
        
        response = requests.get(DSAT_API_URL, headers=headers, timeout=15)
        
        print(f"[DEBUG] Response status: {response.status_code}")
        print(f"[DEBUG] Response headers: {dict(response.headers)}")
        print(f"[DEBUG] Response text (first 500 chars): {response.text[:500] if response.text else 'EMPTY'}")
        
        response.encoding = "UTF-8"
        
        if response.status_code != 200:
            return jsonify({
                "error": f"API錯誤: {response.status_code}", 
                "debug_info": {
                    "status_code": response.status_code,
                    "response_text": response.text[:500] if response.text else "EMPTY"
                },
                "carparks": []
            }), 500
            
        xml_data = response.text
    except requests.exceptions.Timeout:
        return jsonify({"error": "API 超時", "carparks": []}), 500
    except requests.exceptions.ConnectionError as e:
        return jsonify({
            "error": f"連接失敗: {str(e)}", 
            "carparks": []
        }), 500
    except Exception as e:
        return jsonify({"error": f"獲取數據失敗: {str(e)}", "carparks": []}), 500

    try:
        root = ET.fromstring(xml_data)
    except:
        return jsonify({"carparks": []})

    carparks = []
    for cp in root.findall(".//Car_park_info"):
        name = cp.get("name", "")
        light_avail = int(cp.get("Car_CNT", 0) or 0)
        light_total = int(cp.get("Car_Total", 0) or 0)
        heavy_avail = int(cp.get("OT_A_CNT", 0) or 0)
        heavy_total = int(cp.get("OT_A_Total", 0) or 0)
        mc_avail = int(cp.get("MB_CNT", 0) or 0)
        mc_total = int(cp.get("MB_Total", 0) or 0)

        # 合併總車位數據
        cap = EXTRA_CAPACITY.get(name, {})
        if cap.get("light_vehicle"):
            light_total = cap["light_vehicle"]
        if cap.get("motorcycle"):
            mc_total = cap["motorcycle"]
        if cap.get("heavy_vehicle"):
            heavy_total = cap["heavy_vehicle"]

        # EV
        ev_count = 0
        for ev_name, ev_val in EV_CARPARK_DATA.items():
            if ev_name in name or name in ev_name:
                ev_count = ev_val
                break

        if ev_only and ev_count == 0:
            continue

        carparks.append({
            "name": name,
            "light_vehicle": {"available": light_avail, "total": light_total},
            "heavy_vehicle": {"available": heavy_avail, "total": heavy_total},
            "motorcycle": {"available": mc_avail, "total": mc_total},
            "ev_charging": ev_count,
        })

    # 添加位置和距離
    result = []
    for cp in carparks:
        loc = None
        for loc_name, loc_data in CARPARK_LOCATIONS.items():
            if loc_name in cp["name"] or cp["name"] in loc_name:
                loc = loc_data
                break
        
        if loc:
            dist = calculate_distance_km(lat, lng, loc["lat"], loc["lng"])
            cp["distance_km"] = dist
            result.append(cp)

    result.sort(key=lambda x: x.get("distance_km", 999))

    user_address = reverse_geocode(lat, lng)

    return jsonify({
        "updated_at": datetime.now(MACAO_TZ).isoformat(),
        "user_lat": lat,
        "user_lng": lng,
        "user_address": user_address,
        "ev_mode": ev_only,
        "carparks": result[:20],
    })

# ============ Vercel 入口 ============
app.api = app
wsgi_app = app