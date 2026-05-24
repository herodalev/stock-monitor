"""股票技术指标监控主程序 - 轻量版"""

import json
import os
from datetime import datetime

from stock_data import get_stock_kline
from indicators import calc_macd, calc_kdj, calc_rsi, calc_ma_cross, calc_boll
from email_sender import send_email


CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_DIR = os.path.join(BASE_DIR, "site")

COMMON_NAMES = {
    "000001": "平安银行", "000333": "美的集团", "000651": "格力电器",
    "000858": "五粮液", "002415": "海康威视", "002594": "比亚迪",
    "300750": "宁德时代", "600519": "贵州茅台", "600036": "招商银行",
    "600276": "恒瑞医药", "600887": "伊利股份", "601318": "中国平安",
    "601398": "工商银行", "601857": "中国石油", "603259": "药明康德",
    "00700": "腾讯控股", "09988": "阿里巴巴", "03690": "美团",
    "01810": "小米集团", "09961": "携程集团", "09618": "京东集团",
    "01211": "比亚迪股份", "00981": "中芯国际",
    "AAPL": "苹果", "TSLA": "特斯拉", "NVDA": "英伟达",
    "MSFT": "微软", "GOOGL": "谷歌", "AMZN": "亚马逊",
    "META": "Meta", "FUTU": "富途控股",
}

# Apple Design System 配色
C_BG = "#F2F2F7"
C_CARD = "#FFFFFF"
C_TEXT = "#000000"
C_TEXT2 = "#8E8E93"
C_TEXT3 = "#C7C7CC"
C_ACCENT = "#007AFF"
C_UP = "#FF3B30"
C_UP_LIGHT = "#FFF0EF"
C_DOWN = "#34C759"
C_DOWN_LIGHT = "#EEFFF4"
C_BORDER = "#E5E5EA"
C_MUTED_BG = "#F2F2F7"


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return None
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_indicator_label(macd_golden, macd_death, kdj_golden, kdj_death,
                         rsi_golden, rsi_death, ma_golden, ma_death,
                         boll_golden, boll_death):
    parts = []
    for name, g, d in [("MACD", macd_golden, macd_death),
                        ("KDJ", kdj_golden, kdj_death),
                        ("RSI", rsi_golden, rsi_death),
                        ("MA", ma_golden, ma_death),
                        ("BOLL", boll_golden, boll_death)]:
        if g:
            parts.append(f"{name}▲")
        elif d:
            parts.append(f"{name}▼")
    return ",".join(parts) if parts else "-"


def check_signals(stock_code, market, stock_name):
    """检查单只股票的技术指标信号"""
    print(f"  -> 获取 {stock_name}({stock_code}) 数据...", end="")
    kline = get_stock_kline(stock_code, market, days=240)
    if not kline or len(kline["closes"]) < 50:
        print(f" 跳过（数据不足）")
        return False, None

    print(f" 共{len(kline['closes'])}条K线")

    closes = kline["closes"]
    highs = kline["highs"]
    lows = kline["lows"]
    dates = kline["dates"]

    signals = []

    dif, dea, hist, macd_golden, macd_death = calc_macd(closes)
    if macd_golden:
        signals.append(("MACD", "金叉", f"DIF({dif:.3f}) 上穿 DEA({dea:.3f})"))
    if macd_death:
        signals.append(("MACD", "死叉", f"DIF({dif:.3f}) 下穿 DEA({dea:.3f})"))

    k, d, j, kdj_golden, kdj_death = calc_kdj(highs, lows, closes)
    if kdj_golden:
        signals.append(("KDJ", "金叉", f"K({k:.2f}) 上穿 D({d:.2f})"))
    if kdj_death:
        signals.append(("KDJ", "死叉", f"K({k:.2f}) 下穿 D({d:.2f})"))

    rsi_slow, rsi_fast, rsi_golden, rsi_death = calc_rsi(closes)
    if rsi_golden:
        signals.append(("RSI", "金叉", f"快线RSI({rsi_fast:.2f}) 上穿慢线RSI({rsi_slow:.2f})"))
    if rsi_death:
        signals.append(("RSI", "死叉", f"快线RSI({rsi_fast:.2f}) 下穿慢线RSI({rsi_slow:.2f})"))

    ma_val, ma_golden, ma_death = calc_ma_cross(closes)
    if ma_golden:
        signals.append(("MA10", "金叉", f"收盘价({closes[-1]:.3f}) 上穿 MA10({ma_val:.3f})"))
    if ma_death:
        signals.append(("MA10", "死叉", f"收盘价({closes[-1]:.3f}) 下穿 MA10({ma_val:.3f})"))

    boll_mid, boll_upper, boll_lower, boll_golden, boll_death = calc_boll(closes)
    if boll_golden:
        signals.append(("BOLL", "金叉", f"收盘价({closes[-1]:.3f}) 上穿中轨({boll_mid:.3f})"))
    if boll_death:
        signals.append(("BOLL", "死叉", f"收盘价({closes[-1]:.3f}) 下穿中轨({boll_mid:.3f})"))

    latest_date = dates[-1] if dates else datetime.now().strftime("%Y-%m-%d")
    latest_close = closes[-1]
    latest_change = ((closes[-1] - closes[-2]) / closes[-2] * 100) if len(closes) >= 2 else 0

    has_signal = len(signals) > 0

    info = {
        "code": stock_code,
        "market": market,
        "name": stock_name,
        "date": latest_date,
        "close": latest_close,
        "change": latest_change,
        "signals": signals,
        "indicators": {
            "MACD": f"{'金叉' if macd_golden else '死叉' if macd_death else '-'} (DIF:{dif:.3f})" if dif is not None else "-",
            "KDJ": f"{'金叉' if kdj_golden else '死叉' if kdj_death else '-'} (K:{k:.2f} D:{d:.2f})" if k is not None else "-",
            "RSI": f"慢{rsi_slow:.2f} 快{rsi_fast:.2f}" if rsi_slow is not None else "-",
            "MA10": f"{'上穿' if ma_golden else '下穿' if ma_death else '-'} ({ma_val:.3f})" if ma_val is not None else "-",
            "BOLL": f"{'上穿中轨' if boll_golden else '下穿中轨' if boll_death else '-'}" if boll_mid is not None else "-",
        },
        "label": _get_indicator_label(macd_golden, macd_death, kdj_golden, kdj_death,
                                       rsi_golden, rsi_death, ma_golden, ma_death,
                                       boll_golden, boll_death),
    }
    return has_signal, info


