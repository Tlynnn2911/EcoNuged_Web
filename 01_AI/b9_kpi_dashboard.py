"""
B9 – KPI Dashboard & Bảng xếp hạng Tài xế Xanh (Phân hệ 2)
=============================================================
Sửa từ v2:
  - Thêm cột do_tre_phan_hoi_giay (khi App truyền lên)
  - Thêm thong_ke_theo_cang() cho Heatmap dashboard
  - Thêm thong_ke_theo_ngay() cho biểu đồ xu hướng
  - Xuất JSON chuẩn API /kpi/leaderboard
  - Điểm phản hồi tính từ cột do_tre nếu có (không dùng mặc định 20)
"""

import os
import json
import pandas as pd
from datetime import datetime

DIEM_PHAN_HOI_MAX   = 40
DIEM_DUY_TRI_MAX    = 40
DIEM_CO2_MAX        = 20
NGUONG_TOT_GIAY     = 60
NGUONG_CHAP_GIAY    = 120
NGUONG_KEP_GIAY     = 300


class KPIDashboard:
    def __init__(self, ten_file_log="nhat_ky_phat_thai_esg.csv"):
        _dir = os.path.dirname(os.path.abspath(__file__))
        self.path_log = os.path.join(os.path.dirname(_dir), '04_DATA', ten_file_log)
        self.path_kpi = os.path.join(os.path.dirname(_dir), '04_DATA', 'kpi_bang_xep_hang.csv')

    def nap_du_lieu(self) -> pd.DataFrame:
        if not os.path.exists(self.path_log):
            print(f"[B9] Không tìm thấy log: {self.path_log}")
            return pd.DataFrame()
        df = pd.read_csv(self.path_log, encoding='utf-8-sig')
        df.columns = [c.strip() for c in df.columns]
        return df

    # ------------------------------------------------------------------
    @staticmethod
    def tinh_diem_phan_hoi(do_tre: float) -> float:
        if do_tre is None or (hasattr(do_tre, '__class__') and 
                               do_tre.__class__.__name__ == 'float' and 
                               do_tre != do_tre):  # NaN check
            return 20.0  # mặc định trung bình khi chưa có dữ liệu
        if do_tre <= NGUONG_TOT_GIAY:   return 40.0
        if do_tre <= NGUONG_CHAP_GIAY:  return 30.0
        if do_tre <= NGUONG_KEP_GIAY:   return 15.0
        return 0.0

    @staticmethod
    def tinh_diem_duy_tri(tong_giay: float) -> float:
        if tong_giay is None: return 0.0
        return round(min(tong_giay / 3600.0 * DIEM_DUY_TRI_MAX, DIEM_DUY_TRI_MAX), 2)

    @staticmethod
    def tinh_diem_co2(co2_kg: float) -> float:
        if co2_kg is None: return 0.0
        return round(min(co2_kg / 5.0 * DIEM_CO2_MAX, DIEM_CO2_MAX), 2)

    # ------------------------------------------------------------------
    def tinh_kpi_tong_hop(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty: return pd.DataFrame()
        rows = []
        for id_xe, nhom in df.groupby("ID_Xe"):
            tong_giay = nhom["Tổng_Giây_Chờ"].sum()
            tong_co2  = nhom["Lượng_CO2_kg"].sum()
            so_lan    = len(nhom)

            # Điểm phản hồi: dùng cột Do_Tre_Giay nếu có
            if "Do_Tre_Phan_Hoi_Giay" in nhom.columns:
                do_tre_tb = nhom["Do_Tre_Phan_Hoi_Giay"].dropna().mean()
                diem_ph = self.tinh_diem_phan_hoi(do_tre_tb)
            else:
                diem_ph = 20.0

            diem_dt = self.tinh_diem_duy_tri(tong_giay)
            diem_co = self.tinh_diem_co2(tong_co2)
            tong    = round(diem_ph + diem_dt + diem_co, 2)

            rows.append({
                "ID_Xe"         : id_xe,
                "So_Lan_Idling" : so_lan,
                "Tong_Giay_Cho" : round(tong_giay, 1),
                "Tong_Gio_Cho"  : round(tong_giay / 3600, 2),
                "Tong_CO2_kg"   : round(tong_co2, 4),
                "Diem_Phan_Hoi" : diem_ph,
                "Diem_Duy_Tri"  : diem_dt,
                "Diem_CO2"      : diem_co,
                "Tong_Diem"     : tong,
                "Hang"          : "",
            })

        df_kpi = pd.DataFrame(rows).sort_values("Tong_Diem", ascending=False)
        df_kpi = df_kpi.reset_index(drop=True)
        df_kpi["Hang"] = df_kpi.index + 1

        def nhan(h):
            if h == 1: return "🥇 Tài xế Xanh #1"
            if h == 2: return "🥈 Xuất sắc"
            if h == 3: return "🥉 Tốt"
            return "🌿 Tích cực"
        df_kpi["Huy_Hieu"] = df_kpi["Hang"].apply(nhan)
        return df_kpi

    # ------------------------------------------------------------------
    def thong_ke_theo_cang(self) -> dict:
        """Dữ liệu cho Heatmap: CO2 phân bổ theo cụm cảng."""
        df = self.nap_du_lieu()
        if df.empty: return {}
        return df.groupby("Tên_Cảng")["Lượng_CO2_kg"].sum().round(4).to_dict()

    def thong_ke_theo_ngay(self) -> dict:
        """Dữ liệu cho biểu đồ xu hướng theo ngày."""
        df = self.nap_du_lieu()
        if df.empty or "Thời_Điểm_Vào" not in df.columns: return {}
        df["Ngay"] = pd.to_datetime(df["Thời_Điểm_Vào"]).dt.date.astype(str)
        return df.groupby("Ngay")["Lượng_CO2_kg"].sum().round(4).to_dict()

    def thong_ke_tong_quan(self) -> dict:
        df = self.nap_du_lieu()
        if df.empty: return {}
        return {
            "tong_xe_giam_sat"   : int(df["ID_Xe"].nunique()),
            "tong_su_kien_idling": int(len(df)),
            "tong_co2_kg"        : round(float(df["Lượng_CO2_kg"].sum()), 4),
            "tong_gio_cho"       : round(float(df["Tổng_Giây_Chờ"].sum()) / 3600, 2),
            "trung_binh_co2_xe"  : round(float(df["Lượng_CO2_kg"].mean()), 4),
            "phan_bo_theo_cang"  : self.thong_ke_theo_cang(),
            "xu_huong_theo_ngay" : self.thong_ke_theo_ngay(),
        }

    def xuat_bang_xep_hang(self, df_kpi: pd.DataFrame) -> str:
        if df_kpi.empty: return ""
        df_kpi.to_csv(self.path_kpi, index=False, encoding='utf-8-sig')
        print(f"[B9] ✅ Đã xuất bảng xếp hạng: {self.path_kpi}")
        return self.path_kpi

    def lay_top_tai_xe(self, top_n: int = 10) -> list:
        """Response chuẩn cho API GET /kpi/leaderboard."""
        df = self.nap_du_lieu()
        df_kpi = self.tinh_kpi_tong_hop(df)
        if df_kpi.empty: return []
        self.xuat_bang_xep_hang(df_kpi)
        return df_kpi.head(top_n).to_dict(orient='records')

    def response_api_leaderboard(self, top_n: int = 10) -> dict:
        """Đúng format JSON cho endpoint /api/v1/kpi/leaderboard."""
        return {
            "cap_nhat_luc": datetime.now().isoformat(),
            "tong_xe"     : self.thong_ke_tong_quan().get("tong_xe_giam_sat", 0),
            "danh_sach"   : self.lay_top_tai_xe(top_n),
        }


if __name__ == "__main__":
    dash = KPIDashboard()
    print("=" * 55)
    tq = dash.thong_ke_tong_quan()
    print("  TỔNG QUAN:")
    for k, v in tq.items():
        if not isinstance(v, dict):
            print(f"    {k:30s}: {v}")
    print("\n  PHÂN BỔ THEO CẢNG:")
    for cang, co2 in tq.get("phan_bo_theo_cang", {}).items():
        print(f"    {cang:35s}: {co2:.4f} kg")
    print("\n  TOP TÀI XẾ XANH:")
    for item in dash.lay_top_tai_xe(5):
        print(f"    [{item['Hang']}] {str(item['ID_Xe']):30s}  "
              f"Điểm: {item['Tong_Diem']:5.1f}  {item['Huy_Hieu']}")
