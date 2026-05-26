from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram import Update

TOKEN = "8956798122:AAFLWjr-HA0dLQwll5EPPcQk1WJ-Z8lTz-Y"

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        await update.message.reply_text(f"FILE_ID:\n{file_id}")

app = Application.builder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.PHOTO, get_id))
app.run_polling()

