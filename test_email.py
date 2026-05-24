"""发送测试邮件 - Apple 设计风格"""

import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from email_sender import send_email

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

# Apple Design System 配色
BG = "#F2F2F7"
CARD = "#FFFFFF"
TEXT = "#000000"
TEXT2 = "#8E8E93"
TEXT3 = "#C7C7CC"
BLUE = "#007AFF"
RED = "#FF3B30"
RED_BG = "#FFF0EF"
GREEN = "#34C759"
GREEN_BG = "#EEFFF4"
SEP = "#E5E5EA"
MUTED = "#F2F2F7"


def load_config():
    if not os.path.exists(CONFIG_FILE):
        print("未找到 config.json")
        return None
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def build_test_email():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    test_signals = [
        {"name": "贵州茅台", "code": "600519", "market": "SH",
         "close": 1685.50, "change": 2.35,
         "signals": [("MACD", "金叉"), ("KDJ", "金叉")],
         "indicators": {"BOLL": "上穿中轨", "MA10": "上穿 (1652.1)",
                        "MACD": "金叉 DIF:12.35", "KDJ": "金叉 K:72.5 D:58.3",
                        "RSI": "慢58.3 快65.5"}},
        {"name": "宁德时代", "code": "300750", "market": "SZ",
         "close": 198.20, "change": -1.50,
         "signals": [("RSI", "死叉"), ("MA10", "死叉")],
         "indicators": {"BOLL": "—", "MA10": "下穿 (201.50)",
                        "MACD": "DIF:-0.82", "KDJ": "K:35.2 D:40.6",
                        "RSI": "慢51.3 快42.1"}},
        {"name": "比亚迪", "code": "002594", "market": "SZ",
         "close": 285.00, "change": 0.80,
         "signals": [("MACD", "金叉"), ("BOLL", "金叉")],
         "indicators": {"BOLL": "上穿中轨", "MA10": "— (283.50)",
                        "MACD": "金叉 DIF:3.52", "KDJ": "K:55.1 D:52.8",
                        "RSI": "慢56.2 快60.4"}},
        {"name": "英伟达", "code": "NVDA", "market": "US",
         "close": 142.30, "change": -2.10,
         "signals": [("MA10", "死叉")],
         "indicators": {"BOLL": "—", "MA10": "下穿 (145.20)",
                        "MACD": "DIF:-1.20", "KDJ": "K:30.5 D:38.2",
                        "RSI": "慢45.1 快38.7"}},
        {"name": "腾讯控股", "code": "00700", "market": "HK",
         "close": 383.67, "change": -0.21,
         "signals": [],
         "indicators": {"BOLL": "—", "MA10": "— (388.20)",
                        "MACD": "DIF:1.25", "KDJ": "K:48.3 D:50.1",
                        "RSI": "慢52.1 快48.5"}},
    ]

    cards = ""
    for s in test_signals:
        ch = s["change"]
        accent = RED if ch >= 0 else GREEN

        sig_map = {x[0]: x[1] for x in s["signals"]}
        badges = ""
        for sig_name, sig_type in s["signals"]:
            bg = RED if sig_type == "金叉" else GREEN
            arrow = "▲" if sig_type == "金叉" else "▼"
            badges += f'<span style="display:inline-block;background:{bg};color:#fff;font-size:11px;font-weight:600;padding:4px 12px;border-radius:20px;margin:2px 4px 2px 0;">{sig_name} {arrow}</span>'
        if not badges:
            badges = f'<span style="font-size:13px;color:{TEXT3};">—</span>'

        pills = ""
        for k in ["BOLL", "MA10", "MACD", "KDJ", "RSI"]:
            st = sig_map.get(k, "")
            if st == "金叉":
                bg, cl = RED_BG, TEXT
            elif st == "死叉":
                bg, cl = GREEN_BG, TEXT
            else:
                bg, cl = MUTED, TEXT3
            val = s["indicators"].get(k, "—")
            pills += f'<span style="display:inline-block;background:{bg};color:{cl};border-radius:8px;padding:5px 12px;margin:3px 6px 3px 0;font-size:12px;"><b>{k}</b>&nbsp;{val}</span>'

        cards += f'''
        <div style="background:{CARD};border-radius:16px;padding:18px 20px;margin-bottom:10px;box-shadow:0 1px 3px rgba(0,0,0,.04);border-left:4px solid {accent};">
          <div style="margin-bottom:8px;display:flex;align-items:center;flex-wrap:wrap;gap:8px;">
            <span style="font-size:17px;font-weight:600;color:{TEXT};">{s["name"]}</span>
            <span style="font-size:13px;color:{TEXT3};">{s["code"]}</span>
            <span style="font-size:11px;color:{BLUE};background:rgba(0,122,255,.08);padding:3px 8px;border-radius:6px;">{s["market"]}</span>
            <span style="flex:1;"></span>
            <span style="font-size:18px;font-weight:600;color:{TEXT};">{s["close"]:.2f}</span>
            <span style="font-size:15px;font-weight:600;color:{accent};">{'+' if ch>=0 else ''}{ch:.2f}%</span>
          </div>
          <div style="margin-bottom:10px;">{badges}</div>
          <div style="border-top:.5px solid {SEP};padding-top:12px;font-size:12px;line-height:2.2;">
            {pills}
          </div>
        </div>'''

    html = f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:24px 16px 40px;background:{BG};font:15px/1.45 -apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;-webkit-font-smoothing:antialiased;">
<div style="max-width:560px;margin:0 auto;">
  <div style="margin-bottom:28px;padding:0 4px;">
    <div style="font-size:12px;font-weight:600;color:{BLUE};letter-spacing:.06em;text-transform:uppercase;margin-bottom:6px;">Signal Report</div>
    <h1 style="font-size:34px;font-weight:700;color:{TEXT};margin:0 0 8px;letter-spacing:-.01em;">技术指标信号</h1>
    <p style="font-size:15px;color:{TEXT2};margin:0 0 4px;">检测: {now}<span style="margin:0 8px;color:{TEXT3}">|</span>信号 <b style="color:{BLUE}">{len(test_signals)}</b> 只</p>
    <p style="font-size:12px;color:#F59E0B;margin:4px 0 0;font-weight:600;">模拟数据 · 仅用于预览</p>
  </div>
  {cards}
  <div style="text-align:center;font-size:12px;color:{TEXT3};padding:20px 0;">Stock Monitor · 每个交易日 11:00 / 14:30</div>
</div>
</body></html>'''
    return html


def main():
    config = load_config()
    if not config:
        return

    email_cfg = config.get("email", {})
    if not email_cfg.get("password"):
        print("未配置邮箱授权码")
        return

    print("生成测试邮件（模拟数据）...")
    body = build_test_email()
    subject = f"【测试】股票监控 - {datetime.now().strftime('%m-%d %H:%M')}"
    success, msg = send_email(email_cfg, subject, body)
    if success:
        print(f"测试邮件已发送到 {email_cfg['receiver']}")
    else:
        print(f"发送失败: {msg}")


if __name__ == "__main__":
    main()
