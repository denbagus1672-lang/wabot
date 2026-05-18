import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ================================
# KONFIGURASI BOT
# ================================
TOKEN = "8956798122:AAFLWjr-HA0dLQwll5EPPcQk1WJ-Z8lTz-Y"
ADMIN_ID = 8123373116
NOMOR_REKENING = "901727395930"
NAMA_REKENING = "CIT***"
BANK = "SeaBank"
CHANNEL_TESTIMONI = "RanggaShoping"
ADMIN_USERNAME = "Galtzyyo"

PAKET = {
    "paket1": {"nama": "WA Badak Garansi 7 Hari", "deskripsi": "Max Spam 500 Nomor", "harga": 150000, "garansi": "7 Hari", "emoji": "🔥"},
    "paket2": {"nama": "WA Badak + Verif Garansi 3 Bulan", "deskripsi": "Max Spam 1000 Nomor", "harga": 300000, "garansi": "3 Bulan", "emoji": "💎"},
    "paket3": {"nama": "WA Badak + Api + Verif + FBM Garansi 5 Bulan", "deskripsi": "Max Spam 1500 Nomor", "harga": 500000, "garansi": "5 Bulan", "emoji": "👑"},
}

# ================================
# DATABASE
# ================================
def init_db():
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, username TEXT, full_name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        paket TEXT, harga INTEGER, status TEXT DEFAULT "pending",
        waktu TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def register_user(user_id, username, full_name):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?,?,?)", (user_id, username, full_name))
    conn.commit()
    conn.close()

def simpan_order(user_id, paket, harga):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("INSERT INTO orders (user_id, paket, harga) VALUES (?,?,?)", (user_id, paket, harga))
    order_id = c.lastrowid
    conn.commit()
    conn.close()
    return order_id

def get_riwayat(user_id):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("SELECT paket, harga, status, waktu FROM orders WHERE user_id=? ORDER BY waktu DESC LIMIT 5", (user_id,))
    result = c.fetchall()
    conn.close()
    return result

def selesaikan_order(order_id):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("UPDATE orders SET status='selesai' WHERE id=?", (order_id,))
    conn.commit()
    conn.close()

# ================================
# KEYBOARD
# ================================
def keyboard_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Beli Nomor WA", callback_data="beli")],
        [InlineKeyboardButton("📜 Riwayat Order", callback_data="riwayat")],
        [InlineKeyboardButton("📢 Testimoni", url=f"https://t.me/{CHANNEL_TESTIMONI}"),
         InlineKeyboardButton("📞 Admin", url=f"https://t.me/{ADMIN_USERNAME}")]
    ])

