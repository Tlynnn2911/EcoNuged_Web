import pandas as pd
import os

class KPIDashboard:
    def __init__(self, log_path='data/nhat_ky_phat_thai_esg.csv'):
        self.log_path = log_path

    def thong_ke_tong_quan(self):
        if not os.path.exists(self.log_path):
            return {"tong_xe_giam_sat": 0, "tong_co2_kg": 0, "tong_gio_cho": 0, "phan_bo_theo_cang": {}}
        df = pd.read_csv(self.log_path)
        tong_co2 = df['Lượng_CO2_kg'].sum()
        tong_giay = df['Tổng_Giây_Chờ'].sum()
        phan_bo = df.groupby('Tên_Cảng')['Lượng_CO2_kg'].sum().to_dict()
        return {
            "tong_xe_giam_sat": df['ID_Xe'].nunique(),
            "tong_co2_kg": round(tong_co2, 2),
            "tong_gio_cho": round(tong_giay / 3600.0, 2),
            "phan_bo_theo_cang": phan_bo
        }

    def lay_top_tai_xe(self, n=5):
        if not os.path.exists(self.log_path):
            return []
        df = pd.read_csv(self.log_path)
        # Tổng hợp điểm ESG: giảm CO2 => điểm càng cao
        diem = df.groupby('ID_Xe').agg({'Lượng_CO2_kg': 'sum', 'Tổng_Giây_Chờ': 'sum'}).reset_index()
        diem['Diem_Xanh'] = 100 - (diem['Lượng_CO2_kg'] / (diem['Lượng_CO2_kg'].max()+1e-6)) * 100
        diem = diem.sort_values('Diem_Xanh', ascending=False).head(n)
        top = []
        for i, row in diem.iterrows():
            top.append({
                "Hang": len(top)+1,
                "ID_Xe": row['ID_Xe'],
                "Tong_Diem": round(row['Diem_Xanh'], 1),
                "Huy_Hieu": "🏆 Xanh" if row['Diem_Xanh'] > 70 else "🌿 Tiềm năng"
            })
        return top

    def thong_ke_theo_cang(self):
        if not os.path.exists(self.log_path):
            return {}
        df = pd.read_csv(self.log_path)
        thongke = df.groupby('Tên_Cảng').agg({'Lượng_CO2_kg': 'sum', 'Tổng_Giây_Chờ': 'mean'}).to_dict()
        return thongke