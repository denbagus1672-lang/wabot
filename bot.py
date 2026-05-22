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
CHANNEL_TESTI = "RanggaShoping"

PAKET = {
    "1": {"nama": "Nomor WA Badak Garansi 7 Hari", "deskripsi": "Max Spam 500 Nomor/Hari", "harga": 150000, "garansi": "7 Hari", "garansi_hari": 7, "emoji": "🔥"},
    "2": {"nama": "Nomor WA Badak Verif Garansi 3 Bulan", "deskripsi": "Max Spam 1000 Nomor/Hari", "harga": 300000, "garansi": "3 Bulan", "garansi_hari": 90, "emoji": "💎"},
    "3": {"nama": "Nomor WA Badak Api Verif Include FBM Garansi 5 Bulan", "deskripsi": "Max Spam 1500 Nomor/Hari", "harga": 500000, "garansi": "5 Bulan", "garansi_hari": 150, "emoji": "👑"},
}

KODE_PROMO = {
    "BADAK10": 10,
    "BLAST20": 20,
    "VIP30": 30,
}

LUCKY_CHANCE = {
    "paket1": 5,
    "paket2": 2,
    "paket3": 0.5,
    "kalah": 92.5,
}

ORDERS = {}
WAITING_CLAIM = {}
WAITING_LUCKY = {}

def init_db():
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        nama TEXT,
        referral_code TEXT,
        referred_by INTEGER DEFAULT NULL,
        diskon_referral INTEGER DEFAULT 0,
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
    c.execute('''CREATE TABLE IF NOT EXISTS tiket_lucky (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        kode TEXT UNIQUE,
        used INTEGER DEFAULT 0,
        waktu TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS blacklist (
        user_id INTEGER PRIMARY KEY)''')
    conn.commit()
    conn.close()

def generate_kode(panjang=8):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=panjang))

def register_user(user_id, username, nama):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if not c.fetchone():
        kode_referral = "REF" + generate_kode(6)
        c.execute("INSERT INTO users (user_id, username, nama, referral_code) VALUES (?,?,?,?)",
                  (user_id, username, nama, kode_referral))
        conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result

def get_user_by_referral(kode):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE referral_code=?", (kode,))
    result = c.fetchone()
    conn.close()
    return result

def set_referred_by(user_id, referrer_id):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("UPDATE users SET referred_by=? WHERE user_id=? AND referred_by IS NULL",
              (referrer_id, user_id))
    conn.commit()
    conn.close()

def set_diskon_referral(user_id, diskon):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("UPDATE users SET diskon_referral=? WHERE user_id=?", (diskon, user_id))
    conn.commit()
    conn.close()

