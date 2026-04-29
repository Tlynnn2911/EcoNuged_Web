"""
B11 – Tối ưu hóa Tại chỗ (In-situ) & Kinh tế học Hành vi
===========================================================
Tài liệu: 18_4-20_4.docx Mục 3 + 22_4.docx Mục Quy trình

Cập nhật:
  - Giá dầu 31,040 VNĐ/Lít (Petrolimex 19/04/2026)
  - Định mức 2.5 Lít/giờ (khảo sát thực tế xe container)
  - 3 kịch bản thông điệp theo 22_4.docx: Detection, Push, Hướng dẫn chờ
  - Phân tích hành vi 4 nhóm: DIEU_HOA, SO_KHONG_KHOI, THOI_QUEN, KHONG_RO
  - KHÔNG đề xuất đổi lộ trình (ràng buộc Hải quan + Window time)
"""

import os
import json
import random
from datetime import datetime

# Cập nhật theo 22_4.docx
GIA_DIESEL_VND    = 31040   # VNĐ/Lít, Petrolimex Vùng 1, 19/04/2026
LIT_PER_GIO       = 2.5     # Lít/giờ idling xe container hạng nặng
CO2_PER_LIT       = 2.683   # kg CO2/Lít (QĐ 2626/QĐ-BTNMT)
TON_THAT_GIO      = 297600  # VNĐ/giờ/xe (nhiên liệu + nhân công + cơ hội)

# ---------------------------------------------------------------------------
# Thư viện thông điệp Nudge
# ---------------------------------------------------------------------------
NUDGE_LOSS_AVERSION = [
    "⚠️ Bạn đang đốt {tien:,.0f}đ/giờ – tương đương {quy_doi}. Tắt máy ngay!",
    "🔥 Nổ máy chờ đang 'thiêu' {tien:,.0f}đ/giờ. Hành động xanh = Giữ tiền!",
    "💸 {tien:,.0f}đ/giờ đang bay mất. Tài xế Xanh biết cách giữ khoản này.",
]
NUDGE_SOCIAL_PROOF = [
    "👥 {so_xe} xe tại {ten_cang} đã tắt máy. Bạn cũng có thể làm được!",
    "🌿 {phan_tram}% tài xế hôm nay đang 'chờ đợi xanh' tại {ten_cang}.",
    "📊 Cộng đồng tài xế đã tiết kiệm {co2:.1f} kg CO₂. Bạn góp được bao nhiêu?",
]
NUDGE_GIAI_PHAP = [
    "✅ Tắt máy = Tiết kiệm {tien:,.0f}đ + {co2:.3f} kg CO₂. Mở cửa đón gió biển!",
    "🌱 Ngắt máy → dùng điện lưới EPS (nếu có) → mát hơn, rẻ hơn, sạch hơn.",
    "💡 Dự kiến chờ {thoi_gian} phút – đủ thời gian nghỉ ngơi + tiết kiệm dầu.",
]
QUY_DOI = [
    "1 suất cơm đặc biệt", "1 ly cà phê + bánh mì",
    "½ lít dầu cho chuyến sau", "tiền điện 3 ngày",
]

# 3 kịch bản thông điệp theo 22_4.docx
KICH_BAN = {
    "DETECTION": (
        "📍 Phát hiện xe đang dừng tại vùng chờ {ten_cang}. "
        "Vận tốc <5km/h đã hơn 5 phút."
    ),
    "PUSH": (
        "🔔 Bạn đang ở khu vực chờ {ten_cang}. Dự kiến thông quan còn ~{phut} phút. "
        "Vui lòng TẮT MÁY để tiết kiệm {lit:.1f} lít dầu (~{tien:,.0f}đ) "
        "và bảo vệ sức khỏe chính mình."
    ),
    "HUONG_DAN": (
        "ℹ️ Thứ tự của bạn trong hàng đợi đã được ghi nhận. "
        "Bạn có thể tắt máy an toàn – hệ thống sẽ báo trước {bao_truoc} phút khi đến lượt."
    ),
}


