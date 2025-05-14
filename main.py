from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from datetime import datetime

# === Настройки ===
TOKEN = "7296445246:AAHIH8pwGQwb4f_QZVueuRaG9XjKB73OpKs"
CLEANERS_GROUP_ID = -1002620361047  # ← ваш chat_id группы горничных

# === Команда /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот активен. Используйте /checkout <номер комнаты>")

# === Команда /checkout 504 ===
async def checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите номер комнаты: /checkout 504")
        return

    room = context.args[0]
    sender_id = update.effective_user.id

    keyboard = [
        [
            InlineKeyboardButton("✅ Всё в порядке", callback_data=f"ok|{room}|{sender_id}"),
            InlineKeyboardButton("⚠️ Есть проблема", callback_data=f"problem|{room}|{sender_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=CLEANERS_GROUP_ID,
        text=f"Номер {room} — чек-аут.\nПожалуйста, подтвердите состояние номера.",
        reply_markup=reply_markup
    )

    await update.message.reply_text(f"Заявка по номеру {room} отправлена горничным.")

# === Обработка кнопок ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("|")
    action, room, res_id = data
    user = query.from_user
    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    if action == "ok":
        text = (
            f"Номер {room}: ✅ Всё в порядке\n"
            f"Отвечено: {user.full_name} (@{user.username})\n"
            f"Время: {now}"
        )
        await context.bot.send_message(chat_id=int(res_id), text=text)
        await query.edit_message_text(f"Подтверждено: номер {room} — всё в порядке.")

    elif action == "problem":
        await context.bot.send_message(chat_id=user.id,
            text=f"Пожалуйста, опишите проблему в номере {room}.")
        context.user_data['awaiting_problem'] = (room, res_id)
        await query.edit_message_text(f"Ожидаем описание проблемы в номере {room}.")

# === Обработка текста от горничной с описанием ===
async def handle_problem_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'awaiting_problem' in context.user_data:
        room, res_id = context.user_data.pop('awaiting_problem')
        user = update.effective_user
        now = datetime.now().strftime("%d.%m.%Y %H:%M")

        text = (
            f"Номер {room}: ⚠️ Проблема\n"
            f"{update.message.text}\n"
            f"Отвечено: {user.full_name} (@{user.username})\n"
            f"Время: {now}"
        )
        await context.bot.send_message(chat_id=int(res_id), text=text)
        await update.message.reply_text("Спасибо, проблема передана ресепшну.")

# === Запуск приложения ===
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("checkout", checkout))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_problem_text))
app.run_polling()
