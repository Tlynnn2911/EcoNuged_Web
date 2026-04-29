import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime

class KetXuatBaoCaoESG:
    def __init__(self, log_path='data/nhat_ky_phat_thai_esg.csv', report_dir='data/reports'):
        self.log_path = log_path
        self.report_dir = report_dir
        os.makedirs(report_dir, exist_ok=True)

    def xuat_toan_bo(self):
        if not os.path.exists(self.log_path):
            return {'excel': None, 'pdf': None}
        df = pd.read_csv(self.log_path)
        excel_path = os.path.join(self.report_dir, f"esg_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        df.to_excel(excel_path, index=False)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Bao cao ESG - EcoNudge Gate v3", ln=1, align='C')
        pdf.cell(200, 10, txt=f"Ngay xuat: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=1)
        pdf.cell(200, 10, txt=f"Tong so luot idling: {len(df)}", ln=1)
        pdf.cell(200, 10, txt=f"Tong CO2 (kg): {df['Lượng_CO2_kg'].sum():.2f}", ln=1)
        pdf_path = os.path.join(self.report_dir, f"esg_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        pdf.output(pdf_path)
        return {'excel': excel_path, 'pdf': pdf_path}