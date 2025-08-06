import os
import csv
import logging
from threading import Thread
from flask import Flask, request, jsonify
from telegram import Bot, Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

# ===== НАСТРОЙКИ =====
TOKEN = os.environ.get(8037269369:AAEmzmdMCtnVIan6lRHe9CLTjJsbdH4cMYg)  # Из переменных окружения
ADMIN_CHAT_ID = os.environ.get(7771936325)  # Из переменных окружения
WEBAPP_URL = "https://mihailnest.github.io/telegram-mini-app/"  # Ваш URL

# Состояния для администратора
CODE, AMOUNT = range(2)

# Глобальные хранилища
users = {}
codes = {}

# Настройка логов
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== FLASK API =====
app = Flask(__name__)

@app.route('/check-code')
def check_code():
    code = request.args.get('code', '')
    
    if code in codes:
        return jsonify({
            "valid": True,
            "amount": codes[code]
        })
    return jsonify({"valid": False})

@app.route('/record-win', methods=['POST'])
def record_win():
    data = request.json
    user_id = data.get('user_id')
    code = data.get('code')
    amount = data.get('amount')
    
    if user_id and code and amount:
        phone = users.get(int(user_id), {}).get("phone", "UNKNOWN")
        
        # Запись в CSV
        with open('winners.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([phone, code, amount])
        
        return jsonify({"status": "success"})
    return jsonify({"status": "error"})

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

# ===== ФУНКЦИИ БОТА =====
def start(update: Update, context: CallbackContext):
    keyboard = [[KeyboardButton("📱 Поделиться номером", request_contact=True)]]
    update.message.reply_text(
        "🎰 Добро пожаловать в игру на удачу!\n"
        "Для начала поделитесь номером телефона:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )

def handle_contact(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    phone = update.message.contact.phone_number
    users[user_id] = {"phone": phone}
    
    keyboard = [[InlineKeyboardButton("🎮 Перейти в игру", web_app={"url": WEBAPP_URL})]]
    update.message.reply_text(
        "✅ Номер получен! Теперь вы можете перейти в игру:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def admin_start(update: Update, context: CallbackContext):
    if str(update.effective_user.id) != ADMIN_CHAT_ID:
        update.message.reply_text("❌ У вас нет прав администратора")
        return ConversationHandler.END
    
    update.message.reply_text("⚙️ Режим администратора. Введите 4-значный код:")
    return CODE

def handle_code(update: Update, context: CallbackContext):
    code = update.message.text.strip()
    
    if len(code) != 4 or not code.isdigit():
        update.message.reply_text("❌ Неверный формат! Код должен быть 4 цифры")
        return CODE
    
    context.user_data['code'] = code
    update.message.reply_text("✅ Код принят. Теперь введите сумму выигрыша:")
    return AMOUNT

def handle_amount(update: Update, context: CallbackContext):
    try:
        amount = int(update.message.text)
        code = context.user_data['code']
        codes[code] = amount
        
        update.message.reply_text(
            f"✅ Настройки сохранены!\n"
            f"🔑 Код: {code}\n"
            f"💰 Сумма: {amount}₽\n\n"
            f"Теперь клиенты смогут использовать этот код в игре"
        )
        return ConversationHandler.END
    
    except ValueError:
        update.message.reply_text("❌ Введите число!")
        return AMOUNT

def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("❌ Действие отменено")
    return ConversationHandler.END

# ===== ЗАПУСК =====
def main():
    # Запуск Flask в отдельном потоке
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    logger.info("Flask API запущен")

    # Настройка и запуск бота
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    # Обработчики
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.contact, handle_contact))
    
    # Диалог администратора
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('admin', admin_start)],
        states={
            CODE: [MessageHandler(Filters.text & ~Filters.command, handle_code)],
            AMOUNT: [MessageHandler(Filters.text & ~Filters.command, handle_amount)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(conv_handler)

    updater.start_polling()
    logger.info("Бот запущен и готов к работе!")
    updater.idle()

if __name__ == "__main__":
    main()