class ThuatToanNudge:
    def __init__(self):
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            '03_JSON', 'config_he_thong.json'
        )
        self.config = {}
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)

    # ------------------------------------------------------------------
    @staticmethod
    def tinh_ton_that(giay_cho: float) -> dict:
        gio      = giay_cho / 3600
        lit      = gio * LIT_PER_GIO
        nhien_lieu = lit * GIA_DIESEL_VND
        co2      = lit * CO2_PER_LIT
        tong_tien= gio * TON_THAT_GIO
        return {
            "gio"         : round(gio, 4),
            "lit"         : round(lit, 4),
            "tien_nhien_lieu_vnd": round(nhien_lieu),
            "tong_ton_that_vnd"  : round(tong_tien),
            "tong_per_gio"       : TON_THAT_GIO,
            "co2_kg"      : round(co2, 4),
        }

    # ------------------------------------------------------------------
    def nudge_loss_aversion(self, giay_cho: float) -> str:
        t = self.tinh_ton_that(giay_cho)
        return random.choice(NUDGE_LOSS_AVERSION).format(
            tien=t["tong_per_gio"], quy_doi=random.choice(QUY_DOI)
        )

    @staticmethod
    def nudge_social_proof(ten_cang: str, so_xe_tat=8, tong_xe=10) -> str:
        pct  = round(so_xe_tat / max(tong_xe, 1) * 100)
        co2  = so_xe_tat * LIT_PER_GIO * CO2_PER_LIT * 0.5
        return random.choice(NUDGE_SOCIAL_PROOF).format(
            so_xe=so_xe_tat, ten_cang=ten_cang,
            phan_tram=pct, co2=co2
        )

    @staticmethod
    def nudge_giai_phap(giay_cho: float, ten_cang: str = "") -> str:
        t = ThuatToanNudge.tinh_ton_that(giay_cho)
        phut = int(giay_cho / 60)
        return random.choice(NUDGE_GIAI_PHAP).format(
            tien=t["tong_per_gio"], co2=t["co2_kg"],
            thoi_gian=phut,
        )

    # ------------------------------------------------------------------
    def sinh_kich_ban(self, loai: str, ten_cang: str,
                      giay_cho: float = 600,
                      phut_thong_quan: int = 45,
                      bao_truoc_phut: int = 5) -> str:
        """Sinh thông điệp theo 3 kịch bản trong 22_4.docx."""
        t = self.tinh_ton_that(giay_cho)
        return KICH_BAN.get(loai, "").format(
            ten_cang=ten_cang,
            phut=phut_thong_quan,
            lit=t["lit"],
            tien=t["tien_nhien_lieu_vnd"],
            bao_truoc=bao_truoc_phut,
        )

    # ------------------------------------------------------------------
    def tao_payload_canh_bao(self, id_xe: str, ten_cang: str,
                              giay_cho: float,
                              loai_khu_vuc: str = "CANG") -> dict:
        """
        Payload JSON đầy đủ gửi về App (Push Notification).
        Chọn chiến lược Nudge theo thời gian chờ.
        """
        t = self.tinh_ton_that(giay_cho)

        if giay_cho < 900:
            chien_luoc = "GIAI_PHAP"
            thong_diep = self.nudge_giai_phap(giay_cho, ten_cang)
        elif giay_cho < 1800:
            chien_luoc = "LOSS_AVERSION"
            thong_diep = self.nudge_loss_aversion(giay_cho)
        else:
            chien_luoc = "SOCIAL_PROOF"
            thong_diep = self.nudge_social_proof(ten_cang)

        return {
            "version"          : "1.1",
            "timestamp"        : datetime.now().isoformat(),
            "id_xe"            : id_xe,
            "ten_cang"         : ten_cang,
            "loai_khu_vuc"     : loai_khu_vuc,
            "giay_cho_hien_tai": round(giay_cho, 1),
            "ton_that_kinh_te" : {
                "tien_mat_vnd_moi_gio" : t["tong_per_gio"],
                "co2_kg_hien_tai"      : t["co2_kg"],
            },
            "canh_bao" : {
                "loai"           : "IDLING_ALERT",
                "chien_luoc"     : chien_luoc,
                "tieu_de"        : "🌿 Chờ Đợi Xanh – EcoNudge Gate",
                "noi_dung"       : thong_diep,
                "kich_ban_push"  : self.sinh_kich_ban(
                    "PUSH", ten_cang, giay_cho),
                "hanh_dong"      : "XAC_NHAN_TAT_MAY",
                "khong_hanh_dong": "BO_QUA",
            },
            "kpi_preview" : {
                "diem_co_the_dat" : 15 if giay_cho > 600 else 5,
                "hang_huy_hieu"   : "Tài xế Xanh",
            },
            "dieu_huong" : {
                "doi_lo_trinh"   : False,
                "giu_nguyen_cang": True,
                "ly_do"          : "Ràng buộc Hải quan & Window time – chỉ tối ưu ngắt máy tại chỗ",
            },
        }

    # ------------------------------------------------------------------
    @staticmethod
    def phan_tich_hanh_vi(ly_do: str) -> dict:
        """Phân loại nguyên nhân nổ máy theo Kinh tế học hành vi (18_4-20_4.docx)."""
        MAP = {
            "DIEU_HOA": {
                "ten_thien_kien": "Present Bias",
                "mo_ta"         : "Ưu tiên sự mát mẻ ngay lập tức hơn tiết kiệm lâu dài",
                "can_thiep"     : "Cung cấp bóng mát/quạt điện tại bãi chờ (EPS)",
                "nudge_type"    : "GIAI_PHAP",
            },
            "SO_KHONG_KHOI": {
                "ten_thien_kien": "Risk Aversion",
                "mo_ta"         : "Sợ xe không khởi động kịp – mất thứ tự hàng đợi",
                "can_thiep"     : "Hiển thị số thứ tự + thời gian chờ thực tế trên bảng LED",
                "nudge_type"    : "THONG_TIN",
            },
            "THOI_QUEN": {
                "ten_thien_kien": "Status Quo Bias",
                "mo_ta"         : "Mặc định giữ nguyên hành vi cũ dù biết lãng phí",
                "can_thiep"     : "Social Proof – hiển thị số xe đã tắt máy tại cảng",
                "nudge_type"    : "SOCIAL_PROOF",
            },
            "KHONG_RO": {
                "ten_thien_kien": "Information Gap",
                "mo_ta"         : "Không biết chi phí thực tế đang mất đi mỗi giờ",
                "can_thiep"     : "Loss Aversion – lượng hóa tổn thất bằng tiền mặt cụ thể",
                "nudge_type"    : "LOSS_AVERSION",
            },
        }
        return MAP.get(ly_do, MAP["KHONG_RO"])


if __name__ == "__main__":
    nudge = ThuatToanNudge()
    print("=" * 60)
    print("  DEMO: Payload cảnh báo (30 phút chờ tại HICT)")
    print("=" * 60)
    p = nudge.tao_payload_canh_bao("15H-123.45", "Lach Huyen Port", 1800, "CANG")
    print(json.dumps(p, ensure_ascii=False, indent=2))

    print("\n  PHÂN TÍCH HÀNH VI: ĐIỀU HÒA")
    for k, v in nudge.phan_tich_hanh_vi("DIEU_HOA").items():
        print(f"  {k:20s}: {v}")
