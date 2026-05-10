"""生成K线图（含金叉/死叉标记），嵌入邮件HTML"""

import io
import base64
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.font_manager as fm

from indicators import ema, sma

# 中文字体
_CJK_FONT = None
for _name in ['Microsoft YaHei', 'SimHei', 'WenQuanYi Micro Hei', 'Noto Sans CJK SC',
              'WenQuanYi Zen Hei', 'Source Han Sans SC', 'PingFang SC']:
    try:
        _fp = fm.findfont(_name, fallback_to_default=False)
        if _fp and 'dejavu' not in _fp.lower():
            _CJK_FONT = fm.FontProperties(family=_name)
            break
    except Exception:
        continue
if _CJK_FONT is None:
    _CJK_FONT = fm.FontProperties()
_CHINESE_FONT = _CJK_FONT
if _CHINESE_FONT.get_name() and 'dejavu' not in _CHINESE_FONT.get_name().lower():
    plt.rcParams['font.family'] = _CHINESE_FONT.get_name()
plt.rcParams['axes.unicode_minus'] = False

# 莫兰迪配色（来自 pic/配色.jpg）
COLOR_UP = '#50a0e6'       # 阳线蓝
COLOR_DOWN = '#b48c6e'     # 阴线棕
COLOR_MA = '#e6aa50'       # 均线金
COLOR_BOLL = '#5ab4b4'     # 布林带青
COLOR_GOLDEN = '#e6aa50'   # 金叉标记
COLOR_DEATH = '#828c96'    # 死叉标记
COLOR_GRID = '#bebec8'     # 网格线
COLOR_TEXT = '#5a4b3c'     # 深棕文字


def _find_macd_crosses(closes, fast=19, slow=39, signal=9):
    """扫描全量MACD数据，返回所有交叉点列表 [(bar_index, type), ...]"""
    arr = np.array(closes, dtype=float)
    ema_f = ema(arr, fast)
    ema_s = ema(arr, slow)
    dif = ema_f - ema_s
    dea = ema(dif, signal)
    crosses = []
    for i in range(1, len(dif)):
        if dif[i - 1] <= dea[i - 1] and dif[i] > dea[i]:
            crosses.append((i, '金叉'))
        elif dif[i - 1] >= dea[i - 1] and dif[i] < dea[i]:
            crosses.append((i, '死叉'))
    return crosses, dif, dea


def _find_kdj_crosses(highs, lows, closes, period=18, k_weight=3, d_weight=3):
    """扫描全量KDJ数据，返回所有交叉点列表 [(bar_index, type), ...]"""
    h = np.array(highs, dtype=float)
    l = np.array(lows, dtype=float)
    c = np.array(closes, dtype=float)
    n = len(c)
    k_vals = np.zeros(n)
    d_vals = np.zeros(n)
    for i in range(n):
        if i < period - 1:
            continue
        hh = np.max(h[i - period + 1:i + 1])
        ll = np.min(l[i - period + 1:i + 1])
        rsv = (c[i] - ll) / (hh - ll) * 100 if hh != ll else 50
        if i == period - 1:
            k_vals[i] = 50
            d_vals[i] = 50
        else:
            k_vals[i] = (k_weight - 1) / k_weight * k_vals[i - 1] + 1 / k_weight * rsv
            d_vals[i] = (d_weight - 1) / d_weight * d_vals[i - 1] + 1 / d_weight * k_vals[i]
    crosses = []
    for i in range(1, n):
        if k_vals[i - 1] <= d_vals[i - 1] and k_vals[i] > d_vals[i]:
            crosses.append((i, '金叉'))
        elif k_vals[i - 1] >= d_vals[i - 1] and k_vals[i] < d_vals[i]:
            crosses.append((i, '死叉'))
    return crosses, k_vals, d_vals


