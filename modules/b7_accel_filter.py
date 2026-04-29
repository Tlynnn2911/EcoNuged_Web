class BoLocGiaTocAI:
    def __init__(self, nguong_nhieu=0.5):
        self.nguong_nhieu = nguong_nhieu
        self.last_state = "ON_DINH"

    def phan_loai_trang_thai(self, gia_toc_x, gia_toc_y, gia_toc_z):
        # Lọc nhiễu đơn giản: nếu tổng gia tốc nhỏ -> tĩnh
        magnitude = (gia_toc_x**2 + gia_toc_y**2 + gia_toc_z**2)**0.5
        if magnitude < self.nguong_nhieu:
            self.last_state = "TINH"
        else:
            self.last_state = "DA_DONG"
        return self.last_state