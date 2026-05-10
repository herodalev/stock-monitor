"""生成静态站点 index.html（GitHub Pages仪表盘）- 支持按日期查看历史"""

import json
import os
from datetime import datetime

SITE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site")

# 轻快明亮配色（中国股市惯例：红色=涨/金叉，绿色=跌/死叉）
C_BG = "#F0F4F8"
C_CARD = "#FFFFFF"
C_TEXT = "#2C3E50"
C_TEXT2 = "#7F8C8D"
C_TEXT3 = "#95A5A6"
C_ACCENT = "#3498DB"
C_UP = "#E74C3C"
C_UP_LIGHT = "#FDEDEC"
C_DOWN = "#27AE60"
C_DOWN_LIGHT = "#E8F8F0"
C_BORDER = "#E8ECF0"
C_STAT_BG = "#EBF5FB"
C_TABLE_STRIPE = "#F8FAFB"
C_HOVER = "#F0F7FF"


def _color(val):
    """红涨绿跌"""
    if val > 0:
        return C_UP if val < 5 else "#C0392B"
    elif val < 0:
        return C_DOWN if val > -5 else "#1E8449"
    return C_TEXT2


def _build_table(stocks):
    """根据 stocks 数据生成表格 HTML 行"""
    rows = ""
    for i, s in enumerate(stocks):
        change = s.get("change", 0)
        c = _color(change)
        sign = "+" if change >= 0 else ""

        sig_map = dict(s.get("signals", []))
        ind = s.get("indicators", {})

        def _pill_cls(name):
            key = name.split('(')[0]
            st = sig_map.get(key)
            if st == "金叉":
                return "pill-up"
            elif st == "死叉":
                return "pill-down"
            return "pill-muted"

        badge_html = ""
        for sig in s.get("signals", []):
            cls = "golden" if sig[1] == "金叉" else "death"
            badge_html += f'<span class="badge {cls}">{sig[0]} {sig[1]}</span>'

        indicators_text = (
            f'<span class="ind-pill {_pill_cls("BOLL(20,2)")}"><b>BOLL(20,2)</b>: {ind.get("BOLL","-")}</span>'
            f'<span class="ind-pill {_pill_cls("MA10")}"><b>MA10</b>: {ind.get("MA10","-")}</span><br>'
            f'<span class="ind-pill {_pill_cls("MACD(19,39,9)")}"><b>MACD(19,39,9)</b>: {ind.get("MACD","-")}</span>'
            f'<span class="ind-pill {_pill_cls("KDJ(18,3,3)")}"><b>KDJ(18,3,3)</b>: {ind.get("KDJ","-")}</span>'
            f'<span class="ind-pill {_pill_cls("RSI(21,7)")}"><b>RSI(21,7)</b>: {ind.get("RSI","-")}</span>'
        )

        rows += f'''
        <tr class="stock-row" onclick="toggleRow(this)">
            <td class="num">{i+1}</td>
            <td><strong>{s["name"]}</strong><span class="code">{s["code"]}</span></td>
            <td><span class="market-tag">{s["market"]}</span></td>
            <td class="num">{s.get("close", "-")}</td>
            <td class="num" style="color:{c};font-weight:bold;">{sign}{change:.2f}%</td>
            <td>{s.get("label","-")}</td>
            <td>{badge_html}</td>
        </tr>
        <tr class="detail-row" style="display:none;">
            <td colspan="7">
                <div class="detail-card">
                    <div class="indicator-text">{indicators_text}</div>
                </div>
            </td>
        </tr>'''
    return rows


def _build_stats(stocks):
    """统计各指标信号数"""
    counts = {}
    for s in stocks:
        for sig in s.get("signals", []):
            key = f"{sig[0]}{sig[1]}"
            counts[key] = counts.get(key, 0) + 1
    if counts:
        return "".join(
            f'<span class="stat-badge">{k} <em>{n}</em></span>'
            for k, n in sorted(counts.items())
        )
    return '<span class="no-signal">暂无信号</span>'


