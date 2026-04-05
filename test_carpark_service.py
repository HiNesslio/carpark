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
                       Heavy_CNT="0" Heavy_Total="0"
                       Moto_CNT="10" Moto_Total="20"
                       UpdateTime="2026-04-06 10:00:00"/>
    </CarPark>"""
    result = parse_carpark_xml(xml_data)
    assert result == []
