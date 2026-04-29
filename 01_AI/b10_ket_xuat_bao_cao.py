"""
B10 – Kết xuất Báo cáo Phát thải ESG (Scope 3)
================================================
Phân hệ 3 – Định lượng & Kết xuất dữ liệu

Xuất 2 định dạng:
  1. Excel (.xlsx) – bảng chi tiết từng sự kiện + sheet tổng hợp KPI
  2. PDF  (.pdf)  – báo cáo ESG chuẩn để nộp kiểm toán quốc tế

Tiêu chuẩn: GHG Protocol / Scope 3 Category 4 (Upstream Transportation)
Hệ số phát thải: QĐ 2626/QĐ-BTNMT (EF Diesel = 2.683 kg CO2/Lít)
"""

import os
import json
from datetime import datetime
import pandas as pd

# ---------------------------------------------------------------------------
# Thư mục đầu ra
# ---------------------------------------------------------------------------
def _thu_muc_data():
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '04_DATA'
    )

def _thu_muc_json():
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '03_JSON'
    )


# ---------------------------------------------------------------------------
class KetXuatBaoCaoESG:
    """Tổng hợp và xuất báo cáo phát thải chuẩn Scope 3."""

    def __init__(self):
        self.path_log    = os.path.join(_thu_muc_data(), 'nhat_ky_phat_thai_esg.csv')
        self.path_config = os.path.join(_thu_muc_json(), 'cau_hinh_phat_thai.json')
        self.config      = self._nap_config()
        self.ngay_xuat   = datetime.now().strftime('%Y%m%d_%H%M')

    def _nap_config(self) -> dict:
        with open(self.path_config, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _nap_log(self) -> pd.DataFrame:
        if not os.path.exists(self.path_log):
            raise FileNotFoundError(f"Không tìm thấy file log: {self.path_log}")
        df = pd.read_csv(self.path_log, encoding='utf-8-sig')
        df.columns = [c.strip() for c in df.columns]
        return df

    # ------------------------------------------------------------------
    # 1. Tổng hợp số liệu
    # ------------------------------------------------------------------
    def tong_hop_scope3(self, df: pd.DataFrame) -> dict:
        """Tổng hợp các chỉ số chính cho báo cáo Scope 3."""
        tong_co2     = df["Lượng_CO2_kg"].sum()
        tong_gio     = df["Tổng_Giây_Chờ"].sum() / 3600
        so_su_kien   = len(df)
        so_xe        = df["ID_Xe"].nunique()
        # Phân loại theo cụm cảng
        theo_cang    = df.groupby("Tên_Cảng")["Lượng_CO2_kg"].sum().to_dict()

        return {
            "ky_bao_cao"       : datetime.now().strftime("%Y-%m"),
            "tieu_chuan"       : "GHG Protocol – Scope 3 Category 4",
            "nguon_he_so"      : self.config.get("nguon_phap_ly", ""),
            "ef_diesel"        : self.config.get("he_so_ef_diesel", 2.683),
            "don_vi"           : "kg CO2e",
            "tong_co2_kg"      : round(tong_co2, 4),
            "tong_co2_tan"     : round(tong_co2 / 1000, 6),
            "tong_gio_idling"  : round(tong_gio, 2),
            "so_su_kien"       : so_su_kien,
            "so_xe_giam_sat"   : so_xe,
            "phan_bo_theo_cang": {k: round(v, 4) for k, v in theo_cang.items()},
        }

    # ------------------------------------------------------------------
    # 2. Xuất Excel
    # ------------------------------------------------------------------
    def xuat_excel(self) -> str:
        df = self._nap_log()
        tom_tat = self.tong_hop_scope3(df)
        ten_file = f"BaoCao_ESG_Scope3_{self.ngay_xuat}.xlsx"
        path_out = os.path.join(_thu_muc_data(), ten_file)

        with pd.ExcelWriter(path_out, engine='openpyxl') as writer:
            # Sheet 1: Chi tiết từng sự kiện
            df.to_excel(writer, sheet_name='Chi_Tiet_Su_Kien', index=False)

            # Sheet 2: Tổng hợp Scope 3
            df_tomtat = pd.DataFrame([{
                "Chỉ số"   : k,
                "Giá trị"  : v
            } for k, v in tom_tat.items() if not isinstance(v, dict)])
            df_tomtat.to_excel(writer, sheet_name='Tong_Hop_Scope3', index=False)

            # Sheet 3: Phân bổ theo cảng
            df_cang = pd.DataFrame([
                {"Tên Cảng": k, "CO2 (kg)": v}
                for k, v in tom_tat["phan_bo_theo_cang"].items()
            ])
            df_cang.to_excel(writer, sheet_name='Phan_Bo_Theo_Cang', index=False)

            # Sheet 4: KPI tài xế (nếu có)
            kpi_path = os.path.join(_thu_muc_data(), 'kpi_bang_xep_hang.csv')
            if os.path.exists(kpi_path):
                df_kpi = pd.read_csv(kpi_path, encoding='utf-8-sig')
                df_kpi.to_excel(writer, sheet_name='KPI_Tai_Xe', index=False)

        print(f"[B10] ✅ Xuất Excel thành công: {path_out}")
        return path_out

    # ------------------------------------------------------------------
    # 3. Xuất PDF (dùng reportlab)
    # ------------------------------------------------------------------
    def xuat_pdf(self) -> str:
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
            )
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
        except ImportError:
            print("[B10] ⚠️ reportlab chưa cài. Chạy: pip install reportlab --break-system-packages")
            return ""

        df      = self._nap_log()
        tom_tat = self.tong_hop_scope3(df)
        ten_file = f"BaoCao_ESG_Scope3_{self.ngay_xuat}.pdf"
        path_out = os.path.join(_thu_muc_data(), ten_file)

        doc   = SimpleDocTemplate(path_out, pagesize=A4,
                                  topMargin=2*cm, bottomMargin=2*cm,
                                  leftMargin=2*cm, rightMargin=2*cm)
        story = []
        styles = getSampleStyleSheet()

        # Màu xanh thương hiệu
        XANH = colors.HexColor('#1A7A4A')

        style_tieude = ParagraphStyle('tieude', parent=styles['Title'],
                                       fontSize=18, textColor=XANH,
                                       spaceAfter=4, alignment=TA_CENTER)
        style_phude  = ParagraphStyle('phude',  parent=styles['Normal'],
                                       fontSize=10, textColor=colors.grey,
                                       spaceAfter=12, alignment=TA_CENTER)
        style_mucdo  = ParagraphStyle('mucdo',  parent=styles['Heading2'],
                                       fontSize=13, textColor=XANH,
                                       spaceBefore=14, spaceAfter=4)
        style_vb     = ParagraphStyle('vb',     parent=styles['Normal'],
                                       fontSize=10, leading=14)

        # --- Tiêu đề ---
        story.append(Paragraph("BÁO CÁO PHÁT THẢI KHÍ NHÀ KÍNH", style_tieude))
        story.append(Paragraph("EcoNudge Gate – Hành lang Logistics Hải Phòng", style_phude))
        story.append(Paragraph(f"Kỳ báo cáo: {tom_tat['ky_bao_cao']}  |  "
                                f"Xuất ngày: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                                style_phude))
        story.append(HRFlowable(width="100%", thickness=1.5, color=XANH))
        story.append(Spacer(1, 0.4*cm))

        # --- Mục 1: Phạm vi & Tiêu chuẩn ---
        story.append(Paragraph("1. PHẠM VI & TIÊU CHUẨN ÁP DỤNG", style_mucdo))
        story.append(Paragraph(
            f"• Tiêu chuẩn: <b>{tom_tat['tieu_chuan']}</b><br/>"
            f"• Hệ số phát thải Diesel: <b>{tom_tat['ef_diesel']} kg CO₂/Lít</b><br/>"
            f"• Căn cứ pháp lý: <b>{tom_tat['nguon_he_so']}</b><br/>"
            f"• Đơn vị tính: <b>{tom_tat['don_vi']}</b>",
            style_vb
        ))

        # --- Mục 2: Kết quả tổng hợp ---
        story.append(Paragraph("2. KẾT QUẢ PHÁT THẢI TỔNG HỢP", style_mucdo))
        data_tt = [
            ["Chỉ số", "Giá trị"],
            ["Tổng phát thải (Scope 3)",
             f"{tom_tat['tong_co2_kg']:,.4f} kg CO₂e  =  {tom_tat['tong_co2_tan']:,.6f} tấn CO₂e"],
            ["Tổng thời gian nổ máy chờ",
             f"{tom_tat['tong_gio_idling']:,.2f} giờ"],
            ["Số sự kiện Idling ghi nhận",
             f"{tom_tat['so_su_kien']} sự kiện"],
            ["Số xe được giám sát",
             f"{tom_tat['so_xe_giam_sat']} xe"],
        ]
        tbl = Table(data_tt, colWidths=[8*cm, 9*cm])
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), XANH),
            ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
            ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0, 0), (-1,-1), 10),
            ('GRID',       (0, 0), (-1,-1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 1), (-1,-1),
             [colors.HexColor('#F0FFF4'), colors.white]),
            ('PADDING',    (0, 0), (-1,-1), 6),
        ]))
        story.append(tbl)

        # --- Mục 3: Phân bổ theo cảng ---
        story.append(Paragraph("3. PHÂN BỔ PHÁT THẢI THEO CỤM CẢNG", style_mucdo))
        data_cang = [["Cụm Cảng / Khu vực", "CO₂ Phát thải (kg)"]]
        for ten, co2 in tom_tat["phan_bo_theo_cang"].items():
            data_cang.append([ten, f"{co2:,.4f}"])
        tbl2 = Table(data_cang, colWidths=[11*cm, 6*cm])
        tbl2.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), XANH),
            ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
            ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0, 0), (-1,-1), 10),
            ('GRID',       (0, 0), (-1,-1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 1), (-1,-1),
             [colors.HexColor('#F0FFF4'), colors.white]),
            ('PADDING',    (0, 0), (-1,-1), 6),
        ]))
        story.append(tbl2)

        # --- Chữ ký ---
        story.append(Spacer(1, 1*cm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        story.append(Paragraph(
            "Báo cáo được tạo tự động bởi hệ thống EcoNudge Gate. "
            "Dữ liệu sử dụng hệ số phát thải theo Quyết định 2626/QĐ-BTNMT "
            "của Bộ Tài nguyên & Môi trường Việt Nam.",
            ParagraphStyle('footer', parent=styles['Normal'],
                           fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
        ))

        doc.build(story)
        print(f"[B10] ✅ Xuất PDF thành công: {path_out}")
        return path_out

    # ------------------------------------------------------------------
    # 4. Xuất toàn bộ (Excel + PDF)
    # ------------------------------------------------------------------
    def xuat_toan_bo(self) -> dict:
        """Xuất cả Excel và PDF, trả về dict chứa đường dẫn."""
        print("[B10] Bắt đầu kết xuất báo cáo ESG Scope 3...")
        return {
            "excel": self.xuat_excel(),
            "pdf"  : self.xuat_pdf(),
        }


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    xuat = KetXuatBaoCaoESG()
    ket_qua = xuat.xuat_toan_bo()
    print("\nTóm tắt:")
    for dinh_dang, duong_dan in ket_qua.items():
        print(f"  [{dinh_dang.upper()}] → {duong_dan}")
