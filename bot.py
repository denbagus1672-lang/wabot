import random
import sqlite3
from datetime import datetime
import pytz
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8956798122:AAFLWjr-HA0dLQwll5EPPcQk1WJ-Z8lTz-Y"
ADMIN_ID = 8123373116
NOMOR_REKENING = "901727395930"
NAMA_REKENING = "CIT***"
BANK = "SeaBank"
ADMIN_USERNAME = "Galtzyyo"
CHANNEL_TESTI = "@RanggaShoping"
QRIS_URL = "https://raw.githubusercontent.com/denbagus1672-lang/wabot/master/ReactNative-snapshot-image3971213875209633470.png"

PAKET = {
    "1": {"nama": "WA Badak Garansi 7 Hari", "deskripsi": "Max Spam 500 Nomor/Hari", "harga": 150000, "garansi": "7 Hari", "emoji": "🔥"},
    "2": {"nama": "WA Badak Verif Garansi 3 Bulan", "deskripsi": "Max Spam 1000 Nomor/Hari", "harga": 300000, "garansi": "3 Bulan", "emoji": "💎"},
    "3": {"nama": "WA Badak Api Verif FBM Garansi 5 Bulan", "deskripsi": "Max Spam 1500 Nomor/Hari", "harga": 500000, "garansi": "5 Bulan", "emoji": "👑"},
}

ORDERS = {}
USER_INFO = {}

def init_db():
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        nama TEXT,
        waktu TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        paket TEXT,
        harga INTEGER,
        status TEXT DEFAULT "pending",
        waktu TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def register_user(user_id, username, nama):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username, nama) VALUES (?,?,?)",
              (user_id, username, nama))
    conn.commit()
    conn.close()

def simpan_order(user_id, username, paket, harga):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("INSERT INTO orders (user_id, username, paket, harga) VALUES (?,?,?,?)",
              (user_id, username, paket, harga))
    conn.commit()
    conn.close()

def selesai_order(user_id):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("UPDATE orders SET status='selesai' WHERE user_id=? AND status='pending'", (user_id,))
    conn.commit()
    conn.close()

def get_statistik():
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    total_user = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM orders")
    total_order = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM orders WHERE status='selesai'")
    total_selesai = c.fetchone()[0]
    c.execute("SELECT SUM(harga) FROM orders WHERE status='selesai'")
    total_income = c.fetchone()[0] or 0
    wib = pytz.timezone("Asia/Jakarta")
    today = datetime.now(wib).strftime("%Y-%m-%d")
    c.execute("SELECT COUNT(*) FROM orders WHERE waktu LIKE ?", (f"{today}%",))
    order_hari_ini = c.fetchone()[0]
    c.execute("SELECT SUM(harga) FROM orders WHERE status='selesai' AND waktu LIKE ?", (f"{today}%",))
    income_hari_ini = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM users WHERE waktu LIKE ?", (f"{today}%",))
    user_baru = c.fetchone()[0]
    conn.close()
    return total_user, total_order, total_selesai, total_income, order_hari_ini, income_hari_ini, user_baru

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user.id, user.username or "", user.first_name)
    teks = (
        "🔥 Selamat Datang di WA Badak Store!\n\n"
        f"Halo {user.first_name}! 👋\n\n"
        "Kami menyediakan Nomor WA Badak berkualitas tinggi.\n\n"
        "📋 DAFTAR PRODUK:\n\n"
        "🔥 Paket 1 - WA Badak Garansi 7 Hari\n"
        "   📱 Max Spam 500 Nomor/Hari\n"
        "   💰 Rp 150.000\n\n"
        "💎 Paket 2 - WA Badak Verif Garansi 3 Bulan\n"
        "   📱 Max Spam 1000 Nomor/Hari\n"
        "   💰 Rp 300.000\n\n"
        "👑 Paket 3 - WA Badak Api Verif FBM Garansi 5 Bulan\n"
        "   📱 Max Spam 1500 Nomor/Hari\n"
        "   💰 Rp 500.000\n\n"
        "━━━━━━━━━━━━━━━\n"
        "🛒 Cara Order:\n\n"
        "/beli1 - Beli Paket 1\n"
        "/beli2 - Beli Paket 2\n"
        "/beli3 - Beli Paket 3\n\n"
        "/minta_otp - Request kode OTP\n\n"
        f"📢 Testimoni: t.me/RanggaShoping\n"
        f"📞 Admin: t.me/{ADMIN_USERNAME}"
    )
    await update.message.reply_text(teks)

