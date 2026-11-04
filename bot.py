
import os
import re
import html
import random
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

import requests
from bs4 import BeautifulSoup
from ddgs import DDGS

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

# =====================================
# CONFIG
# =====================================

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.getLogger("httpx").setLevel(logging.WARNING)

executor = ThreadPoolExecutor(max_workers=5)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
    )
}

# =====================================
# CATEGORIES
# =====================================

CATEGORIES = {
    "roast": "😂 خیت کردن",
    "love": "❤️ مخ زدن",
    "classy": "🗿 سنگین و باکلاس",
    "fight": "🔥 کل‌کل و دعوا",
    "funny": "🤣 طنز و شوخی",
    "quick": "⚡ جواب فوری"
}

SEARCH_TERMS = {
    "roast": [
        "جواب دندان شکن و حاضر جوابی",
        "جواب تیکه دار و خفن",
        "جواب کوبنده برای این حرف"
    ],
    "love": [
        "جواب عاشقانه و مخ زنی",
        "جملات جذاب برای جواب دادن به کراش",
        "جواب شیطون و رمانتیک"
    ],
    "classy": [
        "جواب سنگین و باکلاس",
        "جواب محترمانه و قاطع",
        "جملات کوتاه و باوقار"
    ],
    "fight": [
        "جواب محکم برای کل کل",
        "جواب قاطع در بحث",
        "جواب کوبنده به این جمله"
    ],
    "funny": [
        "جواب بامزه و خنده دار",
        "جواب طنز برای این حرف",
        "حاضر جوابی خنده دار"
    ],
    "quick": [
        "جواب کوتاه و مناسب",
        "بهترین جواب برای این جمله",
        "جواب حاضر جوابی فارسی"
    ]
}

# =====================================
# LOCAL ANSWERS
# =====================================

