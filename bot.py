import asyncio
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
        user_id INTEGER PRIMARY KEY, username TEXT, full_name TEXT, saldo INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS transaksi (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, jenis TEXT,
        jumlah INTEGER, keterangan TEXT, waktu TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS topup (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        jumlah INTEGER, status TEXT DEFAULT "pending", waktu TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def register_user(user_id, username, full_name):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?,?,?)", (user_id, username, full_name))
    conn.commit()
    conn.close()

def get_saldo(user_id):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("SELECT saldo FROM users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def update_saldo(user_id, jumlah):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("UPDATE users SET saldo=saldo+? WHERE user_id=?", (jumlah, user_id))
    conn.commit()
    conn.close()

def catat_transaksi(user_id, jenis, jumlah, keterangan):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("INSERT INTO transaksi (user_id, jenis, jumlah, keterangan) VALUES (?,?,?,?)", (user_id, jenis, jumlah, keterangan))
    conn.commit()
    conn.close()

def get_riwayat(user_id):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("SELECT jenis, jumlah, keterangan, waktu FROM transaksi WHERE user_id=? ORDER BY waktu DESC LIMIT 5", (user_id,))
    result = c.fetchall()
    conn.close()
    return result

def simpan_topup(user_id, jumlah):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("INSERT INTO topup (user_id, jumlah) VALUES (?,?)", (user_id, jumlah))
    topup_id = c.lastrowid
    conn.commit()
    conn.close()
    return topup_id

def approve_topup_db(topup_id):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("UPDATE topup SET status='approved' WHERE id=?", (topup_id,))
    conn.commit()
    conn.close()

# ================================
# KEYBOARD
# ================================
def keyboard_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Saldo Saya", callback_data="saldo"),
         InlineKeyboardButton("🛒 Beli Nomor", callback_data="beli")],
        [InlineKeyboardButton("💳 Topup Saldo", callback_data="topup"),
         InlineKeyboardButton("📜 Riwayat", callback_data="riwayat")],
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

    elif data == "saldo":
        saldo = get_saldo(user.id)
        await query.edit_message_text(
            f"💰 *Saldo Anda*\n\nSaldo: *Rp {saldo:,}*\n\nGunakan saldo untuk membeli nomor WA Badak.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Topup Sekarang", callback_data="topup")],
                [InlineKeyboardButton("🔙 Kembali", callback_data="menu")]]))

    elif data == "beli":
        keyboard = [[InlineKeyboardButton(
            f"{p['emoji']} {p['nama']} - Rp {p['harga']:,}", callback_data=f"detail_{k}")]
            for k, p in PAKET.items()]
        keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="menu")])
        await query.edit_message_text(
            "🛒 *Pilih Paket WA Badak:*\n\nPilih paket yang sesuai kebutuhan Anda:",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("detail_"):
        k = data.replace("detail_", "")
        p = PAKET[k]
        saldo = get_saldo(user.id)
        cukup = "✅ Saldo mencukupi" if saldo >= p['harga'] else "❌ Saldo tidak mencukupi, silakan topup dulu"
        await query.edit_message_text(
            f"🛒 *Detail Paket*\n\n"
            f"📦 Paket: *{p['nama']}*\n"
            f"📱 {p['deskripsi']}\n"
            f"⏱ Garansi: *{p['garansi']}*\n"
            f"💰 Harga: *Rp {p['harga']:,}*\n\n"
            f"💳 Saldo Anda: *Rp {saldo:,}*\n{cukup}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Konfirmasi Beli", callback_data=f"beli_{k}")],
                [InlineKeyboardButton("🔙 Kembali", callback_data="beli")]]))

    elif data.startswith("beli_"):
        k = data.replace("beli_", "")
        p = PAKET[k]
        saldo = get_saldo(user.id)
        if saldo < p['harga']:
            await query.edit_message_text(
                f"❌ *Saldo Tidak Mencukupi!*\n\nSaldo Anda: Rp {saldo:,}\nHarga: Rp {p['harga']:,}\n\nSilakan topup dulu.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💳 Topup", callback_data="topup")],
                    [InlineKeyboardButton("🔙 Kembali", callback_data="menu")]]))
            return
        update_saldo(user.id, -p['harga'])
        catat_transaksi(user.id, "Pembelian", p['harga'], p['nama'])
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🛒 *ORDER MASUK!*\n\n"
                 f"👤 User: {user.first_name} (@{user.username})\n"
                 f"🆔 ID: {user.id}\n"
                 f"📦 Paket: {p['nama']}\n"
                 f"💰 Harga: Rp {p['harga']:,}\n\n"
                 f"⚡ Segera kirim nomor ke user!",
            parse_mode="Markdown")
        await query.edit_message_text(
            f"✅ *Pembelian Berhasil!*\n\n"
            f"📦 Paket: *{p['nama']}*\n"
            f"💰 Terbayar: *Rp {p['harga']:,}*\n\n"
            f"⏳ Admin akan segera mengirimkan nomor WA Badak Anda.\n"
            f"Harap tunggu maksimal 5-10 menit.\n\nTerima kasih! 🙏",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Menu Utama", callback_data="menu")]]))

    elif data == "topup":
        await query.edit_message_text(
            "💳 *Topup Saldo*\n\nPilih nominal topup:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💵 Rp 150.000", callback_data="nom|150000"),
                 InlineKeyboardButton("💵 Rp 300.000", callback_data="nom|300000")],
                [InlineKeyboardButton("💵 Rp 500.000", callback_data="nom|500000"),
                 InlineKeyboardButton("💵 Rp 1.000.000", callback_data="nom|1000000")],
                [InlineKeyboardButton("🔙 Kembali", callback_data="menu")]]))

    elif data.startswith("nom|"):
        nominal = int(data.split("|")[1])
        topup_id = simpan_topup(user.id, nominal)
        await query.edit_message_text(
            f"💳 *Instruksi Topup*\n\n"
            f"Nominal: *Rp {nominal:,}*\n\n"
            f"Transfer ke:\n"
            f"🏦 Bank: *{BANK}*\n"
            f"💳 No. Rek: `{NOMOR_REKENING}`\n"
            f"👤 Atas Nama: *{NAMA_REKENING}*\n\n"
            f"⚠️ Setelah transfer tap tombol di bawah lalu kirim bukti ke admin.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Saya Sudah Transfer", callback_data=f"kt|{topup_id}|{nominal}|{user.id}")],
                [InlineKeyboardButton("🔙 Kembali", callback_data="topup")]]))

    elif data.startswith("kt|"):
        parts = data.split("|")
        topup_id = parts[1]
        nominal = int(parts[2])
        uid = int(parts[3])
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"💳 *TOPUP REQUEST!*\n\n"
                 f"👤 User: {user.first_name} (@{user.username})\n"
                 f"🆔 ID: {uid}\n"
                 f"💰 Nominal: Rp {nominal:,}\n"
                 f"🔖 ID Topup: #{topup_id}\n\n"
                 f"Cek bukti transfer lalu approve!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"✅ Approve #{topup_id}", callback_data=f"ap|{topup_id}|{uid}|{nominal}")]]))
        await query.edit_message_text(
            f"✅ *Permintaan Topup Terkirim!*\n\n"
            f"Nominal: *Rp {nominal:,}*\n\n"
            f"⏳ Kirim bukti transfer ke admin dan tunggu konfirmasi.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Menu Utama", callback_data="menu")]]))

    elif data.startswith("ap|"):
        if user.id != ADMIN_ID:
            await query.answer("❌ Anda bukan admin!", show_alert=True)
            return
        parts = data.split("|")
        topup_id = int(parts[1])
        uid = int(parts[2])
        jumlah = int(parts[3])
        approve_topup_db(topup_id)
        update_saldo(uid, jumlah)
        catat_transaksi(uid, "Topup", jumlah, f"Topup #{topup_id}")
        await context.bot.send_message(
            chat_id=uid,
            text=f"✅ *Topup Berhasil!*\n\nSaldo *Rp {jumlah:,}* telah ditambahkan.\nTerima kasih! 🙏",
            parse_mode="Markdown")
        await query.edit_message_text(f"✅ Topup #{topup_id} approved! Saldo Rp {jumlah:,} ditambahkan.")

    elif data == "riwayat":
        riwayat = get_riwayat(user.id)
        if not riwayat:
            teks = "📜 *Riwayat Transaksi*\n\nBelum ada transaksi."
        else:
            teks = "📜 *Riwayat Transaksi (5 Terakhir)*\n\n"
            for r in riwayat:
                emoji = "💳" if r[0] == "Topup" else "🛒"
                teks += f"{emoji} {r[0]}: Rp {r[1]:,}\n📝 {r[2]}\n🕐 {r[3]}\n\n"
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
