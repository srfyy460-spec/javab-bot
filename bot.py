import os
import random
import asyncio
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CopyTextButton
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from ddgs import DDGS

# ==============================
# SETTINGS
# ==============================

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

# ==============================
# CATEGORIES
# ==============================

CATEGORIES = {
    "roast": {
        "name": "😂 خیت کردن",
        "emoji": "😂"
    },
    "love": {
        "name": "❤️ مخ زدن",
        "emoji": "❤️"
    },
    "classy": {
        "name": "🗿 سنگین و باکلاس",
        "emoji": "🗿"
    },
    "fight": {
        "name": "🔥 کل‌کل و دعوا",
        "emoji": "🔥"
    },
    "funny": {
        "name": "🤣 طنز و شوخی",
        "emoji": "🤣"
    },
    "quick": {
        "name": "⚡ جواب فوری",
        "emoji": "⚡"
    }
}

# ==============================
# LOCAL ANSWER DATABASE
# ==============================

LOCAL_BANK = {
    "roast": [
        {
            "keywords": ["خودتو میگیری", "مغرور", "غرور"],
            "answers": [
                "خودمو نمی‌گیرم، فقط هرکسی ارزش نزدیک شدن نداره 😎",
                "تو اول به خودت برس، بعد منو تحلیل کن 😂",
                "اعتمادبه‌نفس من مشکل تو نیست!"
            ]
        },
        {
            "keywords": ["احمق", "نفهم", "نادان"],
            "answers": [
                "وقتی حرف حساب نداری، طبیعیه بری سراغ توهین 😂",
                "سطح بحثت رو نشون دادی، ممنون!",
                "قرار نیست همه به اندازه تو فکر کنن 😏"
            ]
        },
        {
            "keywords": ["زشت", "قیافه", "قیافه ات"],
            "answers": [
                "خوشحالم انقدر وقت داری به من فکر کنی 😂",
                "سلیقه‌ات رو کسی نپرسیده بود!",
                "نگران قیافه من نباش، آینه خودت رو چک کن."
            ]
        }
    ],

    "love": [
        {
            "keywords": ["دوستت دارم", "عاشقتم"],
            "answers": [
                "پس مواظب قلبم باش، راحت به دست نیومده ❤️",
                "این حرفت قشنگ‌ترین اتفاق امروزمه 🥹",
                "منم دارم بهت بیشتر از چیزی که فکر می‌کنی علاقه‌مند می‌شم."
            ]
        },
        {
            "keywords": ["دلم برات", "دلتنگ"],
            "answers": [
                "پس بیا کاری کنیم کمتر دلتنگ هم بشیم ❤️",
                "منم جای خالیت رو حس می‌کنم.",
                "کاش فاصله فقط یه کلمه بود."
            ]
        },
        {
            "keywords": ["خوشگلی", "زیبایی", "قشنگی"],
            "answers": [
                "قشنگی از نگاه قشنگ توئه ❤️",
                "تو تعریف می‌کنی یا داری دلمو می‌بری؟ 😂",
                "پس باید بیشتر جلوی چشم تو باشم!"
            ]
        }
    ],

    "classy": [
        {
            "keywords": ["بی ارزش", "ارزش نداری"],
            "answers": [
                "ارزش هرکس رو رفتارش مشخص می‌کنه، نه قضاوت دیگران.",
                "نیازی به اثبات خودم به همه ندارم.",
                "ترجیح می‌دم سکوت کنم تا سطح بحث پایین نیاد."
            ]
        },
        {
            "keywords": ["ضعیف", "ترسو"],
            "answers": [
                "قدرت واقعی نیازی به نمایش نداره.",
                "هرکسی تعریف متفاوتی از قدرت داره.",
                "قضاوت تو چیزی از واقعیت کم نمی‌کنه."
            ]
        }
    ],

    "fight": [
        {
            "keywords": ["خفه", "ساکت", "ساکت شو"],
            "answers": [
                "وقتی حرفی برای گفتن نیست، سکوت بهترین انتخابه.",
                "اول یاد بگیر چطور صحبت کنی.",
                "صدای بلند جای منطق رو نمی‌گیره."
            ]
        },
        {
            "keywords": ["میترسی", "ترسیدی"],
            "answers": [
                "ترس و احتیاط رو با هم اشتباه نگیر.",
                "لازم نیست برای کسی چیزی رو ثابت کنم.",
                "اعتمادبه‌نفس با سر و صدا فرق داره."
            ]
        }
    ],

    "funny": [
        {
            "keywords": ["چطوری", "خوبی"],
            "answers": [
                "فعلاً زنده‌ام، تو چطوری؟ 😂",
                "مثل اینترنت ضعیف، گاهی وصل گاهی قطع!",
                "عالی‌ام، فقط دنیا هنوز خبر نداره!"
            ]
        },
        {
            "keywords": ["کجایی", "کجا هستی"],
            "answers": [
                "درگیر پروژه نجات جهان، فعلاً وقت ندارم 😂",
                "تو فکر اینکه چرا این سؤال رو پرسیدی!",
                "یه جای امن، دور از مشکلات!"
            ]
        }
    ]
}

