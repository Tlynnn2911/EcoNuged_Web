"""
B2 – Kiểm tra GPS & Point-in-Polygon (Phân hệ 1)
===================================================
Thuật toán: Ray-casting thuần Python (KHÔNG cần shapely/CSV trung gian).
Nạp trực tiếp từ GeoJSON du_lieu_cang.json.

Sửa từ v2:
  - Loại bỏ phụ thuộc shapely (không cài được khi offline)
  - Nạp GeoJSON trực tiếp thay vì đọc CSV từ B1
  - Hàm trả về thêm loai_khu_vuc: 'CANG'|'DEPOT'|'DUONG_356'
  - Buffer GPS ~5m xử lý bằng bounding-box mở rộng
"""

import json
import os

_DIR_AI   = os.path.dirname(os.path.abspath(__file__))
_DIR_GOC  = os.path.dirname(_DIR_AI)
_PATH_GEO = os.path.join(_DIR_GOC, '03_JSON', 'du_lieu_cang.json')

_ZONES = []


def _phan_loai(name: str) -> str:
    n = name.lower()
    if 'depot' in n or 'hahugnhai' in n or 'fortune' in n or 'gas' in n:
        return 'DEPOT'
    if '356' in n or 'duong' in n:
        return 'DUONG_356'
    return 'CANG'


def _linestring_bbox(coords, buf=0.0003):
    """Xấp xỉ LineString thành bounding-box polygon."""
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    mn, mx, my, mxy = min(lons)-buf, max(lons)+buf, min(lats)-buf, max(lats)+buf
    return [[mn, my],[mx, my],[mx, mxy],[mn, mxy],[mn, my]]


def _nap():
    global _ZONES
    _ZONES = []
    if not os.path.exists(_PATH_GEO):
        print(f"[B2] ❌ Không tìm thấy GeoJSON: {_PATH_GEO}")
        return
    with open(_PATH_GEO, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for feat in data.get('features', []):
        prop  = feat.get('properties', {})
        geom  = feat.get('geometry',   {})
        gtype = geom.get('type', '')
        coords= geom.get('coordinates', [])
        rings = []
        if gtype == 'Polygon':
            rings = [coords[0]]
        elif gtype == 'MultiPolygon':
            rings = [p[0] for p in coords]
        elif gtype == 'LineString':
            rings = [_linestring_bbox(coords)]
        name = prop.get('name', '')
        _ZONES.append({
            'name'   : name,
            'port_id': prop.get('port_id', ''),
            'loai'   : prop.get('loai', _phan_loai(name)),
            'rings'  : rings,
        })
    print(f"[B2] ✅ Đã nạp {len(_ZONES)} vùng Geofence")


def _pip(lon, lat, ring) -> bool:
    """Ray-casting Point-in-Polygon."""
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > lat) != (yj > lat)) and \
           (lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-12) + xi):
            inside = not inside
        j = i
    return inside


def kiem_tra_xe_trong_cang(vi_do: float, kinh_do: float, buf: float = 0.00005):
    """
    Kiểm tra tọa độ có nằm trong Geofence không.
    buf ≈ 5m để hấp thu sai số GPS.

    Returns: (bool, ten_cang|None, ma_cang|None, loai|None)
    """
    if not _ZONES:
        _nap()
    for z in _ZONES:
        for ring in z['rings']:
            lons = [c[0] for c in ring]
            lats = [c[1] for c in ring]
            # Bounding box nhanh + buffer
            if not (min(lons)-buf <= kinh_do <= max(lons)+buf and
                    min(lats)-buf <= vi_do   <= max(lats)+buf):
                continue
            if _pip(kinh_do, vi_do, ring):
                return True, z['name'], z['port_id'], z['loai']
    return False, None, None, None


def lay_danh_sach_vung() -> list:
    """Danh sách zone cho APP hiển thị bản đồ."""
    if not _ZONES:
        _nap()
    return [{'port_id': z['port_id'], 'ten': z['name'], 'loai': z['loai']}
            for z in _ZONES]


_nap()

if __name__ == "__main__":
    tests = [
        (20.802436, 106.770923, "Tan Vu - bên trong (dự kiến TRUE)"),
        (20.900000, 106.900000, "Ngoài vùng (dự kiến FALSE)"),
    ]
    print("=" * 55)
    print("  B2: Kiểm tra Point-in-Polygon (Ray Casting)")
    print("=" * 55)
    for lat, lon, note in tests:
        ok, ten, ma, loai = kiem_tra_xe_trong_cang(lat, lon)
        status = f"✅ TRONG [{ten}] [{loai}]" if ok else "❌ Ngoài vùng"
        print(f"  ({lat},{lon}) → {status}  | {note}")
    print("\n  Danh sách vùng:")
    for z in lay_danh_sach_vung():
        print(f"    [{z['loai']:10s}] {z['ten']}")
