"""发送测试邮件 - 使用模拟数据预览新模板效果"""

import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from email_sender import send_email

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def load_config():
    if not os.path.exists(CONFIG_FILE):
        print("未找到 config.json，请先运行 setup.py 配置")
        return None
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# 轻快明亮配色（中国股市惯例：红色=涨/金叉，绿色=跌/死叉）
C_BG = "#F0F4F8"
C_CARD = "#FFFFFF"
C_TEXT = "#2C3E50"
C_TEXT2 = "#7F8C8D"
C_TEXT3 = "#95A5A6"
C_ACCENT = "#3498DB"
C_UP = "#E74C3C"       # 涨/金叉 — 红色
C_UP_LIGHT = "#FDEDEC"
C_DOWN = "#27AE60"     # 跌/死叉 — 绿色
C_DOWN_LIGHT = "#E8F8F0"
C_BORDER = "#E8ECF0"
C_STAT_BG = "#EBF5FB"


def build_test_email():
    """构建模拟数据的测试邮件"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    test_signals = [
        {
            "name": "贵州茅台", "code": "600519", "market": "SH",
            "close": 1685.50, "change": 2.35, "date": "2026-05-11",
            "signals": [
                ("MACD", "金叉", "DIF(12.350) 上穿 DEA(8.720)"),
                ("KDJ", "金叉", "K(72.50) 上穿 D(58.30)"),
            ],
            "indicators": {
                "MACD": "金叉 (DIF:12.350)", "KDJ": "金叉 (K:72.50 D:58.30)",
                "RSI": "慢58.32 快65.47", "MA10": "上穿 (1652.100)",
                "BOLL": "上穿中轨",
            },
        },
        {
            "name": "宁德时代", "code": "300750", "market": "SZ",
            "close": 198.20, "change": -1.50, "date": "2026-05-11",
            "signals": [
                ("RSI", "死叉", "快线RSI(42.10) 下穿慢线RSI(51.30)"),
                ("MA10", "死叉", "收盘价(198.20) 下穿 MA10(201.50)"),
            ],
            "indicators": {
                "MACD": "- (DIF:-0.820)", "KDJ": "- (K:35.20 D:40.60)",
                "RSI": "慢51.30 快42.10", "MA10": "下穿 (201.500)",
                "BOLL": "-",
            },
        },
        {
            "name": "比亚迪", "code": "002594", "market": "SZ",
            "close": 285.00, "change": 0.80, "date": "2026-05-11",
            "signals": [
                ("MACD", "金叉", "DIF(3.520) 上穿 DEA(2.180)"),
                ("BOLL", "金叉", "收盘价(285.00) 上穿中轨(281.30)"),
            ],
            "indicators": {
                "MACD": "金叉 (DIF:3.520)", "KDJ": "- (K:55.10 D:52.80)",
                "RSI": "慢56.20 快60.35",
                "MA10": "- (283.500)", "BOLL": "上穿中轨",
            },
        },
    ]

    cards_html = ""
    for item in test_signals:
        change_color = C_UP if item["change"] >= 0 else C_DOWN
        change_sign = "+" if item["change"] >= 0 else ""

        has_golden = any(s[1] == "金叉" for s in item["signals"])
        has_death = any(s[1] == "死叉" for s in item["signals"])
        if has_golden and not has_death:
            accent = C_UP
        elif has_death and not has_golden:
            accent = C_DOWN
        else:
            accent = C_ACCENT

        # 构建指标信号映射
        sig_map = {s[0]: s[1] for s in item["signals"]}
        C_MUTED = "#F0F4F8"

        badges = ""
        for s in item["signals"]:
            bg = C_UP if s[1] == "金叉" else C_DOWN
            badges += (
                f'<span style="display:inline-block;background:{bg};color:#fff;'
                f'font-size:11px;font-weight:bold;padding:2px 8px;border-radius:4px;'
                f'margin:2px 4px 2px 0;">{s[0]} {s[1]}</span>'
            )

        def _pill(name, value):
            key = name.split('(')[0]  # "MACD(19,39,9)" -> "MACD"
            st = sig_map.get(key)
            if st == "金叉":
                bg = C_UP_LIGHT
            elif st == "死叉":
                bg = C_DOWN_LIGHT
            else:
                bg = C_MUTED
            return (f'<span style="display:inline-block;background:{bg};border-radius:6px;'
                    f'padding:4px 10px;margin:3px 6px 3px 0;font-size:11px;'
                    f'color:{C_TEXT if st else C_TEXT3};">'
                    f'<b>{name}</b>: {value}</span>')

        pills_row1 = _pill("BOLL(20,2)", item['indicators']['BOLL']) + _pill("MA10", item['indicators']['MA10'])
        pills_row2 = (_pill("MACD(19,39,9)", item['indicators']['MACD']) +
                      _pill("KDJ(18,3,3)", item['indicators']['KDJ']) +
                      _pill("RSI(21,7)", item['indicators']['RSI']))

        cards_html += f"""
        <div style="background:{C_CARD};border:1px solid {C_BORDER};border-radius:10px;padding:18px;margin-bottom:14px;border-left:4px solid {accent};box-shadow:0 1px 4px rgba(0,0,0,0.04);">
            <div style="margin-bottom:8px;">
                <span style="font-size:15px;font-weight:bold;color:{C_TEXT};">{item['name']}</span>
                <span style="font-size:12px;color:{C_TEXT2};"> {item['code']}</span>
                <span style="font-size:11px;color:{C_TEXT3};background:{C_STAT_BG};padding:1px 6px;border-radius:3px;margin-left:4px;">{item['market']}</span>
            </div>
            <div style="margin-bottom:10px;font-size:14px;color:{C_TEXT};">
                收盘 <b style="font-size:17px;">{item['close']:.2f}</b>
                <span style="color:{change_color};font-weight:bold;"> ({change_sign}{item['change']:.2f}%)</span>
                <span style="color:{C_TEXT2};font-size:12px;margin-left:6px;">{item['date']}</span>
            </div>
            <div style="margin-bottom:4px;">{badges}</div>
            <div style="font-size:11px;color:{C_TEXT2};border-top:1px solid {C_BORDER};padding-top:8px;margin-top:6px;">
                {pills_row1}<br>
                {pills_row2}
            </div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:20px;background:{C_BG};font-family:'Microsoft YaHei','PingFang SC',Arial,sans-serif;">
    <div style="max-width:620px;margin:0 auto;">
        <div style="background:{C_CARD};border-radius:12px;padding:24px;margin-bottom:20px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
            <div style="color:{C_ACCENT};font-size:11px;letter-spacing:2px;margin-bottom:4px;font-weight:bold;">STOCK SIGNAL REPORT</div>
            <h1 style="color:{C_TEXT};font-size:20px;margin:0 0 4px 0;font-weight:bold;">技术指标信号提醒（测试）</h1>
            <p style="color:{C_TEXT2};font-size:12px;margin:0 0 2px 0;">检测时间: {now} | 信号数: {len(test_signals)}</p>
            <p style="color:#F39C12;font-size:11px;margin:8px 0 0 0;font-weight:bold;">⚠ 这是测试邮件，数据为模拟数据</p>
        </div>
        {cards_html}
        <div style="text-align:center;color:{C_TEXT3};font-size:11px;padding:10px 0 20px;">本邮件由股票技术指标监控系统自动发送</div>
    </div>
</body>
</html>"""
    return html


def main():
    config = load_config()
    if not config:
        return

    email_cfg = config.get("email", {})
    if not email_cfg.get("password"):
        print("未配置邮箱授权码，请先运行 setup.py")
        return

    print("生成测试邮件（模拟数据）...")
    body = build_test_email()
    subject = f"【测试邮件】股票监控新模板预览 - {datetime.now().strftime('%m-%d %H:%M')}"
    success, msg = send_email(email_cfg, subject, body)
    if success:
        print(f"测试邮件已发送到 {email_cfg['receiver']}")
    else:
        print(f"发送失败: {msg}")


if __name__ == "__main__":
    main()
