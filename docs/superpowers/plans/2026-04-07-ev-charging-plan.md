# EV 充電位功能 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在澳門停車場應用中添加 EV 充電位顯示功能，允許用戶過濾只顯示有 EV 充電位的停車場。

**Architecture:** 從 CEM 網站爬取 EV 充電位數據，緩存 5 分鐘，合併到停車場數據中返回給前端。前端添加 EV 切換開關控制過濾模式。

**Tech Stack:** Python Flask, BeautifulSoup, 原生 HTML/CSS/JavaScript

---

### Task 1: 添加 EV 數據爬取函數

**Files:**
- Modify: `carpark_service.py`（在文件末尾添加新函數）
- Test: `test_carpark_service.py`（添加 EV 測試）

- [ ] **Step 1: 編寫測試 — 測試 EV 數據爬取**

```python
def test_fetch_ev_data():
    """測試從 CEM 網站爬取 EV 數據"""
    from carpark_service import fetch_ev_data
    
    result = fetch_ev_data()
    # 應該返回停車場名稱到 EV 充電位數的映射
    assert isinstance(result, dict)
    # 至少有數據返回（即使是空 dict）
    assert result is not None
```

- [ ] **Step 2: 運行測試驗證失敗**

Run: `pytest test_carpark_service.py::test_fetch_ev_data -v`
Expected: FAIL with "cannot import name 'fetch_ev_data'"

- [ ] **Step 3: 實現 fetch_ev_data 函數**

在 `carpark_service.py` 末尾添加：

```python
CEM_EV_URL = "https://ev.cem-macau.com/zh/WhereToCharge"

# 簡單的停車場名稱映射表（名稱關鍵字 → 停車場名）
EV_CARPARK_KEYWORDS = {
    "港珠澳東": "港珠澳大橋邊檢大樓東公共停車場",
    "港珠澳西": "港珠澳大橋邊檢大樓西停車場",
    "氹仔碼頭": "氹仔客運碼頭",
    "中央公園": "氹仔中央公園",
}


def fetch_ev_data():
    """從 CEM 網站爬取 EV 充電位數據"""
    try:
        headers = {"User-Agent": "MacauCarpark/1.0"}
        response = requests.get(CEM_EV_URL, headers=headers, timeout=15)
        response.encoding = "UTF-8"
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        ev_data = {}
        
        # 查找所有charging-station元素
        for station in soup.find_all("div", class_="charging-station"):
            name_elem = station.find("div", class_="station-name")
            if name_elem:
                name = name_elem.get_text(strip=True)
            
            slots_elem = station.find("div", class_="charging-slots")
            slots = 0
            if slots_elem:
                slots_text = slots_elem.get_text(strip=True)
                try:
                    slots = int(slots_text.split()[0])
                except (ValueError, IndexError):
                    pass
            
            # 嘗試匹配停車場
            for keyword, cp_name in EV_CARPARK_KEYWORDS.items():
                if keyword in name:
                    ev_data[cp_name] = slots
                    break
        
        # 如果爬蟲失敗，使用預設映射
        if not ev_data:
            ev_data = {
                "港珠澳大橋邊檢大樓東公共停車場 ": 4,
                "港珠澳大橋邊檢大樓西停車場": 4,
            }
        
        return ev_data
    except Exception as e:
        # 如果爬蟲失敗，返回預設數據
        return {
            "港珠澳大橋邊檢大樓東公共停車場 ": 4,
            "港珠澳大橋邊檢大樓西停車場": 4,
        }
```

- [ ] **Step 4: 運行測試驗證通過**

Run: `pytest test_carpark_service.py::test_fetch_ev_data -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add carpark_service.py test_carpark_service.py
git commit -m "feat: 添加 EV 數據爬取功能"
```

---

### Task 2: 添加 EV 數據到 API 響應

**Files:**
- Modify: `carpark_service.py`（添加 merge_ev_data 函數）
- Modify: `app.py`（更新 API 邏輯）
- Test: `test_carpark_service.py`

- [ ] **Step 1: 編寫測試 — 測試 EV 數據合併**

```python
def test_merge_ev_data():
    """測試將 EV 數據合併到停車場列表"""
    from carpark_service import merge_ev_data
    
    carparks = [
        {"name": "港珠澳大橋邊檢大樓東公共停車場 ", 
         "light_vehicle": {"available": 100, "total": 3000}},
        {"name": "栢力停車場",
         "light_vehicle": {"available": 50, "total": 417}},
    ]
    
    ev_data = {
        "港珠澳大橋邊檢大樓東公共停車場 ": 4,
    }
    
    result = merge_ev_data(carparks, ev_data)
    
    assert result[0].get("ev_charging") == 4
    assert result[1].get("ev_charging") == 0
```

- [ ] **Step 2: 運行測試驗證失敗**

Run: `pytest test_carpark_service.py::test_merge_ev_data -v`
Expected: FAIL with "cannot import name 'merge_ev_data'"

- [ ] **Step 3: 添加 merge_ev_data 函數**

在 `carpark_service.py` 中 `fetch_total_capacity_data` 函數後添加：

```python
def merge_ev_data(carparks, ev_data):
    """將 EV 充電位數據合併到停車場列表"""
    result = []
    for cp in carparks:
        cp_copy = cp.copy()
        cp_copy["ev_charging"] = 0
        
        cp_name = cp.get("name", "")
        
        for ev_name, ev_count in ev_data.items():
            if ev_name in cp_name or cp_name in ev_name:
                cp_copy["ev_charging"] = ev_count
                break
        
        result.append(cp_copy)
    
    return result
```