LOCAL_BANK = {
    "roast": [
        {
            "keywords": ["خودتو میگیری", "مغرور"],
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
            "keywords": ["زشت", "قیافه"],
            "answers": [
                "خوشحالم انقدر وقت داری به من فکر کنی 😂",
                "سلیقه‌ات رو کسی نپرسیده بود!",
                "نگران قیافه من نباش، آینه خودت رو چک کن."
            ]
        }
    ],

    "love": [
        {
            "keywords": ["سلام", "درود", "هی"],
            "answers": [
                "سلام به کسی که با یه سلام ساده می‌تونه کل روزمو قشنگ کنه ❤️",
                "سلام، چه خوب شد پیدات شد 😉",
                "سلام به قشنگ‌ترین اتفاق این لحظه من ❤️",
                "سلام، منتظر همین پیامت بودم!"
            ]
        },
        {
            "keywords": ["دوستت دارم", "عاشقتم"],
            "answers": [
                "پس مواظب قلبم باش، راحت به دست نیومده ❤️",
                "این حرفت قشنگ‌ترین اتفاق امروزمه 🥹",
                "منم دارم بیشتر از چیزی که فکر می‌کنی بهت علاقه‌مند می‌شم."
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
                "هرکسی تعریف متفاوتی از قدرته.",
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
    ],

    "quick": [
        {
            "keywords": ["سلام", "درود"],
            "answers": [
                "سلام، چه خبر؟ 😎",
                "سلام به روی ماهت!",
                "سلام، بگو ببینم چه خبره؟"
            ]
        }
    ]
}


# =====================================
# TEXT NORMALIZATION
# =====================================

def normalize(text):
    text = text.lower()
    text = text.replace("ي", "ی").replace("ك", "ک")
    text = text.replace("\u200c", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# =====================================
# LOCAL ANSWER SEARCH
# =====================================

def find_local_answers(category, message):
    bank = LOCAL_BANK.get(category, [])
    normalized = normalize(message)

    answers = []

    for item in bank:
        for keyword in item["keywords"]:
            if normalize(keyword) in normalized:
                answers.extend(item["answers"])
                break

    return list(dict.fromkeys(answers))


# =====================================
# BUILD SEARCH QUERIES
# =====================================

def build_queries(message, category):
    terms = SEARCH_TERMS.get(
        category,
        SEARCH_TERMS["quick"]
    )

    queries = []

    for term in terms:
        queries.append(
            f'"{message}" {term} فارسی'
        )

    queries.append(
        f'برای جمله {message} چی جواب بدم؟ {terms[0]}'
    )

    return queries


# =====================================
# DUCKDUCKGO SEARCH
# =====================================

def search_results(queries):
    collected = []
    seen_urls = set()

    for query in queries:
        try:
            with DDGS(timeout=12) as ddgs:
                results = ddgs.text(
                    query,
                    max_results=6,
                    region="wt-wt"
                )

                for item in results:
                    url = item.get("href", "")

                    if not url or url in seen_urls:
                        continue

                    seen_urls.add(url)

                    collected.append({
                        "title": item.get("title", ""),
                        "body": item.get("body", ""),
                        "url": url
                    })

        except Exception as error:
            logging.warning(
                "DuckDuckGo search failed: %s",
                error
            )

    return collected[:12]


# =====================================
# DOWNLOAD AND EXTRACT WEB PAGE TEXT
# =====================================

def extract_page(url):
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=10
        )

        response.raise_for_status()

        if len(response.content) > 2_000_000:
            return ""

        content_type = response.headers.get(
            "Content-Type",
            ""
        )

        if "html" not in content_type.lower():
            return ""

        soup = BeautifulSoup(
            response.content,
            "html.parser"
        )

        for element in soup([
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "aside",
            "form",
            "noscript",
            "iframe"
        ]):
            element.decompose()

        parts = []

        for element in soup.find_all([
            "p",
            "li",
            "blockquote",
            "h2",
            "h3"
        ]):
            text = element.get_text(
                " ",
                strip=True
            )

            text = re.sub(
                r"\s+",
                " ",
                text
            )

            if len(text) >= 15:
                parts.append(text)

        return "\n".join(parts)[:18000]

    except Exception as error:
        logging.warning(
            "Page extraction failed: %s",
            error
        )
        return ""


# =====================================
# EXTRACT USEFUL ANSWER CANDIDATES
# =====================================

def extract_candidates(text):
    text = html.unescape(text)

    lines = re.split(
        r"[\n.!؟?؛]+",
        text
    )

    candidates = []

    for line in lines:
        line = re.sub(
            r"\s+",
            " ",
            line
        ).strip()

        line = line.strip(
            " -–—:،؛\"'«»"
        )

        if len(line) < 18:
            continue

        if len(line) > 190:
            continue

        if not re.search(
            r"[\u0600-\u06FF]",
            line
        ):
            continue

        if re.search(
            r"(http|www\.|تبلیغات|عضویت|ورود به سایت|"
            r"دانلود|صفحه اصلی|ادامه مطلب|کلیک کنید)",
            line,
            re.IGNORECASE
        ):
            continue

        if len(line.split()) < 3:
            continue

        candidates.append(line)

    return candidates


# =====================================
# SCORE ANSWERS
# =====================================

def score_candidate(candidate, message, category):
    text = normalize(candidate)
    original = normalize(message)

    score = 0

    category_words = {
        "love": [
            "عاشقانه", "سلام", "قلب", "دوست",
            "علاقه", "عزیز", "زیبا", "دلتنگ",
            "خوشحال", "لبخند"
        ],
        "roast": [
            "جواب", "تیکه", "شوخی", "اعتماد",
            "غرور", "حرف", "خنده"
        ],
        "classy": [
            "احترام", "ارزش", "شخصیت", "منطق",
            "رفتار", "سکوت"
        ],
        "fight": [
            "جواب", "محکم", "بحث", "حرف",
            "منطق", "رفتار"
        ],
        "funny": [
            "خنده", "شوخی", "بامزه", "طنز",
            "خنده دار"
        ],
        "quick": [
            "جواب", "سلام", "حرف", "بگو"
        ]
    }

    for word in category_words.get(category, []):
        if word in text:
            score += 2

    if any(
        word in text
        for word in [
            "می‌تونی بگی",
            "بگو",
            "جواب بده",
            "بهش بگو",
            "پاسخ بده"
        ]
    ):
        score += 1

    message_words = [
        word for word in original.split()
        if len(word) > 2
    ]

    for word in message_words:
        if word in text:
            score += 2

    if 25 <= len(candidate) <= 120:
        score += 2

    return score


# =====================================
# DEEP SEARCH ENGINE
# =====================================

def deep_search(message, category):
    queries = build_queries(
        message,
        category
    )

    results = search_results(queries)

    if not results:
        return []

    candidates = []

    # Include useful search snippets
    for result in results:
        snippet = result.get("body", "")

        if snippet:
            candidates.extend(
                extract_candidates(snippet)
            )

    # Read actual pages
    urls = [
        result["url"]
        for result in results[:6]
    ]

    with ThreadPoolExecutor(max_workers=5) as pool:
        page_texts = list(
            pool.map(extract_page, urls)
        )

    for page_text in page_texts:
        if page_text:
            candidates.extend(
                extract_candidates(page_text)
            )

    # Rank candidates
    unique = {}

    for candidate in candidates:
        key = normalize(candidate)

        if key not in unique:
            unique[key] = candidate

    ranked = sorted(
        unique.values(),
        key=lambda item: score_candidate(
            item,
            message,
            category
        ),
        reverse=True
    )

    # Filter weak and repeated answers
    final_answers = []
    seen = set()

    for answer in ranked:
        key = normalize(answer)

        if key in seen:
            continue

        if score_candidate(
            answer,
            message,
            category
        ) < 2:
            continue

        seen.add(key)
        final_answers.append(answer)

        if len(final_answers) >= 5:
            break

    return final_answers


# =====================================
# TELEGRAM MENUS
# =====================================

def main_menu():
    keyboard = []

    for key, name in CATEGORIES.items():
        keyboard.append([
            InlineKeyboardButton(
                name,
                callback_data=f"cat_{key}"
            )
        ])

    return InlineKeyboardMarkup(keyboard)


def answer_keyboard(answer):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📋 کپی جواب",
                copy_text=CopyTextButton(
                    text=answer[:256]
                )
            )
        ]
    ])