def build_email_body(signals_list):
    """生成邮件HTML正文 - Apple 设计风格"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    cards_html = ""
    for item in signals_list:
        ch = item["change"]
        accent = C_UP if ch >= 0 else C_DOWN

        sig_map = {s[0]: s[1] for s in item["signals"]}
        badges = ""
        for s in item["signals"]:
            bg = C_UP if s[1] == "金叉" else C_DOWN
            arrow = "▲" if s[1] == "金叉" else "▼"
            badges += (
                f'<span style="display:inline-block;background:{bg};color:#fff;'
                f'font-size:11px;font-weight:600;padding:4px 12px;border-radius:20px;'
                f'margin:2px 4px 2px 0;">{s[0]} {arrow}</span>'
            )
        if not badges:
            badges = f'<span style="font-size:13px;color:{C_TEXT3};">—</span>'

        def _pill(name, value):
            key = name.split('(')[0]
            st = sig_map.get(key)
            if st == "金叉":
                bg = C_UP_LIGHT
            elif st == "死叉":
                bg = C_DOWN_LIGHT
            else:
                bg = C_MUTED_BG
            return (f'<span style="display:inline-block;background:{bg};border-radius:8px;'
                    f'padding:5px 12px;margin:3px 6px 3px 0;font-size:12px;'
                    f'color:{C_TEXT if st else C_TEXT3};">'
                    f'<b>{name}</b>&nbsp;{value}</span>')

        pills = (_pill("BOLL(20,2)", item['indicators']['BOLL']) +
                 _pill("MA10", item['indicators']['MA10']) +
                 _pill("MACD(19,39,9)", item['indicators']['MACD']) +
                 _pill("KDJ(18,3,3)", item['indicators']['KDJ']) +
                 _pill("RSI(21,7)", item['indicators']['RSI']))

        cards_html += f"""
        <div style="background:{C_CARD};border-radius:16px;padding:18px 20px;margin-bottom:10px;box-shadow:0 1px 3px rgba(0,0,0,.04);border-left:4px solid {accent};">
          <div style="margin-bottom:8px;display:flex;align-items:center;flex-wrap:wrap;gap:8px;">
            <span style="font-size:17px;font-weight:600;color:{C_TEXT};">{item['name']}</span>
            <span style="font-size:13px;color:{C_TEXT3};">{item['code']}</span>
            <span style="font-size:11px;color:{C_ACCENT};background:rgba(0,122,255,.08);padding:3px 8px;border-radius:6px;">{item['market']}</span>
            <span style="flex:1;"></span>
            <span style="font-size:18px;font-weight:600;color:{C_TEXT};">{item['close']:.3f}</span>
            <span style="font-size:15px;font-weight:600;color:{accent};">{'+' if ch>=0 else ''}{ch:.2f}%</span>
          </div>
          <div style="margin-bottom:10px;">{badges}</div>
          <div style="border-top:.5px solid {C_BORDER};padding-top:12px;font-size:12px;line-height:2.2;">
            {pills}
          </div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:24px 16px 40px;background:{C_BG};font:15px/1.45 -apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;-webkit-font-smoothing:antialiased;">
