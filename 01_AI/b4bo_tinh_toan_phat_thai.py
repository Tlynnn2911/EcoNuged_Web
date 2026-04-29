"""
B4 – Bộ tính toán phát thải CO2 (Phân hệ 3)
=============================================
Công thức chuẩn QĐ 2626/QĐ-BTNMT:
  Tổng_CO2 = (D × EF_driving) + (T_idle × EF_idling)

Cập nhật từ 22_4.docx (19/04/2026):
  - Giá dầu: 31,040 VNĐ/Lít (Petrolimex Vùng 1)
  - Định mức Idling: 2.5 Lít/giờ (sửa từ 2.2 → 2.5 theo khảo sát thực tế)
  - Thêm hàm tinh_ton_that_kinh_te() cho B11 và báo cáo ESG
  - Thêm tinh_co2_toan_phan_scope3() với cấu trúc đầy đủ Scope 3
"""

import json
import os
import sys

class BoTinhToanPhatThai:
    def __init__(self, ten_file_config='cau_hinh_phat_thai.json'):
        _dir = os.path.dirname(os.path.abspath(__file__))
        self.path_config = os.path.join(_dir, '..', '03_JSON', ten_file_config)
        try:
            with open(self.path_config, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            self.EF      = self.config['he_so_ef_diesel']
            self.DM_CHO  = self.config['dinh_muc_tieu_thu']['xe_container_cho_lit_gio']
            self.DM_CHAY = self.config['dinh_muc_tieu_thu']['xe_container_chay_lit_km']
            self.nguon   = self.config['nguon_phap_ly']
            print(f"[B4] ✅ EF Diesel = {self.EF} kg CO₂/Lít | "
                  f"Idling = {self.DM_CHO} Lít/h | Chạy = {self.DM_CHAY} Lít/km")
        except FileNotFoundError:
            print(f"[B4] ❌ Không tìm thấy config: {self.path_config}")
            sys.exit(1)
        except KeyError as e:
            print(f"[B4] ❌ Thiếu tham số {e} trong JSON")
            sys.exit(1)

    # ------------------------------------------------------------------
    def tinh_co2_cho_idling(self, giay_cho: float) -> dict:
        """CO2 từ nổ máy chờ: T_idle × EF_idling"""
        gio = giay_cho / 3600
        lit = gio * self.DM_CHO
        co2 = lit * self.EF
        return {
            "giay_cho"      : round(giay_cho, 1),
            "gio_cho"       : round(gio, 4),
            "lit_idling"    : round(lit, 4),
            "co2_idling_kg" : round(co2, 4),
        }

    def tinh_co2_van_hanh(self, km: float) -> dict:
        """CO2 từ di chuyển: D × EF_driving"""
        lit = km * self.DM_CHAY
        co2 = lit * self.EF
        return {
            "km"            : round(km, 3),
            "lit_chay"      : round(lit, 4),
            "co2_driving_kg": round(co2, 4),
        }

    def tinh_co2_toan_phan(self, km_di_chuyen: float, giay_cho: float) -> dict:
        """Công thức đầy đủ Scope 3: (D×EF) + (T×EF)"""
        r_chay = self.tinh_co2_van_hanh(km_di_chuyen)
        r_cho  = self.tinh_co2_cho_idling(giay_cho)
        tong   = r_chay["co2_driving_kg"] + r_cho["co2_idling_kg"]
        return {
            "co2_van_hanh_kg" : r_chay["co2_driving_kg"],
            "co2_idling_kg"   : r_cho["co2_idling_kg"],
            "tong_co2_kg"     : round(tong, 4),
            "tong_lit"        : round(r_chay["lit_chay"] + r_cho["lit_idling"], 4),
            "km_di_chuyen"    : r_chay["km"],
            "nguon_phap_ly"   : self.nguon,
            "tieu_chuan"      : "GHG Protocol – Scope 3 Category 4",
        }

    def tinh_ton_that_kinh_te(self, giay_cho: float,
                               gia_dau: int = 31040,
                               luong_tai_xe_gio: int = 70000,
                               chi_phi_co_hoi_gio: int = 150000) -> dict:
        """
        Lượng hóa tổn thất tài chính theo 22_4.docx:
          - Nhiên liệu: giá_dầu × lít_tiêu_thụ
          - Nhân công:  70,000 đ/giờ
          - Chi phí cơ hội + khấu hao: 150,000 đ/giờ
        """
        gio   = giay_cho / 3600
        lit   = gio * self.DM_CHO
        nhien_lieu = lit * gia_dau
        nhan_cong  = gio * luong_tai_xe_gio
        co_hoi     = gio * chi_phi_co_hoi_gio
        tong       = nhien_lieu + nhan_cong + co_hoi
        return {
            "gio_cho"          : round(gio, 4),
            "chi_phi_nhien_lieu": round(nhien_lieu),
            "chi_phi_nhan_cong" : round(nhan_cong),
            "chi_phi_co_hoi"   : round(co_hoi),
            "tong_ton_that_vnd" : round(tong),
            "tong_ton_that_gio" : round(tong / gio) if gio > 0 else 0,
            "co2_phat_thai_kg"  : self.tinh_co2_cho_idling(giay_cho)["co2_idling_kg"],
        }

    # Alias cũ để không phá các file khác
    def thuc_thi_tinh_toan(self, giay_cho: float) -> dict:
        r = self.tinh_co2_cho_idling(giay_cho)
        return {"so_lit": r["lit_idling"], "so_kg_co2": r["co2_idling_kg"],
                "nguon_phap_ly": self.nguon}


if __name__ == "__main__":
    m = BoTinhToanPhatThai()
    print("\n--- Tính 30 phút nổ máy chờ ---")
    r1 = m.tinh_co2_cho_idling(1800)
    print(f"  CO2 idling: {r1['co2_idling_kg']} kg | Dầu: {r1['lit_idling']} lít")

    print("\n--- Tính toàn phần: 50km + 30 phút chờ ---")
    r2 = m.tinh_co2_toan_phan(50, 1800)
    print(f"  Tổng CO2: {r2['tong_co2_kg']} kg  "
          f"(Chạy: {r2['co2_van_hanh_kg']} + Chờ: {r2['co2_idling_kg']})")

    print("\n--- Tổn thất kinh tế 2 giờ chờ (theo 22_4.docx) ---")
    r3 = m.tinh_ton_that_kinh_te(7200)
    for k, v in r3.items():
        print(f"  {k:30s}: {v:,.0f}" if isinstance(v, (int, float)) else f"  {k}: {v}")
