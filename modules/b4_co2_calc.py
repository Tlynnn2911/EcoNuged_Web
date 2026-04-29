import json
import os

class BoTinhToanPhatThai:
    def __init__(self):
        config_path = os.path.join('data', 'cau_hinh_phat_thai.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        self.EF = config['EF_diesel_kgCO2_per_liter']
        self.DM_CHO = config['idling_consumption_l_per_hour']  # 2.5 L/h
        self.gia_dau = config['gia_dau_ban_le_vnd_per_liter']

    def tinh_co2_idling(self, giay_cho):
        gio_cho = giay_cho / 3600.0
        nhien_lieu = gio_cho * self.DM_CHO
        co2 = nhien_lieu * self.EF
        return co2, nhien_lieu

    def tinh_co2_van_hanh(self, km_chay, so_gio_chay=0):
        # Giả định 0.25 L/km tiêu hau trung bình
        nhien_lieu_km = km_chay * 0.25
        co2 = nhien_lieu_km * self.EF
        return co2, nhien_lieu_km

    def tinh_co2_toan_phan(self, km_chay, giay_cho):
        co2_drive, fuel_drive = self.tinh_co2_van_hanh(km_chay)
        co2_idle, fuel_idle = self.tinh_co2_idling(giay_cho)
        return {
            "tong_co2_kg": co2_drive + co2_idle,
            "co2_van_hanh_kg": co2_drive,
            "co2_idling_kg": co2_idle,
            "nhien_lieu_drive_l": fuel_drive,
            "nhien_lieu_idle_l": fuel_idle
        }