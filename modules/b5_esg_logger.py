import csv
import os
from datetime import datetime

class QuanTriLogESG:
    def __init__(self, log_path='data/nhat_ky_phat_thai_esg.csv'):
        self.log_path = log_path
        if not os.path.exists(log_path):
            with open(log_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['ID_Xe', 'Tên_Cảng', 'Thời_Điểm_Vào', 'Thời_Điểm_Ra', 'Tổng_Giây_Chờ', 'Lượng_CO2_kg', 'Thời_gian'])

    def ghi_nhat_ky(self, du_lieu):
        du_lieu['Thời_gian'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.log_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['ID_Xe', 'Tên_Cảng', 'Thời_Điểm_Vào', 'Thời_Điểm_Ra', 'Tổng_Giây_Chờ', 'Lượng_CO2_kg', 'Thời_gian'])
            writer.writerow(du_lieu)