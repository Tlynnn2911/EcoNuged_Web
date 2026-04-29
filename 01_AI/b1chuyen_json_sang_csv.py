"""
B1 – Chuyển đổi GeoJSON → CSV (Phân hệ 1)
==========================================
Sửa từ v2: Loại bỏ phụ thuộc shapely (không offline-installable).
Dùng thuật toán thuần Python để chuyển đổi geometry → WKT.
B2 bây giờ nạp GeoJSON trực tiếp nên B1 chỉ cần cho tương thích ngược.
"""

import json
import csv
import os
import math


def _ring_to_wkt(coords) -> str:
    """Chuyển list of [lon,lat] thành chuỗi WKT POLYGON."""
    pts = ', '.join(f"{c[0]} {c[1]}" for c in coords)
    return f"POLYGON (({pts}))"


def _linestring_buffer_wkt(coords, buf=0.0003) -> str:
    """Tạo bounding box polygon từ LineString."""
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    mn, mx = min(lons) - buf, max(lons) + buf
    my, mxy = min(lats) - buf, max(lats) + buf
    return (f"POLYGON (({mn} {my}, {mx} {my}, "
            f"{mx} {mxy}, {mn} {mxy}, {mn} {my}))")


class BoChuyenDoiDuLieu:
    def __init__(self):
        self.thu_muc_ai  = os.path.dirname(os.path.abspath(__file__))
        self.thu_muc_goc = os.path.dirname(self.thu_muc_ai)
        self.path_json   = os.path.join(self.thu_muc_goc, '03_JSON', 'du_lieu_cang.json')
        self.path_csv    = os.path.join(self.thu_muc_goc, '04_DATA', 'danh_sach_cang_bien.csv')

    def thuc_thi(self) -> bool:
        print(f"[B1] Đọc GeoJSON: {self.path_json}")
        if not os.path.exists(self.path_json):
            print(f"[B1] ❌ Không tìm thấy: {self.path_json}")
            return False
        try:
            with open(self.path_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            features = data.get('features', [])
            with open(self.path_csv, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Tên Cảng', 'Mã Cảng', 'Mô Tả',
                                 'Trạng Thái', 'Dữ Liệu Hình Học (WKT)'])
                for feat in features:
                    prop  = feat.get('properties', {})
                    geom  = feat.get('geometry', {})
                    gtype = geom.get('type', '')
                    coords= geom.get('coordinates', [])
                    if gtype == 'Polygon':
                        wkt = _ring_to_wkt(coords[0])
                    elif gtype == 'MultiPolygon':
                        wkt = _ring_to_wkt(coords[0][0])
                    elif gtype == 'LineString':
                        wkt = _linestring_buffer_wkt(coords)
                    else:
                        wkt = ""
                    writer.writerow([
                        prop.get('name', ''), prop.get('port_id', ''),
                        prop.get('description', ''), prop.get('status', 'Active'), wkt
                    ])
                    print(f"[B1]   ✓ {prop.get('name')}")
            print(f"[B1] ✅ CSV: {self.path_csv}")
            return True
        except Exception as e:
            print(f"[B1] ❌ Lỗi: {e}")
            return False


if __name__ == "__main__":
    BoChuyenDoiDuLieu().thuc_thi()
