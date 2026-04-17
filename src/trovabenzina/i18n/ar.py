# AR - العربية
TRANSLATIONS = {
    # ─────────── config ───────────
    "language_code": "ar",
    "language_name": "العربية",
    "gasoline": "بنزين",
    "diesel": "ديزل",
    "cng": "الغاز الطبيعي المضغوط",
    "lpg": "غاز البترول المسال",
    "liter_symbol": "L",
    "kilo_symbol": "كغ",

    # ─────────── /start ───────────
    "select_language": "اختر اللغة 🌐️",
    "invalid_language": "⚠️ لغة غير صالحة!",
    "select_fuel": "اختر الوقود ⛽",
    "invalid_fuel": "⚠️ وقود غير صالح!",
    "profile_saved": "✅ تم حفظ الملف الشخصي بنجاح!\n\nاستخدم /search لبدء البحث.",
    "user_already_registered": "⚠️ المستخدم مسجّل بالفعل!\n\nاستخدم /profile لتغيير التفضيلات أو /search لبدء البحث.",

    # ─────────── /help ───────────
    "help": (
        "🚀 /start – بدء البوت وإعداد ملفك الشخصي\n"
        "🔍 /search – العثور على أرخص محطات الوقود\n"
        "👤 /profile – عرض إعداداتك وتعديلها\n"
        "📊 /statistics – عرض إحصاءاتك\n"
        "📢 /help – عرض هذه الرسالة\n\n"
    ),
    "disclaimer": (
        "ℹ️ بيانات الأسعار مقدّمة من <b>وزارة الشركات وصُنع في إيطاليا (MISE)</b>.\n"
        "لا نضمن دقّة أو حداثة المعلومات التي يعرضها البوت."
    ),

    # ─────────── /profile ───────────
    "language": "🌐️ اللغة",
    "fuel": "⛽ الوقود",
    "edit_language": "تعديل اللغة 🌐️",
    "edit_fuel": "تعديل الوقود ⛽",
    "language_updated": "✅ تم تحديث اللغة بنجاح!",
    "fuel_updated": "✅ تم تحديث الوقود بنجاح!",

    # ─────────── /search ───────────
    "choose_search_mode": "اختر نوع البحث.",
    "btn_search_zone": "بالقرب من نقطة 📌",
    "btn_search_route": "على طول مسار 🛣️",
    "ask_location": "اكتب عنوانًا أو أرسل موقعك 📍",
    "ask_route_origin": "اكتب عنوان الانطلاق.",
    "ask_route_destination": "اكتب عنوان الوصول.",
    "send_location": "إرسال الموقع عبر GPS 🌍",
    "geocode_cap_reached": "⚠️ التعرّف على العناوين غير متاح حاليًا!\n\nيرجى المحاولة لاحقًا أو إرسال موقعك.",
    "invalid_address": "⚠️ عنوان غير صالح!\n\nأدخل عنوانًا آخر أو أرسل موقعك.",
    "italy_only": "⚠️ البحث متاح فقط في إيطاليا!\n\nأدخل عنوانًا في إيطاليا أو أرسل موقعك.",
    "processing_search": "جارٍ البحث...🔍",
    "please_wait": "جارٍ العمل، يرجى الانتظار...⏳",
    "search_temporarily_unavailable": "⚠️ الخدمة غير متاحة مؤقتاً!\n\nيرجى المحاولة مرة أخرى لاحقاً.",
    "no_stations": "❌ لم يتم العثور على محطات",
    "area_label": "محطات ضمن نطاق {radius} كم",
    "stations_analyzed": "محطات مُحلّلة",
    "average_zone_price": "متوسط سعر {fuel_name} في المنطقة",
    "route_label": "محطات على طول المسار",
    "average_route_price": "متوسط سعر {fuel_name} على طول المسار",
    "address": "العنوان",
    "no_address": "-",
    "price": "السعر",
    "eur_symbol": "€",
    "slash_symbol": "/\u200b",
    "below_average": "أرخص من المتوسّط",
    "equal_average": "مماثل للمتوسّط",
    "last_update": "آخر تحديث",
    "btn_narrow": "إعادة البحث بنطاق {radius} كم 🔄",
    "btn_widen": "إعادة البحث بنطاق {radius} كم 🔄",
    "search_session_expired": "⚠️ انتهت الجلسة!\n\nاستخدم /search لبدء بحث جديد.",

    # ─────────── /statistics ───────────
    "no_statistics": "⚠️ لا توجد إحصاءات متاحة!\n\nاستخدم /search لبدء البحث.",
    "statistics": (
        "<b><u>إحصائيات {fuel_name}</u></b> 📊\n"
        "<b>{num_searches} عمليات بحث</b> تم تنفيذها.\n"
        "<b>{num_stations} محطة</b> جرى تحليلها.\n"
        "المتوسط الموفَّر: <b>{avg_eur_save_per_unit} {price_unit}</b>، أي <b>{avg_pct_save}%</b>.\n"
        "التوفير السنوي التقديري: <b>{estimated_annual_save_eur}</b>."
    ),
    "statistics_info": "<i>❓ كيف حُسِبت هذه الأرقام؟</i>\n"
                       "• يُحسب المتوسط الموفَّر كمتوسط الفارق، عبر جميع عمليات البحث، بين متوسط سعر المنطقة وأرخص محطة يعثر عليها البوت.\n"
                       "• يُحتسب التوفير السنوي بافتراض قطع 10,000 كم سنويًا مع متوسط استهلاك قدره: \n",
    "fuel_consumption": "  - {fuel_name} = {avg_consumption_per_100km}{uom} لكل 100 كم",
    "reset_statistics": "إعادة تعيين الإحصاءات ♻️",
    "statistics_reset": "✅ تمت إعادة تعيين الإحصاءات بنجاح!\n\nاستخدم /search لبدء البحث.",

    "unknown_command_hint": "⚠️ أمر غير صالح!\n\nاستخدم الأمر /help لعرض قائمة الأوامر المتاحة.",

}
