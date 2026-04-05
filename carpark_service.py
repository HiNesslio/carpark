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
