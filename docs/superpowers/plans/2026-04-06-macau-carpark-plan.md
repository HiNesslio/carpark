# 澳門公共停車場實時資訊 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 構建一個簡單、乾淨的網頁應用，顯示澳門公共停車場實時剩餘車位，按用戶距離排序。

**Architecture:** Flask 後端代理 DSAT XML API，解析數據並計算距離；單一 HTML 前端通過瀏覽器定位獲取用戶位置，每 30 秒自動刷新。

**Tech Stack:** Python Flask, requests, xml.etree.ElementTree, 原生 HTML/CSS/JavaScript

---

### Task 1: 項目基礎結構和依賴

**Files:**
- Create: `requirements.txt`
- Create: `app.py`（基礎骨架）
- Create: `.gitignore`

- [ ] **Step 1: 創建 requirements.txt**

```
flask==3.1.0
requests==2.32.3
python-dotenv==1.0.1
```

- [ ] **Step 2: 創建 .gitignore**

```
__pycache__/
*.pyc
.env
venv/
```

- [ ] **Step 3: 創建 app.py 基礎骨架**

```python
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
```

- [ ] **Step 4: 創建 templates 目錄和空 index.html**

```bash
mkdir -p templates && touch templates/index.html
```

- [ ] **Step 5: 安裝依賴並驗證 Flask 啟動**

```bash
pip install -r requirements.txt
python app.py
```

Expected: Flask starts on http://localhost:5000

- [ ] **Step 6: 提交**

```bash
git add requirements.txt .gitignore app.py templates/index.html
git commit -m "feat: 初始化項目結構和 Flask 基礎"
```

---

### Task 2: 後端 — DSAT API 調用和 XML 解析

**Files:**
- Create: `carpark_service.py`
- Modify: `app.py`（引入 carpark_service）

- [ ] **Step 1: 編寫測試 — 測試 XML 解析**

Create `test_carpark_service.py`:

```python
from carpark_service import parse_carpark_xml


def test_parse_valid_xml():
    xml_data = """<?xml version="1.0" encoding="UTF-8"?>
    <CarPark>
        <Car_park_info name="栢力停車場" Car_CNT="280" Car_Total="417"
                       Heavy_CNT="0" Heavy_Total="0"
                       Moto_CNT="30" Moto_Total="32"
                       UpdateTime="2026-04-06 10:30:00"/>
    </CarPark>"""
    result = parse_carpark_xml(xml_data)
    assert len(result) == 1
    assert result[0]["name"] == "栢力停車場"
    assert result[0]["light_vehicle"] == {"available": 280, "total": 417}
    assert result[0]["heavy_vehicle"] == {"available": 0, "total": 0}
    assert result[0]["motorcycle"] == {"available": 30, "total": 32}


def test_parse_empty_xml():
    xml_data = '<?xml version="1.0" encoding="UTF-8"?><CarPark></CarPark>'
    result = parse_carpark_xml(xml_data)
    assert result == []
```

- [ ] **Step 2: 運行測試驗證失敗**

```bash
pytest test_carpark_service.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'carpark_service'"

- [ ] **Step 3: 實現 carpark_service.py**

```python
import xml.etree.ElementTree as ET
import requests
from datetime import datetime, timezone, timedelta


DSAT_API_URL = "https://dsat.apigateway.data.gov.mo/car_park_maintance"
DSAT_API_CODE = "09d43a591fba407fb862412970667de4"

MACAO_TZ = timezone(timedelta(hours=8))


def fetch_carpark_data():
    """從 DSAT API 獲取 XML 數據"""
    headers = {"Authorization": f"APPCODE {DSAT_API_CODE}"}
    response = requests.get(DSAT_API_URL, headers=headers, timeout=10)
    response.encoding = "UTF-8"
    return response.text


def parse_carpark_xml(xml_data):
    """解析 XML 返回停車場列表"""
    root = ET.fromstring(xml_data)
    carparks = []
    for info in root.findall("Car_park_info"):
        name = info.get("name", "")
        carparks.append({
            "name": name,
            "light_vehicle": {
                "available": int(info.get("Car_CNT", "0")),
                "total": int(info.get("Car_Total", "0")),
            },
            "heavy_vehicle": {
                "available": int(info.get("Heavy_CNT", "0")),
                "total": int(info.get("Heavy_Total", "0")),
            },
            "motorcycle": {
                "available": int(info.get("Moto_CNT", "0")),
                "total": int(info.get("Moto_Total", "0")),
            },
            "updated_at": info.get("UpdateTime", ""),
        })
    return carparks
