# Full Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 部署完整版澳門停車場應用到 Vercel，包含：即時車位、EV 充電位、數據緩存、距離排序、用戶位置

**Architecture:** 使用 Flask 框架部署到 Vercel，調用 DSAT API 獲取停車場數據，合併總車位數據和 EV 數據，計算距離並排序返回

**Tech Stack:** Python Flask, requests, XML parsing, Vercel deployment

---

## File Structure

```
/Users/tiang/Desktop/New/
├── deploy/                     # 部署專用文件夾
│   ├── app.py                  # Flask 應用程序
│   ├── carpark_service.py       # 停車場數據服務
│   ├── carpark_locations.py    # 停車場座標
│   ├── templates/
│   │   └── index.html         # 前端頁面
│   ├── requirements.txt        # Python 依賴
│   └── vercel.json           # Vercel 配置
```

---

## Task 1: Create deploy folder structure

**Files:**
- Create: `deploy/app.py`
- Create: `deploy/carpark_service.py`
- Create: `deploy/carpark_locations.py`
- Create: `deploy/templates/index.html`
- Create: `deploy/requirements.txt`
- Create: `deploy/vercel.json`

- [ ] **Step 1: Create deploy directory**

```bash
mkdir -p /Users/tiang/Desktop/New/deploy/templates
```

- [ ] **Step 2: Create requirements.txt**

```txt
flask==3.1.0
requests==2.32.3
python-dotenv==1.0.1
beautifulsoup4==4.12.3
lxml==5.3.0
```

- [ ] **Step 3: Create vercel.json**

```json
{
  "buildCommand": "pip install -r requirements.txt",
  "outputDirectory": ".",
  "framework": "flask",
  "installCommand": "pip install -r requirements.txt",
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/app.py"
    }
  ]
}
```

---

## Task 2: Create carpark_service.py

**Files:**
- Create: `deploy/carpark_service.py`

- [ ] **Step 1: Write carpark_service.py**

```python
import os
import xml.etree.ElementTree as ET
import requests
import math
from datetime import datetime, timezone, timedelta

MACAO_TZ = timezone(timedelta(hours=8))

DSAT_API_URL = "https://dsat.apigateway.data.gov.mo/car_park_maintance"
DSAT_API_CODE = os.getenv("DSAT_API_CODE") or "09d43a591fba407fb862412970667de4"

DSAT_INFO_URL = "https://www.dsat.gov.mo/dsat/carpark_info2.aspx"

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"


def reverse_geocode(lat, lng):
    """使用 Nominatim 將座標轉換為街名"""
    try:
        params = {
            "format": "json",
            "lat": lat,
            "lon": lng,
            "zoom": 18,
            "addressdetails": 1,
        }
        headers = {"User-Agent": "MacauCarpark/1.0"}
        response = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("display_name", "")
    except Exception:
        pass
    return None


def fetch_carpark_data(max_retries=2):
    """從 DSAT API 獲取 XML 數據，帶重試機制"""
    headers = {"Authorization": f"APPCODE {DSAT_API_CODE}"}
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(DSAT_API_URL, headers=headers, timeout=10)
            response.encoding = "UTF-8"
            response.raise_for_status()
            return response.text
        except requests.exceptions.Timeout:
            last_error = "DSAT API 超時"
        except requests.exceptions.RequestException as e:
            last_error = f"網絡錯誤: {str(e)}"
    raise Exception(last_error or "DSAT API 請求失敗")


def parse_carpark_xml(xml_data):
    """解析 XML 返回停車場列表"""
    if not xml_data:
        return []
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        raise ValueError(f"XML 解析失敗: {str(e)}")
    
    carparks = []
    for info in root.findall("Car_park_info"):
        name = info.get("name", "")
        try:
            carparks.append({
                "name": name,
                "light_vehicle": {
                    "available": int(info.get("Car_CNT", "0") or "0"),
                    "total": int(info.get("Car_Total", "0") or "0"),
                },
                "heavy_vehicle": {
                    "available": int(info.get("OT_A_CNT", "0") or "0"),
                    "total": int(info.get("OT_A_Total", "0") or "0"),
                },
                "motorcycle": {
                    "available": int(info.get("MB_CNT", "0") or "0"),
                    "total": int(info.get("MB_Total", "0") or "0"),
                },
                "updated_at": info.get("Time", ""),
            })
        except (ValueError, TypeError):
            continue
    return carparks


def calculate_distance_km(lat1, lng1, lat2, lng2):
    """使用 Haversine 公式計算兩點距離（公里）"""
    if None in (lat1, lng1, lat2, lng2):
        raise ValueError("所有座標參數都不能為 None")
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


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


def merge_carpark_data(realtime_data, total_capacity):
    """合併即時數據與總車位數據"""
    result = []
    
    for cp in realtime_data:
        name = cp.get("name", "")
        matched_name = None
        
        if name in total_capacity:
            matched_name = name
        else:
            for cap_name in total_capacity:
                if cap_name in name or name in cap_name:
                    matched_name = cap_name
                    break
        
        cp_copy = cp.copy()
        
        if matched_name:
            cap = total_capacity[matched_name]
            if cp_copy["light_vehicle"]["total"] == 0:
                cp_copy["light_vehicle"]["total"] = cap.get("light_vehicle", 0)
            if cp_copy["motorcycle"]["total"] == 0:
                cp_copy["motorcycle"]["total"] = cap.get("motorcycle", 0)
            if cp_copy["heavy_vehicle"]["total"] == 0:
                cp_copy["heavy_vehicle"]["total"] = cap.get("heavy_vehicle", 0)
        
        result.append(cp_copy)
    
    return result


def merge_ev_data(carparks):
    """將 EV 充電位數據合併到停車場列表"""
    result = []
    for cp in carparks:
        cp_copy = cp.copy()
        cp_copy["ev_charging"] = 0
        
        cp_name = cp.get("name", "")
        
        for ev_name, ev_count in EV_CARPARK_DATA.items():
            if ev_name in cp_name or cp_name in ev_name:
                cp_copy["ev_charging"] = ev_count
                break
        
        result.append(cp_copy)
    
    return result
```

