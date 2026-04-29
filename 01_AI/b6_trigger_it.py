import json
import os
import requests

def lay_url_tu_config():
    """Đọc URL webhook từ file config 03_JSON/config_he_thong.json."""
    duong_dan = os.path.join(os.path.dirname(__file__), '..', '03_JSON', 'config_he_thong.json')
    try:
        with open(duong_dan, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("url_app_it", "http://localhost:5000/eco-nudge-trigger")
    except Exception:
        return "http://localhost:5000/eco-nudge-trigger"

def gui_tin_hieu(ban_ghi: dict) -> bool:
    """
    Đẩy sự kiện IDLING sang App.
    Trả về True nếu thành công, False nếu lỗi (offline/demo mode).
    
    Cấu trúc ban_ghi:
    {
        "id_xe": str,
        "ten_cang": str,
        "thoi_diem": str (ISO),
        "trang_thai": "BAT_DAU_IDLING" | "KET_THUC_IDLING",
        "co2_kg": float  (tùy chọn)
    }
    """
    url = lay_url_tu_config()
    print(f"[B6] Webhook → {url}  |  Sự kiện: {ban_ghi.get('trang_thai')}")
    try:
        res = requests.post(url, json=ban_ghi, timeout=3)
        print(f"[B6] Server phản hồi: HTTP {res.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print("[B6] OFFLINE – Lưu sự kiện vào hàng đợi cục bộ (demo mode)")
        _luu_hang_doi_cu_bo(ban_ghi)
        return False
    except Exception as e:
        print(f"[B6] Lỗi không xác định: {e}")
        return False

def _luu_hang_doi_cu_bo(ban_ghi: dict):
    """Lưu sự kiện chưa gửi được vào file pending để gửi lại sau."""
    import json
    pending_path = os.path.join(os.path.dirname(__file__), '..', '04_DATA', 'pending_webhook.jsonl')
    with open(pending_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(ban_ghi, ensure_ascii=False) + '\n')

def gui_lai_hang_doi():
    """Gửi lại các sự kiện bị lưu tạm trong pending_webhook.jsonl."""
    pending_path = os.path.join(os.path.dirname(__file__), '..', '04_DATA', 'pending_webhook.jsonl')
    if not os.path.exists(pending_path):
        return
    with open(pending_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    thanh_cong = []
    for line in lines:
        try:
            ban_ghi = json.loads(line.strip())
            if gui_tin_hieu(ban_ghi):
                thanh_cong.append(line)
        except Exception:
            pass
    # Xoá những dòng đã gửi thành công
    con_lai = [l for l in lines if l not in thanh_cong]
    with open(pending_path, 'w', encoding='utf-8') as f:
        f.writelines(con_lai)
    print(f"[B6] Đã xử lý hàng đợi: {len(thanh_cong)}/{len(lines)} sự kiện gửi thành công.")

if __name__ == "__main__":
    ban_ghi_test = {
        "id_xe": "15H-TEST.01",
        "ten_cang": "Tan Vu Port",
        "thoi_diem": "2026-04-22T10:30:00",
        "trang_thai": "BAT_DAU_IDLING",
        "co2_kg": 0.992
    }
    gui_tin_hieu(ban_ghi_test)
