"""初始化设置脚本"""

import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

MARKET_OPTIONS = {
    "1": ("SH", "上海A股"),
    "2": ("SZ", "深圳A股"),
    "3": ("HK", "港股"),
    "4": ("US", "美股"),
}


def get_stock_list():
    """交互式获取自选股列表"""
    stocks = []

    print("\n请添加要监控的股票（输入空代码结束）:")
    print("示例: A股 600519(茅台), 000001(平安) | 港股 00700(腾讯) | 美股 AAPL(苹果)")
    print("-" * 50)

    while True:
        code = input("股票代码（直接回车结束）: ").strip()
        if not code:
            if not stocks:
                print("至少需要添加一只股票！")
                continue
            break

        code = code.upper()

        # 显示市场选项
        print("\n选择市场:")
        for k, (_, name) in MARKET_OPTIONS.items():
            print(f"  {k}. {name}")
        market_choice = input(f"市场 (1-4, 默认1): ").strip() or "1"
        market = MARKET_OPTIONS.get(market_choice, MARKET_OPTIONS["1"])[0]

        name = input("股票名称（可选，直接回车自动识别）: ").strip()

        stocks.append({
            "code": code,
            "market": market,
            "name": name if name else code,
        })
        print(f"  ✅ 已添加: {code} ({market})")
        print("-" * 50)

    return stocks


def setup_email():
    """设置邮箱配置"""
    print("\n📧 邮箱配置")
    print("-" * 50)
    print("请确保已在QQ邮箱开启SMTP服务并获取授权码")
    print("开启方法: QQ邮箱 -> 设置 -> 账户 -> POP3/SMTP服务 -> 生成授权码")
    print("-" * 50)

    sender = input("发件邮箱: ").strip()
    while not sender:
        sender = input("发件邮箱不能为空: ").strip()

    password = input("SMTP授权码: ").strip()
    while not password:
        password = input("授权码不能为空: ").strip()

    receiver = input("收件邮箱（直接回车使用1737730809@qq.com）: ").strip()
    if not receiver:
        receiver = "1737730809@qq.com"

    return {
        "smtp_server": "smtp.qq.com",
        "smtp_port": 465,
        "sender": sender,
        "password": password,
        "receiver": receiver,
    }


def setup():
    """运行初始化设置"""
    print("=" * 50)
    print("📊 股票技术指标监控 - 初始化设置")
    print("=" * 50)

    stocks = get_stock_list()
    email = setup_email()

    config = {
        "stocks": stocks,
        "email": email,
    }

    save_config(config)

    print("\n" + "=" * 50)
    print("✅ 设置完成！")
    print(f"   监控股票: {len(stocks)} 只")
    print(f"   接收邮箱: {email['receiver']}")
    print(f"   配置文件: {CONFIG_FILE}")
    print("=" * 50)
    print("\n💡 运行监控: python monitor.py")
    print("💡 定时监控推荐使用 Windows 任务计划程序")
    print("   （支持交易时段每30分钟自动运行）")


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 配置已保存: {CONFIG_FILE}")


def edit_stocks():
    """编辑自选股列表"""
    config = load_config()
    if not config:
        print("未找到配置文件，请先运行完整设置")
        return

    print(f"\n当前自选股 ({len(config['stocks'])} 只):")
    for i, s in enumerate(config["stocks"], 1):
        print(f"  {i}. [{s['market']}] {s['code']} - {s.get('name', '')}")

    print("\n操作: 1. 添加  2. 删除  3. 清空并重新添加")
    op = input("请选择 (1/2/3): ").strip()

    if op == "1":
        new_stocks = get_stock_list()
        config["stocks"].extend(new_stocks)
    elif op == "2":
        idx = int(input("输入要删除的序号: ")) - 1
        if 0 <= idx < len(config["stocks"]):
            removed = config["stocks"].pop(idx)
            print(f"已删除: {removed}")
    elif op == "3":
        config["stocks"] = get_stock_list()

    save_config(config)


def edit_email():
    """编辑邮箱配置"""
    config = load_config()
    if not config:
        config = {}

    config["email"] = setup_email()
    save_config(config)


if __name__ == "__main__":
    print("📊 股票监控设置工具")
    print("1. 完整初始化设置")
    print("2. 编辑自选股")
    print("3. 编辑邮箱配置")
    choice = input("请选择 (1/2/3): ").strip()

    if choice == "1":
        setup()
    elif choice == "2":
        edit_stocks()
    elif choice == "3":
        edit_email()
    else:
        print("无效选择")
