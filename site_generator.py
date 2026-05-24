"""生成静态站点 index.html（GitHub Pages仪表盘）- Apple 设计风格"""

import json
import os
from datetime import datetime

SITE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site")

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

CSS = f'''*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:{BG};font:15px/1.45 -apple-system,BlinkMacSystemFont,"SF Pro Text","SF Pro Display","PingFang SC","Microsoft YaHei",sans-serif;color:{TEXT};-webkit-font-smoothing:antialiased;padding:24px 16px 40px}}
.w{{max-width:680px;margin:0 auto}}
header{{margin-bottom:28px;padding:0 4px}}
header .eyebrow{{font-size:12px;font-weight:600;color:{BLUE};letter-spacing:.06em;text-transform:uppercase;margin-bottom:6px}}
header h1{{font-size:34px;font-weight:700;letter-spacing:-.01em;line-height:1.1;margin-bottom:8px}}
header .summary{{font-size:15px;color:{TEXT2};display:flex;align-items:center;gap:6px;flex-wrap:wrap}}
header .summary b{{color:{TEXT};font-weight:600}}
header .params{{font-size:12px;color:{TEXT3};margin-top:4px}}
.date-bar{{display:flex;align-items:center;gap:10px;margin-top:18px}}
.date-bar label{{font-size:13px;font-weight:500;color:{TEXT2}}}
.date-bar select{{-webkit-appearance:none;appearance:none;padding:7px 32px 7px 14px;border:1px solid {SEP};border-radius:10px;font-size:14px;color:{TEXT};background:#fff url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%238E8E93' stroke-width='2'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E") no-repeat right 12px center;cursor:pointer;outline:none;font-family:inherit}}
.date-bar select:focus{{border-color:{BLUE};box-shadow:0 0 0 3px rgba(0,122,255,.15)}}
#ld{{font-size:13px;color:{BLUE}}}
.stock-card{{background:{CARD};border-radius:16px;padding:18px 20px;margin-bottom:10px;box-shadow:0 1px 3px rgba(0,0,0,.04),0 0 0 .5px rgba(0,0,0,.04);cursor:pointer;transition:box-shadow .2s,transform .15s;-webkit-tap-highlight-color:transparent;user-select:none}}
.stock-card:hover{{box-shadow:0 4px 14px rgba(0,0,0,.08),0 0 0 .5px rgba(0,0,0,.06)}}
.stock-card:active{{transform:scale(.995)}}
.stock-card.up{{border-left:4px solid {RED}}}
.stock-card.down{{border-left:4px solid {GREEN}}}
.card-top{{display:flex;align-items:center;gap:10px;flex-wrap:wrap}}
.card-top .name{{font-size:17px;font-weight:600;letter-spacing:-.01em}}
.card-top .code{{font-size:13px;color:{TEXT3};font-weight:400}}
.card-top .mkt{{font-size:11px;font-weight:500;color:{BLUE};background:rgba(0,122,255,.08);padding:3px 8px;border-radius:6px}}
.card-top .spacer{{flex:1}}
.card-top .price{{font-size:18px;font-weight:600;font-variant-numeric:tabular-nums}}
.card-top .change{{font-size:15px;font-weight:600;min-width:68px;text-align:right;font-variant-numeric:tabular-nums}}
.signal-row{{display:flex;gap:5px;flex-wrap:wrap;margin-top:10px;min-height:0}}
.signal-badge{{font-size:11px;font-weight:600;color:#fff;padding:4px 10px;border-radius:20px;letter-spacing:.01em}}
.no-signal{{font-size:12px;color:{TEXT3}}}
.expand-hint{{font-size:12px;color:{TEXT3};margin-top:10px;cursor:pointer;display:flex;align-items:center;gap:4px}}
.expand-hint .arrow{{display:inline-block;transition:transform .2s;font-size:10px}}
.stock-card.open .arrow{{transform:rotate(90deg)}}
.indicator-pills{{display:none;margin-top:12px;padding-top:14px;border-top:.5px solid {SEP}}}
.stock-card.open .indicator-pills{{display:block}}
.pill{{display:inline-block;border-radius:8px;padding:5px 12px;margin:3px 5px 3px 0;font-size:12px;letter-spacing:-.01em}}
.pill b{{font-weight:600}}
.empty{{text-align:center;color:{TEXT2};font-size:15px;padding:60px 20px}}
footer{{text-align:center;font-size:12px;color:{TEXT3};padding:20px 0;margin-top:10px}}
@media(max-width:480px){{
  body{{padding:16px 10px 32px}}
  header h1{{font-size:28px}}
  .stock-card{{padding:14px 16px;border-radius:14px}}
  .card-top .name{{font-size:15px}}
  .card-top .price{{font-size:16px}}
}}'''