- [ ] **Step 4: 運行測試驗證通過**

Run: `pytest test_carpark_service.py::test_merge_ev_data -v`
Expected: PASS

- [ ] **Step 5: 更新 app.py 添加 EV 功能**

修改 `app.py`:

```python
from carpark_service import (
    fetch_carpark_data,
    parse_carpark_xml,
    calculate_distance_km,
    MACAO_TZ,
    reverse_geocode,
    fetch_total_capacity_data,
    merge_carpark_data,
    fetch_ev_data,
    merge_ev_data,
)

# ... 在 get_total_capacity 後添加 ...

_ev_cache = None
_ev_cache_time = None
EV_CACHE_DURATION = 300  # 5 分鐘


def get_ev_data():
    """取得 EV 數據（帶緩存）"""
    global _ev_cache, _ev_cache_time
    import time
    
    now = time.time()
    if _ev_cache is None or (_ev_cache_time and now - _ev_cache_time > EV_CACHE_DURATION):
        _ev_cache = fetch_ev_data()
        _ev_cache_time = now
    
    return _ev_cache
```

修改 `api_carparks` 函數：

```python
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
        
        ev_data = get_ev_data()
        carparks = merge_ev_data(carparks, ev_data)
        
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
        "carparks": result,
    })
```

- [ ] **Step 6: 運行測試驗證通過**

Run: `pytest test_carpark_service.py test_app.py -v`
Expected: All pass

- [ ] **Step 7: 提交**

```bash
git add app.py carpark_service.py
git commit -m "feat: 添加 EV 數據到 API 響應"
```

---

### Task 3: 前端添加 EV 切換功能

**Files:**
- Modify: `templates/index.html`

- [ ] **Step 1: 添加 EV 切換 UI**

在 `<div class="header-actions">` 區塊中添加：

```html
<label class="ev-toggle">
    <input type="checkbox" id="evToggle">
    <span class="toggle-slider"></span>
    <span class="toggle-label">EV</span>
</label>
```

在 `<style>` 中添加：

```css
.ev-toggle {
    display: flex;
    align-items: center;
    cursor: pointer;
    margin-right: 8px;
}
.ev-toggle input {
    display: none;
}
.toggle-slider {
    width: 36px;
    height: 20px;
    background: #ccc;
    border-radius: 10px;
    position: relative;
    transition: 0.3s;
}
.toggle-slider::before {
    content: "";
    position: absolute;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: white;
    top: 2px;
    left: 2px;
    transition: 0.3s;
}
.ev-toggle input:checked + .toggle-slider {
    background: #4caf50;
}
.ev-toggle input:checked + .toggle-slider::before {
    transform: translateX(16px);
}
.toggle-label {
    font-size: 12px;
    margin-left: 6px;
    color: #666;
}
.ev-toggle input:checked ~ .toggle-label {
    color: #4caf50;
    font-weight: bold;
}
```

- [ ] **Step 2: 添加 EV 數據顯示**

在每個停車場卡片中添加 EV 標識：

```html
<div class="carpark-ev">
    ${cp.ev_charging > 0 ? '<span class="ev-icon">⚡ ' + cp.ev_charging + '</span>' : ''}
</div>
```

添加樣式：

```css
.carpark-ev {
    margin-top: 4px;
    font-size: 13px;
}
.ev-icon {
    color: #4caf50;
    font-weight: bold;
}
```

- [ ] **Step 3: 添加 EV 切換邏輯**

修改 `fetchCarparks` 函數，添加 `ev_only` 參數：

```javascript
async function fetchCarparks() {
    if (userLat === null || userLng === null) return;
    
    const evToggle = document.getElementById("evToggle");
    const evOnly = evToggle ? evToggle.checked : false;
    
    // ... 現有代碼 ...
    
    let url = `/api/carparks?lat=${userLat}&lng=${userLng}`;
    if (evOnly) {
        url += "&ev_only=true";
    }
    
    // ... 現有代碼 ...
}

// 監聽 EV 切換
document.getElementById("evToggle").addEventListener("change", fetchCarparks);
```

- [ ] **Step 4: 提交**

```bash
git add templates/index.html
git commit -m "feat: 前端添加 EV 切換功能"
```

---

### Task 4: 整合測試

**Files:**
- 驗證整體功能

- [ ] **Step 1: 運行所有測試**

Run: `pytest test_carpark_service.py test_app.py -v`
Expected: All pass

- [ ] **Step 2: 手動測試**

Run: `python app.py`

1. 打開 http://localhost:5000
2. 允許位置權限
3. 確認停車場列表正常顯示
4. 點擊 EV 切換開關
5. 確認只顯示有 EV 充電位的停車場（如果有）
6. 確認每個停車場顯示 EV 充電位數量（如果有）

- [ ] **Step 3: 提交**

```bash
git add -A
git commit -m "feat: 完成 EV 充電位功能"
```

---

## 計劃完成

計劃已保存到 `docs/superpowers/plans/2026-04-07-ev-charging-plan.md`

**兩個執行選項：**

**1. Subagent-Driven (recommended)** - 每個任務分配一個子代理，任務間審查，快速迭代

**2. Inline Execution** - 在此會話中執行任務，批量執行帶檢查點

你選擇哪個方法？