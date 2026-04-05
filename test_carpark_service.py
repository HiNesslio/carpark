from unittest.mock import patch, MagicMock
from carpark_service import parse_carpark_xml, fetch_carpark_data, calculate_distance_km
from carpark_locations import get_carpark_location


def test_calculate_distance_same_point():
    assert calculate_distance_km(22.2, 113.5, 22.2, 113.5) == 0.0


def test_calculate_distance_known_points():
    # 澳門半島到氹仔約 3-5km
    dist = calculate_distance_km(22.20, 113.54, 22.16, 113.55)
    assert 3.0 < dist < 6.0


def test_parse_valid_xml():
    xml_data = """<?xml version="1.0" encoding="UTF-8"?>
    <CarPark>
        <Car_park_info name="栢力停車場" Car_CNT="280" Car_Total="417"
                       OT_A_CNT="0" OT_A_Total="0"
                       MB_CNT="30" MB_Total="32"
                       Time="2026-04-06 10:30:00"/>
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


def test_fetch_carpark_data():
    mock_response = MagicMock()
    mock_response.text = '<?xml version="1.0" encoding="UTF-8"?><CarPark></CarPark>'
    
    with patch("carpark_service.requests.get", return_value=mock_response) as mock_get:
        result = fetch_carpark_data()
        mock_get.assert_called_once()
        assert result == '<?xml version="1.0" encoding="UTF-8"?><CarPark></CarPark>'


def test_get_carpark_location_exact_match():
    loc = get_carpark_location("栢力停車場")
    assert loc == {"lat": 22.2025, "lng": 113.5430}


def test_get_carpark_location_partial_match():
    loc = get_carpark_location("栢佳")
    assert loc is not None


def test_get_carpark_location_not_found():
    loc = get_carpark_location("不存在的停車場")
    assert loc is None


import pytest


def test_parse_invalid_xml():
    with pytest.raises(ValueError, match="XML 解析失敗"):
        parse_carpark_xml("<invalid><xml>")


def test_parse_malformed_data():
    xml_data = """<?xml version="1.0" encoding="UTF-8"?>
    <CarPark>
        <Car_park_info name="測試停車場" Car_CNT="abc" Car_Total="100"
                       OT_A_CNT="0" OT_A_Total="0"
                       MB_CNT="10" MB_Total="20"
                       Time="2026-04-06 10:00:00"/>
    </CarPark>"""
    result = parse_carpark_xml(xml_data)
    # 應該跳過格式錯誤的記錄
    assert result == []


def test_parse_zero_total():
    """當 total 為 0 時應該視為充足（不知道總數但有車位）"""
    xml_data = """<?xml version="1.0" encoding="UTF-8"?>
    <CarPark>
        <Car_park_info name="栢力停車場" Car_CNT="280" Car_Total="0"
                       OT_A_CNT="0" OT_A_Total="0"
                       MB_CNT="30" MB_Total="0"
                       Time="2026-04-06 10:30:00"/>
    </CarPark>"""
    result = parse_carpark_xml(xml_data)
    assert len(result) == 1
    # 當 total 為 0 時，available > 0 應該視為充足
    assert result[0]["light_vehicle"]["total"] == 0
    assert result[0]["light_vehicle"]["available"] == 280


def test_status_calculation_with_zero_total():
    """當 total 為 0 但 available > 0 時，應該視為充足"""
    # 這個測試模擬前端邏輯：當 total 為 0 時，如果有可用車位，視為充足
    # 邏輯：total = 0 且 available > 0 = 充足 (good)
    #       total > 0 且 available/total > 0.5 = 充足 (good)
    #       total > 0 且 available/total > 0.2 = 一般 (medium)
    #       其他 = 緊張 (bad)
    
    def get_status(available, total):
        if total == 0:
            return "good" if available > 0 else "bad"
        ratio = available / total
        if ratio > 0.5:
            return "good"
        if ratio > 0.2:
            return "medium"
        return "bad"
    
    # 測試案例
    assert get_status(280, 0) == "good"  # 不知道總數但有車位
    assert get_status(0, 0) == "bad"    # 沒車位
    assert get_status(280, 417) == "good"   # 67% > 50%
    assert get_status(100, 417) == "medium" # 24% > 20%
    assert get_status(50, 417) == "bad"      # 12% < 20%


def test_parse_motorcycle_field_names():
    """測試電單車字段名稱 - 可能使用不同的字段名"""
    # DSAT API 使用不同的字段名稱:
    # Car_CNT = 輕型汽車, MB_CNT = 電單車, OT_A_CNT = 重型汽車
    xml_data = """<?xml version="1.0" encoding="UTF-8"?>
    <CarPark>
        <Car_park_info name="下環街市" Car_CNT="28" MB_CNT="57" 
                       OT_A_CNT="10" ELC_CNT="2" DC_CNT="2"
                       Time="4/6/2026 4:32:13 AM"/>
    </CarPark>"""
    result = parse_carpark_xml(xml_data)
    assert len(result) == 1
    # 輕型汽車: Car_CNT = 28
    assert result[0]["light_vehicle"]["available"] == 28
    # 電單車: MB_CNT = 57
    assert result[0]["motorcycle"]["available"] == 57
    # 重型汽車: OT_A_CNT = 10
    assert result[0]["heavy_vehicle"]["available"] == 10


def test_reverse_geocoding():
    """測試逆地理編碼功能 - 將座標轉換為街名"""
    from carpark_service import reverse_geocode
    
    # Test with Macau coordinates
    result = reverse_geocode(22.1987, 113.5439)
    # Should return a display name with street info
    assert result is not None
    assert "澳門" in result or "Macau" in result or "路" in result or "街" in result
