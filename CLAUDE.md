# Stock Monitor - 股票技术指标监控系统

## 项目概述
Python股票技术指标监控系统，定时获取A股/港股/美股数据，检测MACD/KDJ/RSI/MA10/BOLL的金叉死叉信号，通过QQ邮箱发送提醒，并生成GitHub Pages静态仪表盘。

## 需求来源（2026-05-10）
- 从富途牛牛自选股同步监控列表（方案二：手动配置）
- MACD/KDJ/RSI 任意一项金叉或死叉时邮件提醒
- 每个股票独立卡片展示，重点信息高亮
- 卡片按涨跌幅由大到小排序
- 部署到GitHub Pages，固定域名，关闭本地电脑后也能查看

## 技术指标参数
| 指标 | 参数 | 信号条件 |
|------|------|----------|
| MACD | DIF(EMA19-EMA39), DEA(EMA9), Hist | DIF上穿/下穿DEA |
| KDJ | RSV(18), K(3), D(3) | K上穿/下穿D |
| RSI | 慢线(21), 快线(7) | 快线上穿/下穿慢线 |
| MA10 | SMA(10) | 收盘价上穿/下穿MA10 |
| BOLL | SMA(20), ±2σ | 收盘价上穿/下穿中轨 |

## 技术栈
- Python 3（纯标准库 + requests，已移除 matplotlib/numpy）
- 数据源：腾讯财经API（A股/港股）、Yahoo Finance API（美股）
- 邮件：QQ邮箱 SMTP（SSL 465端口）
- 部署：GitHub Pages（gh-pages分支）

## 文件结构
| 文件 | 用途 |
|------|------|
| monitor.py | 主程序，遍历自选股检测信号并发送邮件 |
| stock_data.py | 股票数据获取（腾讯/Yahoo API） |
| indicators.py | 技术指标计算（纯Python，零依赖） |
| email_sender.py | QQ邮箱SMTP发送 |
| site_generator.py | 生成GitHub Pages静态站点 index.html |
| setup.py | 交互式配置（自选股+邮箱） |
| test_email.py | 测试邮件发送（模拟数据） |
| run_monitor.bat | Windows调度入口，调用monitor.py并记录日志 |
| schedule_task.bat | Windows任务计划管理（创建/删除/查看） |
| setup_scheduled_task.ps1 | 创建交易日14:30定时任务（需管理员权限） |
| config.json | 配置文件（自选股+邮箱，已在.gitignore中排除） |
| config.template.json | 配置模板 |

## 配色方案（轻快明亮，红涨绿跌）
- 主背景：#F0F4F8 / 卡片：#FFFFFF / 主文字：#2C3E50
- 涨/金叉：#E74C3C（红色） / 跌/死叉：#27AE60（绿色）
- 强调色：#3498DB（蓝色） / 中性：#7F8C8D

## 推送机制（双通道，本地关了也能推送）

### 通道1：本地Windows定时任务
- Windows任务计划程序，交易日（周一至周五）14:30自动运行
- run_monitor.bat → monitor.py → monitor_log.txt

### 通道2：GitHub Actions CI/CD（云端自动运行）
- 工作流文件：`.github/workflows/stock_check.yml`
- 触发时间：UTC 3:00（北京时间11:00）+ UTC 6:30（北京时间14:30），周一至周五
- 流程：checkout → pip install requests → decode config → run monitor → generate site → deploy to gh-pages
- config.json 通过 GitHub Secret `CONFIG_JSON` 以 base64 编码存储
- 站点通过 `peaceiris/actions-gh-pages@v4` 自动部署到 gh-pages 分支

### 邮件推送
- 检测到信号 → QQ邮箱SMTP HTML邮件 → 1737730809@qq.com
- 发件邮箱：1737730809@qq.com，授权码存储在 config.json 和 GitHub Secret 中

### 站点地址
- https://herodalev.github.io/stock-monitor/site/

## 排序规则
- 信号列表按涨跌幅从大到小排序
- 全量结果同样按涨跌幅从大到小排序
- 站点表格保持排序后的顺序展示

## 当前配置
- 发件/收件邮箱：1737730809@qq.com
- SMTP：smtp.qq.com:465 SSL，授权码已配置在 config.json
- 自选股待完善（当前为 config.template.json 中的示例）

## 部署信息
- GitHub仓库：https://github.com/herodalev/stock-monitor
- GitHub Pages：https://herodalev.github.io/stock-monitor/site/
- gh-pages分支用于静态站点部署

## 指标显示（胶囊样式，颜色联动信号）
- 每个指标独立胶囊卡片，圆角6px，带间距
- 胶囊颜色与金叉/死叉信号联动：
  - 金叉 → 浅红底 #FDEDEC（呼应红色金叉标签）
  - 死叉 → 浅绿底 #E8F8F0（呼应绿色死叉标签）
  - 无信号 → 弱化灰底 #F0F4F8 + 浅色文字
- 第一行：BOLL(20,2) | MA10
- 第二行：MACD(19,39,9) | KDJ(18,3,3) | RSI(21,7)

## 历史变更
- 2026-05-11：删除K线图及matplotlib依赖；indicators.py用纯Python重写（去numpy）；莫兰迪配色→轻快明亮配色；金叉=红色/死叉=绿色；指标顺序调整为 BOLL/MA10/MACD/KDJ/RSI；修正GitHub Actions工作流依赖
- 2026-05-10：初始创建，实现指标检测+邮件+站点+定时任务+CI/CD
