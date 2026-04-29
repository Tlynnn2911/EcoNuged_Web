"""
B3 – Bộ máy trạng thái & Quản lý hành trình (Phân hệ 1)
=========================================================
Sửa từ v2:
  - Tương thích với b2 mới trả về 4 giá trị (thêm loai_khu_vuc)
  - Ghi nhớ ten_cang để dùng khi KET_THUC_IDLING
  - Bộ lọc Moving Average cho GPS Denoising (Kalman-lite)
  - State Machine: DI_CHUYEN → DANG_CHO_XAC_NHAN → CHAY_KHONG_TAI
  - Ngưỡng idling: 600 giây (cấu hình động từ config)
"""

import collections
import json
import os
from datetime import datetime

_DIR_AI  = os.path.dirname(os.path.abspath(__file__))
_DIR_GOC = os.path.dirname(_DIR_AI)

# Tải ngưỡng từ config nếu có
def _nap_nguong():
    path = os.path.join(_DIR_GOC, '03_JSON', 'config_he_thong.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f).get('nguong_idling_giay', 600)
    except Exception:
        return 600

from b2kiem_tra_gps import kiem_tra_xe_trong_cang


class QuanLyHanhTrinhESG:
    """
    State Machine quản lý 1 xe:
      DI_CHUYEN → DANG_CHO_XAC_NHAN (khi vào Geofence + v<5) 
                → CHAY_KHONG_TAI (sau 600s) 
                → DI_CHUYEN (khi rời vùng)
    """

    def __init__(self):
        # GPS Denoising: Moving Average 5 điểm
        self.win_lat = collections.deque(maxlen=5)
        self.win_lon = collections.deque(maxlen=5)

        # State
        self.trang_thai            = "DI_CHUYEN"
        self.thoi_diem_bat_dau_cho = None
        self.ten_cang_hien_tai     = None
        self.ma_cang_hien_tai      = None
        self.loai_khu_vuc          = None
        self.nguong_idling_giay    = _nap_nguong()

    # ------------------------------------------------------------------
    def _loc_toa_do(self, lat, lon):
        """Moving Average để khử GPS Drift."""
        self.win_lat.append(lat)
        self.win_lon.append(lon)
        return (sum(self.win_lat) / len(self.win_lat),
                sum(self.win_lon) / len(self.win_lon))

    # ------------------------------------------------------------------
    def cap_nhat_hanh_trinh(self, lat_tho: float, lon_tho: float,
                             van_toc: float):
        """
        Cập nhật 1 điểm GPS.

        Returns:
            ("BAT_DAU_IDLING",  ten_cang, loai)  khi vừa xác nhận idling
            ("KET_THUC_IDLING", moc_vao,  giay_cho) khi xe rời vùng
            ("DANG_CHO_XAC_NHAN", None, None)
            ("DANG_DI_CHUYEN",    None, None)
        """
        lat, lon = self._loc_toa_do(lat_tho, lon_tho)

        trong_vung, ten, ma, loai = kiem_tra_xe_trong_cang(lat, lon)
        bay_gio = datetime.now()
        dung_cho = trong_vung and van_toc < 5.0

        if dung_cho:
            if self.thoi_diem_bat_dau_cho is None:
                self.thoi_diem_bat_dau_cho = bay_gio
                self.ten_cang_hien_tai     = ten
                self.ma_cang_hien_tai      = ma
                self.loai_khu_vuc          = loai
                print(f"[B3] Bắt đầu theo dõi tại [{ten}] – loại: {loai}")

            giay = (bay_gio - self.thoi_diem_bat_dau_cho).total_seconds()

            if giay >= self.nguong_idling_giay and self.trang_thai != "CHAY_KHONG_TAI":
                self.trang_thai = "CHAY_KHONG_TAI"
                print(f"[B3] ✅ XÁC NHẬN IDLING tại [{self.ten_cang_hien_tai}] "
                      f"({int(giay)}s ≥ {self.nguong_idling_giay}s)")
                return "BAT_DAU_IDLING", self.ten_cang_hien_tai, self.loai_khu_vuc

            return "DANG_CHO_XAC_NHAN", None, None

        else:
            if self.trang_thai == "CHAY_KHONG_TAI":
                giay_cho = (bay_gio - self.thoi_diem_bat_dau_cho).total_seconds()
                moc_vao  = self.thoi_diem_bat_dau_cho
                ten_cu   = self.ten_cang_hien_tai

                # Reset state
                self.trang_thai            = "DI_CHUYEN"
                self.thoi_diem_bat_dau_cho = None
                self.ten_cang_hien_tai     = None

                print(f"[B3] Kết thúc Idling tại [{ten_cu}]. "
                      f"Tổng: {int(giay_cho)}s")
                return "KET_THUC_IDLING", moc_vao, giay_cho

            # Reset nếu chỉ DANG_CHO mà xe đi mất
            self.thoi_diem_bat_dau_cho = None
            self.trang_thai = "DI_CHUYEN"
            return "DANG_DI_CHUYEN", None, None

    def lay_trang_thai_hien_tai(self) -> dict:
        """Snapshot trạng thái cho API /vehicle/{id}/status."""
        bay_gio = datetime.now()
        giay_cho = 0.0
        if self.thoi_diem_bat_dau_cho:
            giay_cho = (bay_gio - self.thoi_diem_bat_dau_cho).total_seconds()
        return {
            "trang_thai"       : self.trang_thai,
            "ten_cang"         : self.ten_cang_hien_tai,
            "loai_khu_vuc"     : self.loai_khu_vuc,
            "thoi_gian_cho_giay": round(giay_cho, 1),
        }


if __name__ == "__main__":
    qly = QuanLyHanhTrinhESG()
    # Giả lập tọa độ Tân Vũ, tốc độ thấp
    sk, a1, a2 = qly.cap_nhat_hanh_trinh(20.8024, 106.7709, 2.0)
    print(f"[TEST] Sự kiện: {sk} | {a1} | {a2}")
    print(f"[TEST] Trạng thái: {qly.lay_trang_thai_hien_tai()}")
