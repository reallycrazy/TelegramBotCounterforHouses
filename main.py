import os
import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- Configuración ---
TOKEN = os.getenv("BOT_TOKEN")  # tu token de Telegram
PORT = int(os.getenv("PORT", 8080))
APP_URL = os.getenv("APP_URL")  # URL pública de tu app en Railway, ej: https://telegrambotcounterforhouses-production.up.railway.app
admin_ids_env = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x) for x in admin_ids_env.split(",") if x.strip()]

CASAS = ["ryutherwing", "kurynpurr", "rowenmaw", "baltopaw"]
DB_FILE = "puntos.db"

# --- Inicializar base de datos ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS casas (
            nombre TEXT PRIMARY KEY,
            puntos INTEGER
        )
    """)
    for casa in CASAS:
        c.execute("INSERT OR IGNORE INTO casas (nombre, puntos) VALUES (?, ?)", (casa, 0))
    conn.commit()
    conn.close()

init_db()

# --- Funciones para manejar puntos ---
def get_puntos():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT nombre, puntos FROM casas")
    data = dict(c.fetchall())
    conn.close()
    return data

def sumar_puntos(casa, cantidad):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE casas SET puntos = puntos + ? WHERE nombre = ?", (cantidad, casa))
    conn.commit()
    conn.close()

def restar_puntos(casa, cantidad):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE casas SET puntos = puntos - ? WHERE nombre = ?", (cantidad, casa))
    conn.commit()
    conn.close()

# --- Verificar admin ---
async def es_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    if user_id in ADMIN_IDS:
        return True
    chat = update.effective_chat
    if chat.type in ["group", "supergroup"]:
        admins = await context.bot.get_chat_administrators(chat.id)
        admin_ids = [a.user.id for a in admins]
        return user_id in admin_ids
    return False

# --- Comandos ---
async def sumar_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await es_admin(update, context):
        await update.message.reply_text("❌ Solo los administradores pueden usar este comando.")
        return
    try:
        cantidad = int(context.args[0])
        casa = context.args[1].lower()
        if casa not in CASAS:
            await update.message.reply_text(f"❌ Casa no válida. Usa: {', '.join(CASAS)}")
            return
        sumar_puntos(casa, cantidad)
        puntos = get_puntos()
        await update.message.reply_text(f"✅ Se sumaron {cantidad} puntos a {casa.capitalize()} (Total: {puntos[casa]})")
    except (IndexError, ValueError):
        await update.message.reply_text("Uso correcto: /sumar <cantidad> <casa>")

async def restar_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await es_admin(update, context):
        await update.message.reply_text("❌ Solo los administradores pueden usar este comando.")
        return
    try:
        cantidad = int(context.args[0])
        casa = context.args[1].lower()
        if casa not in CASAS:
            await update.message.reply_text(f"❌ Casa no válida. Usa: {', '.join(CASAS)}")
            return
        restar_puntos(casa, cantidad)
        puntos = get_puntos()
        await update.message.reply_text(f"✅ Se restaron {cantidad} puntos a {casa.capitalize()} (Total: {puntos[casa]})")
    except (IndexError, ValueError):
        await update.message.reply_text("Uso correcto: /restar <cantidad> <casa>")

async def puntos_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    puntos = get_puntos()
    texto = "\n".join([f"{c.capitalize()}: {p}" for c, p in puntos.items()])
    await update.message.reply_text(f"🏆 Puntos actuales:\n{texto}")

# --- Configurar bot ---
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("sumar", sumar_cmd))
application.add_handler(CommandHandler("restar", restar_cmd))
application.add_handler(CommandHandler("puntos", puntos_cmd))

# --- Ejecutar webhook ---
if __name__ == "__main__":
    print("Bot corriendo...")
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{APP_URL}/{TOKEN}"
    )