- [ ] **Step 2: Commit**

```bash
git add deploy/carpark_service.py
git commit -m "feat(deploy): add carpark service for deployment"
```

---

## Task 3: Create carpark_locations.py

**Files:**
- Create: `deploy/carpark_locations.py`

- [ ] **Step 1: Write carpark_locations.py**

```python
"""停車場座標數據"""

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
    "何��公��": {"lat": 22.1930, "lng": 113.5390},
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


def get_carpark_location(name):
    """根據停車場名稱獲取座標"""
    if not name:
        return None
    
    # 精確匹配
    if name in CARPARK_LOCATIONS:
        return CARPARK_LOCATIONS[name]
    
    # 部分匹配
    for loc_name, loc_data in CARPARK_LOCATIONS.items():
        if loc_name in name or name in loc_name:
            return loc_data
    
    return None
```

- [ ] **Step 2: Commit**

```bash
git add deploy/carpark_locations.py
git commit -m "feat(deploy): add carpark locations"
```

---

## Task 4: Create app.py with caching

**Files:**
- Create: `deploy/app.py`

- [ ] **Step 1: Write app.py with caching**

```python
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
    merge_carpark_data,
    merge_ev_data,
    EXTRA_CAPACITY,
)
from carpark_locations import get_carpark_location

app = Flask(__name__, template_folder="templates")

DSAT_API_URL = "https://dsat.apigateway.data.gov.mo/car_park_maintance"
DSAT_API_CODE = os.getenv("DSAT_API_CODE")

# 緩存配置
_carpark_cache = None
_carpark_cache_time = None
EV_CACHE_DURATION = 300  # 5 分鐘


def get_carpark_data_cached():
    """取得停車場數據（帶 5 分鐘緩存）"""
    global _carpark_cache, _carpark_cache_time
    
    now = time.time()
    if _carpark_cache is None or (_carpark_cache_time and now - _carpark_cache_time > EV_CACHE_DURATION):
        xml_data = fetch_carpark_data()
        carparks = parse_carpark_xml(xml_data)
        
        # 合併總車位數據
        carparks = merge_carpark_data(carparks, EXTRA_CAPACITY)
        
        # 合併 EV 數據
        carparks = merge_ev_data(carparks)
        
        _carpark_cache = carparks
        _carpark_cache_time = now
    
    return _carpark_cache


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
```

- [ ] **Step 2: Commit**

```bash
git add deploy/app.py
git commit -m "feat(deploy): add Flask app with caching"
```

---

## Task 5: Create frontend template

**Files:**
- Create: `deploy/templates/index.html`

- [ ] **Step 1: Copy frontend from templates/index.html**

需要從 `/Users/tiang/Desktop/New/templates/index.html` 複製前端模板，並修改 API URL 指向部署後端

- [ ] **Step 2: Modify API URL**

將前端中的 API URL 改為相對路徑 `/api/carparks`

- [ ] **Step 3: Commit**

```bash
git add deploy/templates/index.html
git commit -m "feat(deploy): add frontend template"
```

---

## Task 6: Deploy to Vercel

**Files:**
- Commit all deploy files
- Push to GitHub

- [ ] **Step 1: Commit all deploy files**

```bash
git add deploy/
git commit -m "feat(deploy): add full deployment package"
```

- [ ] **Step 2: Push to GitHub**

```bash
git push origin main
```

- [ ] **Step 3: Connect Vercel**

1. 打開 https://vercel.com
2. 導入 GitHub 項目
3. 選擇 `deploy` 文件夾作為 root
4. 設置環境變量 `DSAT_API_CODE`
5. 部署

---

## Verification

部署完成後，驗證 API 是否正常運作：

```bash
curl "https://your-vercel-url.vercel.app/api/carparks?lat=22.198&lng=113.544"
```

預期返回：包含所有停車場的 JSON 數據，按距離排序