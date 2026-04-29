import json
import os

class PhanTichTonThat:
    def __init__(self):
        config_path = os.path.join('data', 'cau_hinh_phat_thai.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            self.cfg = json.load(f)
        self.ton_that_gio = self.cfg['tong_ton_that_vnd_per_hour']
        self.hs_tiet_kiem = self.cfg['heso_tiet_kiem_muc_tieu']

    def du_bao_hieu_qua(self, so_xe, so_gio_trung_binh):
        ton_that_hien_tai = so_xe * so_gio_trung_binh * self.ton_that_gio
        tiet_kiem = ton_that_hien_tai * self.hs_tiet_kiem
        return {
            "ton_that_hien_tai_vnd": round(ton_that_hien_tai),
            "tiet_kiem_du_kien_vnd": round(tiet_kiem),
            "roi_message": f"Voi {so_xe} xe, moi xe cho {so_gio_trung_binh} gio, ton that: {ton_that_hien_tai:,.0f} VND. Sau Econudge tiet kiem {tiet_kiem:,.0f} VND ({(self.hs_tiet_kiem*100):.0f}%)."
        }

    def ket_xuat_bao_cao_kinh_te(self):
        # Xuất báo cáo mẫu kinh tế
        report_data = self.du_bao_hieu_qua(50, 2.5)
        with open('data/reports/economic_loss_summary.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        return report_data