```

- [ ] **Step 4: 運行測試驗證通過**

```bash
pytest test_carpark_service.py -v
```

Expected: All tests pass

- [ ] **Step 5: 提交**

```bash
git add carpark_service.py test_carpark_service.py
git commit -m "feat: 實現 DSAT API 調用和 XML 解析"
```

---

### Task 3: 後端 — 停車場座標數據和距離計算

**Files:**
- Create: `carpark_locations.py`
- Modify: `carpark_service.py`（加入距離計算函數）
- Modify: `test_carpark_service.py`（加入距離測試）

- [ ] **Step 1: 創建停車場座標數據**

Create `carpark_locations.py`:

```python
# 澳門公共停車場座標數據（經緯度）
# 來源：DSAT 停車場資料頁面
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
}


def get_carpark_location(name):
    """根據停車場名稱獲取座標，找不到返回 None"""
    # 嘗試完全匹配
    if name in CARPARK_LOCATIONS:
        return CARPARK_LOCATIONS[name]
    # 嘗試部分匹配
    for key, loc in CARPARK_LOCATIONS.items():
        if key in name or name in key:
            return loc
    return None
```

- [ ] **Step 2: 編寫測試 — 測試 Haversine 距離計算**

Add to `test_carpark_service.py`:

```python
from carpark_service import calculate_distance_km


def test_calculate_distance_same_point():
    assert calculate_distance_km(22.2, 113.5, 22.2, 113.5) == 0.0


def test_calculate_distance_known_points():
    # 澳門半島到氹仔約 3-5km
    dist = calculate_distance_km(22.20, 113.54, 22.16, 113.55)
    assert 3.0 < dist < 6.0
```

- [ ] **Step 3: 運行測試驗證失敗**

```bash
pytest test_carpark_service.py -v
```

Expected: FAIL with "ImportError: cannot import name 'calculate_distance_km'"

- [ ] **Step 4: 實現距離計算**

Add to `carpark_service.py`:

```python
import math


def calculate_distance_km(lat1, lng1, lat2, lng2):
    """使用 Haversine 公式計算兩點距離（公里）"""
    R = 6371  # 地球半徑（公里）
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
```

- [ ] **Step 5: 運行測試驗證通過**

```bash
pytest test_carpark_service.py -v
```

Expected: All tests pass

- [ ] **Step 6: 提交**

```bash
git add carpark_service.py carpark_locations.py test_carpark_service.py
git commit -m "feat: 實現停車場座標數據和 Haversine 距離計算"
```

---

### Task 4: 後端 — API 路由整合

**Files:**
- Modify: `app.py`（加入 /api/carparks 路由）

- [ ] **Step 1: 編寫測試 — 測試 API 路由**

Create `test_app.py`:

```python
import pytest
from unittest.mock import patch
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@patch("app.fetch_carpark_data")
@patch("app.parse_carpark_xml")
def test_carparks_api_returns_sorted(mock_parse, mock_fetch, client):
    mock_fetch.return_value = "<xml/>"
    mock_parse.return_value = [
        {
            "name": "遠停車場",
            "light_vehicle": {"available": 100, "total": 200},
            "heavy_vehicle": {"available": 0, "total": 0},
            "motorcycle": {"available": 10, "total": 20},
            "updated_at": "2026-04-06 10:00:00",
        },
        {
            "name": "近停車場",
            "light_vehicle": {"available": 50, "total": 100},
            "heavy_vehicle": {"available": 0, "total": 0},
            "motorcycle": {"available": 5, "total": 10},
            "updated_at": "2026-04-06 10:00:00",
        },
    ]

    resp = client.get("/api/carparks?lat=22.20&lng=113.54")
    data = resp.get_json()

    assert resp.status_code == 200
    assert "carparks" in data
    assert len(data["carparks"]) == 2
    # 近的應該排前面
    assert data["carparks"][0]["name"] == "近停車場"
    assert data["carparks"][1]["name"] == "遠停車場"


