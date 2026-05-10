# Stock Monitor - 股票技术指标监控系统

## 项目概述
Python股票技术指标监控系统，定时获取A股/港股/美股数据，检测MACD/KDJ/RSI/MA10/BOLL的金叉死叉信号，通过QQ邮箱发送提醒，并生成GitHub Pages静态仪表盘。

## 需求来源（2026-05-10）
- 从富途牛牛自选股同步监控列表（方案二：手动配置 config.json）
- MACD/KDJ/RSI 任意一项金叉或死叉时邮件提醒
- 每个股票独立卡片展示，重点信息高亮
- 卡片按涨跌幅由大到小排序
- 部署到GitHub Pages，固定域名，关闭本地电脑后也能查看
- 固定域名支持按日期查看历史推送

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
- 部署：GitHub Pages（gh-pages分支，peaceiris/actions-gh-pages@v4）

## 文件结构
| 文件 | 用途 |
|------|------|
| monitor.py | 主程序，遍历自选股检测信号并发送邮件 |
| stock_data.py | 股票数据获取（腾讯/Yahoo API） |
| indicators.py | 技术指标计算（纯Python，零依赖） |
| email_sender.py | QQ邮箱SMTP发送 |
| site_generator.py | 生成GitHub Pages静态站点（支持历史日期选择） |
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
- Windows任务计划程序，交易日 14:30
- run_monitor.bat → monitor.py → monitor_log.txt

### 通道2：GitHub Actions CI/CD（云端自动运行）
- 工作流：`.github/workflows/stock_check.yml`
- 触发：UTC 3:00（11:00 CST）+ UTC 6:30（14:30 CST），周一至周五
- 流程：checkout → pip install requests → decode config → run monitor → site_generator → deploy gh-pages
- config.json 通过 GitHub Secret `CONFIG_JSON` 以 base64 编码

### 邮件推送
- 检测到信号 → QQ邮箱SMTP HTML邮件 → 1737730809@qq.com

### 站点地址（固定域名）
- **https://herodalev.github.io/stock-monitor/**
- 站点内容部署在 gh-pages 分支根目录（peaceiris 将 ./site 发布为根）

## 站点历史功能
- 每次运行 monitor.py 后，数据自动存档到 `site/history/YYYY-MM-DD.json`
- 站点顶部有日期选择器，可切换查看任意历史日期的数据
- 默认显示最新数据，切换日期时通过 JS fetch 历史 JSON 并动态渲染

## 排序规则
- 信号列表按涨跌幅从大到小排序
- 全量结果同样按涨跌幅从大到小排序

## 指标显示（胶囊样式，颜色联动信号）
- 每个指标独立胶囊卡片，圆角6px
- 胶囊颜色与金叉/死叉信号联动：
  - 金叉 → 浅红底 #FDEDEC
  - 死叉 → 浅绿底 #E8F8F0
  - 无信号 → 弱化灰底 #F0F4F8 + 浅色文字
- 第一行：BOLL(20,2) | MA10
- 第二行：MACD(19,39,9) | KDJ(18,3,3) | RSI(21,7)

## 当前配置
- 发件/收件邮箱：1737730809@qq.com
- SMTP：smtp.qq.com:465 SSL
- 自选股：约70只，覆盖A股ETF/个股、港股、美股（详见 config.json）

## 部署信息
- GitHub仓库：https://github.com/herodalev/stock-monitor
- GitHub Pages：https://herodalev.github.io/stock-monitor/

## 历史变更
- 2026-05-11：轻快明亮配色 + 金叉=红/死叉=绿；删除K线图及matplotlib/numpy；indicators.py纯Python重写；指标胶囊样式联动信号；站点支持按日期查看历史；GitHub Actions新增11:00推送；修正站点URL（gh-pages根目录）
- 2026-05-10：初始创建，指标检测+邮件+站点+CI/CD+定时任务
