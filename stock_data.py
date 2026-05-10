"""股票数据获取 - 腾讯财经API(A股/港股) + Yahoo Finance API(美股)"""

import requests
from datetime import datetime, timedelta

MARKET_PREFIX = {
    "SH": "sh",
    "SZ": "sz",
    "HK": "hk",
    "US": "us",
}


def get_stock_kline(stock_code, market, days=120):
    """
    获取股票日K线数据
    stock_code: 股票代码（如 600519, 00700, AAPL）
    market: 市场（SH, SZ, HK, US）
    days: 获取多少天的数据
    """
    if market.upper() == "US":
        return _get_us_kline(stock_code, days)

    prefix = MARKET_PREFIX.get(market.upper(), "sz")
    secid = f"{prefix}{stock_code.lower()}"

    url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
    params = {"param": f"{secid},day,,,{days},qfq"}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        data = r.json()
        if data.get("code") != 0:
            return None

        stock_data = data.get("data", {})
        if secid not in stock_data:
            return None

        day_data = stock_data[secid]
        klines = day_data.get("qfqday") or day_data.get("day")
        if not klines or len(klines) < 10:
            return None

        return _parse_tencent_kline(klines)
    except Exception as e:
        print(f"  [错误] 获取 {secid} 数据失败: {e}")
        return None


def _get_us_kline(stock_code, days):
    """使用 Yahoo Finance API 获取美股日K线（直接HTTP调用，绕过curl_cffi的TLS问题）"""
    try:
        end = int(datetime.now().timestamp())
        start = int((datetime.now() - timedelta(days=days * 1.5)).timestamp())

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{stock_code.upper()}"
        params = {"period1": start, "period2": end, "interval": "1d"}
        headers = {"User-Agent": "Mozilla/5.0"}

        r = requests.get(url, params=params, headers=headers, timeout=15)
        data = r.json()

        result = data.get("chart", {}).get("result")
        if not result:
            return None

        quotes = result[0]
        timestamps = quotes.get("timestamp", [])
        indicators = quotes.get("indicators", {})

        quote_data = indicators.get("quote", [{}])[0]
        adjclose_data = indicators.get("adjclose", [{}])[0]

        opens = quote_data.get("open", [])
        closes_adj = adjclose_data.get("adjclose", [])
        closes_raw = quote_data.get("close", [])
        highs = quote_data.get("high", [])
        lows = quote_data.get("low", [])
        volumes = quote_data.get("volume", [])

        # 优先使用复权收盘价
        closes = closes_adj if closes_adj and len(closes_adj) == len(closes_raw) else closes_raw

        if not closes or len(closes) < 10:
            return None

        result_data = {
            "dates": [datetime.fromtimestamp(ts).strftime("%Y-%m-%d") for ts in timestamps],
            "opens": opens,
            "closes": closes,
            "highs": highs,
            "lows": lows,
            "volumes": volumes,
        }
        return result_data
    except Exception as e:
        print(f"  [错误] 获取美股 {stock_code} 数据失败: {e}")
        return None


def _parse_tencent_kline(klines):
    """解析腾讯日K数据: [日期, 开盘, 收盘, 最高, 最低, 成交量]"""
    result = {
        "dates": [],
        "opens": [],
        "closes": [],
        "highs": [],
        "lows": [],
        "volumes": [],
    }
    for k in klines:
        result["dates"].append(k[0])
        result["opens"].append(float(k[1]))
        result["closes"].append(float(k[2]))
        result["highs"].append(float(k[3]))
        result["lows"].append(float(k[4]))
        result["volumes"].append(float(k[5]) if len(k) > 5 else 0)
    return result