# =====================================
# START
# =====================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "😈 به ربات حاضر جواب خوش اومدی!\n\n"
        "هر حرفی شنیدی وارد کن تا بهترین جواب‌ها رو پیدا کنیم.\n\n"
        "دسته‌بندی مورد نظرت رو انتخاب کن:",
        reply_markup=main_menu()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start شروع ربات\n"
        "/menu نمایش دسته‌بندی‌ها\n"
        "/cancel لغو عملیات"
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


# =====================================
# CATEGORY CALLBACK
# =====================================

async def category_callback(update, context):
    query = update.callback_query
    await query.answer()

    category = query.data.replace(
        "cat_",
        ""
    )

    if category not in CATEGORIES:
        return

    context.user_data["category"] = category

    await query.message.reply_text(
        f"{CATEGORIES[category]}\n\n"
        "حالا جمله‌ای که طرف مقابل گفته رو بفرست. 👇"
    )


async def extra_callback(update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "back_menu":
        context.user_data.clear()

        await query.message.reply_text(
            "یک دسته‌بندی انتخاب کن:",
            reply_markup=main_menu()
        )


# =====================================
# SEND ANSWERS
# =====================================

async def send_answers(update, answers, source):
    if not answers:
        return

    for index, answer in enumerate(answers, 1):
        await update.message.reply_text(
            f"💬 جواب {index}:\n\n{answer}",
            reply_markup=answer_keyboard(answer)
        )


# =====================================
# PROCESS USER MESSAGE
# =====================================

async def process_message(update, context):
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

    if len(message) > 500:
        await update.message.reply_text(
            "متنت خیلی طولانیه؛ حداکثر ۵۰۰ کاراکتر بفرست."
        )
        return

    status = await update.message.reply_text(
        "🔍 دارم دنبال جواب مناسب می‌گردم..."
    )

    # First check local answers
    local_answers = find_local_answers(
        category,
        message
    )

    # If local answers are enough, use them
    if len(local_answers) >= 3:
        answers = random.sample(
            local_answers,
            min(3, len(local_answers))
        )

        await status.edit_text(
            "😈 اینم جواب‌های پیشنهادی:"
        )

        await send_answers(
            update,
            answers,
            "local"
        )

    else:
        await status.edit_text(
            "🌐 دارم چند عبارت رو جست‌وجو می‌کنم و متن سایت‌ها رو بررسی می‌کنم...\n"
            "یکم صبر کن."
        )

        web_answers = await asyncio.to_thread(
            deep_search,
            message,
            category
        )

        # Combine web and local answers
        combined = []

        for answer in web_answers + local_answers:
            if answer not in combined:
                combined.append(answer)

        # Use fallback only if no good result exists
        if not combined:
            combined = [
                "لازم نیست به هر حرفی جواب بدی؛ گاهی سکوت قوی‌تره.",
                "جوابت رو با اعتمادبه‌نفس بده، نه عصبانیت.",
                "هر حرفی ارزش پاسخ دادن نداره 😎"
            ]

        selected = combined[:5]

        await status.edit_text(
            f"😈 {len(selected)} جواب پیدا کردم:"
        )

        await send_answers(
            update,
            selected,
            "web"
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


# =====================================
# ERROR HANDLER
# =====================================

async def error_handler(update, context):
    logging.exception(
        "Bot error: %s",
        context.error
    )


# =====================================
# MAIN
# =====================================

def main():
    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN در GitHub Secrets پیدا نشد."
        )

    app = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("help", help_command)
    )

    app.add_handler(
        CommandHandler("menu", menu)
    )

    app.add_handler(
        CommandHandler("cancel", cancel)
    )

    app.add_handler(
        CallbackQueryHandler(
            category_callback,
            pattern=r"^cat_"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            extra_callback,
            pattern=r"^back_menu$"
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            process_message
        )
    )

    app.add_error_handler(error_handler)

    logging.info("JAVAB BOT STARTED")

    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
