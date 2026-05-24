import random
import sqlite3
import string
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8956798122:AAFLWjr-HA0dLQwll5EPPcQk1WJ-Z8lTz-Y"
ADMIN_ID = 8123373116
NOMOR_REKENING = "901727395930"
NAMA_REKENING = "CIT***"
BANK = "SeaBank"
ADMIN_USERNAME = "Galtzyyo"
CHANNEL_TESTI = "@RanggaShoping"

PAKET = {
    "1": {"nama": "Nomor WA Badak Garansi 7 Hari", "deskripsi": "Max Spam 500 Nomor/Hari", "harga": 150000, "garansi": "7 Hari", "garansi_hari": 7, "emoji": "🔥"},
    "2": {"nama": "Nomor WA Badak Verif Garansi 3 Bulan", "deskripsi": "Max Spam 1000 Nomor/Hari", "harga": 300000, "garansi": "3 Bulan", "garansi_hari": 90, "emoji": "💎"},
    "3": {"nama": "Nomor WA Badak Api Verif Include FBM Garansi 5 Bulan", "deskripsi": "Max Spam 1500 Nomor/Hari", "harga": 500000, "garansi": "5 Bulan", "garansi_hari": 150, "emoji": "👑"},
}

ORDERS = {}
WAITING_CLAIM = {}

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
        paket_key TEXT,
        harga INTEGER,
        status TEXT DEFAULT "pending",
        garansi_sampai TIMESTAMP,
        waktu TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS stok (
        paket_key TEXT PRIMARY KEY,
        jumlah INTEGER DEFAULT 0)''')
    for k in PAKET.keys():
        c.execute("INSERT OR IGNORE INTO stok (paket_key, jumlah) VALUES (?,?)", (k, 0))
    conn.commit()
    conn.close()

def register_user(user_id, username, nama):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username, nama) VALUES (?,?,?)",
              (user_id, username, nama))
    conn.commit()
    conn.close()

def get_stok(paket_key):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("SELECT jumlah FROM stok WHERE paket_key=?", (paket_key,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def set_stok(paket_key, jumlah):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO stok (paket_key, jumlah) VALUES (?,?)", (paket_key, jumlah))
    conn.commit()
    conn.close()

def kurangi_stok(paket_key):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("UPDATE stok SET jumlah=jumlah-1 WHERE paket_key=? AND jumlah > 0", (paket_key,))
    conn.commit()
    conn.close()

def simpan_order(user_id, username, paket, paket_key, harga):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    garansi_hari = PAKET[paket_key]["garansi_hari"]
    garansi_sampai = (datetime.now() + timedelta(days=garansi_hari)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO orders (user_id, username, paket, paket_key, harga, garansi_sampai) VALUES (?,?,?,?,?,?)",
              (user_id, username, paket, paket_key, harga, garansi_sampai))
    order_id = c.lastrowid
    conn.commit()
    conn.close()
    return order_id, garansi_sampai

def get_order_aktif(user_id):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("SELECT * FROM orders WHERE user_id=? AND status='selesai' AND garansi_sampai > ? ORDER BY waktu DESC",
              (user_id, now))
    result = c.fetchall()
    conn.close()
    return result

def get_orders_user(user_id):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("SELECT id, paket, harga, status, garansi_sampai, waktu FROM orders WHERE user_id=? ORDER BY waktu DESC LIMIT 5",
              (user_id,))
    result = c.fetchall()
    conn.close()
    return result

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user.id, user.username or "", user.first_name)
    s1 = get_stok("1")
    s2 = get_stok("2")
    s3 = get_stok("3")
    teks = (
        "🔥 Selamat Datang di WA Badak Store!\n\n"
        f"Halo {user.first_name}! 👋\n\n"
        "Kami menyediakan Nomor WA Badak berkualitas tinggi.\n\n"
        "📋 DAFTAR PRODUK:\n\n"
        f"🔥 Paket 1 - Nomor WA Badak Garansi 7 Hari\n"
        f"   📱 Max Spam 500 Nomor/Hari\n"
        f"   💰 Rp 150.000\n"
        f"   📦 Stok: {'Tersedia (' + str(s1) + ')' if s1 > 0 else 'Habis'}\n\n"
        f"💎 Paket 2 - Nomor WA Badak Verif Garansi 3 Bulan\n"
        f"   📱 Max Spam 1000 Nomor/Hari\n"
        f"   💰 Rp 300.000\n"
        f"   📦 Stok: {'Tersedia (' + str(s2) + ')' if s2 > 0 else 'Habis'}\n\n"
        f"👑 Paket 3 - Nomor WA Badak Api Verif Include FBM Garansi 5 Bulan\n"
        f"   📱 Max Spam 1500 Nomor/Hari\n"
        f"   💰 Rp 500.000\n"
        f"   📦 Stok: {'Tersedia (' + str(s3) + ')' if s3 > 0 else 'Habis'}\n\n"
        "━━━━━━━━━━━━━━━\n"
        "🛒 Cara Order:\n\n"
        "/beli1 - Beli Paket 1\n"
        "/beli2 - Beli Paket 2\n"
        "/beli3 - Beli Paket 3\n\n"
        "/claim_garansi - Klaim garansi WA bermasalah\n"
        "/cek_order - Cek status order\n"
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

    stok = get_stok(k)
    if stok <= 0:
        await update.message.reply_text(
            f"Maaf stok Paket {k} sedang habis!\n\n"
            "Silakan cek paket lain atau hubungi admin.\n"
            f"Admin: @{ADMIN_USERNAME}")
        return

    p = PAKET[k]
    harga = p["harga"]
    order_id, garansi_sampai = simpan_order(user.id, user.username or "", p["nama"], k, harga)
    ORDERS[user.id] = {"paket": p["nama"], "paket_key": k, "harga": harga, "order_id": order_id}

    teks = (
        f"{p['emoji']} {p['nama']}\n\n"
        f"📱 {p['deskripsi']}\n"
        f"Garansi: {p['garansi']}\n"
        f"💰 Harga: Rp {harga:,}\n\n"
        "━━━━━━━━━━━━━━━\n"
        "💳 Instruksi Pembayaran:\n\n"
        f"Bank: {BANK}\n"
        f"No Rek: {NOMOR_REKENING}\n"
        f"Atas Nama: {NAMA_REKENING}\n\n"
        f"🔖 Order ID: #{order_id}\n\n"
        "📸 Kirim FOTO bukti transfer ke bot ini.\n"
        f"Ada pertanyaan? Hubungi @{ADMIN_USERNAME}"
    )
    await update.message.reply_text(teks)

async def cek_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    orders = get_orders_user(user.id)
    if not orders:
        await update.message.reply_text("Belum ada order. Ketik /beli1, /beli2, atau /beli3!")
        return
    teks = "📋 Riwayat Order Anda:\n\n"
    for o in orders:
        status_emoji = "✅" if o[3] == "selesai" else "⏳"
        teks += (
            f"{status_emoji} Order #{o[0]}\n"
            f"   📦 {o[1]}\n"
            f"   💰 Rp {o[2]:,}\n"
            f"   📌 Status: {o[3]}\n"
            f"   Garansi: {o[4]}\n"
            f"   🕐 {o[5]}\n\n"
        )
    await update.message.reply_text(teks)

async def claim_garansi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    orders_aktif = get_order_aktif(user.id)
    if not orders_aktif:
        await update.message.reply_text(
            "Tidak ada order aktif dengan garansi yang masih berlaku.\n\n"
            "Pastikan order sudah dikonfirmasi admin dan garansi belum habis.")
        return
    teks = "✅ Order aktif dengan garansi berlaku:\n\n"
    for o in orders_aktif:
        teks += (
            f"📦 {o[3]}\n"
            f"🔖 Order ID: #{o[0]}\n"
            f"Garansi sampai: {o[7]}\n\n"
        )
    teks += "Kirim FOTO screenshot WA yang bermasalah sekarang!\nAdmin akan segera memproses klaim Anda."
    WAITING_CLAIM[user.id] = True
    await update.message.reply_text(teks)

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
                "Jika butuh kode OTP ketik /minta_otp\n"
                "Jika WA bermasalah ketik /claim_garansi\n\n"
                "Terima kasih! 🙏"
            ))

        conn = sqlite3.connect("wabot.db")
        c = conn.cursor()
        c.execute("SELECT id, paket, harga FROM orders WHERE user_id=? AND status='pending' ORDER BY waktu DESC LIMIT 1",
                  (user_id,))
        order = c.fetchone()
        if order:
            c.execute("UPDATE orders SET status='selesai' WHERE id=?", (order[0],))
            conn.commit()
            kurangi_stok(ORDERS.get(user_id, {}).get("paket_key", "1"))

            try:
                await context.bot.send_message(
                    chat_id=CHANNEL_TESTI,
                    text=(
                        "✅ Order Berhasil!\n\n"
                        f"📦 Paket: {order[1]}\n"
                        f"💰 Harga: Rp {order[2]:,}\n"
                        f"🕐 {datetime.now().strftime('%d-%m-%Y %H:%M')}\n\n"
                        "Terima kasih telah berbelanja di WA Badak Store! 🔥\n"
                        f"Order sekarang: t.me/{(await context.bot.get_me()).username}"
                    ))
            except Exception:
                pass
        conn.close()

        await update.message.reply_text(f"✅ Nomor berhasil dikirim ke user {user_id}!")
    except Exception as e:
        await update.message.reply_text(f"Gagal kirim! Error: {e}")

async def kirim_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Bukan admin!")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Cara pakai:\n/kirim_otp [ID_USER] [KODE_OTP]")
        return
    user_id = context.args[0]
    kode_otp = context.args[1]
    try:
        await context.bot.send_message(
            chat_id=int(user_id),
            text=(
                "🔐 Kode OTP WhatsApp Anda:\n\n"
                f"🔑 {kode_otp}\n\n"
                "Masukkan kode ini di WhatsApp.\n"
                "Jangan bagikan ke siapapun!\n"
                "Berlaku 60 detik."
            ))
        await update.message.reply_text(f"✅ OTP berhasil dikirim ke user {user_id}!")
    except Exception as e:
        await update.message.reply_text(f"Gagal kirim OTP! Error: {e}")

async def setstok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Bukan admin!")
        return
    if len(context.args) < 2:
        await update.message.reply_text(
            "Cara pakai:\n/setstok [PAKET] [JUMLAH]\n\n"
            "Contoh:\n"
            "/setstok 1 10\n"
            "/setstok 2 5\n"
            "/setstok 3 3")
        return
    paket_key = context.args[0]
    if paket_key not in PAKET:
        await update.message.reply_text("Paket tidak valid! Gunakan 1, 2, atau 3")
        return
    jumlah = int(context.args[1])
    set_stok(paket_key, jumlah)
    p = PAKET[paket_key]
    await update.message.reply_text(
        f"✅ Stok berhasil diupdate!\n\n"
        f"📦 Paket {paket_key}: {p['nama']}\n"
        f"Stok baru: {jumlah}")

async def cek_stok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Bukan admin!")
        return
    teks = "📦 Stok Produk:\n\n"
    for k, p in PAKET.items():
        stok = get_stok(k)
        teks += f"{p['emoji']} Paket {k}: {p['nama']}\n   Stok: {stok}\n\n"
    await update.message.reply_text(teks)

async def terima_foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if WAITING_CLAIM.get(user.id):
        del WAITING_CLAIM[user.id]
        await update.message.forward(chat_id=ADMIN_ID)
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "🔧 KLAIM GARANSI MASUK!\n\n"
                f"👤 {user.first_name} (@{user.username})\n"
                f"🆔 ID: {user.id}\n\n"
                "Foto WA bermasalah ada di atas.\n"
                "Kirim nomor pengganti:\n"
                f"/kirim {user.id} NOMOR_WA_BARU"
            ))
        await update.message.reply_text(
            "✅ Klaim garansi terkirim ke admin!\n\n"
            "Admin akan segera memproses dan mengirim nomor pengganti.\n"
            "Terima kasih! 🙏")
        return

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
    del ORDERS[user.id]

async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user.id, user.username or "", user.first_name)
    teks = update.message.text.lower() if update.message.text else ""
    if any(kata in teks for kata in ["harga", "price", "berapa"]):
        await update.message.reply_text(
            "💰 Harga Paket WA Badak:\n\n"
            "🔥 Paket 1: Rp 150.000\n"
            "💎 Paket 2: Rp 300.000\n"
            "👑 Paket 3: Rp 500.000\n\n"
            "Ketik /start untuk detail lengkap!")
    elif any(kata in teks for kata in ["garansi", "jaminan"]):
        await update.message.reply_text(
            "✅ Garansi WA Badak:\n\n"
            "🔥 Paket 1: 7 Hari\n"
            "💎 Paket 2: 3 Bulan\n"
            "👑 Paket 3: 5 Bulan\n\n"
            f"Hubungi @{ADMIN_USERNAME} untuk info lebih lanjut!")
    elif any(kata in teks for kata in ["cara", "order", "beli", "pesan"]):
        await update.message.reply_text(
            "🛒 Cara Order:\n\n"
            "1. Ketik /beli1, /beli2, atau /beli3\n"
            "2. Transfer sesuai nominal\n"
            "3. Kirim foto bukti transfer\n"
            "4. Tunggu konfirmasi admin\n\n"
            "Mudah kan? 😊")
    elif any(kata in teks for kata in ["bayar", "transfer", "rekening"]):
        await update.message.reply_text(
            "💳 Info Pembayaran:\n\n"
            f"Bank: {BANK}\n"
            f"No Rek: {NOMOR_REKENING}\n"
            f"Atas Nama: {NAMA_REKENING}\n\n"
            "Setelah transfer kirim foto bukti ke bot ini!")
    else:
        await update.message.reply_text(
            f"Halo! Ketik /start untuk melihat menu.\n\n"
            f"Atau hubungi admin: @{ADMIN_USERNAME}")

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("beli1", beli))
    app.add_handler(CommandHandler("beli2", beli))
    app.add_handler(CommandHandler("beli3", beli))
    app.add_handler(CommandHandler("cek_order", cek_order))
    app.add_handler(CommandHandler("claim_garansi", claim_garansi))
    app.add_handler(CommandHandler("minta_otp", minta_otp))
    app.add_handler(CommandHandler("kirim", kirim))
    app.add_handler(CommandHandler("kirim_otp", kirim_otp))
    app.add_handler(CommandHandler("setstok", setstok))
    app.add_handler(CommandHandler("cek_stok", cek_stok))
    app.add_handler(MessageHandler(filters.PHOTO, terima_foto))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))
    print("✅ Bot WA Badak Store sedang berjalan...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
