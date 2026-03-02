from __future__ import annotations

import os
from typing import Iterable

import httpx
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,

)

def _get_env(name: str, *, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or not value.strip():
        raise RuntimeError(f"Missing environment variable: {name}")
    return value.strip()


def _parse_admin_ids(raw: str | None) -> set[int]:
    if not raw:
        return set()
    ids: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.add(int(part))
        except ValueError:
            raise RuntimeError(
                "TELEGRAM_ADMIN_IDS must be comma-separated integers. "
                f"Bad value: {part!r}"
            )
    return ids

# ==================== TELEGRAM COMMAND HANDLERS ====================
# /start, /help, and other basic commands

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi! I’m marCram, your best friend :D.\n\n"
        "Just send me a message and I’ll forward it to Claude, or I can make flashcards for you!\n"
        "Type /help to see commands."
    )
    
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Commands:\n"
        "  /start - Welcome message\n"
        "  /help - Show this help\n"
        "  /newCard - schedule a new flashcard\n"
        "  /viewCards - view flashcards\n"
        "  /dropCard - drop a card\n"
    )

async def send_card(context: ContextTypes.DEFAULT_TYPE):
    # This is the callback function that gets executed
    job = context.job
    await context.bot.send_message(chat_id=job.chat_id, text="Reminder!")

    
async def view_cards(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        context.job_queue.jobs()
    )
    """"""
    
async def drop_card(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.job_queue.get_jobs_by_name("")[0].schedule_removal()

    """"""  
    
## Message handler

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # if not update.message or not update.message.text:
    #     return

    # api_url: str = context.bot_data["API_URL"]
    # user_text = update.message.text.strip()

    # if not user_text:
    #     await update.message.reply_text("Send some text and I’ll ask Claude.")
    #     return

    # await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    # try:
    #     answer = await _call_rag_chat(api_url, user_text)
    #     await update.message.reply_text(answer)
    # except httpx.ConnectError:
    #     await update.message.reply_text(
    #         "I can’t reach Claude's API.\n"
    #         "Make sure your backend is running (Uvicorn/FastAPI), usually at http://localhost:8000."
    #     )
    # except httpx.HTTPStatusError as e:
    #     await update.message.reply_text(f"API error: {e.response.status_code} {e.response.text}")
    # except Exception as e:
    #     await update.message.reply_text(f"Error: {e}")
    await update.message.reply_text("hi!")
    

# ==================== TELEGRAM STATE HANDLERS ====================
# new_card states
# Define states as constants
CONTENT, ANSWER, FREQUENCY = range(3)
async def new_card_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Yay!", callback_data="yes"), 
         InlineKeyboardButton("Nay!", callback_data="no")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(f"Alright, let's make a new flashcard :3", 
                                    reply_markup=reply_markup)
    return CONTENT

# Button click handler
async def new_card_button(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "yes":
        await query.message.reply_text(text="You said yay! :D")
        await query.message.reply_text(text="What is the question?")
        return ANSWER
    elif query.data == "no":
        await query.message.reply_text(text="You said nay! D: Goodbye!")
        return ConversationHandler.END
    else:
        await query.message.reply_text(text="Unknown option selected.")
        return ConversationHandler.END
    
async def new_card_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    card_content = update.message.text
    context.user_data['content'] = card_content
    await update.message.reply_text(f"""
<b>Ok, so the question will be: </b>
{card_content}
===========================================
what will the answer be? 
    """)
    
    return FREQUENCY

async def new_card_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    card_answer = update.message.text
    card_content = context.user_data['content']
    
    keyboard = [
        [InlineKeyboardButton("Daily", callback_data="option1")],
        [InlineKeyboardButton("Hourly", callback_data="option2")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"""
So, the question will be: 
{card_content} 
and the answer will be: 
{card_answer}
How often should I send this card to you?
        """,
        reply_markup=reply_markup,
        # parse_mode=<e.ParseMode.HTML
        )
    
    return ConversationHandler.END

# Button click handler
async def frequency_button(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "daily":
        await query.message.reply_text(text="What is the question?")
        return ANSWER
    elif query.data == "hourly":
        await query.message.reply_text(text="You said nay! D: Goodbye!")
        return ConversationHandler.END
    else:
        await query.message.reply_text(text="Unknown option selected.")
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Command cancelled!")
    return ConversationHandler.END
# ==================== API COMMUNICATION ====================
# Call the backend

async def _call_claude(api_url: str, message: str) -> str:
    """
    Calls the FastAPI endpoint implemented in `api.py`:
      POST /chat
      body: {"message": "..."}
      response: {"response": "..."}
    """
    timeout = httpx.Timeout(60.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(f"{api_url}/chat", json={"message": message})
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict) or "response" not in data:
            raise RuntimeError("Unexpected API response format (expected JSON with 'response').")
        return str(data["response"])
    

# ==================== BOT INITIALIZATION & MAIN ====================
# Sets up the bot, registers all handlers, and starts polling

def main() -> None:
    load_dotenv()

    token = _get_env("TELEGRAM_BOT_TOKEN")
    # api_url = os.getenv("API_BASE_URL", "http://localhost:8080").strip()
    admin_ids = _parse_admin_ids(os.getenv("TELEGRAM_ADMIN_IDS"))

    app = Application.builder().token(token).build()

    # app.bot_data["API_BASE_URL"] = api_url
    app.bot_data["TELEGRAM_ADMIN_IDS"] = admin_ids

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(ConversationHandler(
        entry_points= [CommandHandler("newCard", new_card_start)],
        states={
            CONTENT: [CallbackQueryHandler(new_card_button)],
            ANSWER: [MessageHandler(filters.TEXT & ~filters.COMMAND, new_card_answer)],
            FREQUENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, new_card_frequency)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
        ))
    app.add_handler(CommandHandler("viewCards", view_cards))
    # app.add_handler(CommandHandler("dropCard", dropCard))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    # print(f"Using API: {api_url}")
    if admin_ids:
        print(f"Admin IDs enabled: {sorted(admin_ids)}")
    app.run_polling(close_loop=False)


if __name__ == "__main__":
    main()

