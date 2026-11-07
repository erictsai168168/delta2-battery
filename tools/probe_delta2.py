"""
ROG Delta II (2.4G dongle) HID 探測工具
VID 0x0B05 / PID 0x1AFA

用法（Windows，需 Python 3.9+）：
    pip install hidapi
    python probe_delta2.py            # 被動監聽 20 秒 + 讀取 feature report
    python probe_delta2.py --listen 60   # 監聽 60 秒
    python probe_delta2.py --no-feature  # 不讀 feature report，只被動監聽

此腳本只「讀取」資料，不會對耳機寫入任何指令。
結果會同時存成 probe_result.txt，請把它的內容貼給我。

建議操作：執行時，順便做這幾件事讓資料有變化：
  1. 開/關耳機電源（或重新插拔接收器）
  2. 調整音量、按靜音鍵
  3. 插上/拔掉充電線
"""
import argparse
import sys
import threading
import time

try:
    import hid
except ImportError:
    print("找不到 hid 模組，請先執行：pip install hidapi")
    sys.exit(1)

VID, PID = 0x0B05, 0x1AFA
LOG = []


def out(msg=""):
    print(msg)
    LOG.append(msg)


def hexs(data):
    return " ".join(f"{b:02X}" for b in data)


def listen(info, seconds):
    path = info["path"]
    tag = f"MI_{info['interface_number']:02d} UP=0x{info['usage_page']:04X} U=0x{info['usage']:04X}"
    try:
        dev = hid.device()
        dev.open_path(path)
        dev.set_nonblocking(True)
    except Exception as e:
        out(f"[{tag}] 無法開啟：{e}")
        return
    out(f"[{tag}] 開始監聽 {seconds} 秒…")
    end = time.time() + seconds
    last = None
    count = 0
    while time.time() < end:
        try:
            data = dev.read(128)
        except Exception as e:
            out(f"[{tag}] 讀取錯誤：{e}")
            break
        if data:
            if data != last:  # 只記錄有變化的
                out(f"[{tag}] {time.strftime('%H:%M:%S')} len={len(data)}  {hexs(data)}")
                last = data
            count += 1
        else:
            time.sleep(0.005)
    out(f"[{tag}] 結束，共收到 {count} 筆回報")
    dev.close()


def feature_scan(info):
    tag = f"MI_{info['interface_number']:02d} UP=0x{info['usage_page']:04X}"
    try:
        dev = hid.device()
        dev.open_path(info["path"])
    except Exception as e:
        out(f"[{tag}] feature 掃描無法開啟：{e}")
        return
    found = 0
    for rid in range(0, 256):
        try:
            data = dev.get_feature_report(rid, 64)
        except Exception:
            continue
        if data and any(data[1:]):
            out(f"[{tag}] feature report id=0x{rid:02X}: {hexs(data)}")
            found += 1
    if not found:
        out(f"[{tag}] 沒有可讀的 feature report")
    dev.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--listen", type=int, default=20)
    ap.add_argument("--no-feature", action="store_true")
    args = ap.parse_args()

    devs = hid.enumerate(VID, PID)
    if not devs:
        out("找不到裝置，請確認接收器已插上且耳機已開機。")
        sys.exit(1)

    out(f"找到 {len(devs)} 個 HID 介面：")
    for d in devs:
        out(
            f"  MI_{d['interface_number']:02d}  UP=0x{d['usage_page']:04X}  "
            f"U=0x{d['usage']:04X}  product={d.get('product_string')!r}"
        )
        out(f"      path={d['path']}")
    out()

    if not args.no_feature:
        out("== Feature report 掃描 ==")
        for d in devs:
            if d["usage_page"] >= 0xFF00:
                feature_scan(d)
        out()

    out(f"== 被動監聽（{args.listen} 秒）— 現在請開關耳機、調音量、插拔充電線 ==")
    threads = []
    for d in devs:
        t = threading.Thread(target=listen, args=(d, args.listen), daemon=True)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    with open("probe_result.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(LOG))
    out("\n已存到 probe_result.txt，請把內容貼給我。")


if __name__ == "__main__":
    main()
