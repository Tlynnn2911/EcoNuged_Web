import json
import os

def point_in_polygon(lat, lng, polygon):
    """Ray casting algorithm, thuần Python"""
    inside = False
    n = len(polygon)
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i+1) % n]
        # Kiểm tra tia
        if ((y1 > lng) != (y2 > lng)) and (lat < (x2 - x1) * (lng - y1) / (y2 - y1) + x1):
            inside = not inside
    return inside

def lay_danh_sach_vung():
    json_path = os.path.join('data', 'geofence_zones.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['zones']

def kiem_tra_xe_trong_cang(lat, lon):
    zones = lay_danh_sach_vung()
    for zone in zones:
        if point_in_polygon(lat, lon, zone['polygon']):
            return zone['ten'], zone['loai']
    return None, None