# ==============================
# MAIN MENU
# ==============================

def main_menu():
    keyboard = []

    for key, value in CATEGORIES.items():
        keyboard.append([
            InlineKeyboardButton(
                value["name"],
                callback_data=f"cat_{key}"
            )
        ])

    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "😈 به ربات حاضر جواب خوش اومدی!\n\n"
        "هر حرفی شنیدی وارد کن تا جواب مناسبش رو پیدا کنیم.\n\n"
        "یکی از دسته‌بندی‌ها رو انتخاب کن:",
        reply_markup=main_menu()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 راهنمای ربات\n\n"
        "/start شروع ربات\n"
        "/menu نمایش دسته‌بندی‌ها\n"
        "/cancel لغو عملیات\n\n"
        "یک دسته‌بندی انتخاب کن، جمله رو بفرست و جواب بگیر!"
    )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "دسته‌بندی مورد نظرت رو انتخاب کن:",
        reply_markup=main_menu()
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "عملیات لغو شد.",
        reply_markup=main_menu()
    )


# ==============================
# CATEGORY SELECTION
# ==============================

async def category_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    category = query.data.replace("cat_", "")

    if category not in CATEGORIES:
        return

    context.user_data["category"] = category

    await query.message.reply_text(
        f"{CATEGORIES[category]['name']}\n\n"
        "حالا جمله‌ای که طرف مقابل گفته رو بفرست. 👇"
    )


# ==============================
# SEARCH ENGINE
# ==============================

def search_web(query, category):
    search_terms = {
        "roast": "جواب دندان شکن حاضر جوابی",
        "love": "جملات عاشقانه و مخ زنی",
        "classy": "جواب سنگین و باکلاس",
        "fight": "جواب محکم برای کل کل",
        "funny": "جواب طنز و خنده دار",
        "quick": "جواب حاضر جوابی مناسب"
    }

    search_query = (
        f"{query} {search_terms.get(category, '')} فارسی"
    )

    results = []

    try:
        with DDGS() as ddgs:
            found = ddgs.text(
                search_query,
                max_results=5
            )

            for item in found:
                title = item.get("title", "")
                body = item.get("body", "")
                url = item.get("href", "")

                if title or body:
                    results.append({
                        "title": title,
                        "body": body,
                        "url": url
                    })

    except Exception as error:
        logging.warning("Search error: %s", error)

    return results


# ==============================
# LOCAL ANSWER FINDER
# ==============================

def find_local_answers(category, message):
    if category not in LOCAL_BANK:
        return []

    text = message.lower().replace("ي", "ی").replace("ك", "ک")

    answers = []

    for item in LOCAL_BANK[category]:
        for keyword in item["keywords"]:
            if keyword in text:
                answers.extend(item["answers"])
                break

    return list(dict.fromkeys(answers))


