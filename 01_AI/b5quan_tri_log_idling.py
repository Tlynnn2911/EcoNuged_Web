import pandas as pd
import os

class QuanTriLogESG:
    def __init__(self, ten_file="nhat_ky_phat_thai_esg.csv"):
        """
        Nhiệm vụ: Lưu trữ dữ liệu phát thải vào thư mục 04_DATA.
        """
        # Xác định đường dẫn: Từ 01_AI lùi ra ngoài rồi vào 04_DATA
        thu_muc_hien_tai = os.path.dirname(os.path.abspath(__file__))
        self.thu_muc_data = os.path.join(os.path.dirname(thu_muc_hien_tai), '04_DATA')
        self.path_log = os.path.join(self.thu_muc_data, ten_file)
        
        # Tạo thư mục 04_DATA nếu chưa có để tránh lỗi FileNotFoundError
        if not os.path.exists(self.thu_muc_data):
            os.makedirs(self.thu_muc_data)
        
        # Cấu trúc cột chuẩn (Dùng làm danh sách kiểm tra)
        self.cac_cot = [
            "ID_Xe", 
            "Tên_Cảng", 
            "Thời_Điểm_Vào", 
            "Thời_Điểm_Ra", 
            "Tổng_Giây_Chờ", 
            "Lượng_CO2_kg"
        ]

    def ghi_nhat_ky(self, du_lieu):
        """
        Ghi dữ liệu mới vào tệp nhật ký CSV.
        """
        try:
            # Chuyển dữ liệu sang DataFrame
            df_moi = pd.DataFrame([du_lieu])
            
            # Đảm bảo thứ tự cột đúng như cấu trúc chuẩn
            # Nếu du_lieu thiếu cột nào, nó sẽ tự thêm cột đó với giá trị rỗng
            df_moi = df_moi.reindex(columns=self.cac_cot)
            
            # Kiểm tra tệp đã tồn tại chưa
            tep_ton_tai = os.path.exists(self.path_log)
            
            # Ghi vào file (mode='a' là ghi thêm, utf-8-sig để đọc được dấu trên Excel)
            df_moi.to_csv(
                self.path_log, 
                mode='a', 
                header=not tep_ton_tai, 
                index=False, 
                encoding='utf-8-sig'
            )
            print(f"Nhật ký: Đã ghi dữ liệu cho xe {du_lieu.get('ID_Xe')} vào tệp thành công.")
            print(f"Đường dẫn file: {self.path_log}")
            
        except Exception as e:
            print(f"Lỗi hệ thống: Không thể ghi nhật ký. Chi tiết: {e}")

# --- KIỂM TRA THỰC THI ---
if __name__ == "__main__":
    quan_tri = QuanTriLogESG()
    
    # --- PHẦN CUỐI FILE B5 ---
if __name__ == "__main__":
    # Thay vì ghi mẫu, ta chỉ khởi tạo để kiểm tra đường dẫn
    quan_tri = QuanTriLogESG()
    print("Hệ thống: Phân hệ B5 đã sẵn sàng nhận dữ liệu tự động.")
    print(f"File lưu trữ tại: {quan_tri.path_log}")
    