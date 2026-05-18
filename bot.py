from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8956798122:AAFLWjr-HA0dLQwll5EPPcQk1WJ-Z8lTz-Y"
ADMIN_ID = 8123373116
NOMOR_REKENING = "901727395930"
NAMA_REKENING = "CIT***"
BANK = "SeaBank"
ADMIN_USERNAME = "Galtzyyo"
CHANNEL_TESTI = "RanggaShoping"

PAKET = {
    "1": {"nama": "WA Badak Garansi 7 Hari", "deskripsi": "Max Spam 500 Nomor", "harga": 150000, "garansi": "7 Hari", "emoji": "🔥"},
    "2": {"nama": "WA Badak + Verif Garansi 3 Bulan", "deskripsi": "Max Spam 1000 Nomor", "harga": 300000, "garansi": "3 Bulan", "emoji": "💎"},
    "3": {"nama": "WA Badak + Api + Verif + FBM Garansi 5 Bulan", "deskripsi": "Max Spam 1500 Nomor", "harga": 500000, "garansi": "5 Bulan", "emoji": "👑"},
}

ORDER_COUNTER = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    teks = (
        f"🔥 *Selamat Datang di WA Badak Store!*\n\n"
        f"Halo {user.first_name}! 👋\n\n"
        f"Kami menyediakan Nomor WA Badak berkualitas tinggi.\n\n"
        f"📋 *DAFTAR PRODUK:*\n\n"
        f"🔥 Paket 1 — WA Badak Garansi 7 Hari\n"
        f"   📱 Max Spam 500 Nomor\n"
        f"   💰 Rp 150.000\n\n"
        f"💎 Paket 2 — WA Badak + Verif Garansi 3 Bulan\n"
        f"   📱 Max Spam 1000 Nomor\n"
        f"   💰 Rp 300.000\n\n"
        f"👑 Paket 3 — WA Badak + Api + Verif + FBM Garansi 5 Bulan\n"
        f"   📱 Max Spam 1500 Nomor\n"
        f"   💰 Rp 500.000\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🛒 *Cara Order:*\n"
        f"Ketik perintah berikut untuk memesan:\n\n"
        f"/beli1 — Beli Paket 1\n"
        f"/beli2 — Beli Paket 2\n"
        f"/beli3 — Beli Paket 3\n\n"
        f"📢 Testimoni: t.me/{CHANNEL_TESTI}\n"
        f"📞 Admin: t.me/{ADMIN_USERNAME}"
    )
    await update.message.reply_text(teks, parse_mode="Markdown")

async def beli(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cmd = update.message.text.strip().lower()

    if cmd == "/beli1":
        k = "1"
    elif cmd == "/beli2":
        k = "2"
    elif cmd == "/beli3":
        k = "3"
    else:
        await update.message.reply_text("❌ Perintah tidak valid. Gunakan /beli1, /beli2, atau /beli3")
        return

    p = PAKET[k]
    ORDER_COUNTER[user.id] = {"paket": p['nama'], "harga": p['harga'], "key": k}

    await update.message.reply_text(
        f"{p['emoji']} *{p['nama']}*\n\n"
        f"📱 {p['deskripsi']}\n"
        f"⏱ Garansi: *{p['garansi']}*\n"
        f"💰 Harga: *Rp {p['harga']:,}*\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💳 *Instruksi Pembayaran:*\n\n"
        f"Transfer ke:\n"
        f"🏦 Bank: *{BANK}*\n"
        f"💳 No. Rek: `{NOMOR_REKENING}`\n"
        f"👤 Atas Nama: *{NAMA_REKENING}*\n\n"
        f"📸 Setelah transfer, kirim *foto bukti transfer* ke bot ini.\n"
        f"Admin akan konfirmasi dan kirim nomor Anda.\n\n"
        f"❓ Ada pertanyaan? Hubungi @{ADMIN_USERNAME}",
        parse_mode="Markdown"
    )

async def terima_bukti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    order_info = ORDER_COUNTER.get(user.id)

    if not order_info:
        await update.message.reply_text(
            "⚠️ Silakan pilih paket dulu dengan /beli1, /beli2, atau /beli3")
        return

    paket = order_info["paket"]
    harga = order_info["harga"]

    import random
    order_id = random.randint(10000, 99999)

    await update.message.forward(chat_id=ADMIN_ID)
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"💳 *BUKTI TRANSFER MASUK!*\n\n"
             f"👤 User: {user.first_name} (@{user.username})\n"
             f"🆔 ID: {user.id}\n"
             f"📦 Paket: {paket}\n"
             f"💰 Harga: Rp {harga:,}\n"
             f"🔖 Order ID: #{order_id}\n\n"
             f"Cek bukti di atas lalu kirim nomor ke user!\n"
             f"Balas user: /kirim {user.id}",
        parse_mode="Markdown")

    await update.message.reply_text(
        f"✅ *Bukti transfer terkirim ke admin!*\n\n"
        f"📦 Paket: *{paket}*\n"
        f"💰 Total: *Rp {harga:,}*\n"
        f"🔖 Order ID: *#{order_id}*\n\n"
        f"⏳ Tunggu konfirmasi dari admin.\n"
        f"Nomor WA Badak akan segera dikirimkan.\n\n"
        f"Terima kasih! 🙏",
        parse_mode="Markdown")

    del ORDER_COUNTER[user.id]

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("beli1", beli))
    app.add_handler(CommandHandler("beli2", beli))
    app.add_handler(CommandHandler("beli3", beli))
    app.add_handler(MessageHandler(filters.PHOTO, terima_bukti))
    print("✅ Bot WA Badak Store sedang berjalan...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
