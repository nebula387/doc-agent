import asyncio
import logging
import re
import time
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart, Command

from config import TELEGRAM_TOKEN, BOT_NAMES
from llm import ask, FREE_MODELS

# Fast = самая стабильная (llama), Smart = самая мощная (nemotron-super)
MODEL_FREE  = FREE_MODELS[1]   # meta-llama/llama-3.3-70b-instruct:free
MODEL_SMART = FREE_MODELS[0]   # nvidia/nemotron-3-super-120b-a12b:free
from search import legal_search
from voice import transcribe
from documents import (
    save_document, get_documents, get_combined_text,
    remove_document, clear_documents, list_documents
)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# ─── Состояние пользователей ──────────────────────────────────────────────────
# { user_id: { "smart": bool, "history": [...], "last_time": float } }
user_state: dict = {}

CONTEXT_TIMEOUT = 60 * 60   # 1 час для юридических диалогов
MAX_HISTORY = 20             # больше истории — важен контекст всего дела

def get_state(user_id: int) -> dict:
    if user_id not in user_state:
        user_state[user_id] = {"smart": False, "history": [], "last_time": time.time()}
    data = user_state[user_id]
    # Сброс истории по таймауту, режим модели сохраняем
    if time.time() - data["last_time"] > CONTEXT_TIMEOUT:
        data["history"] = []
    data["last_time"] = time.time()
    return data

def is_smart(user_id: int) -> bool:
    return get_state(user_id)["smart"]

def set_smart(user_id: int, value: bool):
    get_state(user_id)["smart"] = value

def get_history(user_id: int) -> list:
    return get_state(user_id)["history"]

def save_message(user_id: int, role: str, content: str):
    history = get_state(user_id)["history"]
    history.append({"role": role, "content": content})
    if len(history) > MAX_HISTORY * 2:
        history[:] = history[-(MAX_HISTORY * 2):]

def reset_history(user_id: int):
    get_state(user_id)["history"] = []

# ─── Форматирование ───────────────────────────────────────────────────────────

