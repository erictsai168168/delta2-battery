"""
ROG Delta II (2.4G dongle) 電量查詢探測工具 v2
VID 0x0B05 / PID 0x1AFA，目標介面：UP=0xFF00 (MI_03 Col04)

用法（Windows）：
    pip install hidapi
    python probe_delta2_query.py              # 階段 1：只送 CC 12 09（最保守）
    python probe_delta2_query.py --stage 2    # 階段 2：再嘗試 CC 12 00（需先確認階段 1 沒反應）

執行前請：
  1. 關閉 Armoury Crate 及華碩背景服務
  2. 耳機開機、已連上接收器
  3. 記下此刻 Armoury Crate 顯示的電量 %（腳本會問你）

腳本送出任何封包之前，會先列出內容並等你按 Enter。
結果存成 probe_query_result.txt，請貼給我。
"""
import argparse
import sys
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


def pad(prefix, length):
    return list(prefix) + [0] * (length - len(prefix))


def drain(dev, seconds):
    """讀取 seconds 秒內所有回報，回傳清單。"""
    got = []
    end = time.time() + seconds
    while time.time() < end:
        d = dev.read(128)
        if d:
            got.append(d)
        else:
            time.sleep(0.005)
    return got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", type=int, default=1, choices=[1, 2])
    args = ap.parse_args()

    out(f"耳機目前在 Armoury Crate 顯示的電量：", )
    pct = input("請輸入電量 %（不確定就直接 Enter）：").strip()
    out(f"使用者回報電量：{pct or '未提供'}%")

    path = None
    for d in hid.enumerate(VID, PID):
        if d["usage_page"] == 0xFF00:
            path = d["path"]
    if path is None:
        out("找不到 UP=0xFF00 介面，請確認接收器已插上。")
        sys.exit(1)

    # 要送的查詢封包（第一個 byte 是 Report ID 0xCC，第 2 byte 0x12 是命令類別）
    queries = [("電量候選欄位 09", [0xCC, 0x12, 0x09])]
    if args.stage >= 2:
        queries.append(("狀態欄位 00", [0xCC, 0x12, 0x00]))

    out("\n即將送出以下封包（其餘位元組補 0；會嘗試 64 與 65 byte 兩種長度，另試一次 feature report）：")
    for name, p in queries:
        out(f"  {name}: {hexs(p)} …(補 0)")
    input("\n確認無誤請按 Enter 開始，Ctrl+C 取消：")

    dev = hid.device()
    dev.open_path(path)
    dev.set_nonblocking(True)

    # 先清掉殘留回報
    drain(dev, 0.3)

    for name, prefix in queries:
        out(f"\n=== {name} ===")
        for length in (64, 65):
            buf = pad(prefix, length)
            try:
                n = dev.write(buf)
            except Exception as e:
                out(f"[write len={length}] 例外：{e}")
                continue
            out(f"[write len={length}] 回傳 {n}")
            if n < 0:
                try:
                    out(f"    錯誤：{dev.error()}")
                except Exception:
                    pass
                continue
            for r in drain(dev, 1.5):
                out(f"    回應 len={len(r)}: {hexs(r)}")

        # feature report 變體
        try:
            n = dev.send_feature_report(pad(prefix, 64))
            out(f"[feature len=64] 回傳 {n}")
            for r in drain(dev, 1.5):
                out(f"    回應 len={len(r)}: {hexs(r)}")
        except Exception as e:
            out(f"[feature] 例外：{e}")

    dev.close()
    with open("probe_query_result.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(LOG))
    out("\n已存到 probe_query_result.txt，請把內容貼給我。")


if __name__ == "__main__":
    main()
