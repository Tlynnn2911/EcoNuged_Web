import sys
import os
import logging
from datetime import datetime, timedelta
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file

_DIR = os.path.dirname(os.path.abspath(__file__))
_AI = os.path.join(_DIR, '01_AI')
if _AI not in sys.path:
    sys.path.insert(0, _AI)

from b2kiem_tra_gps import kiem_tra_xe_trong_cang, lay_danh_sach_vung
from b3quan_ly_hanh_trinh import QuanLyHanhTrinhESG
from b4bo_tinh_toan_phat_thai import BoTinhToanPhatThai
from b5quan_tri_log_idling import QuanTriLogESG
from b6_trigger_it import gui_tin_hieu
from b7_xu_ly_gia_toc import BoLocGiaTocAI
from b8_do_thoi_gian_tuan_thu import BoDoTuanThuAI
from b9_kpi_dashboard import KPIDashboard
from b10_ket_xuat_bao_cao import KetXuatBaoCaoESG
from b11_toi_uu_tai_cho import ThuatToanNudge
from b12_phan_tich_ton_that import PhanTichTonThat

app = Flask(__name__)
app.secret_key = 'econudge2025'

co2_calc = BoTinhToanPhatThai()
logger = QuanTriLogESG()
dashboard = KPIDashboard()
nudge = ThuatToanNudge()
economic = PhanTichTonThat()
report_exporter = KetXuatBaoCaoESG()

xe_state = {}

def get_or_create_state(vehicle_id):
    if vehicle_id not in xe_state:
        xe_state[vehicle_id] = QuanLyHanhTrinhESG(vehicle_id)
    return xe_state[vehicle_id]

@app.route('/')
def app_page():
    return render_template('app.html')

@app.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html')

# ... (các API khác giữ nguyên như cũ, chỉ sửa actual_statistics) ...

@app.route('/api/actual_statistics', methods=['GET'])
def actual_statistics():
    df = dashboard.nap_du_lieu()
    if df.empty:
        return jsonify({"so_xe": 0, "trung_binh_gio_cho": 0, "tong_co2_kg": 0})
    
    # Chuyển cột thời gian vào thành datetime
    if "Thời_Điểm_Vào" in df.columns:
        df["Thời_Điểm_Vào"] = pd.to_datetime(df["Thời_Điểm_Vào"], errors='coerce')
        # Chỉ lấy dữ liệu 7 ngày gần nhất (loại bỏ dữ liệu cũ gây nhiễu)
        last_7_days = datetime.now() - timedelta(days=7)
        df = df[df["Thời_Điểm_Vào"] >= last_7_days]
    
    if df.empty:
        return jsonify({"so_xe": 0, "trung_binh_gio_cho": 0, "tong_co2_kg": 0})
    
    # Lọc bỏ giá trị âm và outlier (> 24h)
    df["Tổng_Giây_Chờ"] = df["Tổng_Giây_Chờ"].abs()
    df = df[df["Tổng_Giây_Chờ"] <= 86400]  # 24 giờ
    
    so_xe = df["ID_Xe"].nunique()
    tong_giay = df["Tổng_Giây_Chờ"].sum()
    tong_gio = tong_giay / 3600
    trung_binh_gio_cho = tong_gio / so_xe if so_xe > 0 else 0
    tong_co2 = df["Lượng_CO2_kg"].abs().sum()
    
    return jsonify({
        "so_xe": so_xe,
        "trung_binh_gio_cho": round(trung_binh_gio_cho, 2),
        "tong_co2_kg": round(tong_co2, 2)
    })

# Các route còn lại giữ nguyên (simulate_idling, kpi, heatmap, export...)
# ... (copy từ các câu trước, đảm bảo đầy đủ)

if __name__ == '__main__':
    os.makedirs('04_DATA', exist_ok=True)
    os.makedirs('04_DATA/reports', exist_ok=True)
    os.makedirs('03_JSON', exist_ok=True)
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True, host='0.0.0.0', port=5000)