"""技术指标计算：MACD, KDJ, RSI, 均线, 布林带 金叉/死叉检测"""

import numpy as np


def ema(data, period):
    """指数移动平均"""
    result = np.zeros_like(data, dtype=float)
    alpha = 2.0 / (period + 1)
    result[0] = data[0]
    for i in range(1, len(data)):
        result[i] = alpha * data[i] + (1 - alpha) * result[i - 1]
    return result


def sma(data, period):
    """简单移动平均"""
    result = np.zeros_like(data, dtype=float)
    for i in range(len(data)):
        if i < period - 1:
            result[i] = np.nan
        else:
            result[i] = np.mean(data[i - period + 1:i + 1])
    return result


def calc_macd(closes, fast=19, slow=39, signal=9):
    """
    计算 MACD 指标
    DIF = EMA(fast) - EMA(slow), DEA = EMA(DIF, signal)
    返回: (dif, dea, macd_hist, golden, death)
    - 金叉: dif 上穿 dea
    - 死叉: dif 下穿 dea
    """
    if len(closes) < max(fast, slow, signal) + 5:
        return None, None, None, None, None

    ema_fast = ema(np.array(closes, dtype=float), fast)
    ema_slow = ema(np.array(closes, dtype=float), slow)
    dif = ema_fast - ema_slow
    dea = ema(dif, signal)
    macd_hist = 2 * (dif - dea)

    golden = False
    death = False
    if len(dif) >= 2:
        if dif[-2] <= dea[-2] and dif[-1] > dea[-1]:
            golden = True
        if dif[-2] >= dea[-2] and dif[-1] < dea[-1]:
            death = True

    return dif[-1], dea[-1], macd_hist[-1], golden, death


def calc_kdj(highs, lows, closes, period=18, k_weight=3, d_weight=3):
    """
    计算 KDJ 指标
    period: RSV计算周期 (默认19)
    k_weight: K平滑参数 (默认39, 1/39权重)
    d_weight: D平滑参数 (默认9, 1/9权重)
    返回: (k, d, j, golden, death)
    - 金叉: K 上穿 D
    - 死叉: K 下穿 D
    """
    if len(closes) < period + 1:
        return None, None, None, None, None

    closes_arr = np.array(closes, dtype=float)
    highs_arr = np.array(highs, dtype=float)
    lows_arr = np.array(lows, dtype=float)

    n = len(closes_arr)
    k_vals = np.zeros(n)
    d_vals = np.zeros(n)

    for i in range(n):
        if i < period - 1:
            continue
        hh = np.max(highs_arr[i - period + 1:i + 1])
        ll = np.min(lows_arr[i - period + 1:i + 1])
        rsv = (closes_arr[i] - ll) / (hh - ll) * 100 if hh != ll else 50

        if i == period - 1:
            k_vals[i] = 50
            d_vals[i] = 50
        else:
            k_vals[i] = (k_weight - 1) / k_weight * k_vals[i - 1] + 1 / k_weight * rsv
            d_vals[i] = (d_weight - 1) / d_weight * d_vals[i - 1] + 1 / d_weight * k_vals[i]

    j_vals = 3 * k_vals - 2 * d_vals

    golden = False
    death = False
    if n >= 2:
        if k_vals[n - 2] <= d_vals[n - 2] and k_vals[n - 1] > d_vals[n - 1]:
            golden = True
        if k_vals[n - 2] >= d_vals[n - 2] and k_vals[n - 1] < d_vals[n - 1]:
            death = True

    return k_vals[-1], d_vals[-1], j_vals[-1], golden, death


def calc_rsi(closes, period1=21, period2=7):
    """
    计算 RSI 双线交叉
    period1: 慢线RSI周期 (默认21)
    period2: 快线RSI周期 (默认7)
    返回: (rsi_slow, rsi_fast, golden, death)
    - 金叉: RSI2(快线) 上穿 RSI1(慢线)
    - 死叉: RSI2(快线) 下穿 RSI1(慢线)
    """
    def _single_rsi(data, period):
        if len(data) < period + 1:
            return None
        arr = np.array(data, dtype=float)
        deltas = np.diff(arr)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])

        rsi_vals = np.zeros(len(deltas))
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

        # Pad front to align with original data length
        result = np.empty(len(data))
        result[:] = np.nan
        result[period:] = rsi_vals[period - 1:]
        return result

    rsi_slow_arr = _single_rsi(closes, period1)
    rsi_fast_arr = _single_rsi(closes, period2)

    if rsi_slow_arr is None or rsi_fast_arr is None:
        return None, None, None, None

    rsi_slow = rsi_slow_arr[-1]
    rsi_fast = rsi_fast_arr[-1]

    golden = False
    death = False
    if not np.isnan(rsi_slow_arr[-2]) and not np.isnan(rsi_fast_arr[-2]):
        if rsi_fast_arr[-2] <= rsi_slow_arr[-2] and rsi_fast_arr[-1] > rsi_slow_arr[-1]:
            golden = True
        if rsi_fast_arr[-2] >= rsi_slow_arr[-2] and rsi_fast_arr[-1] < rsi_slow_arr[-1]:
            death = True

    return rsi_slow, rsi_fast, golden, death


def calc_ma_cross(closes, period=10):
    """
    计算股价与均线的交叉
    返回: (ma_val, golden, death)
    - 金叉: 收盘价上穿均线
    - 死叉: 收盘价下穿均线
    """
    if len(closes) < period + 1:
        return None, None, None

    arr = np.array(closes, dtype=float)
    ma_vals = sma(arr, period)

    golden = False
    death = False
    if not np.isnan(ma_vals[-1]) and not np.isnan(ma_vals[-2]):
        if arr[-2] <= ma_vals[-2] and arr[-1] > ma_vals[-1]:
            golden = True
        if arr[-2] >= ma_vals[-2] and arr[-1] < ma_vals[-1]:
            death = True

    return ma_vals[-1], golden, death


def calc_boll(closes, period=20, std_mult=2.0):
    """
    计算布林带
    返回: (mid, upper, lower, golden, death)
    - 金叉: 收盘价上穿中轨
    - 死叉: 收盘价下穿中轨
    """
    if len(closes) < period + 1:
        return None, None, None, None, None

    arr = np.array(closes, dtype=float)

    # 计算SMA和标准差
    mid_vals = np.zeros_like(arr)
    std_vals = np.zeros_like(arr)
    for i in range(len(arr)):
        if i < period - 1:
            mid_vals[i] = np.nan
            std_vals[i] = np.nan
        else:
            window = arr[i - period + 1:i + 1]
            mid_vals[i] = np.mean(window)
            std_vals[i] = np.std(window, ddof=1)

    mid = mid_vals[-1]
    upper = mid + std_mult * std_vals[-1]
    lower = mid - std_mult * std_vals[-1]

    golden = False  # 上穿中轨
    death = False   # 下穿中轨
    if not np.isnan(mid_vals[-1]) and not np.isnan(mid_vals[-2]):
        if arr[-2] <= mid_vals[-2] and arr[-1] > mid_vals[-1]:
            golden = True
        if arr[-2] >= mid_vals[-2] and arr[-1] < mid_vals[-1]:
            death = True

    return mid, upper, lower, golden, death