JS = f'''function t(e){{e.classList.toggle("open")}}
function L(d){{
  if(d==="latest"){{R();return}}
  document.getElementById("ld").style.display="inline";
  fetch("history/"+d+".json").then(function(r){{return r.json()}}).then(function(data){{
    document.getElementById("ld").style.display="none";
    document.getElementById("meta").innerHTML=H(data);
    document.getElementById("list").innerHTML=B(data.stocks);
  }}).catch(function(e){{
    document.getElementById("ld").style.display="none";
    alert("加载失败");
  }});
}}
function R(){{document.getElementById("meta").innerHTML=LD.meta;document.getElementById("list").innerHTML=LD.html}}
function H(d){{return'更新: '+d.update_time+'<span style="margin:0 6px;color:{TEXT3}">|</span>监控 <b>'+d.total+'</b> 只<span style="margin:0 6px;color:{TEXT3}">|</span>信号 <b style="color:{BLUE}">'+d.signal_count+'</b> 只'}}
function B(ss){{
  var h="",i,s,ch,c,m,v,k,ind,st,bg,cl;
  for(i=0;i<ss.length;i++){{
    s=ss[i];ch=s.change||0;c=ch>0?"{RED}":ch<0?"{GREEN}":"{TEXT2}";m={{}};
    (s.signals||[]).forEach(function(x){{m[x[0]]=x[1]}});
    v="";
    for(k in m){{v+='<span class="signal-badge" style="background:'+(m[k]==="金叉"?"{RED}":"{GREEN}")+'">'+k+' '+(m[k]==="金叉"?"▲":"▼")+'</span>'}}
    if(!v)v='<span class="no-signal">—</span>';
    ind=s.indicators||{{}};
    p="";
    ["BOLL","MA10","MACD","KDJ","RSI"].forEach(function(k){{
      st=m[k]||"";bg="{MUTED}";cl="{TEXT3}";
      if(st==="金叉"){{bg="{RED_BG}";cl="{TEXT}"}}
      if(st==="死叉"){{bg="{GREEN_BG}";cl="{TEXT}"}}
      p+='<span class="pill" style="background:'+bg+';color:'+cl+'"><b>'+k+'</b>: '+(ind[k]||"-")+'</span>'
    }});
    h+='<div class="stock-card'+(ch>0?" up":ch<0?" down":"")+'" onclick="t(this)">'+
      '<div class="card-top">'+
        '<span class="name">'+s.name+'</span>'+
        '<span class="code">'+s.code+'</span>'+
        '<span class="mkt">'+s.market+'</span>'+
        '<span class="spacer"></span>'+
        '<span class="price">'+(s.close||"-")+'</span>'+
        '<span class="change" style="color:'+c+'">'+(ch>=0?"+":"")+ch.toFixed(2)+"%</span>"+
      '</div>'+
      '<div class="signal-row">'+v+'</div>'+
      '<div class="expand-hint"><span class="arrow">▸</span> 指标详情</div>'+
      '<div class="indicator-pills">'+p+'</div>'+
    '</div>'
  }}
  return h||'<div class="empty">暂无数据</div>'
}}'''


def generate():
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

    history_dir = os.path.join(SITE_DIR, "history")
    history_dates = []
    if os.path.isdir(history_dir):
        for fname in sorted(os.listdir(history_dir), reverse=True):
            if fname.endswith(".json"):
                history_dates.append(fname.replace(".json", ""))

    if history_dates:
        opts = ""
        for d in history_dates:
            sel = " selected" if d == history_dates[0] else ""
            opts += f'<option value="{d}"{sel}>{d}</option>\n'
        history_bar = f'''<div class="date-bar">
            <label>历史日期</label>
            <select id="ds" onchange="L(this.value)">{opts}</select>
            <span id="ld" style="display:none">加载中...</span>
        </div>'''
    else:
        history_bar = ""

    summary_html = f'更新: {update_time}<span style="margin:0 6px;color:{TEXT3}">|</span>监控 <b>{total}</b> 只<span style="margin:0 6px;color:{TEXT3}">|</span>信号 <b style="color:{BLUE}">{signal_count}</b> 只'

    import json as _json
    cards_js = (
        f'var LD={{meta:`{summary_html}`,html:`__`}};'
        f'document.getElementById("meta").innerHTML=LD.meta;'
        f'document.getElementById("list").innerHTML=B({_json.dumps(stocks, ensure_ascii=False)});'
    )

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=yes">
<title>股票指标监控</title>
<style>{CSS}</style>
</head>
<body>
<div class="w">
<header>
  <div class="eyebrow">Stock Monitor</div>
  <h1>技术指标</h1>
  <div class="summary" id="meta">{summary_html}</div>
  <div class="params">BOLL(20,2) · MA10 · MACD(19,39,9) · KDJ(18,3,3) · RSI(21,7)</div>
  {history_bar}
</header>
<div id="list"></div>
<footer>每个交易日 11:00 / 14:30 更新 · GitHub Actions</footer>
</div>
<script>
{JS}
{cards_js}
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
