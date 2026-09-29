import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = 5907200145

WELCOME_MESSAGE = """👋 Welcome!

Goagame ki game uid send kro bro or reply ka wait kro...
"""

message_map = {}


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

    def log_message(self, format, *args):
        pass


def start_health_server():
    port = int(os.environ.get("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE)


async def user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "📩 NEW MESSAGE\n\n"
            f"Name: {user.full_name}\n"
            f"User ID: {user.id}\n"
            f"Username: @{user.username or 'N/A'}"
        ),
    )

    copied = await context.bot.copy_message(
        chat_id=ADMIN_ID,
        from_chat_id=update.effective_chat.id,
        message_id=update.message.message_id,
    )

    message_map[copied.message_id] = update.effective_chat.id


async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return

    if not update.message.reply_to_message:
        return

    original_id = update.message.reply_to_message.message_id
    user_chat_id = message_map.get(original_id)

    if not user_chat_id:
        await update.message.reply_text("⚠️ User mapping nahi mila.")
        return

    await context.bot.copy_message(
        chat_id=user_chat_id,
        from_chat_id=ADMIN_ID,
        message_id=update.message.message_id,
    )


def main():
    Thread(target=start_health_server, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(
            filters.Chat(ADMIN_ID) & filters.REPLY,
            admin_reply,
        )
    )

    app.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & ~filters.COMMAND,
            user_message,
        )
    )

    print("🤖 Bot is running...")
    app.run_polling()


if name == "main":
    main()
