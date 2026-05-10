"""生成静态站点 index.html（GitHub Pages仪表盘）"""

import json
import os

SITE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site")


def _color(val):
    """根据涨跌幅返回莫兰迪色"""
    if val > 0:
        return "#8FA88A" if val < 5 else "#6B8F6B"
    elif val < 0:
        return "#B88A8A" if val > -5 else "#A06B6B"
    return "#9A8B7A"


def _signal_label(typ):
    """金叉/死叉 → CSS类"""
    return "golden" if typ == "金叉" else "death"


def generate():
    with open(os.path.join(SITE_DIR, "results.json"), "r", encoding="utf-8") as f:
        data = json.load(f)

    stocks = data["stocks"]
    update_time = data["update_time"]
    signal_count = data["signal_count"]
    total = data["total"]

    rows = ""
    for i, s in enumerate(stocks):
        change = s.get("change", 0)
        c = _color(change)
        sign = "+" if change >= 0 else ""

        # 信号标签
        badge_html = ""
        for sig in s.get("signals", []):
            cls = _signal_label(sig[1])
            badge_html += f'<span class="badge {cls}">{sig[0]} {sig[1]}</span>'

        # 图表（如有）
        chart_html = ""
        chart_file = s.get("chart_file", "")
        if chart_file:
            chart_html = f'''<div class="chart-wrap">
                <img src="{chart_file}" style="width:100%;max-width:560px;border-radius:6px;" alt="K-line">
            </div>'''

        # 指标文本
        ind = s.get("indicators", {})
        indicators_text = (
            f'MACD:{ind.get("MACD","-")} | KDJ:{ind.get("KDJ","-")} | '
            f'RSI:{ind.get("RSI","-")} | MA10:{ind.get("MA10","-")} | BOLL:{ind.get("BOLL","-")}'
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
                    {chart_html}
                    <div class="indicator-text">{indicators_text}</div>
                    <div class="signal-desc">{"; ".join(s[2] for s in s.get("signals",[]))}</div>
                </div>
            </td>
        </tr>'''

    # 统计：各指标信号数
    label_counts = {}
    for s in stocks:
        for sig in s.get("signals", []):
            key = f"{sig[0]}{sig[1]}"
            label_counts[key] = label_counts.get(key, 0) + 1
    stats_html = "".join(
        f'<span class="stat-badge">{k} <em>{n}</em></span>'
        for k, n in sorted(label_counts.items())
    ) if label_counts else "<span style='color:#9A8B7A;font-size:13px;'>暂无信号</span>"

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>股票技术指标监控</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
    background:#F2EDE7; font-family:'Microsoft YaHei','PingFang SC',Arial,sans-serif;
    padding:20px; color:#5A4B3C;
}}
.container {{ max-width:1100px; margin:0 auto; }}

/* 头部 */
.header {{
    background:#FCFAF7; border-radius:12px; padding:24px 28px;
    margin-bottom:20px; box-shadow:0 2px 8px rgba(0,0,0,0.06);
}}
.header .sub {{ color:#8B7E6F; font-size:11px; letter-spacing:2px; margin-bottom:4px; }}
.header h1 {{ font-size:22px; font-weight:normal; margin:0 0 6px 0; color:#5A4B3C; }}
.header .meta {{ color:#9A8B7A; font-size:13px; }}
.header .params {{ color:#B5A898; font-size:11px; margin-top:4px; }}

/* 统计条 */
.stats-bar {{
    display:flex; flex-wrap:wrap; gap:6px; margin-top:12px; padding-top:12px;
    border-top:1px solid #E5DDD4;
}}
.stat-badge {{
    font-size:12px; color:#8B7E6F; background:#F0EBE4;
    padding:3px 10px; border-radius:12px;
}}
.stat-badge em {{ font-style:normal; font-weight:bold; color:#5A4B3C; margin-left:3px; }}

/* 表格 */
.table-wrap {{
    background:#FCFAF7; border-radius:12px; overflow:hidden;
    box-shadow:0 2px 8px rgba(0,0,0,0.06);
}}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
thead th {{
    background:#F5F0E8; color:#8B7E6F; font-weight:normal; font-size:11px;
    letter-spacing:1px; padding:10px 12px; text-align:left; border-bottom:1px solid #E5DDD4;
}}
tbody td {{ padding:10px 12px; border-bottom:1px solid #F0EBE4; }}
.stock-row {{ cursor:pointer; transition:background 0.15s; }}
.stock-row:hover {{ background:#FAF6F0; }}
.stock-row.active {{ background:#F5EFE8; }}
.num {{ font-family:'SF Mono','Consolas',monospace; text-align:right; }}
.code {{ font-size:11px; color:#A89888; margin-left:5px; }}
.market-tag {{ font-size:10px; color:#B5A898; background:#F0EBE4; padding:1px 5px; border-radius:3px; }}

/* 信号标签 */
.badge {{
    display:inline-block; font-size:10px; font-weight:bold; padding:1px 7px;
    border-radius:4px; margin:1px 2px;
}}
.badge.golden {{ background:#A1B5A0; color:#fff; }}
.badge.death {{ background:#C4A4A4; color:#fff; }}

/* 展开详情 */
.detail-card {{
    padding:12px 12px 12px 32px; background:#FAF7F3; border-radius:8px; margin:4px 0;
}}
.chart-wrap {{ margin-bottom:8px; }}
.indicator-text {{ font-size:11px; color:#9A8B7A; line-height:1.6; }}
.signal-desc {{ font-size:11px; color:#8B7E6F; margin-top:4px; }}

/* 底部 */
.footer {{ text-align:center; color:#B5A898; font-size:11px; padding:16px 0; }}

/* 响应式 */
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
        <div class="meta">
            更新时间: {update_time} &nbsp;|&nbsp;
            监控 {total} 只股票 &nbsp;|&nbsp;
            <strong style="color:#5A4B3C;">{signal_count}</strong> 只出现信号
        </div>
        <div class="params">MACD(19,39,9) · KDJ(18,3,3) · RSI(21,7) · MA10 · BOLL(20,2)</div>
        <div class="stats-bar">{stats_html}</div>
    </div>

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
            <tbody>{rows}</tbody>
        </table>
    </div>
    <div class="footer">Stock Monitor · 每个交易日 14:30 更新</div>
</div>
<script>
function toggleRow(tr) {{
    var detail = tr.nextElementSibling;
    if (detail && detail.classList.contains('detail-row')) {{
        var visible = detail.style.display === 'table-row';
        detail.style.display = visible ? 'none' : 'table-row';
        tr.classList.toggle('active', !visible);
    }}
}}
</script>
</body>
</html>'''

    out_path = os.path.join(SITE_DIR, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"站点已生成: {out_path} ({len(html)} bytes)")


if __name__ == "__main__":
    generate()
