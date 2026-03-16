from __future__ import annotations

import os
from typing import Iterable
import re

#database_model.py
import database_model 

import httpx
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.constants import (
    ChatAction,
    ParseMode
)
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,

)


import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
import asyncio

import html
import datetime

# Load environment variables from .env file
load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN").strip()
TELE_RENDER_URL = os.environ.get("TELE_RENDER_URL") or None
TELE_PORT = os.environ.get("TELE_PORT") or 0

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

def is_alphanumeric(text):
    return any(i.isdigit() for i in text)


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
        "  /help - Show this help message\n"
        "  /newCard - schedule a new flashcard\n"
        "  /viewCards - view flashcards\n"
        "  /dropCard - drop a card\n"
    )
    
async def post_init(application):
    await _load_flashcards(application)
    
async def _load_flashcards(app: Application):
    try:
        rows = database_model.select_all_flashcards() or []
        for chat_id, job_name, text, interval in rows:
            app.job_queue.run_repeating(
                card_job,
                interval=int(interval),
                chat_id=chat_id,
                name=job_name,
                data=text
            )
        print(f"Loaded {len(rows)} flashcard(s) from DB.")
    except Exception as e:
        print(f"DB error — cards not loaded: {e}")
    
# ==================== MESSAGING CLAUDE ====================

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    api_url: str = API_BASE_URL
    user_text = update.message.text.strip()

    if not user_text:
        await update.message.reply_text("Send some text and I’ll ask Claude.")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    try:
        answer = await _call_claude(api_url, user_text)
        await update.message.reply_text(answer)
    except httpx.ConnectError:
        await update.message.reply_text(
            "I can’t reach Claude's API.\n"
            "Make sure your backend is running."
        )
    except httpx.HTTPStatusError as e:
        await update.message.reply_text(f"API error: {e.response.status_code} {e.response.text}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    

# ==================== TELEGRAM STATE HANDLERS ====================
# new_card states
# Define states as constants
keyboard = [[
    InlineKeyboardButton("Yay!", callback_data="yes"), 
    InlineKeyboardButton("Nay!", callback_data="no")
],]
reply_markup = InlineKeyboardMarkup(keyboard)
QUESTION, CONTENT, FREQUENCY, CONFIRM, CONFIRM_BTN = range(5)

async def new_card_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: 
    context.user_data["is_invalid"] = False;   
    await update.message.reply_text(f"Alright, let's make a new flashcard :3", 
                                    reply_markup=reply_markup)
    context.user_data["previous_state"] = "STARTCARD"
    return CONFIRM_BTN

#QUESTION
async def new_card_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: 
    card_name = update.message.text
    
    if any(job.name == card_name for job in context.job_queue.jobs()):
        await update.message.reply_text(
            text=f"Oh dear, looks like '{html.escape(card_name)}' already exists! Please give me another name!", parse_mode="HTML"
        )
        return QUESTION
    
    context.user_data["card_name"] = html.escape(card_name)    
    await update.message.reply_text(text="What is the question?")
    
    context.user_data["previous_state"] = "QUESTION"
    return CONTENT

#CONTENT
async def new_card_answer(update: Update, context: ContextTypes.DEFAULT_TYPE): 

    card_content = update.message.text
    context.user_data['content'] = html.escape(card_content)
    card_name = context.user_data["card_name"]    
    
    text = f"<b>Ok, so the card's name is: </b>\n<code>" + card_name + "</code>\n<b>The question will be: </b>\n<code>" + card_content + "</code>\n" + ("_" * 25)  + "\n<b>What will the answer be?</b>"
    await update.message.reply_text(text, parse_mode='HTML')
    
    context.user_data["previous_state"] = "CONTENT"
    
    return FREQUENCY

#FREQUENCY
async def new_card_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    card_answer = update.message.text
    context.user_data['answer'] = html.escape(card_answer)
    card_content = context.user_data['content']
    card_name = context.user_data["card_name"]    
    
    await update.message.reply_text(f"<b>Ok, so the card's name is: </b>\n<code>" + card_name + "</code>\n<b>The question will be: </b>\n<code>" + card_content + "</code>"
                                    + "\n<b>and the answer will be: </b>\n<code>" + card_answer + "</code>\n" + ("_" * 25)  
                                    + "\n<b><i>How often should I send this card to you? In terms of hours, seconds etc.</i></b>"
                                    ,parse_mode='HTML')
    context.user_data["previous_state"] = "FREQUENCY"
    
    return CONFIRM

#CONFIRM
async def new_card_confirm(update: Update, context: CallbackContext) -> int:
    card_answer = context.user_data['answer']
    card_content = context.user_data['content']
    card_frequency_text = update.message.text.lower().strip()
    card_name = context.user_data["card_name"]    
    
    # extract timing
    pattern = r'(\d+\.?\d*)\s*(day?|hour?|minute?|min?|second?|sec?)'
    matches = re.findall(pattern, card_frequency_text)
    
    times = [(float(num), unit.lower()) for num, unit in matches]
    timeLength = 0;
    
    for val, unit in times:
        if unit.startswith("d"):  
            timeLength += val * 86400
        elif unit.startswith("h"):  
            timeLength += val * 3600
        elif unit.startswith("m"):  
            timeLength += val * 60
        else:  
            timeLength += val
                
    if (timeLength > 0):
        timeString = ""
        days = timeLength // 86400
        hours = (timeLength % 86400) // 3600
        minutes = (timeLength % 3600) // 60
        seconds = timeLength % 60
        
        if days: timeString += str(int(days)) + " days, "
        if hours: timeString += str(int(hours)) + " hours, "
        if minutes: timeString += str(int(minutes)) + " minutes, "
        if seconds: timeString += str(int(seconds)) + " seconds, "
        
        timeString = timeString[:-2]
        
        nextTime = (datetime.datetime.now()+ datetime.timedelta(seconds=timeLength)).strftime("%Y-%m-%d, %a, %I:%M:%S%p")
        
        await update.message.reply_text(f"<b>Ok, so the card's name is: </b>\n<code>" + card_name + "</code>\n<b>The question will be: </b>\n<code>" + card_content + "</code>\n" 
                                        + "\n<b>and the answer will be: </b>\n<code>" + card_answer + "</code>\n" + ("_" * 25)  
                                        + f"\nIn terms of hours or days, I will send this card in <code>{timeString}</code>!"
                                        + f"\n\nOr, at approximately at <code>{nextTime}</code>!"
                                        + "\n\n<b>Is this correct?</b>",parse_mode='HTML',reply_markup=reply_markup
        )
        context.user_data['intervals'] = timeLength;
        context.user_data["previous_state"] = "CONFIRM"
        
        return CONFIRM_BTN
        
    else:
        context.user_data["is_invalid"] = True;
        await update.message.reply_text(f"Whoops! Looks like you made an invalid input, do you still want to continue?"
                                        ,parse_mode='HTML',reply_markup=reply_markup)
        return CONFIRM_BTN
        
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Command cancelled!")
    return ConversationHandler.END


# ==================== BUTTON HANDLERS ====================
# Button click handler
#CONFIRM_BTN
async def confirm_button(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    
    previous_state = context.user_data["previous_state"] 
    await query.answer()

    if query.data == "yes":
        ##invalid input found
        if (context.user_data["is_invalid"]):
            context.user_data["is_invalid"] = False;
            await query.message.reply_text(text="Ok, let's try again!")
            match previous_state:
                case "FREQUENCY":
                    card_name = context.user_data["card_name"]    
                    card_answer = context.user_data['answer'] 
                    card_content = context.user_data['content']
                    await query.message.reply_text(
                        f"<b>Ok, so the card's name is: </b>\n<code>" + card_name + "</code>\n<b>The question will be: </b>\n<code>" + card_content + "</code>"  
                        + "\n<b>and the answer will be: </b>\n<code>" + card_answer + "</code>\n" + ("_" * 25)  
                        + "\n<b><i>In terms of hours or days, How often should I send this card to you?</i></b>"
                        ,parse_mode='HTML')
                    context.user_data["previous_state"] = "FREQUENCY"
                    
                    return CONFIRM
        else:
            match previous_state:
                case "STARTCARD":
                    await query.message.reply_text(f"What will you call this card? :D", parse_mode='HTML')
                    return QUESTION
                    
                case "CONFIRM":
                    card_repeat = context.user_data['intervals']    
                    card_name = context.user_data["card_name"]    
                    card_answer = context.user_data['answer'] 
                    card_content = context.user_data['content']

                    chat_id = update.effective_chat.id
                    user_id = update.effective_user.id  
                    
                    content = f"<b><u>{card_name}</u></b>\n\n<b>Question:</b>\n<code>" + card_content + "</code>\n" + ("_" * 25) + "\n<b>Answer:</b>\n<span class='tg-spoiler'><b>" + card_answer + "</b></span>"
                                
                    await query.message.reply_text(text="Alright, card created!! Here is a preview of your new card!")
                    await query.message.reply_text(text=content, parse_mode= "HTML")
                    
                    database_model.insert_flashcard(chat_id, card_name, content, float(card_repeat));
                    
                    flashcard_data = database_model.select_flashcard(chat_id, card_name);
                    
                    context.job_queue.run_repeating(
                        card_job,
                        interval=float(flashcard_data[3]),        # seconds
                        name=flashcard_data[1],
                        chat_id=chat_id,
                        user_id=user_id,
                        data=flashcard_data[2]
                    )
                    return ConversationHandler.END
                    
                    
    else:
        await query.message.reply_text("You said nay D: Command cancelled!")
        return ConversationHandler.END
    


# ==================== CRUD CARD ====================
# sets card content to schedule

async def card_job(context: CallbackContext):
    flashcard_data = context.job.data;

    await context.bot.send_message(chat_id=context.job.chat_id, text="DING DING! Time for a recall!!")
    await context.bot.send_message(chat_id=context.job.chat_id, 
                                text=html.escape(flashcard_data)
                                , parse_mode= "HTML")
    

async def view_cards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jobs = context.job_queue.jobs()
    if not jobs:
        await update.message.reply_text("No cards running.")
        return

    lines = []
    for job in jobs:
        next_run = job.next_t  # datetime of next scheduled run
        if next_run:
            next_str = next_run.astimezone().strftime("%Y-%m-%d %H:%M:%S%I:%M:%S %p")
        else:
            next_str = "N/A"
        lines.append(f"• <code>{html.escape(job.name)}</code> | next run: {next_str}")

    await update.message.reply_text("<b> Running cards:</b>\n" + "\n".join(lines), parse_mode = "HTML")
    
    

keyboard = [[
    InlineKeyboardButton("Yes, delete this.", callback_data="yes"), 
    InlineKeyboardButton("Nope!", callback_data="no")
],]
delete_markup = InlineKeyboardMarkup(keyboard)

DELETE_CONFIRM, DELETE_BTN = range(2);
async def drop_card_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Type the name of the card you want to delete.")
    return DELETE_CONFIRM
    
async def drop_card_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    name_ = update.message.text
    name = html.escape(name_)
    
    jobs = context.job_queue.jobs()
    if not jobs:
        await update.message.reply_text("No jobs are currently running. Delete cancelled.")
        return ConversationHandler.END

    if (bool(context.job_queue.get_jobs_by_name(name))):
        context.user_data["card_name"] = html.escape(name)    
        
        await update.message.reply_text(f"Are you sure you want to delete <code>{name}</code>?", parse_mode="HTML", reply_markup = delete_markup)
        return DELETE_BTN
    
    await update.message.reply_text(f"Unable to find <code>{name}</code>. Delete cancelled.", parse_mode="HTML")
    return ConversationHandler.END
    
    
    
async def delete_button(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    
    await query.answer()

    card_name = context.user_data["card_name"]
    if query.data == "yes":
        database_model.delete_flashcard(update.effective_chat.id, html.escape(card_name));
        for job in context.job_queue.get_jobs_by_name(html.escape(card_name)):
            job.schedule_removal()
            
        await query.message.reply_text(f"Deleted <code>{html.escape(card_name)}</code> D:", parse_mode="HTML")
    else:
        await query.message.reply_text("Delete cancelled.")
    
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
    admin_ids = _parse_admin_ids(os.getenv("TELEGRAM_ADMIN_IDS"))

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()
    app.bot_data["API_BASE_URL"] = API_BASE_URL
    app.bot_data["TELEGRAM_ADMIN_IDS"] = admin_ids

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(ConversationHandler(
        entry_points= [CommandHandler("newCard", new_card_start)],
        states={
            QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, new_card_question)],
            CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, new_card_answer)],
            FREQUENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, new_card_frequency)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, new_card_confirm)],
            CONFIRM_BTN: [CallbackQueryHandler(confirm_button)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
        ))
    app.add_handler(CommandHandler("viewCards", view_cards))
    app.add_handler(ConversationHandler(
        entry_points= [CommandHandler("dropCard", drop_card_start)],
        states={
            DELETE_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, drop_card_confirm)],
            DELETE_BTN: [CallbackQueryHandler(delete_button)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
        ))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    if admin_ids:
        print(f"Admin IDs enabled: {sorted(admin_ids)}")

    if TELE_RENDER_URL is not None:
        # Webhook mode (production/Render)
        asyncio.run(deployment(app))
    else:
        # Polling mode (local dev)
        asyncio.run(app.bot.delete_webhook())
        app.run_polling()

    

async def deployment(app: Application):
    # Clear any old polling sessions first
    await app.bot.delete_webhook(drop_pending_updates=True)  # ← add this line
    
    await app.bot.set_webhook(
        url=f"{TELE_RENDER_URL.strip()}/telegram",
        allowed_updates=Update.ALL_TYPES
    )

    async def telegram(request: Request) -> Response:
        await app.update_queue.put(
            Update.de_json(data=await request.json(), bot=app.bot)
        )
        return Response()

    async def health(_: Request) -> PlainTextResponse:
        return PlainTextResponse(content="The bot is still running fine :)")

    starlette_app = Starlette(
        routes=[
            Route("/telegram", telegram, methods=["POST"]),
            Route("/healthcheck", health, methods=["GET"]),
        ]
    )
    
    webserver = uvicorn.Server(
        config=uvicorn.Config(
            app=starlette_app,
            port=int(TELE_PORT),
            host="0.0.0.0",
        )
    )

    async with app:
        await app.start()
        await _load_flashcards(app)
        await webserver.serve()
        await app.stop()

if __name__ == "__main__":
        main()