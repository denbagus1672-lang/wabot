import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = "8956798122:AAFLWjr-HA0dLQwll5EPPcQk1WJ-Z8lTz-Y"
ADMIN_ID = 8123373116
NOMOR_REKENING = "901727395930"
NAMA_REKENING = "CIT***"
BANK = "SeaBank"
ADMIN_USERNAME = "Galtzyyo"
CHANNEL_TESTI = "RanggaShoping"

PAKET = {
    "A": {"nama": "WA Badak Garansi 7 Hari", "deskripsi": "Max Spam 500 Nomor", "harga": 150000, "garansi": "7 Hari", "emoji": "🔥"},
    "B": {"nama": "WA Badak + Verif Garansi 3 Bulan", "deskripsi": "Max Spam 1000 Nomor", "harga": 300000, "garansi": "3 Bulan", "emoji": "💎"},
    "C": {"nama": "WA Badak + Api + Verif + FBM Garansi 5 Bulan", "deskripsi": "Max Spam 1500 Nomor", "harga": 500000, "garansi": "5 Bulan", "emoji": "👑"},
}

def init_db():
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, username TEXT, paket TEXT,
        harga INTEGER, waktu TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def simpan_order(user_id, username, paket, harga):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("INSERT INTO orders (user_id, username, paket, harga) VALUES (?,?,?,?)",
              (user_id, username, paket, harga))
    order_id = c.lastrowid
    conn.commit()
    conn.close()
    return order_id

def get_order(order_id):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("SELECT * FROM orders WHERE id=?", (order_id,))
    result = c.fetchone()
    conn.close()
    return result

def menu_utama():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Produk", callback_data="produk")],
        [InlineKeyboardButton("📢 Testimoni", url=f"https://t.me/{CHANNEL_TESTI}"),
         InlineKeyboardButton("📞 Admin", url=f"https://t.me/{ADMIN_USERNAME}")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"🔥 *Selamat Datang di WA Badak Store!*\n\n"
        f"Halo {user.first_name}! 👋\n\n"
        f"Kami menyediakan Nomor WA Badak berkualitas tinggi.\n\n"
        f"Pilih menu di bawah ini:",
        parse_mode="Markdown",
        reply_markup=menu_utama())

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = update.effective_user

    if data == "menu":
        await query.edit_message_text(
            "🔥 *WA Badak Store*\n\nPilih menu:",
            parse_mode="Markdown",
            reply_markup=menu_utama())

    elif data == "produk":
        keyboard = []
        for k, p in PAKET.items():
            keyboard.append([InlineKeyboardButton(
                f"{p['emoji']} {p['nama']} - Rp {p['harga']:,}",
                callback_data="DT" + k)])
        keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="menu")])
        await query.edit_message_text(
            "🛒 *Pilih Paket WA Badak:*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("DT"):
        k = data[2:]
        p = PAKET[k]
        await query.edit_message_text(
            f"{p['emoji']} *{p['nama']}*\n\n"
            f"📱 {p['deskripsi']}\n"
            f"⏱ Garansi: *{p['garansi']}*\n"
            f"💰 Harga: *Rp {p['harga']:,}*\n\n"
            f"Lanjutkan pembelian?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Beli Sekarang", callback_data="BY" + k)],
                [InlineKeyboardButton("🔙 Kembali", callback_data="produk")]]))

    elif data.startswith("BY"):
        k = data[2:]
        p = PAKET[k]
        order_id = simpan_order(user.id, user.username or "", p['nama'], p['harga'])
        await query.edit_message_text(
            f"💳 *Instruksi Pembayaran*\n\n"
            f"📦 Paket: *{p['nama']}*\n"
            f"💰 Total: *Rp {p['harga']:,}*\n\n"
            f"Transfer ke:\n"
            f"🏦 Bank: *{BANK}*\n"
            f"💳 No. Rek: `{NOMOR_REKENING}`\n"
            f"👤 Atas Nama: *{NAMA_REKENING}*\n\n"
            f"📸 Setelah transfer kirim *foto bukti transfer* ke bot ini.\n"
            f"Admin akan konfirmasi dan kirim nomor Anda.\n\n"
            f"🔖 Order ID: *#{order_id}*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📸 Kirim Bukti Transfer", callback_data="BUKTI" + str(order_id) + "K" + k)],
                [InlineKeyboardButton("🔙 Kembali", callback_data="produk")]]))

    elif data.startswith("BUKTI"):
        info = data[5:]
        parts = info.split("K")
        order_id = parts[0]
        k = parts[1]
        p = PAKET[k]
        order = get_order(int(order_id))
        await query.edit_message_text(
            f"📸 *Kirim Bukti Transfer*\n\n"
            f"Silakan kirim *foto bukti transfer* Anda sekarang.\n\n"
            f"📦 Paket: *{p['nama']}*\n"
            f"💰 Total: *Rp {p['harga']:,}*\n"
            f"🔖 Order ID: *#{order_id}*\n\n"
            f"⚠️ Kirim foto langsung di chat ini.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Kembali", callback_data="BY" + k)]]))
        context.user_data["order_id"] = order_id
        context.user_data["paket"] = p['nama']
        context.user_data["harga"] = p['harga']
        context.user_data["uid"] = user.id
        context.user_data["username"] = user.username or ""

    elif data.startswith("OK"):
        if user.id != ADMIN_ID:
            await query.answer("❌ Bukan admin!", show_alert=True)
            return
        parts = data[2:].split("Z")
        uid = int(parts[0])
        order_id = parts[1]
        await context.bot.send_message(
            chat_id=uid,
            text=f"✅ *Pembayaran Dikonfirmasi!*\n\n"
                 f"Order *#{order_id}* telah disetujui.\n"
                 f"Nomor WA Badak Anda akan segera dikirim.\n\n"
                 f"Terima kasih! 🙏",
            parse_mode="Markdown")
        await query.edit_message_text(
            f"✅ Order #{order_id} dikonfirmasi. Notifikasi terkirim ke user.")

async def terima_bukti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    order_id = context.user_data.get("order_id", "?")
    paket = context.user_data.get("paket", "?")
    harga = context.user_data.get("harga", 0)

    await update.message.forward(chat_id=ADMIN_ID)
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"💳 *BUKTI TRANSFER MASUK!*\n\n"
             f"👤 User: {user.first_name} (@{user.username})\n"
             f"🆔 ID: {user.id}\n"
             f"📦 Paket: {paket}\n"
             f"💰 Harga: Rp {harga:,}\n"
             f"🔖 Order ID: #{order_id}\n\n"
             f"Tap tombol di bawah untuk konfirmasi!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Konfirmasi Order",
             callback_data="OK" + str(user.id) + "Z" + str(order_id))]
        ]))
    await update.message.reply_text(
        f"✅ *Bukti transfer terkirim ke admin!*\n\n"
        f"⏳ Tunggu konfirmasi dari admin.\n"
        f"Nomor WA Badak akan segera dikirimkan.\n\n"
        f"Terima kasih! 🙏",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Menu Utama", callback_data="menu")]]))

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handler))
    app.add_handler(MessageHandler(filters.PHOTO, terima_bukti))
    print("✅ Bot WA Badak Store sedang berjalan...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
