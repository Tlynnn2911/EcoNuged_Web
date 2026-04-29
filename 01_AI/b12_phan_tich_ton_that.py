"""
B12 – Phân tích Tổn thất Kinh tế do Chạy không tải (MỚI – từ 22_4.docx)
=========================================================================
Phân hệ bổ sung: Kinh tế học & Nghiên cứu tối ưu

Nhiệm vụ:
  - Tính toán thiệt hại tài chính & CO2 theo tài liệu 22_4.docx
  - Dự báo tiết kiệm khi áp dụng EcoNudge Gate
  - Phân tích theo quy mô đội xe (doanh nghiệp vừa/nhỏ)
  - Cung cấp dữ liệu cho Slide 2-3 bài trình bày
"""

import os
import json
from datetime import datetime

# Hằng số từ 22_4.docx (đã xác minh 19/04/2026)
GIA_DIESEL        = 31040   # VNĐ/Lít
DM_IDLING         = 2.5     # Lít/giờ/xe container
EF_CO2            = 2.683   # kg CO2/Lít (QĐ 2626/QĐ-BTNMT)
LUONG_TAI_XE      = 70000   # VNĐ/giờ (18tr/tháng ÷ 26 ngày ÷ 10h)
CP_CO_HOI         = 150000  # VNĐ/giờ (khấu hao + phí bãi + lợi nhuận mất)


