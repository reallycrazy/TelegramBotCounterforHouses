import os
import json
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")  # en Railway/Render se pone como variable de entorno
PORT = int(os.getenv("PORT", 8080))

# Archivo local donde se guardan puntos
DATA_FILE = "puntos.json"

# Inicializar datos
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        puntos = json.load(f)
else:
    puntos = {"gryffindor": 0, "slytherin": 0, "ravenclaw": 0, "hufflepuff": 0}

def guardar_puntos():
    with open(DATA_FILE, "w") as f:
        json.dump(puntos, f, indent=2)

# Comando: /añadir <cantidad> <casa>
async def añadir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        cantidad = int(context.args[0])
        casa = context.args[1].lower()

        if casa not in puntos:
            await update.message.reply_text("❌ Casa no válida. Usa gryffindor, slytherin, ravenclaw o hufflepuff.")
            return

        puntos[casa] += cantidad
        guardar_puntos()
        await update.message.reply_text(f"✅ Se añadieron {cantidad} puntos a {casa.capitalize()}.\nTotal: {puntos[casa]}")
    except (IndexError, ValueError):
        await update.message.reply_text("Uso correcto: /añadir <cantidad> <casa>")

# Comando: /puntos
async def puntos_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ranking = "\n".join([f"{c.capitalize()}: {p}" for c, p in puntos.items()])
    await update.message.reply_text(f"🏆 Puntos actuales:\n{ranking}")

# Flask app para webhook
app = Flask(__name__)
telegram_app = Application.builder().token(TOKEN).build()
telegram_app.add_handler(CommandHandler("añadir", añadir))
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
