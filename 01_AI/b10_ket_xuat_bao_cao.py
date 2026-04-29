"""
B10 – Kết xuất Báo cáo Phát thải ESG (Scope 3)
Đã sửa lỗi dữ liệu âm, dùng font mặc định (không cần DejaVuSans).
"""

import os
import json
from datetime import datetime
import pandas as pd

def _thu_muc_data():
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '04_DATA'
    )

def _thu_muc_json():
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '03_JSON'
    )

class KetXuatBaoCaoESG:
    def __init__(self):
        self.path_log = os.path.join(_thu_muc_data(), 'nhat_ky_phat_thai_esg.csv')
        self.path_config = os.path.join(_thu_muc_json(), 'cau_hinh_phat_thai.json')
        self.config = self._nap_config()
        self.ngay_xuat = datetime.now().strftime('%Y%m%d_%H%M')

    def _nap_config(self) -> dict:
        with open(self.path_config, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _nap_log(self) -> pd.DataFrame:
        if not os.path.exists(self.path_log):
            raise FileNotFoundError(f"Không tìm thấy file log: {self.path_log}")
        df = pd.read_csv(self.path_log, encoding='utf-8-sig')
        df.columns = [c.strip() for c in df.columns]
        
        # Làm sạch dữ liệu: loại bỏ giá trị âm và outlier
        if "Tổng_Giây_Chờ" in df.columns:
            df["Tổng_Giây_Chờ"] = df["Tổng_Giây_Chờ"].abs()
            df = df[df["Tổng_Giây_Chờ"] <= 86400]  # bỏ nếu > 24h
        if "Lượng_CO2_kg" in df.columns:
            df["Lượng_CO2_kg"] = df["Lượng_CO2_kg"].abs()
        return df

    def tong_hop_scope3(self, df: pd.DataFrame) -> dict:
        if df.empty:
            return {}
        tong_co2 = df["Lượng_CO2_kg"].sum()
        tong_gio = df["Tổng_Giây_Chờ"].sum() / 3600
        so_su_kien = len(df)
        so_xe = df["ID_Xe"].nunique()
        theo_cang = df.groupby("Tên_Cảng")["Lượng_CO2_kg"].sum().to_dict()
        return {
            "ky_bao_cao": datetime.now().strftime("%Y-%m"),
            "tieu_chuan": "GHG Protocol – Scope 3 Category 4",
            "nguon_he_so": self.config.get("nguon_phap_ly", "QĐ 2626/QĐ-BTNMT"),
            "ef_diesel": self.config.get("he_so_ef_diesel", 2.683),
            "don_vi": "kg CO2e",
            "tong_co2_kg": round(tong_co2, 4),
            "tong_co2_tan": round(tong_co2 / 1000, 6),
            "tong_gio_idling": round(tong_gio, 2),
            "so_su_kien": so_su_kien,
            "so_xe_giam_sat": so_xe,
            "phan_bo_theo_cang": {k: round(v, 4) for k, v in theo_cang.items()},
        }

    def xuat_excel(self) -> str:
        df = self._nap_log()
        if df.empty:
            raise ValueError("Không có dữ liệu hợp lệ để xuất báo cáo.")
        tom_tat = self.tong_hop_scope3(df)
        ten_file = f"BaoCao_ESG_Scope3_{self.ngay_xuat}.xlsx"
        path_out = os.path.join(_thu_muc_data(), ten_file)
        with pd.ExcelWriter(path_out, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Chi_Tiet_Su_Kien', index=False)
            df_tomtat = pd.DataFrame([{"Chỉ số": k, "Giá trị": v} for k, v in tom_tat.items() if not isinstance(v, dict)])
            df_tomtat.to_excel(writer, sheet_name='Tong_Hop_Scope3', index=False)
            df_cang = pd.DataFrame([{"Tên Cảng": k, "CO2 (kg)": v} for k, v in tom_tat["phan_bo_theo_cang"].items()])
            df_cang.to_excel(writer, sheet_name='Phan_Bo_Theo_Cang', index=False)
            kpi_path = os.path.join(_thu_muc_data(), 'kpi_bang_xep_hang.csv')
            if os.path.exists(kpi_path):
                df_kpi = pd.read_csv(kpi_path, encoding='utf-8-sig')
                df_kpi.to_excel(writer, sheet_name='KPI_Tai_Xe', index=False)
        print(f"[B10] ✅ Xuất Excel thành công: {path_out}")
        return path_out

    def xuat_pdf(self) -> str:
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
        except ImportError:
            print("[B10] ⚠️ reportlab chưa cài. Chạy: pip install reportlab")
            return ""

        df = self._nap_log()
        if df.empty:
            raise ValueError("Không có dữ liệu hợp lệ để xuất báo cáo.")
        tom_tat = self.tong_hop_scope3(df)
        ten_file = f"BaoCao_ESG_Scope3_{self.ngay_xuat}.pdf"
        path_out = os.path.join(_thu_muc_data(), ten_file)

        doc = SimpleDocTemplate(path_out, pagesize=A4,
                                topMargin=2*cm, bottomMargin=2*cm,
                                leftMargin=2*cm, rightMargin=2*cm)
        story = []
        styles = getSampleStyleSheet()

        # Dùng font mặc định Helvetica (không cần font ngoài, tránh lỗi)
        XANH = colors.HexColor('#1A7A4A')

        style_tieude = ParagraphStyle('tieude', parent=styles['Title'],
                                       fontSize=18, textColor=XANH,
                                       spaceAfter=4, alignment=TA_CENTER)
        style_phude = ParagraphStyle('phude', parent=styles['Normal'],
                                      fontSize=10, textColor=colors.grey,
                                      spaceAfter=12, alignment=TA_CENTER)
        style_mucdo = ParagraphStyle('mucdo', parent=styles['Heading2'],
                                      fontSize=13, textColor=XANH,
                                      spaceBefore=14, spaceAfter=4)
        style_vb = ParagraphStyle('vb', parent=styles['Normal'],
                                   fontSize=10, leading=14)

        story.append(Paragraph("BÁO CÁO PHÁT THẢI KHÍ NHÀ KÍNH", style_tieude))
        story.append(Paragraph("EcoNudge Gate – Hành lang Logistics Hải Phòng", style_phude))
        story.append(Paragraph(f"Kỳ báo cáo: {tom_tat['ky_bao_cao']}  |  Xuất ngày: {datetime.now().strftime('%d/%m/%Y %H:%M')}", style_phude))
        story.append(HRFlowable(width="100%", thickness=1.5, color=XANH))
        story.append(Spacer(1, 0.4*cm))

        story.append(Paragraph("1. PHẠM VI & TIÊU CHUẨN ÁP DỤNG", style_mucdo))
        story.append(Paragraph(
            f"• Tiêu chuẩn: <b>{tom_tat['tieu_chuan']}</b><br/>"
            f"• Hệ số phát thải Diesel: <b>{tom_tat['ef_diesel']} kg CO₂/Lít</b><br/>"
            f"• Căn cứ pháp lý: <b>{tom_tat['nguon_he_so']}</b><br/>"
            f"• Đơn vị tính: <b>{tom_tat['don_vi']}</b>",
            style_vb
        ))

        story.append(Paragraph("2. KẾT QUẢ PHÁT THẢI TỔNG HỢP", style_mucdo))
        data_tt = [
            ["Chỉ số", "Giá trị"],
            ["Tổng phát thải (Scope 3)", f"{tom_tat['tong_co2_kg']:,.4f} kg CO₂e  =  {tom_tat['tong_co2_tan']:,.6f} tấn CO₂e"],
            ["Tổng thời gian nổ máy chờ", f"{tom_tat['tong_gio_idling']:,.2f} giờ"],
            ["Số sự kiện Idling ghi nhận", f"{tom_tat['so_su_kien']} sự kiện"],
            ["Số xe được giám sát", f"{tom_tat['so_xe_giam_sat']} xe"],
        ]
        tbl = Table(data_tt, colWidths=[8*cm, 9*cm])
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), XANH),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F0FFF4'), colors.white]),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(tbl)

        if tom_tat.get("phan_bo_theo_cang"):
            story.append(Paragraph("3. PHÂN BỔ PHÁT THẢI THEO CỤM CẢNG", style_mucdo))
            data_cang = [["Cụm Cảng / Khu vực", "CO₂ Phát thải (kg)"]]
            for ten, co2 in tom_tat["phan_bo_theo_cang"].items():
                data_cang.append([ten, f"{co2:,.4f}"])
            tbl2 = Table(data_cang, colWidths=[11*cm, 6*cm])
            tbl2.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), XANH),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F0FFF4'), colors.white]),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(tbl2)

        story.append(Spacer(1, 1*cm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        story.append(Paragraph(
            "Báo cáo được tạo tự động bởi hệ thống EcoNudge Gate. Dữ liệu sử dụng hệ số phát thải theo Quyết định 2626/QĐ-BTNMT.",
            ParagraphStyle('footer', parent=styles['Normal'],
                           fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
        ))

        doc.build(story)
        print(f"[B10] ✅ Xuất PDF thành công: {path_out}")
        return path_out

    def xuat_toan_bo(self) -> dict:
        print("[B10] Bắt đầu kết xuất báo cáo ESG Scope 3...")
        excel = None
        pdf = None
        try:
            excel = self.xuat_excel()
        except Exception as e:
            print(f"[B10] Lỗi xuất Excel: {e}")
        try:
            pdf = self.xuat_pdf()
        except Exception as e:
            print(f"[B10] Lỗi xuất PDF: {e}")
        return {"excel": excel, "pdf": pdf}