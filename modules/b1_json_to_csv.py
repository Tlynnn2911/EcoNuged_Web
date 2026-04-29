import json
import csv
import os

def convert_geojson_to_csv(json_path, csv_path):
    if not os.path.exists(json_path):
        return False
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    zones = data.get('zones', [])
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ten', 'loai', 'polygon_str'])
        for z in zones:
            writer.writerow([z['ten'], z['loai'], str(z['polygon'])])
    return True