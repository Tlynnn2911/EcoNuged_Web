import time
from datetime import datetime

class BoDoTuanThuAI:
    def __init__(self):
        # 3 mốc thời gian quan trọng theo yêu cầu
        self.moc_1_phat_canh_bao = None
        self.moc_2_tat_may_thuc_te = None
        self.moc_3_roi_cang = None
        
        self.da_tat_may = False

    def ghi_nhan_moc_1(self):
        """(1) Thời điểm phát cảnh báo Idling"""
        self.moc_1_phat_canh_bao = datetime.now()
        print(f"⏰ [MỐC 1] Phát cảnh báo lúc: {self.moc_1_phat_canh_bao.strftime('%H:%M:%S')}")

    def ghi_nhan_moc_2(self, trang_thai_gia_toc):
        """(2) Thời điểm tắt máy thực tế (Dựa vào file b7)"""
        if trang_thai_gia_toc == "TINH_TUYET_DOI" and self.moc_1_phat_canh_bao:
            if not self.da_tat_may:
                self.moc_2_tat_may_thuc_te = datetime.now()
                self.da_tat_may = True
                
                # Tính độ trễ phản hồi của tài xế (Buffer thời gian)
                do_tre = (self.moc_2_tat_may_thuc_te - self.moc_1_phat_canh_bao).total_seconds()
                print(f"✅ [MỐC 2] Xác nhận tắt máy thực tế sau: {round(do_tre, 1)} giây.")
                return round(do_tre, 1)
        return None

    def ghi_nhan_moc_3(self):
        """(3) Thời gian ngắt máy cho đến khi rời cảng"""
        if self.da_tat_may:
            self.moc_3_roi_cang = datetime.now()
            
            # Tính tổng thời gian tắt máy chờ (Thời gian ngắt máy)
            tong_thoi_gian_ngat_may = (self.moc_3_roi_cang - self.moc_2_tat_may_thuc_te).total_seconds()
            print(f"🚢 [MỐC 3] Xe rời cảng. Tổng thời gian ngắt máy bảo vệ môi trường: {round(tong_thoi_gian_ngat_may, 1)} giây.")
            return round(tong_thoi_gian_ngat_may, 1)
        return 0

# --- PHẦN CHẠY THỬ ĐỂ MINH KIỂM TRA ---
if __name__ == "__main__":
    dong_ho = BoDoTuanThuAI()
    
    # Giả lập quy trình
    dong_ho.ghi_nhan_moc_1() # Bước 1: Phát cảnh báo
    time.sleep(2)            # Giả lập 2 giây sau tài xế mới tắt máy
    dong_ho.ghi_nhan_moc_2("TINH_TUYET_DOI") # Bước 2: B7 báo xe tĩnh
    time.sleep(3)            # Giả lập 3 giây sau xe mới rời cảng
    dong_ho.ghi_nhan_moc_3() # Bước 3: Rời cảng