async def beli(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cmd = update.message.text.strip().lower()

    if "/beli1" in cmd:
        k = "1"
    elif "/beli2" in cmd:
        k = "2"
    elif "/beli3" in cmd:
        k = "3"
    else:
        await update.message.reply_text("Gunakan /beli1, /beli2, atau /beli3")
        return

    p = PAKET[k]
    order_id = random.randint(10000, 99999)
    ORDERS[user.id] = {"paket": p["nama"], "harga": p["harga"], "order_id": order_id}
    USER_INFO[user.id] = {"username": user.username or "", "nama": user.first_name}
    simpan_order(user.id, user.username or "", p["nama"], p["harga"])

    teks = (
        f"{p['emoji']} {p['nama']}\n\n"
        f"📱 {p['deskripsi']}\n"
        f"Garansi: {p['garansi']}\n"
        f"💰 Harga: Rp {p['harga']:,}\n\n"
        "━━━━━━━━━━━━━━━\n"
        "💳 Pilih Metode Pembayaran:\n\n"
        "/seabank - Transfer SeaBank\n"
        "/qris - Bayar via QRIS\n\n"
        f"🔖 Order ID: #{order_id}\n\n"
        f"Ada pertanyaan? Hubungi @{ADMIN_USERNAME}"
    )
    await update.message.reply_text(teks)

async def seabank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    order_info = ORDERS.get(user.id)
    if not order_info:
        await update.message.reply_text("Pilih paket dulu dengan /beli1, /beli2, atau /beli3")
        return
    teks = (
        "🏦 Pembayaran via SeaBank\n\n"
        f"📦 Paket: {order_info['paket']}\n"
        f"💰 Total: Rp {order_info['harga']:,}\n\n"
        "Transfer ke:\n"
        f"Bank: {BANK}\n"
        f"No Rek: {NOMOR_REKENING}\n"
        f"Atas Nama: {NAMA_REKENING}\n\n"
        f"🔖 Order ID: #{order_info['order_id']}\n\n"
        "📸 Kirim FOTO bukti transfer ke bot ini setelah transfer."
    )
    await update.message.reply_text(teks)

async def qris(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    order_info = ORDERS.get(user.id)
    if not order_info:
        await update.message.reply_text("Pilih paket dulu dengan /beli1, /beli2, atau /beli3")
        return
    caption = (
        "🔳 Pembayaran via QRIS\n\n"
        f"📦 Paket: {order_info['paket']}\n"
        f"💰 Total: Rp {order_info['harga']:,}\n\n"
        "Scan QR di atas lalu masukkan nominal sesuai harga paket.\n\n"
        f"🔖 Order ID: #{order_info['order_id']}\n\n"
        "📸 Kirim FOTO bukti pembayaran ke bot ini setelah bayar."
    )
    await update.message.reply_photo(photo=QRIS_URL, caption=caption)

async def statistik(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Bukan admin!")
        return
    total_user, total_order, total_selesai, total_income, order_hari_ini, income_hari_ini, user_baru = get_statistik()
    wib = pytz.timezone("Asia/Jakarta")
    waktu = datetime.now(wib).strftime("%d-%m-%Y %H:%M")
    teks = (
        "📊 STATISTIK BOT\n\n"
        f"👥 Total Pengguna: {total_user}\n"
        f"🆕 Pengguna Baru Hari Ini: {user_baru}\n"
        f"🛒 Total Order Masuk: {total_order}\n"
        f"✅ Order Selesai: {total_selesai}\n"
        f"⏳ Order Pending: {total_order - total_selesai}\n"
        f"💰 Total Pemasukan: Rp {total_income:,}\n\n"
        "━━━━━━━━━━━━━━━\n"
        "📅 Hari Ini:\n"
        f"🛒 Order: {order_hari_ini}\n"
        f"💰 Pemasukan: Rp {income_hari_ini:,}\n\n"
        f"🕐 Update: {waktu} WIB"
    )
    await update.message.reply_text(teks)

async def kirim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Bukan admin!")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Cara pakai:\n/kirim [ID_USER] [NOMOR_WA]")
        return
    user_id = int(context.args[0])
    nomor_wa = context.args[1]
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "✅ Pembayaran Dikonfirmasi!\n\n"
                f"📱 Nomor WA Badak Anda: {nomor_wa}\n\n"
                "Silakan login WA menggunakan nomor di atas.\n"
                "Jika butuh kode OTP ketik /minta_otp\n\n"
                "Terima kasih! 🙏"
            ))
        selesai_order(user_id)
        await update.message.reply_text(f"✅ Nomor berhasil dikirim ke user {user_id}!")
    except Exception as e:
        await update.message.reply_text(f"Gagal kirim! Error: {e}")