<div style="max-width:560px;margin:0 auto;">
  <div style="margin-bottom:28px;padding:0 4px;">
    <div style="font-size:12px;font-weight:600;color:{C_ACCENT};letter-spacing:.06em;text-transform:uppercase;margin-bottom:6px;">Signal Report</div>
    <h1 style="font-size:34px;font-weight:700;color:{C_TEXT};margin:0 0 8px;letter-spacing:-.01em;">技术指标信号</h1>
    <p style="font-size:15px;color:{C_TEXT2};margin:0 0 4px;">检测: {now}<span style="margin:0 8px;color:{C_TEXT3}">|</span>信号 <b style="color:{C_ACCENT}">{len(signals_list)}</b> 只</p>
    <p style="font-size:12px;color:{C_TEXT3};margin:0;">BOLL(20,2) · MA10 · MACD(19,39,9) · KDJ(18,3,3) · RSI(21,7)</p>
  </div>
  {cards_html}
  <div style="text-align:center;font-size:12px;color:{C_TEXT3};padding:20px 0;">Stock Monitor · 每个交易日 11:00 / 14:30</div>
</div>
</body></html>"""
    return html


def _save_site_data(all_results, signals_found):
    """保存站点数据到 results.json"""
    os.makedirs(SITE_DIR, exist_ok=True)

    # 移除信号描述（缩短JSON），只保留摘要
    site_results = []
    for item in all_results:
        entry = {
            "code": item["code"],
            "market": item["market"],
            "name": item["name"],
            "date": item["date"],
            "close": item["close"],
            "change": item["change"],
            "signals": [(s[0], s[1]) for s in item["signals"]],  # 只保留指标名和类型
            "indicators": item["indicators"],
            "label": item["label"],
        }
        site_results.append(entry)

    data = {
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(site_results),
        "signal_count": len(signals_found),
        "stocks": site_results,
    }
    with open(os.path.join(SITE_DIR, "results.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 按日期存档到 history/
    today = datetime.now().strftime("%Y-%m-%d")
    history_dir = os.path.join(SITE_DIR, "history")
    os.makedirs(history_dir, exist_ok=True)
    with open(os.path.join(history_dir, f"{today}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"站点数据已保存: {len(site_results)}只股票, {len(signals_found)}个信号")


def run_monitor():
    """主监控流程"""
    config = load_config()
    if not config:
        print("未找到配置文件，请先运行 setup.py 进行初始化设置")
        return

    stocks = config.get("stocks", [])
    if not stocks:
        print("自选股列表为空，请先添加股票")
        return

    email_cfg = config.get("email", {})
    if not email_cfg.get("password"):
        print("未配置邮箱授权码")
        return

    print(f"\n{'='*60}")
    print(f"股票技术指标监控 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"指标: BOLL(20,2) MA10 MACD(19,39,9) KDJ(18,3,3) RSI(21,7)")
    print(f"监控股票数: {len(stocks)}")
    print(f"{'='*60}\n")

    signals_found = []
    all_results = []

    for s in stocks:
        code = s["code"]
        market = s["market"]
        name = s.get("name") or COMMON_NAMES.get(code.upper(), code)
        has_signal, info = check_signals(code, market, name)
        if info:
            all_results.append(info)
            if has_signal:
                signals_found.append(info)

    signals_found.sort(key=lambda x: x["change"], reverse=True)
    all_results.sort(key=lambda x: x.get("change", 0), reverse=True)

    print(f"\n{'='*60}")
    if signals_found:
        print(f"共检测到 {len(signals_found)} 个信号！")
        for s in signals_found:
            sig_str = ", ".join(f"{x[0]}{x[1]}" for x in s["signals"])
            print(f"   {s['name']} ({s['code']}): {sig_str}")

        subject = f"【股票提醒】{len(signals_found)}只股票出现技术指标信号 - {datetime.now().strftime('%m-%d %H:%M')}"
        body = build_email_body(signals_found)
        success, msg = send_email(email_cfg, subject, body)
        if success:
            print(f"邮件已发送到 {email_cfg['receiver']}")
        else:
            print(f"邮件发送失败: {msg}")
    else:
        print("未检测到金叉/死叉信号")

    _save_site_data(all_results, signals_found)
    print(f"{'='*60}\n")


if __name__ == "__main__":
    run_monitor()
