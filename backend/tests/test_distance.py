import pytest
from app.services.matching_service import haversine_distance

def test_haversine_same_point():
    lat, lng = 18.5314, 73.8446
    dist = haversine_distance(lat, lng, lat, lng)
    assert dist == 0.0

def test_haversine_known_distance():
    # Pune Shivajinagar (18.5314, 73.8446) to Pune Station (18.5284, 73.8739) ~ 3.1 km
    pune_shivajinagar = (18.5314, 73.8446)
    pune_station = (18.5284, 73.8739)
    dist = haversine_distance(
        pune_shivajinagar[0], pune_shivajinagar[1],
        pune_station[0], pune_station[1]
    )
    assert 2.8 <= dist <= 3.4

def test_haversine_long_distance():
    # Pune (18.5204, 73.8567) to Mumbai (19.0760, 72.8777) ~ 120 km
    pune = (18.5204, 73.8567)
    mumbai = (19.0760, 72.8777)
    dist = haversine_distance(pune[0], pune[1], mumbai[0], mumbai[1])
    assert 115.0 <= dist <= 130.0
