import numpy as np
import pandas as pd

class BoLocGiaTocAI:
    def __init__(self, kich_thuoc_cua_so=20):
        """
        xử lý rung động để xác định trạng thái thực tế của xe.
        - kich_thuoc_cua_so: Độ dài mẫu để tính toán độ ổn định (Sigma).
        """
        self.du_lieu_dem = []
        self.window_size = kich_thuoc_cua_so
        
        # Ngưỡng mặc định (Sẽ được cập nhật sau khi chạy hàm calibrate)
        self.nguong_tinh = 0.05       
        self.nguong_no_may = 0.2     

    def calibrate_tu_file_thuc_te(self, duong_dan_csv):
        """
        Mục tiêu 22/04: Xác lập ngưỡng từ dữ liệu thực tế.
        Đọc file CSV (thoi_gian, rung_doc, rung_ngang, rung_sau, trang_thai_xe).
        """
        try:
            df = pd.read_csv(duong_dan_csv, encoding='utf-8')
            # Lọc lấy các dòng khi xe ở trạng thái TẮT MÁY (TINH)
            df_tinh = df[df['trang_thai_xe'] == 'TINH']
            
            if df_tinh.empty:
                print("⚠️ Cảnh báo: File không có dữ liệu trạng thái 'TINH'.")
                return

            # Tính Cường độ rung tổng hợp (loại bỏ trọng lực 9.8)
            luc_tong_hop = np.sqrt(df_tinh['rung_doc']**2 + df_tinh['rung_ngang']**2 + df_tinh['rung_sau']**2) - 9.8
            sai_so_cam_bien = np.std(luc_tong_hop)
            
            # Tự động thiết lập ngưỡng dựa trên thực tế
            self.nguong_tinh = round(sai_so_cam_bien * 1.5, 4)
            self.nguong_no_may = round(self.nguong_tinh * 4.5, 4)
            
            print(f"--- KẾT QUẢ CÂN CHỈNH AI ---")
            print(f"Ngưỡng Tĩnh: < {self.nguong_tinh}")
            print(f"Ngưỡng Nổ Máy: < {self.nguong_no_may}")
            print(f"---------------------------")
        except Exception as e:
            print(f"❌ Lỗi xử lý file: {e}")

    def phan_loai_trang_thai(self, doc, ngang, sau):
        """
        Nhận 3 hướng rung và trả về kết quả cho IT & Kinh tế.
        """
        # 1. Công thức Magnitude: Giúp AI không phụ thuộc vào hướng đặt điện thoại
        cuong_do_tong_hop = np.sqrt(doc**2 + ngang**2 + sau**2)
        rung_thuan = abs(cuong_do_tong_hop - 9.8)
        
        self.du_lieu_dem.append(rung_thuan)
        
        # Đợi đủ dữ liệu cửa sổ trượt
        if len(self.du_lieu_dem) < self.window_size:
            return "KHOI_TAO", 0
            
        if len(self.du_lieu_dem) > self.window_size:
            self.du_lieu_dem.pop(0)
            
        # 2. Tính Sigma (σ) - Độ ổn định của rung động
        sigma = np.std(self.du_lieu_dem)
        
        # 3. Trả kết quả logic
        if sigma < self.nguong_tinh:
            ket_qua = "TINH_TUYET_DOI"  # App hiện nút "Xác nhận tắt máy"
        elif sigma < self.nguong_no_may:
            ket_qua = "DONG_CO_DANG_NO" # AI tiếp tục tính CO2 phát thải
        else:
            ket_qua = "NHIEU_TAI_XE"    # Bỏ qua rung động do con người
            
        return ket_qua, round(sigma, 4)

# --- DEMO CHẠY THỬ ---
if __name__ == "__main__":
    ai = BoLocGiaTocAI()
    # Giả lập 1 dòng dữ liệu thực tế
    kq, do_on = ai.phan_loai_trang_thai(doc=9.82, ngang=0.01, sau=0.03)
    print(f"AI xác nhận: {kq} (Độ nhiễu: {do_on})")