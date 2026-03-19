# ZH - 中文
TRANSLATIONS = {
    # ─────────── config ───────────
    "language_code": "zh",
    "language_name": "中文",
    "gasoline": "汽油",
    "diesel": "柴油",
    "cng": "压缩天然气",
    "lpg": "液化石油气",
    "liter_symbol": "L",
    "kilo_symbol": "kg",

    # ─────────── /start ───────────
    "select_language": "选择语言 🌐️",
    "invalid_language": "⚠️ 语言无效！",
    "select_fuel": "选择燃料 ⛽",
    "invalid_fuel": "⚠️ 燃料无效！",
    "profile_saved": "✅ 个人资料已保存！\n\n使用 /search 开始一次搜索。",
    "user_already_registered": "⚠️ 用户已注册！\n\n使用 /profile 修改偏好设置，或使用 /search 开始搜索。",

    # ─────────── /help ───────────
    "help": (
        "🚀 /start – 启动机器人并设置个人资料\n"
        "🔍 /search – 查找最便宜的加油站\n"
        "👤 /profile – 查看并修改设置\n"
        "📊 /statistics – 查看统计数据\n"
        "📢 /help – 显示此消息\n\n"
    ),
    "disclaimer": (
        "ℹ️ 加油站数据由 <b>意大利企业与制造部（MISE）</b> 提供。\n"
        "机器人显示的信息不保证准确或及时。"
    ),

    # ─────────── /profile ───────────
    "language": "🌐️ 语言",
    "fuel": "⛽ 燃料",
    "edit_language": "修改语言 🌐️",
    "edit_fuel": "修改燃料 ⛽",
    "language_updated": "✅ 语言已更新！",
    "fuel_updated": "✅ 燃料已更新！",

    # ─────────── /search ───────────
    "ask_location": "输入地址或发送你的位置 📍",
    "send_location": "发送 GPS 位置 🌍",
    "geocode_cap_reached": "⚠️ 目前无法识别地址！\n\n请稍后再试，或者发送你的位置。",
    "invalid_address": "⚠️ 地址无效！\n\n请输入其他地址或发送你的位置。",
    "italy_only": "⚠️ 搜索仅限意大利！\n\n请输入意大利地址或发送你的位置。",
    "processing_search": "正在搜索。🔍",
    "please_wait": "正在处理，请稍候。⏳",
    "search_temporarily_unavailable": "⚠️ 服务暂时不可用！\n\n请稍后再试。",
    "no_stations": "❌ 未找到加油站",
    "area_label": "半径 {radius} 公里内的加油站",
    "stations_analyzed": "个加油站已分析",
    "average_zone_price": "区域 {fuel_name} 平均价格",
    "address": "地址",
    "no_address": "-",
    "price": "价格",
    "eur_symbol": "€",
    "slash_symbol": "/\u200b",
    "below_average": "低于平均价",
    "equal_average": "与平均价相当",
    "last_update": "最后更新",
    "btn_narrow": "以 {radius} 公里半径重复搜索 🔄",
    "btn_widen": "以 {radius} 公里半径重复搜索 🔄",
    "search_session_expired": "⚠️ 会话已过期！\n\n使用 /search 开始新的搜索。",

    # ─────────── /statistics ───────────
    "no_statistics": "⚠️ 暂无统计数据！\n\n使用 /search 开始一次搜索。",
    "statistics": (
        "<b><u>{fuel_name} 统计</u></b> 📊\n"
        "<b>已进行 {num_searches} 次搜索</b>。\n"
        "<b>已分析 {num_stations} 个加油站</b>。\n"
        "平均节省：<b>{avg_eur_save_per_unit} {price_unit}</b>，即 <b>{avg_pct_save}%</b>。\n"
        "预计年度节省：<b>{estimated_annual_save_eur}</b>。"
    ),
    "statistics_info": "<i>❓ 我们如何计算这些数据？</i>\n"
                       "• 平均节省是所有搜索中，区域平均价与机器人找到的最低价格之间差值的平均值。\n"
                       "• 年度节省假设每年行驶 10,000km，平均油耗为： \n",
    "fuel_consumption": "  - {fuel_name} = {avg_consumption_per_100km}{uom} 每 100km",
    "reset_statistics": "重置统计数据 ♻️",
    "statistics_reset": "✅ 统计数据已重置！\n\n使用 /search 开始一次搜索。",

    "unknown_command_hint": "⚠️ 命令无效！\n\n使用 /help 命令查看可用命令列表。",

}