# ==============================
# ANSWER DISPLAY
# ==============================

async def send_answer(update, answer, number):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📋 کپی جواب",
                copy_text=CopyTextButton(
                    text=answer[:256]
                )
            )
        ]
    ])

    await update.message.reply_text(
        f"💬 جواب {number}:\n\n{answer}",
        reply_markup=keyboard
    )


async def process_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    category = context.user_data.get("category")

    if not category:
        await update.message.reply_text(
            "اول یک دسته‌بندی انتخاب کن:",
            reply_markup=main_menu()
        )
        return

    message = update.message.text.strip()

    if not message:
        return

    if len(message) > 1000:
        await update.message.reply_text(
            "متنت خیلی طولانیه! حداکثر ۱۰۰۰ کاراکتر بفرست."
        )
        return

    status = await update.message.reply_text(
        "🔍 دارم دنبال بهترین جواب می‌گردم..."
    )

    answers = find_local_answers(category, message)

    # Use internet search when local database has no suitable match
    if len(answers) < 2:
        await status.edit_text(
            "🌐 جواب مناسبی پیدا نکردم؛ دارم اینترنت رو جست‌وجو می‌کنم..."
        )

        results = await asyncio.to_thread(
            search_web,
            message,
            category
        )

        if results:
            await status.edit_text(
                "🔎 نتایج جست‌وجوی اینترنتی:"
            )

            for index, result in enumerate(results[:5], 1):
                title = result["title"][:200]
                body = result["body"][:500]
                url = result["url"]

                text = f"🌐 {title}\n\n{body}"

                if url:
                    text += f"\n\n🔗 {url}"

                copy_text = body if body else title

                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "📋 کپی",
                            copy_text=CopyTextButton(
                                text=copy_text[:256]
                            )
                        )
                    ]
                ])

                await update.message.reply_text(
                    text,
                    reply_markup=keyboard
                )

        else:
            await status.edit_text(
                "⚠️ فعلاً نتیجه‌ای از اینترنت پیدا نشد."
            )

            if not answers:
                answers = [
                    "لازم نیست به هر حرفی جواب بدی؛ گاهی سکوت قوی‌تره.",
                    "جوابت رو با اعتمادبه‌نفس بده، نه با عصبانیت.",
                    "هر حرفی ارزش پاسخ دادن نداره 😎"
                ]

    if answers:
        await status.edit_text(
            f"😈 {len(answers)} جواب از بانک داخلی پیدا شد:"
        )

        selected = random.sample(
            answers,
            min(3, len(answers))
        )

        for index, answer in enumerate(selected, 1):
            await send_answer(
                update,
                answer,
                index
            )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔄 جواب جدید",
                callback_data=f"cat_{category}"
            )
        ],
        [
            InlineKeyboardButton(
                "📂 تغییر دسته‌بندی",
                callback_data="back_menu"
            )
        ]
    ])

    await update.message.reply_text(
        "انتخاب بعدی با خودته 😈",
        reply_markup=keyboard
    )


# ==============================
# EXTRA CALLBACK
# ==============================

async def extra_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    if query.data == "back_menu":
        context.user_data.clear()

        await query.message.reply_text(
            "دسته‌بندی جدید رو انتخاب کن:",
            reply_markup=main_menu()
        )


# ==============================
# ERROR HANDLER
# ==============================

async def error_handler(update, context):
    logging.error(
        "Bot error: %s",
        context.error
    )


# ==============================
# RUN BOT
# ==============================

def main():
    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is missing from GitHub Secrets"
        )

    application = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("help", help_command)
    )

    application.add_handler(
        CommandHandler("menu", menu)
    )

    application.add_handler(
        CommandHandler("cancel", cancel)
    )

    application.add_handler(
        CallbackQueryHandler(
            category_callback,
            pattern=r"^cat_"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            extra_callback,
            pattern=r"^back_menu$"
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            process_message
        )
    )

    application.add_error_handler(error_handler)

    logging.info("JAVAB BOT IS RUNNING!")

    application.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
