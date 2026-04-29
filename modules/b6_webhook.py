import requests
import json
import logging

def gui_tin_hieu(payload):
    # Giả lập webhook, có thể thay bằng requests.post nếu có endpoint thật
    logging.info(f"[WEBHOOK] Gửi tin hiệu: {json.dumps(payload, indent=2)}")
    # Ví dụ gửi tới endpoint giả định
    # try:
    #     requests.post('https://your-app.com/webhook', json=payload, timeout=2)
    # except:
    #     pass
    return True