import os
import json
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")  # tu token de Telegram
PORT = int(os.getenv("PORT", 8080))

# --- Leer admins desde variable de entorno ---
# Poner en el hosting: 123456789,987654321,...
admin_ids_env = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x) for x in admin_ids_env.split(",") if x.strip()]

# Archivo local para guardar puntos
DATA_FILE = "puntos.json"

# Cargar o inicializar puntos
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        puntos = json.load(f)
else:
    puntos = {"gryffindor": 0, "slytherin": 0, "ravenclaw": 0, "hufflepuff": 0}

def guardar_puntos():
    with open(DATA_FILE, "w") as f:
        json.dump(puntos, f, indent=2)

# --- Helper para verificar admins ---
async def es_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Devuelve True si el usuario es admin del chat o está en la lista de ADMIN_IDS"""
    user_id = update.effective_user.id

    # Verificar lista blanca
    if user_id in ADMIN_IDS:
        return True

    # Verificar admins del grupo
    chat = update.effective_chat
    if chat.type in ["group", "supergroup"]:
        admins = await context.bot.get_chat_administrators(chat.id)
        admin_ids = [a.user.id for a in admins]
        return user_id in admin_ids

    return False

# --- Comandos ---
# /sumar <cantidad> <casa>
async def sumar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await es_admin(update, context):
        await update.message.reply_text("❌ Solo los administradores pueden usar este comando.")
        return

    try:
        cantidad = int(context.args[0])
        casa = context.args[1].lower()

        if casa not in puntos:
            await update.message.reply_text("❌ Casa no válida. Usa gryffindor, slytherin, ravenclaw o hufflepuff.")
            return

        puntos[casa] += cantidad
        guardar_puntos()
        await update.message.reply_text(
            f"✅ Se sumaron {cantidad} puntos a {casa.capitalize()}.\n"
            f"Total: {puntos[casa]}"
        )
    except (IndexError, ValueError):
        await update.message.reply_text("Uso correcto: /sumar <cantidad> <casa>")

# /restar <cantidad> <casa>
async def restar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await es_admin(update, context):
        await update.message.reply_text("❌ Solo los administradores pueden usar este comando.")
        return

    try:
        cantidad = int(context.args[0])
        casa = context.args[1].lower()

        if casa not in puntos:
            await update.message.reply_text("❌ Casa no válida. Usa gryffindor, slytherin, ravenclaw o hufflepuff.")
            return

        puntos[casa] -= cantidad
        guardar_puntos()
        await update.message.reply_text(
            f"✅ Se restaron {cantidad} puntos a {casa.capitalize()}.\n"
            f"Total: {puntos[casa]}"
        )
    except (IndexError, ValueError):
        await update.message.reply_text("Uso correcto: /restar <cantidad> <casa>")

# /puntos → todos pueden ver
async def puntos_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ranking = "\n".join([f"{c.capitalize()}: {p}" for c, p in puntos.items()])
    await update.message.reply_text(f"🏆 Puntos actuales:\n{ranking}")

# --- Telegram + Flask ---
app = Flask(__name__)
telegram_app = Application.builder().token(TOKEN).build()

telegram_app.add_handler(CommandHandler("sumar", sumar))
telegram_app.add_handler(CommandHandler("restar", restar))
telegram_app.add_handler(CommandHandler("puntos", puntos_cmd))

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put_nowait(update)
    return "ok"

@app.route("/")
def index():
    return "Bot de puntos Harry Potter corriendo!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
