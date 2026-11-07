"""
ROG Delta II (2.4G 接收器) 電量讀取核心。

協定（由實機探測得出）：
  - 裝置：VID 0x0B05 / PID 0x1AFA，Usage Page 0xFF00 的 HID 介面
  - 查詢：寫入 64 bytes，內容 CC 12 09 00 ...（其餘補 0）
  - 回應：64 bytes，CC 12 09 00 00 <電量%> 00 ...
    耳機連線時也會主動推送同格式的封包。
  - 充電狀態：CC 12 08 00 00 <0/1> 00 ...
    插拔充電線時耳機會主動推送（已由實機確認）。
    哪個值代表「充電中」由 CHARGING_VALUE 決定；目前假設為 1，
    若發現圖示顯示相反，把它改成 0 即可。
"""
import hid

VID, PID = 0x0B05, 0x1AFA
USAGE_PAGE = 0xFF00
REPORT_LEN = 64
CHARGING_VALUE = 1

_QUERIES = [
    [0xCC, 0x12, 0x09] + [0x00] * (REPORT_LEN - 3),  # 電量
    [0xCC, 0x12, 0x08] + [0x00] * (REPORT_LEN - 3),  # 充電狀態
]


def parse_battery(data):
    """從一筆 HID 輸入回報解出電量百分比；不是電量封包則回傳 None。"""
    if len(data) < 6:
        return None
    if data[0] != 0xCC or data[1] != 0x12 or data[2] != 0x09:
        return None
    pct = data[5]
    if 0 <= pct <= 100:
        return pct
    return None


def parse_charging(data):
    """解出是否充電中（True/False）；不是充電狀態封包則回傳 None。"""
    if len(data) < 6:
        return None
    if data[0] != 0xCC or data[1] != 0x12 or data[2] != 0x08:
        return None
    if data[5] not in (0, 1):
        return None
    return data[5] == CHARGING_VALUE


class BatteryReader:
    def __init__(self):
        self.dev = None

    @property
    def is_open(self):
        return self.dev is not None

    def open(self):
        """找到接收器的 0xFF00 介面並開啟；成功回傳 True。"""
        try:
            for info in hid.enumerate(VID, PID):
                if info.get("usage_page") == USAGE_PAGE:
                    dev = hid.device()
                    dev.open_path(info["path"])
                    dev.set_nonblocking(True)
                    self.dev = dev
                    return True
        except (OSError, ValueError):
            pass
        return False

    def close(self):
        if self.dev is not None:
            try:
                self.dev.close()
            except Exception:
                pass
            self.dev = None

    def send_query(self):
        for q in _QUERIES:
            if self.dev.write(list(q)) < 0:
                raise OSError("write failed")

    def read_status(self):
        """讀完目前佇列中的回報，回傳最新的 (電量, 充電中)；沒收到的項目為 None。"""
        pct = None
        charging = None
        for _ in range(32):
            data = self.dev.read(REPORT_LEN)
            if not data:
                break
            p = parse_battery(data)
            if p is not None:
                pct = p
            c = parse_charging(data)
            if c is not None:
                charging = c
        return pct, charging
