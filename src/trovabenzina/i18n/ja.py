# JA - 日本語
TRANSLATIONS = {
    # ─────────── config ───────────
    "language_code": "ja",
    "language_name": "日本語",
    "gasoline": "ガソリン",
    "diesel": "ディーゼル",
    "cng": "圧縮天然ガス",
    "lpg": "液化石油ガス",
    "liter_symbol": "L",
    "kilo_symbol": "kg",

    # ─────────── /start ───────────
    "select_language": "言語を選択 🌐️",
    "invalid_language": "⚠️ 無効な言語です！",
    "select_fuel": "燃料を選択 ⛽",
    "invalid_fuel": "⚠️ 無効な燃料です！",
    "profile_saved": "✅ プロフィールを保存しました！\n\n/search コマンドで検索を開始できます。",
    "user_already_registered": "⚠️ すでに登録済みのユーザーです！\n\n設定を変更するには /profile、検索を開始するには /search を使用してください。",

    # ─────────── /help ───────────
    "help": (
        "🚀 /start – ボットを開始してプロフィールを設定\n"
        "🔍 /search – 最安の給油所を検索\n"
        "👤 /profile – 設定を表示・編集\n"
        "📊 /statistics – 統計を表示\n"
        "📢 /help – このメッセージを表示\n\n"
    ),
    "disclaimer": (
        "ℹ️ 給油所データは <b>イタリア企業・メイド・イン・イタリー省（MISE）</b> によって提供されています。\n"
        "ボットが表示する情報の正確性や最新性は保証されません。"
    ),

    # ─────────── /profile ───────────
    "language": "🌐️ 言語",
    "fuel": "⛽ 燃料",
    "edit_language": "言語を編集 🌐️",
    "edit_fuel": "燃料を編集 ⛽",
    "language_updated": "✅ 言語を更新しました！",
    "fuel_updated": "✅ 燃料を更新しました！",

    # ─────────── /search ───────────
    "choose_search_mode": "検索の種類を選択してください。",
    "btn_search_zone": "地点の周辺 📌",
    "btn_search_route": "ルート沿い 🛣️",
    "ask_location": "住所を入力するか、位置情報を送信してください 📍",
    "ask_route_origin": "出発地の住所を入力してください。",
    "ask_route_destination": "到着地の住所を入力してください。",
    "send_location": "GPS 位置情報を送信 🌍",
    "geocode_cap_reached": "⚠️ 現在、住所の認識は利用できません！\n\n後でもう一度お試しいただくか、位置情報を送信してください。",
    "invalid_address": "⚠️ 無効な住所です！\n\n別の住所を入力するか、位置情報を送信してください。",
    "italy_only": "⚠️ 検索はイタリア国内のみ利用可能です！\n\nイタリアの住所を入力するか、位置情報を送信してください。",
    "processing_search": "検索中です。🔍",
    "please_wait": "処理中です。少々お待ちください。⏳",
    "search_temporarily_unavailable": "⚠️ サービスは一時的に利用できません。\n\nしばらくしてからもう一度お試しください。",
    "no_stations": "❌ スタンドが見つかりませんでした",
    "area_label": "{radius} km 圏内のスタンド",
    "stations_analyzed": "件のスタンドを分析",
    "average_zone_price": "エリアの {fuel_name} 平均価格",
    "route_label": "ルート沿いのスタンド",
    "average_route_price": "ルート沿いの{fuel_name}平均価格",
    "address": "住所",
    "no_address": "-",
    "price": "価格",
    "eur_symbol": "€",
    "slash_symbol": "/\u200b",
    "below_average": "平均より安い",
    "equal_average": "平均並み",
    "last_update": "最終更新",
    "btn_narrow": "半径 {radius} km で再検索 🔄",
    "btn_widen": "半径 {radius} km で再検索 🔄",
    "search_session_expired": "⚠️ セッションの有効期限が切れました！\n\n新しく検索するには /search を使用してください。",

    # ─────────── /statistics ───────────
    "no_statistics": "⚠️ 利用できる統計はありません！\n\n/search を使って検索を開始してください。",
    "statistics": (
        "<b><u>{fuel_name} の統計</u></b> 📊\n"
        "<b>{num_searches} 件の検索</b> を実行しました。\n"
        "<b>{num_stations} 箇所のスタンド</b> を分析しました。\n"
        "平均節約額：<b>{avg_eur_save_per_unit} {price_unit}</b>、すなわち <b>{avg_pct_save}%</b>。\n"
        "推定年間節約額：<b>{estimated_annual_save_eur}</b>。"
    ),
    "statistics_info": "<i>❓ これらの数値はどのように計算していますか？</i>\n"
                       "• 平均節約額は、各検索におけるエリア平均価格とボットが見つけた最安スタンドの価格差の平均です。\n"
                       "• 年間節約額は、年間 10,000km の走行と次の平均消費量を前提としています: \n",
    "fuel_consumption": "  - {fuel_name} = {avg_consumption_per_100km}{uom} /100km あたり",
    "reset_statistics": "統計をリセット ♻️",
    "statistics_reset": "✅ 統計をリセットしました！\n\n/search を使って検索を開始してください。",

    "unknown_command_hint": "⚠️ 無効なコマンドです！\n\n利用可能なコマンド一覧は /help コマンドで確認できます。",

}
