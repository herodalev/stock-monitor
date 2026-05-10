"""股票技术指标监控主程序"""

import json
import os
from datetime import datetime

from stock_data import get_stock_kline
from indicators import calc_macd, calc_kdj, calc_rsi, calc_ma_cross, calc_boll
from chart_generator import generate_chart
from email_sender import send_email


CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

# 常用股票名称映射（便于识别）
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


def load_config():
    """加载配置"""
    if not os.path.exists(CONFIG_FILE):
        return None

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config):
    """保存配置"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def check_signals(stock_code, market, stock_name):
    """
    检查单只股票的技术指标信号
    返回: (has_signal, signal_info_dict or None)
    """
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

    # MACD(19,39,9) 检测
    dif, dea, hist, macd_golden, macd_death = calc_macd(closes)
    if macd_golden:
        signals.append(("MACD", "金叉", f"DIF({dif:.3f}) 上穿 DEA({dea:.3f})"))
    if macd_death:
        signals.append(("MACD", "死叉", f"DIF({dif:.3f}) 下穿 DEA({dea:.3f})"))

    # KDJ(18,3,3) 检测
    k, d, j, kdj_golden, kdj_death = calc_kdj(highs, lows, closes)
    if kdj_golden:
        signals.append(("KDJ", "金叉", f"K({k:.2f}) 上穿 D({d:.2f})"))
    if kdj_death:
        signals.append(("KDJ", "死叉", f"K({k:.2f}) 下穿 D({d:.2f})"))

    # RSI(21,7) 双线交叉检测
    rsi_slow, rsi_fast, rsi_golden, rsi_death = calc_rsi(closes)
    if rsi_golden:
        signals.append(("RSI", "金叉", f"快线RSI({rsi_fast:.2f}) 上穿慢线RSI({rsi_slow:.2f})"))
    if rsi_death:
        signals.append(("RSI", "死叉", f"快线RSI({rsi_fast:.2f}) 下穿慢线RSI({rsi_slow:.2f})"))

    # 均线(10) 检测
    ma_val, ma_golden, ma_death = calc_ma_cross(closes)
    if ma_golden:
        signals.append(("MA10", "金叉", f"收盘价({closes[-1]:.3f}) 上穿 MA10({ma_val:.3f})"))
    if ma_death:
        signals.append(("MA10", "死叉", f"收盘价({closes[-1]:.3f}) 下穿 MA10({ma_val:.3f})"))

    # 布林带(20,2) 检测
    boll_mid, boll_upper, boll_lower, boll_golden, boll_death = calc_boll(closes)
    if boll_golden:
        signals.append(("BOLL", "金叉", f"收盘价({closes[-1]:.3f}) 上穿中轨({boll_mid:.3f})"))
    if boll_death:
        signals.append(("BOLL", "死叉", f"收盘价({closes[-1]:.3f}) 下穿中轨({boll_mid:.3f})"))

    if signals:
        latest_date = dates[-1] if dates else datetime.now().strftime("%Y-%m-%d")
        latest_close = closes[-1]
        latest_change = ((closes[-1] - closes[-2]) / closes[-2] * 100) if len(closes) >= 2 else 0

        # 生成K线图
        chart_b64 = generate_chart(kline, stock_name, stock_code)

        return True, {
            "code": stock_code,
            "market": market,
            "name": stock_name,
            "date": latest_date,
            "close": latest_close,
            "change": latest_change,
            "signals": signals,
            "chart_b64": chart_b64,
            "indicators": {
                "MACD": f"{'金叉' if macd_golden else '死叉' if macd_death else '-'} (DIF:{dif:.3f})" if dif is not None else "-",
                "KDJ": f"{'金叉' if kdj_golden else '死叉' if kdj_death else '-'} (K:{k:.2f} D:{d:.2f})" if k is not None else "-",
                "RSI": f"慢{rsi_slow:.2f} 快{rsi_fast:.2f}" if rsi_slow is not None else "-",
                "MA10": f"{'上穿' if ma_golden else '下穿' if ma_death else '-'} ({ma_val:.3f})" if ma_val is not None else "-",
                "BOLL": f"{'上穿中轨' if boll_golden else '下穿中轨' if boll_death else '-'}" if boll_mid is not None else "-",
            }
        }

    return False, None


def build_email_body(signals_list):
    """生成邮件HTML正文 - 莫兰迪配色卡片布局"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    cards_html = ""
    for item in signals_list:
        change_color = "#8FA88A" if item["change"] >= 0 else "#B88A8A"
        change_sign = "+" if item["change"] >= 0 else ""

        # 卡片左边框颜色：根据信号类型
        has_golden = any(s[1] == "金叉" for s in item["signals"])
        has_death = any(s[1] == "死叉" for s in item["signals"])
        if has_golden and not has_death:
            accent = "#A1B5A0"
        elif has_death and not has_golden:
            accent = "#C4A4A4"
        else:
            accent = "#B5A488"

        # 信号标签
        badges = ""
        for s in item["signals"]:
            bg = "#A1B5A0" if s[1] == "金叉" else "#C4A4A4"
            badges += (
                f'<span style="display:inline-block;background:{bg};color:#fff;'
                f'font-size:11px;font-weight:bold;padding:2px 8px;border-radius:4px;'
                f'margin:2px 4px 2px 0;">{s[0]} {s[1]}</span>'
            )

        cards_html += f"""
        <div style="background:#FCFAF7;border:1px solid #D6CDBF;border-radius:10px;padding:16px;margin-bottom:14px;border-left:4px solid {accent};box-shadow:0 1px 4px rgba(0,0,0,0.04);">
            <div style="margin-bottom:8px;">
                <span style="font-size:15px;font-weight:bold;color:#5A4B3C;">{item['name']}</span>
                <span style="font-size:12px;color:#A89888;"> {item['code']}</span>
                <span style="font-size:11px;color:#B5A898;background:#F0EBE4;padding:1px 6px;border-radius:3px;margin-left:4px;">{item['market']}</span>
            </div>
            <div style="margin-bottom:8px;font-size:14px;color:#5A4B3C;">
                收盘 <b style="font-size:17px;">{item['close']:.3f}</b>
                <span style="color:{change_color};font-weight:bold;"> ({change_sign}{item['change']:.2f}%)</span>
                <span style="color:#9A8B7A;font-size:12px;margin-left:6px;">{item['date']}</span>
            </div>
            <div style="margin-bottom:6px;">{badges}</div>
            <div style="margin-bottom:8px;">
                <img src="data:image/png;base64,{item['chart_b64']}" style="width:100%;max-width:560px;border-radius:6px;display:block;" alt="K-line">
            </div>
            <div style="font-size:11px;color:#9A8B7A;border-top:1px solid #E5DDD4;padding-top:7px;">
                MACD: {item['indicators']['MACD']} &nbsp;|&nbsp; KDJ: {item['indicators']['KDJ']} &nbsp;|&nbsp; RSI: {item['indicators']['RSI']}<br>
                MA10: {item['indicators']['MA10']} &nbsp;|&nbsp; BOLL: {item['indicators']['BOLL']}
            </div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:20px;background:#F2EDE7;font-family:'Microsoft YaHei','PingFang SC',Arial,sans-serif;">
    <div style="max-width:620px;margin:0 auto;">
        <div style="background:#FCFAF7;border-radius:12px;padding:24px;margin-bottom:20px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
            <div style="color:#8B7E6F;font-size:11px;letter-spacing:2px;margin-bottom:4px;">STOCK SIGNAL REPORT</div>
            <h1 style="color:#5A4B3C;font-size:20px;margin:0 0 4px 0;font-weight:normal;">技术指标信号提醒</h1>
            <p style="color:#9A8B7A;font-size:12px;margin:0 0 2px 0;">检测时间: {now} &nbsp;|&nbsp; 信号数: {len(signals_list)}</p>
            <p style="color:#B5A898;font-size:11px;margin:0;">MACD(19,39,9) · KDJ(18,3,3) · RSI(21,7) · MA10 · BOLL(20,2)</p>
        </div>
        {cards_html}
        <div style="text-align:center;color:#B5A898;font-size:11px;padding:10px 0 20px;">本邮件由股票技术指标监控系统自动发送</div>
    </div>
</body>
</html>"""
    return html


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
    print(f"指标: MACD(19,39,9) KDJ(18,3,3) RSI(21,7) MA10 BOLL(20,2)")
    print(f"监控股票数: {len(stocks)}")
    print(f"{'='*60}\n")

    signals_found = []

    for s in stocks:
        code = s["code"]
        market = s["market"]
        name = s.get("name") or COMMON_NAMES.get(code.upper(), code)
        has_signal, info = check_signals(code, market, name)
        if has_signal:
            signals_found.append(info)

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
    print(f"{'='*60}\n")


if __name__ == "__main__":
    run_monitor()
