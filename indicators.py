"""技术指标计算：MACD, KDJ, RSI, 均线, 布林带 金叉/死叉检测（纯Python，零依赖）"""

import math


def ema(data, period):
    """指数移动平均"""
    alpha = 2.0 / (period + 1)
    result = [data[0]]
    for i in range(1, len(data)):
        result.append(alpha * data[i] + (1 - alpha) * result[i - 1])
    return result


def sma(data, period):
    """简单移动平均"""
    result = []
    for i in range(len(data)):
        if i < period - 1:
            result.append(float('nan'))
        else:
            result.append(sum(data[i - period + 1:i + 1]) / period)
    return result


def calc_macd(closes, fast=19, slow=39, signal=9):
    """
    MACD: DIF = EMA(fast) - EMA(slow), DEA = EMA(DIF, signal)
    返回: (dif, dea, macd_hist, golden, death)
    """
    if len(closes) < max(fast, slow, signal) + 5:
        return None, None, None, None, None

    data = [float(x) for x in closes]
    ema_fast = ema(data, fast)
    ema_slow = ema(data, slow)
    dif = [f - s for f, s in zip(ema_fast, ema_slow)]
    dea = ema(dif, signal)
    macd_hist = 2 * (dif[-1] - dea[-1])

    golden = dif[-2] <= dea[-2] and dif[-1] > dea[-1]
    death = dif[-2] >= dea[-2] and dif[-1] < dea[-1]

    return dif[-1], dea[-1], macd_hist, golden, death


def calc_kdj(highs, lows, closes, period=18, k_weight=3, d_weight=3):
    """
    KDJ指标
    返回: (k, d, j, golden, death)
    """
    if len(closes) < period + 1:
        return None, None, None, None, None

    h = [float(x) for x in highs]
    l = [float(x) for x in lows]
    c = [float(x) for x in closes]
    n = len(c)
    k_vals = [0.0] * n
    d_vals = [0.0] * n

    for i in range(n):
        if i < period - 1:
            continue
        window_h = max(h[i - period + 1:i + 1])
        window_l = min(l[i - period + 1:i + 1])
        rsv = (c[i] - window_l) / (window_h - window_l) * 100 if window_h != window_l else 50

        if i == period - 1:
            k_vals[i] = 50
            d_vals[i] = 50
        else:
            k_vals[i] = (k_weight - 1) / k_weight * k_vals[i - 1] + 1 / k_weight * rsv
            d_vals[i] = (d_weight - 1) / d_weight * d_vals[i - 1] + 1 / d_weight * k_vals[i]

    j_vals = [3 * k_vals[i] - 2 * d_vals[i] for i in range(n)]

    golden = k_vals[n - 2] <= d_vals[n - 2] and k_vals[n - 1] > d_vals[n - 1]
    death = k_vals[n - 2] >= d_vals[n - 2] and k_vals[n - 1] < d_vals[n - 1]

    return k_vals[-1], d_vals[-1], j_vals[-1], golden, death


def calc_rsi(closes, period1=21, period2=7):
    """
    RSI双线交叉: period1(慢线), period2(快线)
    返回: (rsi_slow, rsi_fast, golden, death)
    """
    def _single_rsi(data, period):
        if len(data) < period + 1:
            return None
        arr = [float(x) for x in data]
        deltas = [arr[i] - arr[i - 1] for i in range(1, len(arr))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]

        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period

        rsi_vals = [0.0] * len(deltas)
        if avg_loss == 0:
            rsi_vals[period - 1] = 100
        else:
            rs = avg_gain / avg_loss
            rsi_vals[period - 1] = 100 - 100 / (1 + rs)

        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            if avg_loss == 0:
                rsi_vals[i] = 100
            else:
                rs = avg_gain / avg_loss
                rsi_vals[i] = 100 - 100 / (1 + rs)

        result = [float('nan')] * len(data)
        result[period:] = rsi_vals[period - 1:]
        return result

    rsi_slow_arr = _single_rsi(closes, period1)
    rsi_fast_arr = _single_rsi(closes, period2)

    if rsi_slow_arr is None or rsi_fast_arr is None:
        return None, None, None, None

    fast_prev, fast_cur = rsi_fast_arr[-2], rsi_fast_arr[-1]
    slow_prev, slow_cur = rsi_slow_arr[-2], rsi_slow_arr[-1]

    golden = death = False
    if not (math.isnan(fast_prev) or math.isnan(slow_prev)):
        golden = fast_prev <= slow_prev and fast_cur > slow_cur
        death = fast_prev >= slow_prev and fast_cur < slow_cur

    return rsi_slow_arr[-1], rsi_fast_arr[-1], golden, death


def calc_ma_cross(closes, period=10):
    """
    股价与均线交叉
    返回: (ma_val, golden, death)
    """
    if len(closes) < period + 1:
        return None, None, None

    arr = [float(x) for x in closes]
    ma_vals = sma(arr, period)

    golden = death = False
    if not (math.isnan(ma_vals[-1]) or math.isnan(ma_vals[-2])):
        golden = arr[-2] <= ma_vals[-2] and arr[-1] > ma_vals[-1]
        death = arr[-2] >= ma_vals[-2] and arr[-1] < ma_vals[-1]

    return ma_vals[-1], golden, death


def calc_boll(closes, period=20, std_mult=2.0):
    """
    布林带，金叉=上穿中轨，死叉=下穿中轨
    返回: (mid, upper, lower, golden, death)
    """
    if len(closes) < period + 1:
        return None, None, None, None, None

    arr = [float(x) for x in closes]
    n = len(arr)

    def _std(window):
        m = sum(window) / len(window)
        return math.sqrt(sum((x - m) ** 2 for x in window) / (len(window) - 1))

    mid_vals = [float('nan')] * n
    std_vals = [float('nan')] * n
    for i in range(n):
        if i < period - 1:
            continue
        window = arr[i - period + 1:i + 1]
        mid_vals[i] = sum(window) / period
        std_vals[i] = _std(window)

    mid = mid_vals[-1]
    upper = mid + std_mult * std_vals[-1]
    lower = mid - std_mult * std_vals[-1]

    golden = death = False
    if not (math.isnan(mid_vals[-1]) or math.isnan(mid_vals[-2])):
        golden = arr[-2] <= mid_vals[-2] and arr[-1] > mid_vals[-1]
        death = arr[-2] >= mid_vals[-2] and arr[-1] < mid_vals[-1]

    return mid, upper, lower, golden, death
