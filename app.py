import sys
import os
import logging
from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime

# Thêm đường dẫn đến thư mục 01_AI (chứa các module backend)
_DIR = os.path.dirname(os.path.abspath(__file__))
_AI = os.path.join(_DIR, '01_AI')
if _AI not in sys.path:
    sys.path.insert(0, _AI)

# Import các module xử lý (tên tiếng Việt)
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

# Khởi tạo Flask app
app = Flask(__name__)
app.secret_key = 'econudge2025'

# Khởi tạo các đối tượng chính (các module tự tìm đường dẫn cấu hình và log)
co2_calc = BoTinhToanPhatThai()
logger = QuanTriLogESG()
dashboard = KPIDashboard()          # Quản lý KPI
nudge = ThuatToanNudge()
economic = PhanTichTonThat()
report_exporter = KetXuatBaoCaoESG()

# Dictionary lưu trạng thái xe (nếu cần cho state machine)
xe_state = {}

def get_or_create_state(vehicle_id):
    if vehicle_id not in xe_state:
        xe_state[vehicle_id] = QuanLyHanhTrinhESG(vehicle_id)
    return xe_state[vehicle_id]

# ------------------------- ROUTES -------------------------

@app.route('/')
def app_page():
    """Trang chính dành cho người dùng (App) – chỉ mô phỏng idling"""
    return render_template('app.html')

@app.route('/dashboard')
def dashboard_page():
    """Trang quản trị (Dashboard) – KPI, heatmap, báo cáo, phân tích kinh tế"""
    return render_template('dashboard.html')

# API lấy danh sách các vùng geofence
@app.route('/api/zones', methods=['GET'])
def get_zones():
    zones = lay_danh_sach_vung()
    return jsonify(zones)

# API kiểm tra một điểm có nằm trong cảng hay không
@app.route('/api/check_geofence', methods=['POST'])
def check_geofence():
    data = request.json
    lat = data.get('lat')
    lon = data.get('lon')
    cang, loai = kiem_tra_xe_trong_cang(lat, lon)
    return jsonify({'inside': cang is not None, 'cang': cang, 'loai': loai})

# API mô phỏng idling (tự tính thời gian chờ từ client)
@app.route('/api/simulate_idling', methods=['POST'])
def simulate_idling():
    data = request.json
    vehicle_id = data['vehicle_id']
    port_name = data['port_name']
    idle_seconds = float(data['idle_seconds'])
    km_driven = float(data.get('km_driven', 0))

    # Tính CO₂
    co2_data = co2_calc.tinh_co2_toan_phan(km_driven, idle_seconds)
    
    # Ghi log ESG
    log_entry = {
        "ID_Xe": vehicle_id,
        "Tên_Cảng": port_name,
        "Thời_Điểm_Vào": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "Thời_Điểm_Ra": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "Tổng_Giây_Chờ": idle_seconds,
        "Lượng_CO2_kg": co2_data['co2_idling_kg']
    }
    logger.ghi_nhat_ky(log_entry)
    
    # Tạo thông điệp Nudge
    nud = nudge.tao_payload_canh_bao(vehicle_id, port_name, idle_seconds, "CANG")
    gui_tin_hieu({"event": "simulate_idling", "data": log_entry, "nudge": nud})
    
    return jsonify({
        "status": "ok",
        "co2_kg": co2_data['co2_idling_kg'],
        "nudge": nud
    })

# API lấy tổng quan KPI và top tài xế
@app.route('/api/kpi', methods=['GET'])
def get_kpi():
    total_stats = dashboard.thong_ke_tong_quan()
    top_drivers = dashboard.lay_top_tai_xe(5)
    return jsonify({"total": total_stats, "top_drivers": top_drivers})

# API lấy dữ liệu cho heatmap (CO₂ theo cảng)
@app.route('/api/heatmap', methods=['GET'])
def get_heatmap():
    heat_data = dashboard.thong_ke_theo_cang()   # dict {tên cảng: CO₂}
    ports = list(heat_data.keys())
    co2_vals = list(heat_data.values())
    return jsonify({"ports": ports, "co2": co2_vals})

# API xuất báo cáo Excel
@app.route('/api/export/excel', methods=['GET'])
def export_excel():
    result = report_exporter.xuat_toan_bo()
    if result.get('excel'):
        return send_file(result['excel'], as_attachment=True)
    return jsonify({"error": "No data"}), 404

# API xuất báo cáo PDF (đã fix font Unicode)
@app.route('/api/export/pdf', methods=['GET'])
def export_pdf():
    result = report_exporter.xuat_toan_bo()
    if result.get('pdf'):
        return send_file(result['pdf'], as_attachment=True)
    return jsonify({"error": "No data"}), 404

# API phân tích tổn thất kinh tế (dự báo hiệu quả)
@app.route('/api/economic_analysis', methods=['GET'])
def economic_analysis():
    so_xe = int(request.args.get('so_xe', 50))
    so_gio = float(request.args.get('so_gio', 2.5))
    analysis = economic.du_bao_hieu_qua(so_xe, so_gio)
    # analysis = {
    #   "truoc_ap_dung": {...},
    #   "ty_le_giam_pct": 30,
    #   "tiet_kiem_vnd": ...,
    #   "roi_message": "..."
    # }
    return jsonify({
        "ton_that_hien_tai_vnd": analysis.get("truoc_ap_dung", {}).get("tong_ton_that_vnd", 0),
        "tiet_kiem_du_kien_vnd": analysis.get("tiet_kiem_vnd", 0),
        "ty_le_giam_pct": analysis.get("ty_le_giam_pct", 30),
        "roi_message": analysis.get("roi_message", ""),
        "truoc_ap_dung": analysis.get("truoc_ap_dung", {})
    })

# ------------------------- MAIN -------------------------
if __name__ == '__main__':
    # Tạo các thư mục cần thiết nếu chưa có
    os.makedirs('04_DATA', exist_ok=True)
    os.makedirs('04_DATA/reports', exist_ok=True)
    os.makedirs('03_JSON', exist_ok=True)
    
    # Cấu hình logging
    logging.basicConfig(level=logging.INFO)
    
    # Chạy server, cho phép truy cập từ mạng nội bộ (để chạy trên máy ảo Android hoặc thiết bị khác)
    app.run(debug=True, host='0.0.0.0', port=5000)