def test_carparks_api_missing_params(client):
    resp = client.get("/api/carparks")
    assert resp.status_code == 400
```

- [ ] **Step 2: 運行測試驗證失敗**

```bash
pytest test_app.py -v
```

Expected: FAIL

- [ ] **Step 3: 實現 API 路由**

Update `app.py`:

```python
from flask import Flask, jsonify, render_template, request
import os
from datetime import datetime

from carpark_service import (
    fetch_carpark_data,
    parse_carpark_xml,
    calculate_distance_km,
    MACAO_TZ,
)

app = Flask(__name__, static_folder="static", static_url_path="", template_folder="templates")

DSAT_API_URL = "https://dsat.apigateway.data.gov.mo/car_park_maintance"
DSAT_API_CODE = os.getenv("DSAT_API_CODE", "09d43a591fba407fb862412970667de4")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/carparks")
def api_carparks():
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)

    if lat is None or lng is None:
        return jsonify({"error": "需要提供 lat 和 lng 參數"}), 400

    try:
        xml_data = fetch_carpark_data()
        carparks = parse_carpark_xml(xml_data)
    except Exception as e:
        return jsonify({"error": f"數據獲取失敗: {str(e)}"}), 500

    # 計算距離並排序
    result = []
    for cp in carparks:
        loc = get_carpark_location(cp["name"])
        if loc:
            cp["distance_km"] = calculate_distance_km(lat, lng, loc["lat"], loc["lng"])
            result.append(cp)

    result.sort(key=lambda x: x["distance_km"])

    return jsonify({
        "updated_at": datetime.now(MACAO_TZ).isoformat(),
        "user_lat": lat,
        "user_lng": lng,
        "carparks": result,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
```

- [ ] **Step 4: 運行測試驗證通過**

```bash
pytest test_app.py test_carpark_service.py -v
```

Expected: All tests pass

- [ ] **Step 5: 提交**

```bash
git add app.py test_app.py
git commit -m "feat: 實現 /api/carparks 路由，整合距離計算和排序"
```

---

### Task 5: 前端 — 基礎頁面和樣式

**Files:**
- Create: `templates/index.html`

- [ ] **Step 1: 創建前端頁面**

```html
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>澳門停車場實時資訊</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f5f5f5;
            color: #333;
            padding: 16px;
        }
        .container { max-width: 600px; margin: 0 auto; }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }
        .header h1 { font-size: 20px; }
        .header-actions { display: flex; gap: 8px; align-items: center; }
        .status { font-size: 12px; color: #666; }
        .refresh-btn {
            background: #1976d2;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
        }
        .refresh-btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .location-status {
            background: #e3f2fd;
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 12px;
            font-size: 13px;
            color: #1565c0;
        }
        .location-status.error {
            background: #ffebee;
            color: #c62828;
        }
        .carpark-card {
            background: white;
            padding: 14px;
            border-radius: 8px;
            margin-bottom: 10px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border-left: 4px solid #ccc;
        }
        .carpark-card.status-good { border-left-color: #4caf50; }
        .carpark-card.status-medium { border-left-color: #ff9800; }
        .carpark-card.status-bad { border-left-color: #f44336; }
        .carpark-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .carpark-name { font-weight: bold; font-size: 16px; }
        .carpark-distance { color: #666; font-size: 14px; }
        .carpark-slots {
            display: flex;
            gap: 16px;
            margin-top: 8px;
            font-size: 15px;
        }
        .slot-good { color: #4caf50; }
        .slot-medium { color: #ff9800; }
        .slot-bad { color: #f44336; }
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        .error-msg {
            background: #ffebee;
            color: #c62828;
            padding: 12px;
            border-radius: 6px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🅿️ 澳門停車場</h1>
            <div class="header-actions">
                <span class="status" id="status">等待定位...</span>
                <button class="refresh-btn" id="refreshBtn" disabled>🔄</button>
            </div>
        </div>
        <div class="location-status" id="locationStatus">正在獲取您的位置...</div>
        <div id="carparkList">
            <div class="loading">等待定位完成...</div>
        </div>
    </div>
    <script>
        let userLat = null;
        let userLng = null;
        let refreshInterval = null;

        function getStatusClass(ratio) {
            if (ratio > 0.5) return "good";
            if (ratio > 0.2) return "medium";
            return "bad";
        }

        function renderCarparks(data) {
            const list = document.getElementById("carparkList");
            if (!data.carparks || data.carparks.length === 0) {
                list.innerHTML = '<div class="error-msg">暫無停車場數據</div>';
                return;
            }
            list.innerHTML = data.carparks.map(cp => {
                const lv = cp.light_vehicle;
                const ratio = lv.total > 0 ? lv.available / lv.total : 0;
                const status = getStatusClass(ratio);
                const hv = cp.heavy_vehicle;
                const mc = cp.motorcycle;
                return `
                    <div class="carpark-card status-${status}">
                        <div class="carpark-header">
                            <span class="carpark-name">${cp.name}</span>
                            <span class="carpark-distance">${cp.distance_km}km</span>
                        </div>
                        <div class="carpark-slots">
                            <span class="slot-${status}">🚗 ${lv.available}/${lv.total}</span>
                            <span class="slot-${getStatusClass(hv.total > 0 ? hv.available / hv.total : 0)}">🚛 ${hv.available}/${hv.total}</span>
                            <span class="slot-${getStatusClass(mc.total > 0 ? mc.available / mc.total : 0)}">🛵 ${mc.available}/${mc.total}</span>
                        </div>
                    </div>
                `;
            }).join("");
        }

        async function fetchCarparks() {
            if (userLat === null || userLng === null) return;
            const btn = document.getElementById("refreshBtn");
            const status = document.getElementById("status");
            btn.disabled = true;
            status.textContent = "更新中...";
            try {
                const resp = await fetch(`/api/carparks?lat=${userLat}&lng=${userLng}`);
                if (!resp.ok) throw new Error("API 請求失敗");
                const data = await resp.json();
                renderCarparks(data);
                const now = new Date().toLocaleTimeString("zh-Hant");
                status.textContent = `已更新 ${now}`;
            } catch (err) {
                document.getElementById("carparkList").innerHTML =
                    '<div class="error-msg">數據獲取失敗，請稍後重試</div>';
                status.textContent = "更新失敗";
            } finally {
                btn.disabled = false;
            }
        }

        function startAutoRefresh() {
            if (refreshInterval) clearInterval(refreshInterval);
            refreshInterval = setInterval(fetchCarparks, 30000);
        }

        // 獲取用戶位置
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (pos) => {
                    userLat = pos.coords.latitude;
                    userLng = pos.coords.longitude;
                    document.getElementById("locationStatus").textContent =
                        `📍 位置已獲取`;
                    document.getElementById("refreshBtn").disabled = false;
                    fetchCarparks();
                    startAutoRefresh();
                },
                (err) => {
                    const el = document.getElementById("locationStatus");
                    el.textContent = "❌ 需要位置權限才能顯示附近停車場";
                    el.classList.add("error");
                    document.getElementById("carparkList").innerHTML =
                        '<div class="error-msg">請在瀏覽器設置中允許位置訪問</div>';
                }
            );
        } else {
            document.getElementById("locationStatus").textContent =
                "❌ 您的瀏覽器不支持定位功能";
            document.getElementById("locationStatus").classList.add("error");
        }

        // 手動刷新
        document.getElementById("refreshBtn").addEventListener("click", fetchCarparks);
    </script>
</body>
</html>
```

- [ ] **Step 2: 手動驗證前端**

```bash
python app.py
```

訪問 http://localhost:5000，確認：
- 頁面正常載入
- 定位請求彈出
- 允許後顯示停車場列表
- 點擊刷新按鈕可手動更新

- [ ] **Step 3: 提交**

```bash
git add templates/index.html
git commit -m "feat: 實現前端頁面，包含定位、自動刷新、車位狀態顏色"
```

---

### Task 6: 錯誤處理和邊界情況

**Files:**
- Modify: `app.py`（完善錯誤處理）
- Modify: `carpark_service.py`（加入超時和重試）

- [ ] **Step 1: 加入 API 超時和重試邏輯**

Add to `carpark_service.py`:

```python
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
    raise Exception(last_error)
```

- [ ] **Step 2: 加入 XML 解析錯誤處理**

Update `parse_carpark_xml` in `carpark_service.py`:

```python
def parse_carpark_xml(xml_data):
    """解析 XML 返回停車場列表"""
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
                    "available": int(info.get("Car_CNT", "0")),
                    "total": int(info.get("Car_Total", "0")),
                },
                "heavy_vehicle": {
                    "available": int(info.get("Heavy_CNT", "0")),
                    "total": int(info.get("Heavy_Total", "0")),
                },
                "motorcycle": {
                    "available": int(info.get("Moto_CNT", "0")),
                    "total": int(info.get("Moto_Total", "0")),
                },
                "updated_at": info.get("UpdateTime", ""),
            })
        except (ValueError, TypeError):
            # 跳過數據格式錯誤的記錄
            continue
    return carparks
```

- [ ] **Step 3: 更新 app.py 錯誤處理**

Update the error handler in `app.py`:

```python
@app.route("/api/carparks")
def api_carparks():
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)

    if lat is None or lng is None:
        return jsonify({"error": "需要提供 lat 和 lng 參數"}), 400

    try:
        xml_data = fetch_carpark_data()
        carparks = parse_carpark_xml(xml_data)
    except ValueError as e:
        return jsonify({"error": f"數據格式錯誤: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"數據獲取失敗: {str(e)}"}), 500

    for cp in carparks:
        cp["distance_km"] = calculate_distance_km(lat, lng, lat, lng)

    carparks.sort(key=lambda x: x["distance_km"])

    return jsonify({
        "updated_at": datetime.now(MACO_TZ).isoformat(),
        "user_lat": lat,
        "user_lng": lng,
        "carparks": carparks,
    })
```

- [ ] **Step 4: 加入錯誤處理測試**

Add to `test_carpark_service.py`:

```python
import pytest


def test_parse_invalid_xml():
    with pytest.raises(ValueError, match="XML 解析失敗"):
        parse_carpark_xml("<invalid><xml>")


def test_parse_malformed_data():
    xml_data = """<?xml version="1.0" encoding="UTF-8"?>
    <CarPark>
        <Car_park_info name="測試停車場" Car_CNT="abc" Car_Total="100"
                       Heavy_CNT="0" Heavy_Total="0"
                       Moto_CNT="10" Moto_Total="20"
                       UpdateTime="2026-04-06 10:00:00"/>
    </CarPark>"""
    result = parse_carpark_xml(xml_data)
    # 應該跳過格式錯誤的記錄
    assert result == []
```

- [ ] **Step 5: 運行所有測試**

```bash
pytest test_carpark_service.py test_app.py -v
```

Expected: All tests pass

- [ ] **Step 6: 提交**

```bash
git add carpark_service.py app.py test_carpark_service.py
git commit -m "feat: 完善錯誤處理和邊界情況"
```

---

### Task 7: 修復已知 Bug 和最終測試

**Files:**
- Modify: `app.py`（修復 MACO_TZ 拼寫錯誤）

- [ ] **Step 1: 修復拼寫錯誤**

在 Task 4 的代碼中，`MACO_TZ` 應為 `MACAO_TZ`。修正 `app.py` 中的引用：

```python
from carpark_service import (
    fetch_carpark_data,
    parse_carpark_xml,
    calculate_distance_km,
    MACAO_TZ,
)

# ... 在 api_carparks 函數中 ...
    return jsonify({
        "updated_at": datetime.now(MACAO_TZ).isoformat(),
        "user_lat": lat,
        "user_lng": lng,
        "carparks": carparks,
    })
```

- [ ] **Step 2: 運行完整測試套件**

```bash
pytest test_carpark_service.py test_app.py -v
```

Expected: All tests pass

- [ ] **Step 3: 手動端到端測試**

```bash
python app.py
```

訪問 http://localhost:5000，驗證：
- 定位功能正常
- 停車場列表按距離排序
- 車位顏色正確顯示
- 30 秒自動刷新
- 手動刷新按鈕正常
- 錯誤情況有友好提示

- [ ] **Step 4: 最終提交**

```bash
git add -A
git commit -m "fix: 修復拼寫錯誤，完成最終測試"
```
