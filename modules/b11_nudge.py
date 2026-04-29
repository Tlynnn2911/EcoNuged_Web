import json
import os

class ThuatToanNudge:
    def __init__(self):
        config_path = os.path.join('data', 'cau_hinh_phat_thai.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

    def tao_payload_canh_bao(self, id_xe, ten_cang, giay_cho, loai_khu_vuc):
        phut_cho = giay_cho / 60.0
        gio_cho = giay_cho / 3600.0
        ton_that_vnd = gio_cho * self.config['tong_ton_that_vnd_per_hour']

        if giay_cho < 900:
            chien_luoc = "loss_aversion"
            thong_diep = f"⚠️ Xe {id_xe} đã chờ {phut_cho:.0f} phút tại {ten_cang}. Nguy cơ mất {ton_that_vnd:,.0f} VND. Hãy rời cảng ngay."
        elif giay_cho < 2100:
            chien_luoc = "social_proof"
            thong_diep = f"🌱 85% tài xế xanh tại cảng {ten_cang} rời sau dưới 20 phút. Bạn đã chờ {phut_cho:.0f} phút. Hãy cải thiện!"
        else:
            chien_luoc = "giai_phap"
            thong_diep = f"💡 Xe {id_xe} chờ {phut_cho:.0f} phút (~{ton_that_vnd:,.0f} VND thiệt hại). Đề xuất sử dụng cổng ưu tiên hoặc off-port parking."

        return {
            "id_xe": id_xe,
            "ten_cang": ten_cang,
            "giay_cho": giay_cho,
            "canh_bao": {
                "chien_luoc": chien_luoc,
                "noi_dung": thong_diep,
                "ton_that_du_kien": round(ton_that_vnd)
            }
        }