def get_diskon_referral(user_id):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("SELECT diskon_referral FROM users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

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

def update_status_order(order_id):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("UPDATE orders SET status='selesai' WHERE id=?", (order_id,))
    conn.commit()
    conn.close()

def punya_order_selesai(user_id):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("SELECT id FROM orders WHERE user_id=? AND status='selesai'", (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def buat_tiket_lucky(user_id):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    kode = "LCK" + generate_kode(7)
    c.execute("INSERT INTO tiket_lucky (user_id, kode) VALUES (?,?)", (user_id, kode))
    conn.commit()
    conn.close()
    return kode

def get_tiket_lucky(user_id):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("SELECT kode FROM tiket_lucky WHERE user_id=? AND used=0", (user_id,))
    result = c.fetchall()
    conn.close()
    return [r[0] for r in result]

def pakai_tiket_lucky(kode):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("SELECT user_id, used FROM tiket_lucky WHERE kode=?", (kode,))
    result = c.fetchone()
    if not result or result[1] == 1:
        conn.close()
        return False
    c.execute("UPDATE tiket_lucky SET used=1 WHERE kode=?", (kode,))
    conn.commit()
    conn.close()
    return True

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
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT COUNT(*) FROM orders WHERE waktu LIKE ?", (f"{today}%",))
    order_hari_ini = c.fetchone()[0]
    c.execute("SELECT SUM(harga) FROM orders WHERE status='selesai' AND waktu LIKE ?", (f"{today}%",))
    income_hari_ini = c.fetchone()[0] or 0
    conn.close()
    return total_user, total_order, total_selesai, total_income, order_hari_ini, income_hari_ini

def get_semua_user():
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("SELECT user_id, username, nama FROM users LIMIT 50")
    result = c.fetchall()
    conn.close()
    return result

def is_blacklist(user_id):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("SELECT user_id FROM blacklist WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def tambah_blacklist(user_id):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO blacklist (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def hapus_blacklist(user_id):
    conn = sqlite3.connect("wabot.db")
    c = conn.cursor()
    c.execute("DELETE FROM blacklist WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_blacklist(user.id):
        await update.message.reply_text("❌ Akun Anda telah diblokir. Hubungi admin.")
        return
    register_user(user.id, user.username or "", user.first_name)

    if context.args:
        kode_ref = context.args[0]
        referrer = get_user_by_referral(kode_ref)
        if referrer and referrer[0] != user.id:
            set_referred_by(user.id, referrer[0])

    teks = (
        "🔥 Selamat Datang di WA Badak Store!\n\n"
        f"Halo {user.first_name}! 👋\n\n"
        "Kami menyediakan Nomor WA Badak berkualitas tinggi.\n\n"
        "📋 DAFTAR PRODUK:\n\n"
        "🔥 Paket 1 - Nomor WA Badak Garansi 7 Hari\n"
        "   📱 Max Spam 500 Nomor/Hari\n"
        "   💰 Rp 150.000\n\n"
        "💎 Paket 2 - Nomor WA Badak Verif Garansi 3 Bulan\n"
        "   📱 Max Spam 1000 Nomor/Hari\n"
        "   💰 Rp 300.000\n\n"
        "👑 Paket 3 - Nomor WA Badak Api Verif Include FBM Garansi 5 Bulan\n"
        "   📱 Max Spam 1500 Nomor/Hari\n"
        "   💰 Rp 500.000\n\n"
        "━━━━━━━━━━━━━━━\n"
        "🛒 Cara Order:\n\n"
        "/beli1 - Beli Paket 1\n"
        "/beli2 - Beli Paket 2\n"
        "/beli3 - Beli Paket 3\n\n"
        "/referral - Dapatkan kode referral\n"
        "/lucky - Lucky Draw (khusus yang sudah order)\n"
        "/claim_garansi - Klaim garansi WA bermasalah\n"
        "/cek_order - Cek status order\n"
        "/promo - Lihat kode promo\n"
        "/rating - Beri rating\n"
        "/minta_otp - Request kode OTP\n\n"
        f"📢 Testimoni: t.me/{CHANNEL_TESTI}\n"
        f"📞 Admin: t.me/{ADMIN_USERNAME}"
    )
    await update.message.reply_text(teks)

async def beli(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_blacklist(user.id):
        await update.message.reply_text("❌ Akun Anda telah diblokir.")
        return
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
    harga = p["harga"]
    diskon = 0
    diskon_info = ""

    diskon_ref = get_diskon_referral(user.id)
    if diskon_ref > 0:
        diskon = int(harga * diskon_ref / 100)
        harga = harga - diskon
        diskon_info = f"   🎁 Diskon Referral {diskon_ref}%: -Rp {diskon:,}\n   💰 Harga Akhir: Rp {harga:,}\n"
        set_diskon_referral(user.id, 0)

    if context.args and context.args[0].upper() in KODE_PROMO:
        persen = KODE_PROMO[context.args[0].upper()]
        diskon2 = int(harga * persen / 100)
        harga = harga - diskon2
        diskon_info += f"   🏷 Diskon Promo {persen}%: -Rp {diskon2:,}\n   💰 Harga Akhir: Rp {harga:,}\n"

    order_id, garansi_sampai = simpan_order(user.id, user.username or "", p["nama"], k, harga)
    ORDERS[user.id] = {"paket": p["nama"], "paket_key": k, "harga": harga, "order_id": order_id}

    teks = (
        f"{p['emoji']} {p['nama']}\n\n"
        f"📱 {p['deskripsi']}\n"
        f"⏱ Garansi: {p['garansi']}\n"
        f"💰 Harga Normal: Rp {p['harga']:,}\n"
        f"{diskon_info}\n"
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

async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = get_user(user.id)
    if not data:
        register_user(user.id, user.username or "", user.first_name)
        data = get_user(user.id)
    kode = data[3]
    bot_info = await context.bot.get_me()
    link = f"https://t.me/{bot_info.username}?start={kode}"
    teks = (
        "🔗 Kode Referral Anda:\n\n"
        f"Kode: {kode}\n"
        f"Link: {link}\n\n"
        "Bagikan link ini ke teman!\n\n"
        "Keuntungan:\n"
        "✅ Teman yang daftar via link Anda dapat diskon 2.5%\n"
        "✅ Anda dapat diskon 2.5% setelah teman berhasil order\n\n"
        "Diskon otomatis aktif saat order berikutnya!"
    )
    await update.message.reply_text(teks)

async def lucky(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_blacklist(user.id):
        await update.message.reply_text("❌ Akun Anda telah diblokir.")
        return
    if not punya_order_selesai(user.id):
        await update.message.reply_text(
            "❌ Lucky Draw hanya untuk customer yang sudah pernah order!\n\n"
            "Lakukan order dulu dengan /beli1, /beli2, atau /beli3")
        return
    tiket = get_tiket_lucky(user.id)
    if not tiket:
        await update.message.reply_text(
            "❌ Anda tidak punya tiket Lucky Draw!\n\n"
            "Tiket didapat setiap kali order berhasil dikonfirmasi admin.")
        return
    await update.message.reply_text(
        "🎰 Tiket Lucky Draw Anda:\n\n" +
        "\n".join([f"🎫 {t}" for t in tiket]) +
        "\n\nKetik kode tiket untuk spin!\nContoh: /spin LCKXXXXXXX")

async def spin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.args:
        await update.message.reply_text("Cara pakai: /spin KODE_TIKET")
        return
    kode = context.args[0].upper()
    if not pakai_tiket_lucky(kode):
        await update.message.reply_text("❌ Kode tiket tidak valid atau sudah dipakai!")
        return

    rand = random.uniform(0, 100)
    if rand <= 0.5:
        hadiah = "paket3"
        teks_hadiah = "👑 JACKPOT! Free Paket 3 - WA Badak Api Verif Include FBM Garansi 5 Bulan!"
    elif rand <= 2.5:
        hadiah = "paket2"
        teks_hadiah = "💎 MENANG! Free Paket 2 - WA Badak Verif Garansi 3 Bulan!"
    elif rand <= 7.5:
        hadiah = "paket1"
        teks_hadiah = "🔥 MENANG! Free Paket 1 - WA Badak Garansi 7 Hari!"
    else:
        hadiah = "kalah"
        teks_hadiah = "😢 Belum beruntung kali ini. Coba lagi di order berikutnya!"

    if hadiah != "kalah":
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "🎰 LUCKY DRAW MENANG!\n\n"
                f"👤 {user.first_name} (@{user.username})\n"
                f"🆔 ID: {user.id}\n"
                f"🎁 Hadiah: {teks_hadiah}\n"
                f"🎫 Tiket: {kode}\n\n"
                "Segera kirim hadiah ke customer!\n"
                f"/kirim {user.id} NOMOR_WA_BADAK"
            ))
        await update.message.reply_text(
            f"🎉 SELAMAT!\n\n{teks_hadiah}\n\n"
            "Admin akan segera mengirimkan nomor hadiah Anda!\n"
            "Terima kasih telah bermain Lucky Draw! 🙏")
    else:
        await update.message.reply_text(
            f"🎰 Hasil Spin:\n\n{teks_hadiah}\n\n"
            "Semangat! Tiket baru akan didapat di order berikutnya.")

async def claim_garansi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_blacklist(user.id):
        await update.message.reply_text("❌ Akun Anda telah diblokir.")
        return
    orders_aktif = get_order_aktif(user.id)
    if not orders_aktif:
        await update.message.reply_text(
            "❌ Tidak ada order aktif dengan garansi yang masih berlaku.\n\n"
            "Pastikan order Anda sudah dikonfirmasi admin dan garansi belum habis.")
        return
    teks = "✅ Order aktif dengan garansi berlaku:\n\n"
    for o in orders_aktif:
        teks += (
            f"📦 {o[2]}\n"
            f"🔖 Order ID: #{o[0]}\n"
            f"⏱ Garansi sampai: {o[7]}\n\n"
        )
    teks += "Kirim FOTO screenshot WA yang bermasalah sekarang!\n\nAdmin akan memproses klaim Anda."
    WAITING_CLAIM[user.id] = True
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
            f"   ⏱ Garansi: {o[4]}\n"
            f"   🕐 {o[5]}\n\n"
        )
    await update.message.reply_text(teks)

async def promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teks = "🎁 Kode Promo Aktif:\n\n"
    for kode, persen in KODE_PROMO.items():
        teks += f"🏷 {kode} - Diskon {persen}%\n"
    teks += "\nCara pakai: /beli1 KODEPROMO\nContoh: /beli1 BADAK10"
    await update.message.reply_text(teks)

async def rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.args:
        await update.message.reply_text(
            "Beri rating untuk kami!\n\n"
            "Cara pakai:\n"
            "/rating [1-5] [KOMENTAR]\n\n"
            "Contoh:\n"
            "/rating 5 Pelayanan cepat!")
        return
    bintang = context.args[0]
    komentar = " ".join(context.args[1:]) if len(context.args) > 1 else "Tidak ada komentar"
    bintang_emoji = "⭐" * int(bintang) if bintang.isdigit() and 1 <= int(bintang) <= 5 else "⭐"
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "⭐ RATING MASUK!\n\n"
            f"👤 {user.first_name} (@{user.username})\n"
            f"🆔 ID: {user.id}\n"
            f"Rating: {bintang_emoji} ({bintang}/5)\n"
            f"Komentar: {komentar}"
        ))
    await update.message.reply_text(f"Terima kasih atas rating Anda {bintang_emoji}")

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
        await update.message.reply_text("❌ Bukan admin!")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Cara pakai:\n/kirim [ID_USER] [NOMOR_WA]")
        return
    user_id = context.args[0]
    nomor_wa = context.args[1]
    try:
        await context.bot.send_message(
            chat_id=int(user_id),
            text=(
                "✅ Pembayaran Dikonfirmasi!\n\n"
                f"📱 Nomor WA Badak Anda: {nomor_wa}\n\n"
                "Silakan login WA menggunakan nomor di atas.\n"
                "Jika butuh kode OTP ketik /minta_otp\n"
                "Jika WA bermasalah ketik /claim_garansi\n\n"
                "Terima kasih! 🙏"
            ))
        await update.message.reply_text(f"✅ Nomor berhasil dikirim ke user {user_id}!")

        conn = sqlite3.connect("wabot.db")
        c = conn.cursor()
        c.execute("SELECT id FROM orders WHERE user_id=? AND status='pending' ORDER BY waktu DESC LIMIT 1",
                  (int(user_id),))
        order = c.fetchone()
        if order:
            c.execute("UPDATE orders SET status='selesai' WHERE id=?", (order[0],))
            conn.commit()
        conn.close()

        tiket = buat_tiket_lucky(int(user_id))
        await context.bot.send_message(
            chat_id=int(user_id),
            text=(
                "🎫 Anda mendapat tiket Lucky Draw!\n\n"
                f"Kode Tiket: {tiket}\n\n"
                "Ketik /lucky untuk lihat tiket dan /spin untuk spin!\n"
                "Siapa tahu menang hadiah gratis! 🎰"
            ))

        data_user = get_user(int(user_id))
        if data_user and data_user[4]:
            referrer_id = data_user[4]
            set_diskon_referral(referrer_id, 2.5)
            set_diskon_referral(int(user_id), 0)
            await context.bot.send_message(
                chat_id=referrer_id,
                text=(
                    "🎉 Teman Anda berhasil order!\n\n"
                    "Anda mendapat diskon 2.5% untuk order berikutnya!\n"
                    "Diskon otomatis aktif saat Anda order lagi."
                ))
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal kirim! Error: {e}")

async def kirim_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Bukan admin!")
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
        await update.message.reply_text(f"❌ Gagal kirim OTP! Error: {e}")

async def statistik(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Bukan admin!")
        return
    total_user, total_order, total_selesai, total_income, order_hari_ini, income_hari_ini = get_statistik()
    teks = (
        "📊 STATISTIK BOT\n\n"
        f"👥 Total Customer: {total_user}\n"
        f"🛒 Total Order: {total_order}\n"
        f"✅ Order Selesai: {total_selesai}\n"
        f"💰 Total Pemasukan: Rp {total_income:,}\n\n"
        "━━━━━━━━━━━━━━━\n"
        "📅 Hari Ini:\n"
        f"🛒 Order: {order_hari_ini}\n"
        f"💰 Pemasukan: Rp {income_hari_ini:,}"
    )
    await update.message.reply_text(teks)

async def daftar_customer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Bukan admin!")
        return
    users = get_semua_user()
    if not users:
        await update.message.reply_text("Belum ada customer.")
        return
    teks = f"👥 Daftar Customer ({len(users)}):\n\n"
    for u in users:
        teks += f"🆔 {u[0]} | @{u[1]} | {u[2]}\n"
    await update.message.reply_text(teks)

async def blacklist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Bukan admin!")
        return
    if not context.args:
        await update.message.reply_text("Cara pakai:\n/blacklist [ID_USER]")
        return
    user_id = int(context.args[0])
    tambah_blacklist(user_id)
    await update.message.reply_text(f"✅ User {user_id} berhasil diblokir!")

async def unblacklist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Bukan admin!")
        return
    if not context.args:
        await update.message.reply_text("Cara pakai:\n/unblacklist [ID_USER]")
        return
    user_id = int(context.args[0])
    hapus_blacklist(user_id)
    await update.message.reply_text(f"✅ User {user_id} berhasil dibuka blokirnya!")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Bukan admin!")
        return
    if not context.args:
        await update.message.reply_text("Cara pakai:\n/broadcast PESAN")
        return
    pesan = " ".join(context.args)
    users = get_semua_user()
    berhasil = 0
    gagal = 0
    for u in users:
        try:
            await context.bot.send_message(
                chat_id=u[0],
                text=f"📢 INFO DARI ADMIN:\n\n{pesan}")
            berhasil += 1
        except:
            gagal += 1
    await update.message.reply_text(
        f"✅ Broadcast selesai!\nBerhasil: {berhasil}\nGagal: {gagal}")

async def terima_foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_blacklist(user.id):
        await update.message.reply_text("❌ Akun Anda telah diblokir.")
        return

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
                "Segera proses dan kirim nomor pengganti!\n"
                f"/kirim {user.id} NOMOR_WA_BARU"
            ))
        await update.message.reply_text(
            "✅ Klaim garansi terkirim ke admin!\n\n"
            "⏳ Admin akan segera memproses dan mengirim nomor pengganti.\n"
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
        "⏳ Tunggu konfirmasi dari admin.\n"
        "Terima kasih! 🙏")
    del ORDERS[user.id]

async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_blacklist(user.id):
        return
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
            "Halo! Ketik /start untuk melihat menu.\n\n"
            f"Atau hubungi admin: @{ADMIN_USERNAME}")

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("beli1", beli))
    app.add_handler(CommandHandler("beli2", beli))
    app.add_handler(CommandHandler("beli3", beli))
    app.add_handler(CommandHandler("referral", referral))
    app.add_handler(CommandHandler("lucky", lucky))
    app.add_handler(CommandHandler("spin", spin))
    app.add_handler(CommandHandler("claim_garansi", claim_garansi))
    app.add_handler(CommandHandler("cek_order", cek_order))
    app.add_handler(CommandHandler("promo", promo))
    app.add_handler(CommandHandler("rating", rating))
    app.add_handler(CommandHandler("minta_otp", minta_otp))
    app.add_handler(CommandHandler("kirim", kirim))
    app.add_handler(CommandHandler("kirim_otp", kirim_otp))
    app.add_handler(CommandHandler("statistik", statistik))
    app.add_handler(CommandHandler("daftar_customer", daftar_customer))
    app.add_handler(CommandHandler("blacklist", blacklist_cmd))
    app.add_handler(CommandHandler("unblacklist", unblacklist_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.PHOTO, terima_foto))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))
    print("✅ Bot WA Badak Store sedang berjalan...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