def generate():
    # 读取最新数据
    results_path = os.path.join(SITE_DIR, "results.json")
    if not os.path.exists(results_path):
        print("results.json 不存在，请先运行 monitor.py")
        return

    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    stocks = data["stocks"]
    update_time = data["update_time"]
    signal_count = data["signal_count"]
    total = data["total"]

    # 扫描历史记录
    history_dir = os.path.join(SITE_DIR, "history")
    history_dates = []
    if os.path.isdir(history_dir):
        for fname in sorted(os.listdir(history_dir), reverse=True):
            if fname.endswith(".json"):
                history_dates.append(fname.replace(".json", ""))

    # 构建最新数据表格
    rows = _build_table(stocks)
    stats_html = _build_stats(stocks)

    # 历史日期选择器
    if history_dates:
        today = datetime.now().strftime("%Y-%m-%d")
        opts = ""
        for d in history_dates:
            label = f"{d} (今日)" if d == today else d
            sel = " selected" if d == history_dates[0] else ""
            opts += f'<option value="{d}"{sel}>{label}</option>\n'
        history_bar = f'''
        <div class="history-bar">
            <span class="history-label">选择日期:</span>
            <select id="dateSelect" onchange="loadHistory(this.value)">{opts}</select>
            <span id="loadingHint" style="display:none;color:{C_ACCENT};margin-left:8px;font-size:12px;">加载中...</span>
        </div>'''
    else:
        history_bar = ""

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>股票技术指标监控</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
    background:{C_BG}; font-family:'Microsoft YaHei','PingFang SC',Arial,sans-serif;
    padding:20px; color:{C_TEXT};
}}
.container {{ max-width:1100px; margin:0 auto; }}

.header {{
    background:{C_CARD}; border-radius:12px; padding:24px 28px;
    margin-bottom:20px; box-shadow:0 2px 8px rgba(0,0,0,0.06);
}}
.header .sub {{ color:{C_ACCENT}; font-size:11px; letter-spacing:2px; margin-bottom:4px; font-weight:bold; }}
.header h1 {{ font-size:22px; font-weight:bold; margin:0 0 6px 0; color:{C_TEXT}; }}
.header .meta {{ color:{C_TEXT2}; font-size:13px; }}
.header .params {{ color:{C_TEXT3}; font-size:11px; margin-top:4px; }}

.stats-bar {{
    display:flex; flex-wrap:wrap; gap:6px; margin-top:12px; padding-top:12px;
    border-top:1px solid {C_BORDER};
}}
.stat-badge {{
    font-size:12px; color:{C_ACCENT}; background:{C_STAT_BG};
    padding:3px 10px; border-radius:12px;
}}
.stat-badge em {{ font-style:normal; font-weight:bold; color:{C_TEXT}; margin-left:3px; }}
.no-signal {{ color:{C_TEXT3}; font-size:13px; }}

.history-bar {{
    background:{C_CARD}; border-radius:12px; padding:14px 28px;
    margin-bottom:20px; box-shadow:0 2px 8px rgba(0,0,0,0.06);
    display:flex; align-items:center; gap:10px;
}}
.history-label {{ font-size:13px; color:{C_TEXT2}; font-weight:600; }}
.history-bar select {{
    padding:6px 12px; border:1px solid {C_BORDER}; border-radius:6px;
    font-size:13px; color:{C_TEXT}; background:{C_CARD}; cursor:pointer;
    outline:none;
}}
.history-bar select:focus {{ border-color:{C_ACCENT}; }}

