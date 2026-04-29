class BoDoTuanThuAI:
    def __init__(self):
        self.moc1 = False  # Xác nhận đã idling >=600s
        self.moc2 = False  # Tuyệt đối rời cảng
        self.moc3 = False  # Hoàn thành chu trình

    def ghi_nhan_moc_1(self):
        self.moc1 = True
        print("[Compliance] Mốc 1: Idling vượt ngưỡng 600s")

    def ghi_nhan_moc_2(self, loai_tuan_thu="TINH_TUYET_DOI"):
        self.moc2 = True
        print(f"[Compliance] Mốc 2: {loai_tuan_thu} - Rời cảng")

    def ghi_nhan_moc_3(self):
        self.moc3 = True
        print("[Compliance] Mốc 3: Hoàn thành chu trình ESG")