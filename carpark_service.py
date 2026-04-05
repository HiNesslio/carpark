import os
import xml.etree.ElementTree as ET
import requests
import math

DSAT_API_URL = "https://dsat.apigateway.data.gov.mo/car_park_maintance"
DSAT_API_CODE = os.getenv("DSAT_API_CODE") or "09d43a591fba407fb862412970667de4"


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