class PhanTichTonThat:
    """Tính toán tổn thất kinh tế và dự báo tác động của EcoNudge Gate."""

    def __init__(self):
        _dir = os.path.dirname(os.path.abspath(__file__))
        path_config = os.path.join(_dir, '..', '03_JSON', 'cau_hinh_phat_thai.json')
        try:
            with open(path_config, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception:
            self.config = {}

    # ------------------------------------------------------------------
    def tinh_ton_that_mot_xe(self, gio_cho: float) -> dict:
        """
        Tổn thất cho 1 xe trong gio_cho giờ.
        Công thức từ 22_4.docx:
          Nhiên liệu = 2.5 × 31,040 × gio
          Nhân công  = 70,000 × gio
          Cơ hội     = 150,000 × gio
          Tổng       = 297,600 VNĐ/giờ/xe
        """
        nhien_lieu = gio_cho * DM_IDLING * GIA_DIESEL
        nhan_cong  = gio_cho * LUONG_TAI_XE
        co_hoi     = gio_cho * CP_CO_HOI
        tong       = nhien_lieu + nhan_cong + co_hoi
        co2        = gio_cho * DM_IDLING * EF_CO2
        return {
            "gio_cho"             : round(gio_cho, 2),
            "phi_nhien_lieu_vnd"  : round(nhien_lieu),
            "phi_nhan_cong_vnd"   : round(nhan_cong),
            "chi_phi_co_hoi_vnd"  : round(co_hoi),
            "tong_ton_that_vnd"   : round(tong),
            "tong_per_gio_vnd"    : round(tong / gio_cho) if gio_cho > 0 else 0,
            "co2_phat_thai_kg"    : round(co2, 4),
            "co2_per_gio_kg"      : round(DM_IDLING * EF_CO2, 4),
        }

    # ------------------------------------------------------------------
    def tinh_ton_that_doi_xe(self, so_xe: int, gio_cho_ngay: float,
                              so_ngay_thang: int = 26) -> dict:
        """
        Tổng hợp cho đội xe trong 1 tháng (mặc định 26 ngày làm việc).
        Ví dụ từ 22_4.docx: 50 xe × 2h × 26 ngày = 2,600 giờ/tháng
        """
        tong_gio      = so_xe * gio_cho_ngay * so_ngay_thang
        ton_that_gio  = self.tinh_ton_that_mot_xe(1)
        tong_vnd      = tong_gio * ton_that_gio["tong_per_gio_vnd"]
        tong_co2_kg   = tong_gio * DM_IDLING * EF_CO2
        return {
            "so_xe"               : so_xe,
            "gio_cho_xe_ngay"     : gio_cho_ngay,
            "so_ngay_thang"       : so_ngay_thang,
            "tong_gio_thang"      : round(tong_gio, 1),
            "tong_ton_that_vnd"   : round(tong_vnd),
            "tong_ton_that_ty"    : round(tong_vnd / 1e9, 3),
            "tong_co2_kg"         : round(tong_co2_kg, 2),
            "tong_co2_tan"        : round(tong_co2_kg / 1000, 4),
        }

    # ------------------------------------------------------------------
    def du_bao_hieu_qua(self, so_xe: int, gio_cho_ngay: float,
                         ty_le_giam_pct: float = 30.0,
                         so_ngay_thang: int = 26) -> dict:
        """
        Dự báo tác động của EcoNudge Gate.
        Mặc định: giảm 30% thời gian nổ máy chờ vô ích (theo 22_4.docx).
        """
        truoc = self.tinh_ton_that_doi_xe(so_xe, gio_cho_ngay, so_ngay_thang)
        tiet_kiem_vnd = truoc["tong_ton_that_vnd"] * ty_le_giam_pct / 100
        cat_giam_co2  = truoc["tong_co2_kg"] * ty_le_giam_pct / 100
        return {
            "truoc_ap_dung"      : truoc,
            "ty_le_giam_pct"     : ty_le_giam_pct,
            "tiet_kiem_vnd"      : round(tiet_kiem_vnd),
            "tiet_kiem_trieu_vnd": round(tiet_kiem_vnd / 1e6, 2),
            "cat_giam_co2_kg"    : round(cat_giam_co2, 2),
            "cat_giam_co2_tan"   : round(cat_giam_co2 / 1000, 4),
            "roi_message": (
                f"Với {so_xe} xe, giảm {ty_le_giam_pct:.0f}% idling → "
                f"tiết kiệm {tiet_kiem_vnd/1e6:.0f} triệu VNĐ/tháng "
                f"+ cắt giảm {cat_giam_co2/1000:.1f} tấn CO₂/tháng"
            ),
        }

    # ------------------------------------------------------------------
    def ket_xuat_bao_cao_kinh_te(self) -> str:
        """Xuất báo cáo phân tích kinh tế ra file text."""
        _dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(os.path.dirname(_dir), '04_DATA',
                            f"BaoCao_KinhTe_{datetime.now().strftime('%Y%m%d_%H%M')}.txt")

        lines = [
            "=" * 65,
            "  BÁO CÁO PHÂN TÍCH KINH TẾ – ECONUDGE GATE",
            f"  Xuất ngày: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            "=" * 65,
            "",
            "1. THÔNG SỐ TÍNH TOÁN (22_4.docx – 19/04/2026)",
            f"   Giá dầu Diesel  : {GIA_DIESEL:,.0f} VNĐ/Lít (Petrolimex Vùng 1)",
            f"   Định mức Idling : {DM_IDLING} Lít/giờ (xe container hạng nặng)",
            f"   Lương tài xế    : {LUONG_TAI_XE:,.0f} VNĐ/giờ",
            f"   Chi phí cơ hội  : {CP_CO_HOI:,.0f} VNĐ/giờ",
            f"   Hệ số CO₂       : {EF_CO2} kg CO₂/Lít (QĐ 2626/QĐ-BTNMT)",
            "",
            "2. THIỆT HẠI MỖI GIỜ MỖI XE",
        ]

        r1 = self.tinh_ton_that_mot_xe(1)
        lines += [
            f"   Nhiên liệu   : {r1['phi_nhien_lieu_vnd']:,.0f} VNĐ",
            f"   Nhân công    : {r1['phi_nhan_cong_vnd']:,.0f} VNĐ",
            f"   Cơ hội + KH  : {r1['chi_phi_co_hoi_vnd']:,.0f} VNĐ",
            f"   TỔNG CỘNG    : {r1['tong_per_gio_vnd']:,.0f} VNĐ/giờ/xe",
            f"   Phát thải CO₂: {r1['co2_per_gio_kg']:,.4f} kg/giờ/xe",
            "",
            "3. PHÂN TÍCH QUY MÔ ĐỘI XE (50 xe × 2h × 26 ngày/tháng)",
        ]

        r2 = self.tinh_ton_that_doi_xe(50, 2)
        lines += [
            f"   Tổng giờ idling : {r2['tong_gio_thang']:,.0f} giờ/tháng",
            f"   Tổng thiệt hại  : {r2['tong_ton_that_vnd']:,.0f} VNĐ/tháng",
            f"   Phát thải CO₂   : {r2['tong_co2_kg']:,.0f} kg/tháng",
            "",
            "4. DỰ BÁO HIỆU QUẢ SAU KHI ÁP DỤNG (Giảm 30%)",
        ]

        r3 = self.du_bao_hieu_qua(50, 2)
        lines += [
            f"   Tiết kiệm tài chính: {r3['tiet_kiem_vnd']:,.0f} VNĐ/tháng",
            f"                      = {r3['tiet_kiem_trieu_vnd']:.1f} triệu VNĐ/tháng",
            f"   Cắt giảm CO₂       : {r3['cat_giam_co2_tan']:.1f} tấn CO₂/tháng",
            "",
            f"  ➡️  {r3['roi_message']}",
            "",
            "=" * 65,
            "  Căn cứ: QĐ 2626/QĐ-BTNMT | GHG Protocol Scope 3",
            "=" * 65,
        ]

        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"[B12] ✅ Báo cáo kinh tế: {path}")
        return path


if __name__ == "__main__":
    pt = PhanTichTonThat()

    print("=" * 60)
    print("  B12: PHÂN TÍCH TỔN THẤT KINH TẾ")
    print("=" * 60)

    print("\n▶ Thiệt hại 1 xe, 1 giờ:")
    r = pt.tinh_ton_that_mot_xe(1)
    for k, v in r.items():
        print(f"  {k:30s}: {v:,.4g}" if isinstance(v, float) else f"  {k:30s}: {v:,}")

    print("\n▶ Đội 50 xe, 2h/ngày, 26 ngày/tháng:")
    r2 = pt.tinh_ton_that_doi_xe(50, 2)
    for k, v in r2.items():
        print(f"  {k:30s}: {v:,.4g}" if isinstance(v, float) else f"  {k:30s}: {v:,}")

    print("\n▶ Dự báo hiệu quả (giảm 30%):")
    r3 = pt.du_bao_hieu_qua(50, 2)
    print(f"  {r3['roi_message']}")

    pt.ket_xuat_bao_cao_kinh_te()
