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
