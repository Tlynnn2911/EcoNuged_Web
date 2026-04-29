from datetime import datetime, timedelta
import collections

class QuanLyHanhTrinhESG:
    def __init__(self, vehicle_id="UNKNOWN"):
        self.vehicle_id = vehicle_id
        self.trang_thai = "DUNG_YEN"  # DUNG_YEN, CHAY_KHONG_TAI, IDLING
        self.last_gps = []
        self.max_buffer = 5
        self.thoi_diem_bat_dau_cho = None
        self.ten_cang_hien_tai = None
        self.loai_khu_vuc = None
        self.nguong_idling_giay = 600

    def _moving_average(self, new_lat, new_lon):
        self.last_gps.append((new_lat, new_lon))
        if len(self.last_gps) > self.max_buffer:
            self.last_gps.pop(0)
        avg_lat = sum(p[0] for p in self.last_gps) / len(self.last_gps)
        avg_lon = sum(p[1] for p in self.last_gps) / len(self.last_gps)
        return avg_lat, avg_lon

    def cap_nhat_hanh_trinh(self, lat, lon, van_toc=0, loai_khu_vuc=None, ten_cang=None):
        smoothed_lat, smoothed_lon = self._moving_average(lat, lon)
        su_kien = "KHONG_DOI"
        giay_cho = 0

        # Xác định trạng thái di chuyển
        if van_toc > 1.0:  # Đang chạy
            if self.trang_thai == "IDLING":
                # Kết thúc idling
                if self.thoi_diem_bat_dau_cho:
                    giay_cho = (datetime.now() - self.thoi_diem_bat_dau_cho).total_seconds()
                self.trang_thai = "CHAY_KHONG_TAI"
                su_kien = "KET_THUC_IDLING"
                self.thoi_diem_bat_dau_cho = None
            else:
                self.trang_thai = "CHAY_KHONG_TAI"
        else:  # Dừng xe
            if self.trang_thai != "IDLING":
                # Bắt đầu giai đoạn chờ
                if self.thoi_diem_bat_dau_cho is None:
                    self.thoi_diem_bat_dau_cho = datetime.now()
                    self.ten_cang_hien_tai = ten_cang
                    self.loai_khu_vuc = loai_khu_vuc
                    su_kien = "BAT_DAU_IDLING"
                # Kiểm tra ngưỡng 600s
                elapsed = (datetime.now() - self.thoi_diem_bat_dau_cho).total_seconds()
                if elapsed >= self.nguong_idling_giay:
                    self.trang_thai = "IDLING"
                    su_kien = "IDLING_XAC_NHAN"
                else:
                    self.trang_thai = "DUNG_YEN"
            else:
                su_kien = "DANG_IDLING"

        return su_kien, self.thoi_diem_bat_dau_cho, (datetime.now() - self.thoi_diem_bat_dau_cho).total_seconds() if self.thoi_diem_bat_dau_cho else 0