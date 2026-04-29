import sys
import os
import logging
import traceback
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

# ---------- ROUTES ----------
@app.route('/')
def app_page():
    return render_template('app.html')

@app.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html')

@app.route('/api/zones', methods=['GET'])
def get_zones():
    zones = lay_danh_sach_vung()
    return jsonify(zones)

@app.route('/api/check_geofence', methods=['POST'])
def check_geofence():
    data = request.json
    lat = data.get('lat')
    lon = data.get('lon')
    cang, loai = kiem_tra_xe_trong_cang(lat, lon)
    return jsonify({'inside': cang is not None, 'cang': cang, 'loai': loai})

@app.route('/api/simulate_idling', methods=['POST'])
def simulate_idling():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400
        
        vehicle_id = data.get('vehicle_id')
        port_name = data.get('port_name')
        idle_seconds = float(data.get('idle_seconds', 0))
        km_driven = float(data.get('km_driven', 0))
        
        if idle_seconds < 0:
            idle_seconds = 0
        
        # Tính CO₂
        co2_data = co2_calc.tinh_co2_toan_phan(km_driven, idle_seconds)
        
        # Ghi log
        log_entry = {
            "ID_Xe": vehicle_id,
            "Tên_Cảng": port_name,
            "Thời_Điểm_Vào": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "Thời_Điểm_Ra": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "Tổng_Giây_Chờ": idle_seconds,
            "Lượng_CO2_kg": co2_data['co2_idling_kg']
        }
        logger.ghi_nhat_ky(log_entry)
        
        # Tạo Nudge
        nud = nudge.tao_payload_canh_bao(vehicle_id, port_name, idle_seconds, "CANG")
        gui_tin_hieu({"event": "simulate_idling", "data": log_entry, "nudge": nud})
        
        return jsonify({
            "status": "ok",
            "co2_kg": co2_data['co2_idling_kg'],
            "nudge": nud
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/kpi', methods=['GET'])
def get_kpi():
    total_stats = dashboard.thong_ke_tong_quan()
    top_drivers = dashboard.lay_top_tai_xe(5)
    return jsonify({"total": total_stats, "top_drivers": top_drivers})

@app.route('/api/heatmap', methods=['GET'])
def get_heatmap():
    heat_data = dashboard.thong_ke_theo_cang()
    ports = list(heat_data.keys())
    co2_vals = list(heat_data.values())
    return jsonify({"ports": ports, "co2": co2_vals})

@app.route('/api/export/excel', methods=['GET'])
def export_excel():
    try:
        result = report_exporter.xuat_toan_bo()
        excel_path = result.get('excel')
        if excel_path and os.path.exists(excel_path):
            abs_path = os.path.abspath(excel_path)
            filename = os.path.basename(abs_path)
            return send_file(
                abs_path,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        return jsonify({"error": "Không tìm thấy file Excel. Hãy đảm bảo có dữ liệu idling."}), 404
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/export/pdf', methods=['GET'])
def export_pdf():
    try:
        result = report_exporter.xuat_toan_bo()
        pdf_path = result.get('pdf')
        if pdf_path and os.path.exists(pdf_path):
            abs_path = os.path.abspath(pdf_path)
            filename = os.path.basename(abs_path)
            return send_file(
                abs_path,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
        return jsonify({"error": "Không tìm thấy file PDF. Hãy đảm bảo reportlab đã được cài đặt và có dữ liệu."}), 404
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/economic_analysis', methods=['GET'])
def economic_analysis():
    so_xe = int(request.args.get('so_xe', 50))
    so_gio = float(request.args.get('so_gio', 2.5))
    analysis = economic.du_bao_hieu_qua(so_xe, so_gio)
    return jsonify({
        "ton_that_hien_tai_vnd": analysis.get("truoc_ap_dung", {}).get("tong_ton_that_vnd", 0),
        "tiet_kiem_du_kien_vnd": analysis.get("tiet_kiem_vnd", 0),
        "ty_le_giam_pct": analysis.get("ty_le_giam_pct", 30),
        "roi_message": analysis.get("roi_message", ""),
        "truoc_ap_dung": analysis.get("truoc_ap_dung", {})
    })

@app.route('/api/actual_statistics', methods=['GET'])
def actual_statistics():
    df = dashboard.nap_du_lieu()
    if df.empty:
        return jsonify({"so_xe": 0, "trung_binh_gio_cho": 0, "tong_co2_kg": 0})
    
    # Chuyển cột thời gian vào thành datetime
    if "Thời_Điểm_Vào" in df.columns:
        df["Thời_Điểm_Vào"] = pd.to_datetime(df["Thời_Điểm_Vào"], errors='coerce')
        # Chỉ lấy 24 giờ gần nhất (hoặc 7 ngày – tuỳ ý)
        last_day = datetime.now() - timedelta(days=1)
        df = df[df["Thời_Điểm_Vào"] >= last_day]
    
    if df.empty:
        return jsonify({"so_xe": 0, "trung_binh_gio_cho": 0, "tong_co2_kg": 0})
    
    # Lọc giá trị âm và outlier: chỉ lấy thời gian chờ <= 7200 giây (2 giờ)
    df["Tổng_Giây_Chờ"] = df["Tổng_Giây_Chờ"].abs()
    df = df[df["Tổng_Giây_Chờ"] <= 7200]  # 2 giờ
    
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

if __name__ == '__main__':
    os.makedirs('04_DATA', exist_ok=True)
    os.makedirs('04_DATA/reports', exist_ok=True)
    os.makedirs('03_JSON', exist_ok=True)
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True, host='0.0.0.0', port=5000)