# ================================
# HANDLERS
# ================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user.id, user.username or "", user.first_name)
    await update.message.reply_text(
        f"🔥 *Selamat Datang di WA Badak Store!*\n\n"
        f"Halo {user.first_name}! 👋\n"
        f"Kami menyediakan nomor WA Badak berkualitas tinggi.\n\n"
        f"✅ Pembayaran langsung via transfer\n"
        f"✅ Proses cepat setelah konfirmasi\n"
        f"✅ Garansi sesuai paket\n\n"
        f"Silakan pilih menu di bawah ini:",
        parse_mode="Markdown",
        reply_markup=keyboard_menu()
    )

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = update.effective_user

    if data == "menu":
        await query.edit_message_text(
            "🔥 *WA Badak Store*\n\nSilakan pilih menu:",
            parse_mode="Markdown", reply_markup=keyboard_menu())

    elif data == "beli":
        keyboard = [[InlineKeyboardButton(
            f"{p['emoji']} {p['nama']} - Rp {p['harga']:,}", callback_data=f"detail|{k}")]
            for k, p in PAKET.items()]
        keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="menu")])
        await query.edit_message_text(
            "🛒 *Pilih Paket WA Badak:*\n\nPilih paket yang sesuai kebutuhan Anda:",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("detail|"):
        k = data.split("|")[1]
        p = PAKET[k]
        await query.edit_message_text(
            f"{p['emoji']} *Detail Paket*\n\n"
            f"📦 *{p['nama']}*\n"
            f"📱 {p['deskripsi']}\n"
            f"⏱ Garansi: *{p['garansi']}*\n"
            f"💰 Harga: *Rp {p['harga']:,}*\n\n"
            f"Lanjutkan pembelian?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Beli Sekarang", callback_data=f"bayar|{k}")],
                [InlineKeyboardButton("🔙 Kembali", callback_data="beli")]]))

    elif data.startswith("bayar|"):
        k = data.split("|")[1]
        p = PAKET[k]
        order_id = simpan_order(user.id, p['nama'], p['harga'])
        await query.edit_message_text(
            f"💳 *Instruksi Pembayaran*\n\n"
            f"📦 Paket: *{p['nama']}*\n"
            f"💰 Total: *Rp {p['harga']:,}*\n\n"
            f"Transfer ke:\n"
            f"🏦 Bank: *{BANK}*\n"
            f"💳 No. Rek: `{NOMOR_REKENING}`\n"
            f"👤 Atas Nama: *{NAMA_REKENING}*\n\n"
            f"⚠️ Setelah transfer, tap tombol di bawah dan kirim bukti transfer ke admin.\n\n"
            f"🔖 Order ID: *#{order_id}*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Saya Sudah Transfer", callback_data=f"konfirm|{order_id}|{user.id}|{p['harga']}|{k}")],
                [InlineKeyboardButton("❌ Batalkan", callback_data="beli")]]))

    elif data.startswith("konfirm|"):
        parts = data.split("|")
        order_id = parts[1]
        uid = int(parts[2])
        harga = int(parts[3])
        k = parts[4]
        p = PAKET[k]
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🛒 *ORDER BARU!*\n\n"
                 f"👤 User: {user.first_name} (@{user.username})\n"
                 f"🆔 ID: {uid}\n"
                 f"📦 Paket: {p['nama']}\n"
                 f"💰 Harga: Rp {harga:,}\n"
                 f"🔖 Order ID: #{order_id}\n\n"
                 f"Cek bukti transfer lalu kirim nomor ke user!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"✅ Selesaikan Order #{order_id}", callback_data=f"selesai|{order_id}|{uid}")]
            ]))
        await query.edit_message_text(
            f"✅ *Konfirmasi Terkirim!*\n\n"
            f"📦 Paket: *{p['nama']}*\n"
            f"💰 Total: *Rp {harga:,}*\n"
            f"🔖 Order ID: *#{order_id}*\n\n"
            f"⏳ Segera kirim bukti transfer ke admin.\n"
            f"Nomor WA Badak akan dikirim setelah pembayaran dikonfirmasi.\n\n"
            f"Terima kasih! 🙏",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📞 Hubungi Admin", url=f"https://t.me/{ADMIN_USERNAME}")],
                [InlineKeyboardButton("🔙 Menu Utama", callback_data="menu")]]))

    elif data.startswith("selesai|"):
        if user.id != ADMIN_ID:
            await query.answer("❌ Anda bukan admin!", show_alert=True)
            return
        parts = data.split("|")
        order_id = int(parts[1])
        uid = int(parts[2])
        selesaikan_order(order_id)
        await context.bot.send_message(
            chat_id=uid,
            text=f"✅ *Pembayaran Dikonfirmasi!*\n\n"
                 f"Order *#{order_id}* telah selesai diproses.\n"
                 f"Nomor WA Badak Anda akan segera dikirim.\n\n"
                 f"Terima kasih telah berbelanja! 🙏",
            parse_mode="Markdown")
        await query.edit_message_text(
            f"✅ Order #{order_id} selesai! Notifikasi telah dikirim ke user.")

    elif data == "riwayat":
        riwayat = get_riwayat(user.id)
        if not riwayat:
            teks = "📜 *Riwayat Order*\n\nBelum ada order."
        else:
            teks = "📜 *Riwayat Order (5 Terakhir)*\n\n"
            for r in riwayat:
                status_emoji = "✅" if r[2] == "selesai" else "⏳"
                teks += f"{status_emoji} {r[0]}\n💰 Rp {r[1]:,} | {r[2]}\n🕐 {r[3]}\n\n"
        await query.edit_message_text(
            teks, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Kembali", callback_data="menu")]]))

# ================================
# MAIN
# ================================
def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handler))
    print("✅ Bot WA Badak Store sedang berjalan...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