def _find_rsi_crosses(closes, period1=21, period2=7):
    """扫描全量RSI数据，返回所有交叉点列表 [(bar_index, type), ...]"""
    def _single(data, period):
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
        result = np.empty(len(data))
        result[:] = np.nan
        result[period:] = rsi_vals[period - 1:]
        return result

    r1 = _single(closes, period1)
    r2 = _single(closes, period2)
    crosses = []
    for i in range(1, len(closes)):
        if np.isnan(r1[i]) or np.isnan(r2[i]) or np.isnan(r1[i - 1]) or np.isnan(r2[i - 1]):
            continue
        if r2[i - 1] <= r1[i - 1] and r2[i] > r1[i]:
            crosses.append((i, '金叉'))
        elif r2[i - 1] >= r1[i - 1] and r2[i] < r1[i]:
            crosses.append((i, '死叉'))
    return crosses, r2, r1


def _find_ma_crosses(closes, period=10):
    """扫描全量MA交叉点"""
    arr = np.array(closes, dtype=float)
    ma = sma(arr, period)
    crosses = []
    for i in range(1, len(arr)):
        if np.isnan(ma[i]) or np.isnan(ma[i - 1]):
            continue
        if arr[i - 1] <= ma[i - 1] and arr[i] > ma[i]:
            crosses.append((i, '金叉'))
        elif arr[i - 1] >= ma[i - 1] and arr[i] < ma[i]:
            crosses.append((i, '死叉'))
    return crosses, ma


def _find_boll_crosses(closes, period=20, std_mult=2.0):
    """扫描全量BOLL中轨交叉点"""
    arr = np.array(closes, dtype=float)
    n = len(arr)
    mid = np.zeros(n)
    for i in range(n):
        if i < period - 1:
            mid[i] = np.nan
        else:
            mid[i] = np.mean(arr[i - period + 1:i + 1])
    crosses = []
    for i in range(1, n):
        if np.isnan(mid[i]) or np.isnan(mid[i - 1]):
            continue
        if arr[i - 1] <= mid[i - 1] and arr[i] > mid[i]:
            crosses.append((i, '金叉'))
        elif arr[i - 1] >= mid[i - 1] and arr[i] < mid[i]:
            crosses.append((i, '死叉'))
    return crosses, mid


def _get_window(data_list, window=30):
    """取最后window个数据"""
    if len(data_list) <= window:
        return data_list, 0
    return data_list[-window:], len(data_list) - window