async def minta_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text("🔐 Request OTP dikirim ke admin. Tunggu sebentar!")
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "🔐 REQUEST OTP!\n\n"
            f"👤 {user.first_name} (@{user.username})\n"
            f"🆔 ID: {user.id}\n\n"
            "Kirim OTP:\n"
            f"/kirim_otp {user.id} KODE_OTP"
        ))

async def kirim_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Bukan admin!")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Cara pakai:\n/kirim_otp [ID_USER] [KODE_OTP]")
        return
    user_id = int(context.args[0])
    kode_otp = context.args[1]
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "🔐 Kode OTP WhatsApp Anda:\n\n"
                f"🔑 {kode_otp}\n\n"
                "Masukkan kode ini di WhatsApp.\n"
                "Jangan bagikan ke siapapun!\n"
                "Berlaku 60 detik."
            ))
        await update.message.reply_text(f"✅ OTP berhasil dikirim ke user {user_id}!")

        info = USER_INFO.get(user_id, {})
        username = info.get("username", "")
        order_info = ORDERS.get(user_id, {})
        paket = order_info.get("paket", "")
        harga = order_info.get("harga", 0)

        wib = pytz.timezone("Asia/Jakarta")
        waktu = datetime.now(wib).strftime("%d-%m-%Y %H:%M")
        bot_info = await context.bot.get_me()

        try:
            await context.bot.send_message(
                chat_id=CHANNEL_TESTI,
                text=(
                    "✅ Order Berhasil!\n\n"
                    f"👤 Customer: {'@' + username if username else 'Customer'}\n"
                    f"📦 Paket: {paket}\n"
                    f"💰 Harga: Rp {harga:,}\n"
                    f"🕐 {waktu} WIB\n\n"
                    "Bergabung dan order sekarang!\n"
                    f"t.me/{bot_info.username}"
                ))
        except Exception:
            pass

    except Exception as e:
        await update.message.reply_text(f"Gagal kirim OTP! Error: {e}")

async def terima_bukti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    order_info = ORDERS.get(user.id)
    if not order_info:
        await update.message.reply_text(
            "Silakan pilih paket dulu dengan /beli1, /beli2, atau /beli3")
        return
    paket = order_info["paket"]
    harga = order_info["harga"]
    order_id = order_info["order_id"]
    await update.message.forward(chat_id=ADMIN_ID)
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "💳 BUKTI TRANSFER MASUK!\n\n"
            f"👤 {user.first_name} (@{user.username})\n"
            f"🆔 ID: {user.id}\n"
            f"📦 Paket: {paket}\n"
            f"💰 Harga: Rp {harga:,}\n"
            f"🔖 Order ID: #{order_id}\n\n"
            "Kirim nomor ke customer:\n"
            f"/kirim {user.id} NOMOR_WA_BADAK"
        ))
    await update.message.reply_text(
        "✅ Bukti transfer terkirim ke admin!\n\n"
        f"📦 Paket: {paket}\n"
        f"💰 Total: Rp {harga:,}\n"
        f"🔖 Order ID: #{order_id}\n\n"
        "Tunggu konfirmasi dari admin.\n"
        "Terima kasih! 🙏")

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("beli1", beli))
    app.add_handler(CommandHandler("beli2", beli))
    app.add_handler(CommandHandler("beli3", beli))
    app.add_handler(CommandHandler("seabank", seabank))
    app.add_handler(CommandHandler("qris", qris))
    app.add_handler(CommandHandler("kirim", kirim))
    app.add_handler(CommandHandler("kirim_otp", kirim_otp))
    app.add_handler(CommandHandler("minta_otp", minta_otp))
    app.add_handler(CommandHandler("statistik", statistik))
    app.add_handler(MessageHandler(filters.PHOTO, terima_bukti))
    print("✅ Bot WA Badak Store sedang berjalan...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