.table-wrap {{
    background:{C_CARD}; border-radius:12px; overflow:hidden;
    box-shadow:0 2px 8px rgba(0,0,0,0.06);
}}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
thead th {{
    background:{C_TABLE_STRIPE}; color:{C_TEXT2}; font-weight:600; font-size:11px;
    letter-spacing:1px; padding:10px 12px; text-align:left; border-bottom:1px solid {C_BORDER};
}}
tbody td {{ padding:10px 12px; border-bottom:1px solid {C_BORDER}; }}
.stock-row {{ cursor:pointer; transition:background 0.15s; }}
.stock-row:hover {{ background:{C_HOVER}; }}
.stock-row.active {{ background:#E8F2FC; }}
.num {{ font-family:'SF Mono','Consolas',monospace; text-align:right; }}
.code {{ font-size:11px; color:{C_TEXT3}; margin-left:5px; }}
.market-tag {{ font-size:10px; color:{C_ACCENT}; background:{C_STAT_BG}; padding:1px 5px; border-radius:3px; }}

.badge {{
    display:inline-block; font-size:10px; font-weight:bold; padding:1px 7px;
    border-radius:4px; margin:1px 2px;
}}
.badge.golden {{ background:{C_UP}; color:#fff; }}
.badge.death {{ background:{C_DOWN}; color:#fff; }}

.detail-card {{
    padding:12px 12px 12px 32px; background:{C_TABLE_STRIPE}; border-radius:8px; margin:4px 0;
}}
.indicator-text {{ font-size:11px; color:{C_TEXT2}; line-height:2.2; }}
.ind-pill {{
    display:inline-block; border-radius:6px; padding:4px 10px;
    margin:3px 6px 3px 0; font-size:11px;
}}
.pill-up {{ background:{C_UP_LIGHT}; color:{C_TEXT}; }}
.pill-down {{ background:{C_DOWN_LIGHT}; color:{C_TEXT}; }}
.pill-muted {{ background:#F0F4F8; color:{C_TEXT3}; }}

.footer {{ text-align:center; color:{C_TEXT3}; font-size:11px; padding:16px 0; }}

@media(max-width:700px) {{
    table {{ font-size:12px; }}
    thead th, tbody td {{ padding:8px 6px; }}
    .code {{ display:none; }}
}}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <div class="sub">STOCK MONITOR DASHBOARD</div>
        <h1>股票技术指标监控仪表盘</h1>
        <div id="headerMeta" class="meta">
            更新时间: {update_time} &nbsp;|&nbsp;
            监控 {total} 只股票 &nbsp;|&nbsp;
            <strong style="color:{C_ACCENT};">{signal_count}</strong> 只出现信号
        </div>
        <div class="params">BOLL(20,2) · MA10 · MACD(19,39,9) · KDJ(18,3,3) · RSI(21,7)</div>
        <div id="statsBar" class="stats-bar">{stats_html}</div>
    </div>

    {history_bar}

    <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th style="width:32px;">#</th>
                    <th>名称</th>
                    <th style="width:36px;">市场</th>
                    <th style="width:80px;" class="num">收盘</th>
                    <th style="width:80px;" class="num">涨跌幅</th>
                    <th>信号</th>
                    <th style="width:140px;">详情</th>
                </tr>
            </thead>
            <tbody id="tableBody">{rows}</tbody>
        </table>
    </div>
    <div class="footer">Stock Monitor · 每个交易日 11:00 / 14:30 更新 · GitHub Actions 云端运行</div>
</div>

<script>
// 缓存最新数据，用于恢复
var latestHtml = {{
    rows: `{rows}`,
    stats: `{stats_html}`,
    meta: `更新时间: {update_time} &nbsp;|&nbsp; 监控 {total} 只股票 &nbsp;|&nbsp; <strong style="color:{C_ACCENT};">{signal_count}</strong> 只出现信号`
}};

function toggleRow(tr) {{
    var detail = tr.nextElementSibling;
    if (detail && detail.classList.contains('detail-row')) {{
        var visible = detail.style.display === 'table-row';
        detail.style.display = visible ? 'none' : 'table-row';
        tr.classList.toggle('active', !visible);
    }}
}}

function loadHistory(date) {{
    if (date === 'latest') {{
        document.getElementById('tableBody').innerHTML = latestHtml.rows;
        document.getElementById('statsBar').innerHTML = latestHtml.stats;
        document.getElementById('headerMeta').innerHTML = latestHtml.meta;
        return;
    }}
    var hint = document.getElementById('loadingHint');
    hint.style.display = 'inline';
    fetch('history/' + date + '.json')
        .then(function(r) {{ return r.json(); }})
        .then(function(data) {{
            hint.style.display = 'none';
            document.getElementById('tableBody').innerHTML = buildRows(data.stocks);
            document.getElementById('statsBar').innerHTML = buildStats(data.stocks);
            document.getElementById('headerMeta').innerHTML =
                '更新时间: ' + data.update_time + ' &nbsp;|&nbsp; ' +
                '监控 ' + data.total + ' 只股票 &nbsp;|&nbsp; ' +
                '<strong style="color:{C_ACCENT};">' + data.signal_count + '</strong> 只出现信号';
        }})
        .catch(function(e) {{
            hint.style.display = 'none';
            alert('加载失败: ' + e);
        }});
}}

function buildRows(stocks) {{
    var html = '';
    for (var i = 0; i < stocks.length; i++) {{
        var s = stocks[i];
        var c = s.change > 0 ? '{C_UP}' : s.change < 0 ? '{C_DOWN}' : '{C_TEXT2}';
        if (s.change > 5) c = '#C0392B';
        if (s.change < -5) c = '#1E8449';
        var sign = s.change >= 0 ? '+' : '';
        var sigMap = {{}};
        (s.signals || []).forEach(function(sig) {{ sigMap[sig[0]] = sig[1]; }});
        var badges = '';
        (s.signals || []).forEach(function(sig) {{
            var cls = sig[1] === '金叉' ? 'golden' : 'death';
            badges += '<span class="badge ' + cls + '">' + sig[0] + ' ' + sig[1] + '</span>';
        }});
        var ind = s.indicators || {{}};
        function pill(key) {{
            var st = sigMap[key];
            if (st === '金叉') return 'pill-up';
            if (st === '死叉') return 'pill-down';
            return 'pill-muted';
        }}
        var indText =
            '<span class="ind-pill ' + pill('BOLL') + '"><b>BOLL(20,2)</b>: ' + (ind.BOLL||'-') + '</span>' +
            '<span class="ind-pill ' + pill('MA10') + '"><b>MA10</b>: ' + (ind.MA10||'-') + '</span><br>' +
            '<span class="ind-pill ' + pill('MACD') + '"><b>MACD(19,39,9)</b>: ' + (ind.MACD||'-') + '</span>' +
            '<span class="ind-pill ' + pill('KDJ') + '"><b>KDJ(18,3,3)</b>: ' + (ind.KDJ||'-') + '</span>' +
            '<span class="ind-pill ' + pill('RSI') + '"><b>RSI(21,7)</b>: ' + (ind.RSI||'-') + '</span>';
        html +=
            '<tr class="stock-row" onclick="toggleRow(this)">' +
            '<td class="num">' + (i+1) + '</td>' +
            '<td><strong>' + s.name + '</strong><span class="code">' + s.code + '</span></td>' +
            '<td><span class="market-tag">' + s.market + '</span></td>' +
            '<td class="num">' + (s.close||'-') + '</td>' +
            '<td class="num" style="color:' + c + ';font-weight:bold;">' + sign + (s.change||0).toFixed(2) + '%</td>' +
            '<td>' + (s.label||'-') + '</td>' +
            '<td>' + badges + '</td></tr>' +
            '<tr class="detail-row" style="display:none;">' +
            '<td colspan="7"><div class="detail-card"><div class="indicator-text">' + indText + '</div></div></td></tr>';
    }}
    return html;
}}

function buildStats(stocks) {{
    var counts = {{}};
    stocks.forEach(function(s) {{
        (s.signals || []).forEach(function(sig) {{
            var k = sig[0] + sig[1];
            counts[k] = (counts[k] || 0) + 1;
        }});
    }});
    var keys = Object.keys(counts).sort();
    if (keys.length === 0) return '<span class="no-signal">暂无信号</span>';
    var html = '';
    keys.forEach(function(k) {{
        html += '<span class="stat-badge">' + k + ' <em>' + counts[k] + '</em></span>';
    }});
    return html;
}}
</script>
</body>
</html>'''

    out_path = os.path.join(SITE_DIR, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"站点已生成: {out_path} ({len(html)} bytes)")
    print(f"历史记录: {len(history_dates)} 天")


if __name__ == "__main__":
    generate()