def generate_chart(kline, stock_name, stock_code):
    """
    生成近一个月K线图，高亮金叉/死叉位置
    返回: base64字符串
    """
    # 取最近30个交易日
    dates_raw = kline['dates']
    opens = kline['opens']
    closes = kline['closes']
    highs = kline['highs']
    lows = kline['lows']

    if len(closes) < 30:
        offset = 0
        dates = dates_raw
        opens_arr = opens
        closes_arr = closes
        highs_arr = highs
        lows_arr = lows
    else:
        offset = len(closes) - 30
        dates = dates_raw[-30:]
        opens_arr = opens[-30:]
        closes_arr = closes[-30:]
        highs_arr = highs[-30:]
        lows_arr = lows[-30:]

    n = len(closes_arr)

    # 计算全量交叉点
    macd_crosses, _, _ = _find_macd_crosses(closes)
    kdj_crosses, _, _ = _find_kdj_crosses(highs, lows, closes)
    rsi_crosses, _, _ = _find_rsi_crosses(closes)
    ma_crosses, ma_vals = _find_ma_crosses(closes)
    boll_crosses, boll_mid = _find_boll_crosses(closes)

    # 筛选窗口内的交叉点
    def filter_crosses(crosses, offset, n):
        result = []
        for idx, typ in crosses:
            chart_idx = idx - offset
            if 0 <= chart_idx < n:
                result.append((chart_idx, typ))
        return result

    window_macd = filter_crosses(macd_crosses, offset, n)
    window_kdj = filter_crosses(kdj_crosses, offset, n)
    window_rsi = filter_crosses(rsi_crosses, offset, n)
    window_ma = filter_crosses(ma_crosses, offset, n)
    window_boll = filter_crosses(boll_crosses, offset, n)

    # 取窗口内的辅助线数据
    ma_window = ma_vals[-30:] if len(ma_vals) > 30 else ma_vals
    boll_window = boll_mid[-30:] if len(boll_mid) > 30 else boll_mid

    # 计算价格范围
    price_min = min(lows_arr)
    price_max = max(highs_arr)
    price_range = price_max - price_min
    y_margin = price_range * 0.15 if price_range > 0 else 1
    y_min = price_min - y_margin
    y_max = price_max + y_margin + price_range * 0.10  # 顶部留更多空间给标记

    # 创建图表
    fig, ax = plt.subplots(figsize=(7, 3.2))
    fig.patch.set_facecolor('#fcfaf7')
    ax.set_facecolor('#fcfaf7')
    ax.set_xlim(-0.5, n - 0.5)
    ax.set_ylim(y_min, y_max)
    ax.tick_params(colors=COLOR_TEXT, labelsize=7)

    # 隐藏上边和右边框
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(COLOR_GRID)
    ax.spines['bottom'].set_color(COLOR_GRID)

    # 网格
    ax.grid(True, linestyle='--', alpha=0.3, color=COLOR_GRID)

    # 绘制K线
    for i in range(n):
        o = opens_arr[i]
        c = closes_arr[i]
        h = highs_arr[i]
        l_ = lows_arr[i]
        color = COLOR_UP if c >= o else COLOR_DOWN
        # 影线
        ax.plot([i, i], [l_, h], color=color, linewidth=1)
        # 实体
        if c >= o:
            ax.bar(i, c - o, bottom=o, width=0.6, color=color, alpha=0.9)
        else:
            ax.bar(i, c - o, bottom=o, width=0.6, color=color, alpha=0.9)

    # 绘制MA10
    valid_x = [i for i in range(n) if not np.isnan(ma_window[i])]
    valid_y = [ma_window[i] for i in valid_x]
    if valid_x:
        ax.plot(valid_x, valid_y, color=COLOR_MA, linewidth=1.2, alpha=0.8, label='MA10')

    # 绘制BOLL中轨
    valid_x = [i for i in range(n) if not np.isnan(boll_window[i])]
    valid_y = [boll_window[i] for i in valid_x]
    if valid_x:
        ax.plot(valid_x, valid_y, color=COLOR_BOLL, linewidth=1, alpha=0.7, linestyle='--', label='BOLL Mid')

    # 标记交叉点
    legend_entries = []

    def draw_cross_marker(chart_idx, typ, label_prefix):
        price_pos = y_max - price_range * 0.02
        if typ == '金叉':
            ax.annotate(f'{label_prefix}↑',
                        xy=(chart_idx, price_pos),
                        fontsize=6.5, fontweight='bold',
                        color=COLOR_GOLDEN, ha='center', va='bottom',
                        rotation=30)
        else:
            ax.annotate(f'{label_prefix}↓',
                        xy=(chart_idx, price_pos),
                        fontsize=6.5, fontweight='bold',
                        color=COLOR_DEATH, ha='center', va='bottom',
                        rotation=30)

    # 集合：同一位置多个信号显示一个标记
    for crosses_list, prefix in [(window_macd, 'MACD'), (window_kdj, 'KDJ'),
                                  (window_rsi, 'RSI'), (window_ma, 'MA'),
                                  (window_boll, 'BOLL')]:
        for chart_idx, typ in crosses_list:
            draw_cross_marker(chart_idx, typ, prefix)

    # X轴标签（日期）
    tick_step = max(1, n // 6)
    tick_positions = list(range(0, n, tick_step))
    tick_labels = []
    for pos in tick_positions:
        if pos < len(dates):
            d = dates[pos]
            tick_labels.append(d[5:] if len(d) >= 10 else d)
        else:
            tick_labels.append('')
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels)

    # 标题（根据字体是否支持中文选择显示方式）
    has_cjk = 'dejavu' not in _CHINESE_FONT.get_name().lower()
    display_name = f'{stock_name}({stock_code})' if has_cjk else f'{stock_code}'
    ax.set_title(display_name, fontsize=10, color=COLOR_TEXT, fontweight='bold', loc='left', pad=8)

    # 紧凑布局
    plt.tight_layout(pad=1.0)

    # 输出为base64 PNG
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=110, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()
