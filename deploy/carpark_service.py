import os
import xml.etree.ElementTree as ET
import requests
import math
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

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


def fetch_total_capacity_data():
    """從停車場資料頁面獲取總車位數據"""
    extra_capacity = {
        "塔石廣場地下上落客區(重型客車)": {"light_vehicle": 0, "motorcycle": 0, "heavy_vehicle": 20},
        "交通教育局大樓": {"light_vehicle": 145, "motorcycle": 118, "heavy_vehicle": 0},
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
    
    try:
        response = requests.get(DSAT_INFO_URL, timeout=15)
        response.encoding = "UTF-8"
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", class_="my_table")
        
        if not table:
            return extra_capacity
        
        result = extra_capacity.copy()
        
        for tr in table.find_all("tr"):
            cells = [cell.get_text(strip=True) for cell in tr.find_all(["td", "th"])]
            
            if not cells:
                continue
            
            if "名稱" in cells and "輕型車輛" in cells:
                continue
            
            if len(cells) < 5:
                continue
            
            name = None
            light = "0"
            motorcycle = "0"
            location = ""
            
            if len(cells) >= 16 and cells[0].endswith("堂區"):
                name = cells[2]
                location = cells[3]
                light = cells[4]
                motorcycle = cells[5]
            elif len(cells) >= 15 and cells[0].isdigit():
                name = cells[1]
                location = cells[2]
                light = cells[3]
                motorcycle = cells[4]
            
            if not name or name.startswith("重型") or name == "公共車場總計":
                continue
            
            name_clean = name.rstrip("*")
            
            light_val = int(light) if light.lstrip("-").isdigit() else 0
            moto_val = int(motorcycle) if motorcycle.lstrip("-").isdigit() else 0
            
            result[name_clean] = {
                "light_vehicle": light_val,
                "motorcycle": moto_val,
                "heavy_vehicle": 0,
                "location": location,
            }
        
        for name, cap in extra_capacity.items():
            result[name] = cap
        
        return result
    except Exception as e:
        return extra_capacity


# EV 停車場數據（靜態數據）
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