def _convert_table(match: re.Match) -> str:
    """Конвертирует markdown-таблицу в читаемый текст для Telegram."""
    lines = match.group(0).strip().splitlines()
    result = []
    for line in lines:
        # Пропускаем разделительные строки (| --- | :--: | и т.д.)
        if re.match(r"^\|[\s\-:|]+\|", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        cells = [c for c in cells if c]
        if not cells:
            continue
        if len(cells) == 2:
            result.append(f"{cells[0]}: {cells[1]}")
        else:
            result.append("  |  ".join(cells))
    return "\n".join(result)

def md_to_html(text: str) -> str:
    text = text.replace("&", "&amp;")
    text = re.sub(
        r"```(\w+)?\n?(.*?)```",
        lambda m: f"<pre><code>{m.group(2).strip()}</code></pre>",
        text, flags=re.DOTALL
    )
    # Таблицы — до обработки звёздочек, чтобы не сломать <b> внутри ячеек
    text = re.sub(r"(?:^\|.+\|[ \t]*\n?)+", _convert_table, text, flags=re.MULTILINE)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    text = re.sub(r"_(.+?)_", r"<i>\1</i>", text)
    text = re.sub(r"^#{1,3} (.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', text)
    return text.strip()

def split_long_message(text: str, limit: int = 4000) -> list[str]:
    if len(text) <= limit:
        return [text]
    parts = []
    while len(text) > limit:
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = limit
        parts.append(text[:split_at])
        text = text[split_at:].lstrip()
    parts.append(text)
    return parts

async def send_response(message: Message, text: str):
    html = md_to_html(text)
    for part in split_long_message(html):
        try:
            await message.reply(part, parse_mode="HTML")
        except Exception:
            await message.reply(part)

def model_badge(user_id: int) -> str:
    return "💎 Smart" if is_smart(user_id) else "⚡ Fast"

# ─── Клавиатура проверки через интернет ──────────────────────────────────────

def response_keyboard(user_id: int, query: str) -> InlineKeyboardMarkup:
    """Кнопки под каждым ответом: переключение модели + проверка"""
    smart = is_smart(user_id)
    model_btn = InlineKeyboardButton(
        text="⚡ Fast модель" if smart else "💎 Smart модель",
        callback_data="toggle_model"
    )
    verify_btn = InlineKeyboardButton(
        text="🔍 Проверить в интернете",
        callback_data=f"verify:{query[:100]}"
    )
    return InlineKeyboardMarkup(inline_keyboard=[[model_btn, verify_btn]])

# ─── Команды ─────────────────────────────────────────────────────────────────

@dp.message(CommandStart())
async def start(message: Message):
    await message.reply(
        "⚖️ <b>Юридический ассистент</b>\n\n"
        "Помогу с:\n"
        "• Анализом юридических документов (PDF, DOCX, TXT)\n"
        "• Вопросами по законодательству\n"
        "• Сравнением нескольких документов\n"
        "• Проверкой информации в интернете\n\n"
        f"Текущая модель: <b>{model_badge(message.from_user.id)}</b>\n\n"
        "Отправь документ или задай вопрос.\n"
        "/help — все команды",
        parse_mode="HTML"
    )

@dp.message(Command("smart"))
async def cmd_smart(message: Message):
    set_smart(message.from_user.id, True)
    await message.reply(
        f"💎 Включена умная модель: <b>{MODEL_SMART}</b>\n"
        "Более точные ответы, глубокий анализ документов.\n\n"
        "/fast — вернуться к быстрой модели",
        parse_mode="HTML"
    )

@dp.message(Command("fast"))
async def cmd_fast(message: Message):
    set_smart(message.from_user.id, False)
    await message.reply(
        f"⚡ Включена быстрая модель: <b>{MODEL_FREE}</b>\n\n"
        "/smart — включить умную модель",
        parse_mode="HTML"
    )

@dp.message(Command("model"))
async def cmd_model(message: Message):
    user_id = message.from_user.id
    current = MODEL_SMART if is_smart(user_id) else MODEL_FREE
    badge = model_badge(user_id)
    await message.reply(
        f"Текущая модель: <b>{badge}</b>\n<code>{current}</code>\n\n"
        f"/smart — 💎 {MODEL_SMART}\n"
        f"/fast — ⚡ {MODEL_FREE}",
        parse_mode="HTML"
    )

@dp.message(Command("new"))
async def cmd_new(message: Message):
    reset_history(message.from_user.id)
    await message.reply("🔄 Контекст сброшен. Документы сохранены.")

@dp.message(Command("docs"))
async def cmd_docs(message: Message):
    await message.reply(list_documents(message.from_user.id), parse_mode="HTML")

@dp.message(Command("deldoc"))
async def cmd_deldoc(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("Укажи имя файла:\n<code>/deldoc договор.pdf</code>", parse_mode="HTML")
        return
    result = remove_document(message.from_user.id, parts[1].strip())
    reset_history(message.from_user.id)
    await message.reply(result, parse_mode="HTML")

@dp.message(Command("cleardocs"))
async def cmd_cleardocs(message: Message):
    clear_documents(message.from_user.id)
    reset_history(message.from_user.id)
    await message.reply("🗑 Все документы удалены.")

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.reply(
        "⚖️ <b>Юридический ассистент — справка</b>\n\n"
        "<b>Переключение модели:</b>\n"
        "Кнопка под каждым ответом:\n"
        "⚡ Fast — быстрая бесплатная (по умолчанию)\n"
        "💎 Smart — умная для сложных случаев\n\n"
        "<b>Диалог:</b>\n"
        "/new — сбросить контекст\n\n"
        "<b>Документы:</b>\n"
        "/docs — список загруженных\n"
        "/deldoc <i>имя.pdf</i> — удалить файл\n"
        "/cleardocs — удалить все\n\n"
        "<b>Что умею:</b>\n"
        "• Отвечаю на вопросы по праву\n"
        "• Анализирую PDF, DOCX, TXT (до 5 файлов)\n"
        "• Сравниваю несколько документов\n"
        "• Проверяю информацию в интернете\n"
        "• Принимаю голосовые сообщения\n\n"
        "⚠️ <i>Не заменяет профессионального юриста</i>",
        parse_mode="HTML"
    )

# ─── Обработка документов ─────────────────────────────────────────────────────

@dp.message(F.document)
async def handle_document(message: Message):
    doc = message.document
    filename = doc.file_name or "document"

    if not any(filename.lower().endswith(ext) for ext in [".pdf", ".docx", ".txt"]):
        await message.reply("❌ Поддерживаются: <b>PDF, DOCX, TXT</b>", parse_mode="HTML")
        return

    if doc.file_size > 20 * 1024 * 1024:
        await message.reply("❌ Файл слишком большой. Максимум 20 МБ.")
        return

    status = await message.reply(f"📄 <i>Читаю {filename}...</i>", parse_mode="HTML")

    try:
        file = await bot.get_file(doc.file_id)
        file_bytes = await bot.download_file(file.file_path)
        result = save_document(message.from_user.id, filename, file_bytes.read())
        reset_history(message.from_user.id)
        await status.delete()
        await message.reply(result, parse_mode="HTML")
    except Exception as e:
        await status.delete()
        await message.reply(f"❌ Ошибка загрузки: {e}")

# ─── Обработка голоса ─────────────────────────────────────────────────────────

@dp.message(F.voice)
async def handle_voice(message: Message):
    status = await message.reply("🎤 <i>Распознаю речь...</i>", parse_mode="HTML")
    try:
        file = await bot.get_file(message.voice.file_id)
        audio_bytes = await bot.download_file(file.file_path)
        text = transcribe(audio_bytes.read(), "voice.ogg")

        if text.startswith("ERROR:") or not text:
            await status.delete()
            await message.reply("❌ Не удалось распознать речь.")
            return

        await status.edit_text(f"🎤 <i>Распознано:</i> {text}", parse_mode="HTML")
        await process_message(message, text)
    except Exception as e:
        await status.delete()
        await message.reply(f"❌ Ошибка: {e}")

# ─── Callbacks ───────────────────────────────────────────────────────────────

@dp.callback_query(F.data == "toggle_model")
async def handle_toggle_model(callback: CallbackQuery):
    user_id = callback.from_user.id
    new_smart = not is_smart(user_id)
    set_smart(user_id, new_smart)

    badge = model_badge(user_id)
    model_name = MODEL_SMART if new_smart else MODEL_FREE
    await callback.answer(f"Переключено на {badge}")

    # Обновляем кнопки у сообщения
    try:
        await callback.message.edit_reply_markup(
            reply_markup=response_keyboard(user_id, "")
        )
    except Exception:
        pass

    await callback.message.reply(
        f"{'💎' if new_smart else '⚡'} Модель переключена: <b>{model_name}</b>",
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("verify:"))
async def handle_verify(callback: CallbackQuery):
    query = callback.data[7:]
    await callback.answer("Ищу в интернете...")

    status = await callback.message.reply("🔍 <i>Проверяю информацию...</i>", parse_mode="HTML")
    results = legal_search(query)

    await status.delete()
    await callback.message.reply(
        f"🔍 <b>Результаты проверки:</b>\n\n{results}",
        parse_mode="HTML",
        disable_web_page_preview=True
    )

# ─── Основная логика ──────────────────────────────────────────────────────────

async def process_message(message: Message, user_text: str):
    user_id = message.from_user.id
    smart = is_smart(user_id)
    history = get_history(user_id)
    doc_text = get_combined_text(user_id)
    docs = get_documents(user_id)
    badge = model_badge(user_id)

    if doc_text:
        status_text = f"⚖️ <i>Анализирую документы ({len(docs)} шт.) [{badge}]...</i>"
    else:
        status_text = f"⚖️ <i>Думаю [{badge}]...</i>"

    status = await message.reply(status_text, parse_mode="HTML")
    await bot.send_chat_action(message.chat.id, "typing")

    save_message(user_id, "user", user_text)
    response = ask(
        user_text,
        use_smart=smart,
        history=history[:-1],
        document=doc_text,
    )
    save_message(user_id, "assistant", response)

    await status.delete()

    # Кнопки: переключение модели + проверка в интернете
    keyboard = response_keyboard(user_id, user_text)
    html = md_to_html(f"⚖️ {response}")
    parts = split_long_message(html)

    for i, part in enumerate(parts):
        try:
            is_last = (i == len(parts) - 1)
            await message.reply(
                part,
                parse_mode="HTML",
                reply_markup=keyboard if is_last else None
            )
        except Exception:
            await message.reply(part)


@dp.message(F.text)
async def handle_message(message: Message):
    user_text = message.text or ""

    if message.chat.type in ["group", "supergroup"]:
        bot_info = await bot.get_me()
        text_lower = user_text.lower()
        is_reply_to_bot = (
            message.reply_to_message and
            message.reply_to_message.from_user.id == bot_info.id
        )
        is_mentioned = f"@{bot_info.username}".lower() in text_lower
        is_called_by_name = any(name in text_lower for name in BOT_NAMES)

        if not is_reply_to_bot and not is_mentioned and not is_called_by_name:
            return

        for name in BOT_NAMES:
            user_text = user_text.replace(name, "").strip()
        user_text = user_text.replace(f"@{bot_info.username}", "").strip()

    if not user_text:
        await message.reply("Задай вопрос 🙂")
        return

    await process_message(message, user_text)


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
