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
