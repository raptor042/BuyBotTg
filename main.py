import os
from dotenv import load_dotenv
import time

from web3 import Web3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters
)

from __db__.db import connect_db, get_chat, set_chat, update_chat, set_comp
from __web3__.web3 import validateAddress
from __api__.api import getTokenVolume

import logging

logging.basicConfig(format="%(asctime)s -%(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MAINNET_API_URL= os.getenv("MAINNET_API_URL")

START, END = range(2)
db = None

web3 = None

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.username)

    try:
        if update.message.chat.type != "private":
            chat_id = update.effective_chat.id
            user_id = update.effective_user.id

            chat_member = await context.bot.get_chat_member(chat_id, user_id)
            user_status = chat_member.status
            print(f"CHAT MEMBER: {user_status}")

            if user_status not in ["administrator", "creator"]:
                reply_msg = "<b>🚨 You do not have Non-Anonymous Admin Rights to the token group chat.</b>"
                await update.message.reply_html(text=reply_msg)

                return ConversationHandler.END

            chat_id = update.message.chat_id

            query = {"chat_id": chat_id}
            existing_token = get_chat(db=db, query=query)

            if existing_token:
                reply_msg = "<b>🚨 A token address is already set for this group.</b>"
                await update.message.reply_html(text=reply_msg)

                return ConversationHandler.END

            keyboard = [
                [InlineKeyboardButton("Click to get started 🚀", callback_data="start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            reply_msg = f"<b>Hello ${user.username} 👋, Welcome to the 0xBuyBot 🤖.</b>\n\n<i>It provides blockchain powered trending insights on any token of your choice on BSC & ETH 🚀.</i>\n\n<b>To get started:</b>\n\n<i>✅ Start by sending your the token address ie: 0x23exb......</i>\n<i>✅ You must have Non-Anonymous Admin Rights in your token's group chat.</i>\n<i>✅ Use the settings command to add an identity (emoji, photo or GIF) to your token group chat.</i>"

            await update.message.reply_html(text=reply_msg, reply_markup=reply_markup)

            return START
        else:
            reply_msg = "<b>🚨 This command is only used in group chats.</b>"
            await update.message.reply_html(text=reply_msg)

            return ConversationHandler.END
    except Exception as e:
        logging.error(f"An error has occurred: {e}")

        reply_msg = "<b>🚨 An error occured while using the bot.</b>"
        await update.message.reply_html(text=reply_msg)

        return ConversationHandler.END

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    try:
        keyboard = [
            [InlineKeyboardButton("Binance Smart Chain", callback_data="bsc")],
            [InlineKeyboardButton("Ethereum", callback_data="eth")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        reply_msg = "<b>🔰 Please select the blockchain of choice.....</b>"
        await query.message.reply_html(text=reply_msg, reply_markup=reply_markup)

        return START
    except Exception as e:
        logging.error(f"An error has occurred: {e}")

        reply_msg = "<b>🚨 An error occured while using the bot.</b>"
        await query.message.reply_html(text=reply_msg)

        return ConversationHandler.END
    
async def chain(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    try:
        context.user_data["chain"] = query.data

        reply_msg = "<b>🔰 Enter your token address ie: 0x1234....</b>"
        await query.message.reply_html(text=reply_msg)

        return START
    except Exception as e:
        logging.error(f"An error has occurred: {e}")

        reply_msg = "<b>🚨 An error occured while using the bot.</b>"
        await query.message.reply_html(text=reply_msg)

        return ConversationHandler.END
    
async def token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info("User %s sent a token address.", user.username)

    try:
        is_valid = validateAddress(update.message.text)
        print(is_valid)

        if is_valid:
            chat_id = update.message.chat_id
            chain = context.user_data["chain"]

            volume = getTokenVolume(token=update.message.text)
            print(volume)

            value = {"chat_id": chat_id, "chain": chain, "token": update.message.text, "volume": volume, "buys": []}
            chat = set_chat(db=db, value=value)
            print(chat)

            keyboard = [
                [InlineKeyboardButton("End Conversation", callback_data="end")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            reply_msg = f"<b>Congratulations {user.username} 🎉, You have successfully added the 0xBuyBot to your token group chat. Get ready for super-powered trending insights 🚀.</b>"

            await update.message.reply_html(text=reply_msg, reply_markup=reply_markup)

            return START
        else:
            reply_msg = "<b>🚨 Token Address is not valid.</b>"
            await update.message.reply_html(text=reply_msg)

            return ConversationHandler.END

    except Exception as e:
        logging.error(f"An error has occurred: {e}")

        reply_msg = "<b>🚨 An error occured while using the bot.</b>"
        await update.message.reply_html(text=reply_msg)

        return ConversationHandler.END
        
async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    await query.message.reply_html("See you soon.")

    return ConversationHandler.END

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    logger.info("User %s has entered the /settings command.", user.username)

    try:
        keyboard = [
            [InlineKeyboardButton("🎭 Add a group Emoji/Photo/GIF", callback_data="identity")],
            [InlineKeyboardButton("🏆 Start a Biggest Buy Comp", callback_data="buy_comp")],
            [InlineKeyboardButton("🏅 Start a Last Buy Comp", callback_data="last_comp")],
            [InlineKeyboardButton("⏬ Set Min Buy", callback_data="min_buy")],
            [InlineKeyboardButton("⏩ Set Buy Step", callback_data="buy_step")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        reply_msg = "<b>🔰 Add an emoji, photo or GIF to identify your token group chat.</b>"
        await update.message.reply_html(text=reply_msg, reply_markup=reply_markup)

    except Exception as e:
        logging.error(f"An error has occurred: {e}")

        reply_msg = "<b>🚨 An error occured while using the bot.</b>"
        await update.message.reply_html(text=reply_msg)

async def identity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        keyboard = [
            [InlineKeyboardButton("Emoji", callback_data="emoji")],
            [InlineKeyboardButton("Photo", callback_data="photo")],
            [InlineKeyboardButton("GIF", callback_data="gif")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        reply_msg = "<b>🔰 Add a group Emoji/Photo/GIF....</b>"

        await query.message.reply_html(text=reply_msg, reply_markup=reply_markup)
    except Exception as e:
        logging.error(f"An error has occurred: {e}")

        reply_msg = "<b>🚨 An error occured while using the bot.</b>"
        await query.message.reply_html(text=reply_msg)

async def _identity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        if query.data == "emoji":
            reply_msg = "<b>🔰 Send an emoji....</b>"
        elif query.data == "photo":
            reply_msg = "<b>🔰 Send a photo....</b>"
        elif query.data == "gif":
            reply_msg = "<b>🔰 Send a GIF....</b>"

        await query.message.reply_html(text=reply_msg)
    except Exception as e:
        logging.error(f"An error has occurred: {e}")

        reply_msg = "<b>🚨 An error occured while using the bot.</b>"
        await query.message.reply_html(text=reply_msg)
    
async def set_emoji(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    logger.info("User %s sent an emoji.", user.username)

    try:
        chat_id = update.message.chat_id
        query = {"chat_id": chat_id}

        chat = get_chat(db=db, query=query)
        print(chat)

        value = {"$set": {"emoji": update.message.text}}
        chat = update_chat(db=db, query=query, value=value)
        print(chat)

        reply_msg = f"<b>Congratulations {user.username} 🎉, You have successfully added an emoji to identify your token group chat. Get ready for super-powered trending insights 🚀.</b>"

        await update.message.reply_html(text=reply_msg)

    except Exception as e:
        logging.error(f"An error has occurred: {e}")

        reply_msg = "<b>🚨 An error occured while using the bot.</b>"
        await update.message.reply_html(text=reply_msg)

async def set_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    logger.info("User %s sent an photo.", user.username)

    try:
        chat_id = update.message.chat_id
        query = {"chat_id": chat_id}

        chat = get_chat(db=db, query=query)
        print(chat)

        if "gif" in chat:
            reply_msg = "<b>🚨 This token group chat already has an GIF.</b>"
            await update.message.reply_html(text=reply_msg)
        else:
            file = await update.message.effective_attachment[-1].get_file()
            print(file)

            value = {"$set": {"photo": file["file_id"]}}
            chat = update_chat(db=db, query=query, value=value)
            print(chat)

            reply_msg = f"<b>Congratulations {user.username} 🎉, You have successfully added a photo to identify your token group chat. Get ready for super-powered trending insights 🚀.</b>"

            await update.message.reply_html(text=reply_msg)

    except Exception as e:
        logging.error(f"An error has occurred: {e}")

        reply_msg = "<b>🚨 An error occured while using the bot.</b>"
        await update.message.reply_html(text=reply_msg)
    
async def set_gif(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    logger.info("User %s sent an GIF.", user.username)

    try:
        chat_id = update.message.chat_id
        query = {"chat_id": chat_id}

        chat = get_chat(db=db, query=query)
        print(chat)

        if "photo" in chat:
            reply_msg = "<b>🚨 This token group chat already has an photo.</b>"
            await update.message.reply_html(text=reply_msg)
        else:
            file = await update.message.effective_attachment.get_file()
            print(file)

            value = {"$set": {"gif": file["file_id"]}}
            chat = update_chat(db=db, query=query, value=value)
            print(chat)

            reply_msg = f"<b>Congratulations {user.username} 🎉, You have successfully added a GIF to identify your token group chat. Get ready for super-powered trending insights 🚀.</b>"

            await update.message.reply_html(text=reply_msg)

    except Exception as e:
        logging.error(f"An error has occurred: {e}")

        reply_msg = "<b>🚨 An error occured while using the bot.</b>"
        await update.message.reply_html(text=reply_msg)

async def buy_comp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        keyboard = [
            [InlineKeyboardButton("⏳ Comp duration (24 hours)", callback_data="comp_duartion")],
            [InlineKeyboardButton("🥇 1st Prize (1 BNB)", callback_data="1st_prize")],
            [InlineKeyboardButton("🥈 2nd Prize (Not Set)", callback_data="2nd_prize")],
            [InlineKeyboardButton("🥉 3rd Prize (Not Set)", callback_data="3rd_prize")],
            [InlineKeyboardButton("💼 Must Hold (Not Set)", callback_data="must_hold")],
            [InlineKeyboardButton("💰 Minimum Buy", callback_data="min_buy")],
            [InlineKeyboardButton("🏆 Start Biggest Buy Comp", callback_data="start_biggest_buy_comp")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        reply_msg = "<b>🔰 Set up your Biggest Buy Competiton.</b>"
        await query.message.reply_html(text=reply_msg, reply_markup=reply_markup)
    except Exception as e:
        logging.error(f"An error has occurred: {e}")

        reply_msg = "<b>🚨 An error occured while using the bot.</b>"
        await query.message.reply_html(text=reply_msg)

async def last_comp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        keyboard = [
            [InlineKeyboardButton("⏳ Countdown (5 minutes)", callback_data="comp_duartion")],
            [InlineKeyboardButton("🥇 1st Prize (1 BNB)", callback_data="1st_prize")],
            [InlineKeyboardButton("💼 Must Hold (Not Set)", callback_data="must_hold")],
            [InlineKeyboardButton("💰 Minimum Buy", callback_data="min_buy")],
            [InlineKeyboardButton("🏆 Start Biggest Buy Comp", callback_data="start_last_buy_comp")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        reply_msg = "<b>🔰 Set up your Last Buy Competiton.</b>"
        await query.message.reply_html(text=reply_msg, reply_markup=reply_markup)
    except Exception as e:
        logging.error(f"An error has occurred: {e}")

        reply_msg = "<b>🚨 An error occured while using the bot.</b>"
        await query.message.reply_html(text=reply_msg)

async def comp_duration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    try:
        reply_msg = "<b>🔰 Enter your competiton's duration in hours ie: duration: 24</b>"
        await query.message.reply_html(text=reply_msg)
    except Exception as e:
        logging.error(f"An error has occurred: {e}")

        reply_msg = "<b>🚨 An error occured while using the bot.</b>"
        await query.message.reply_html(text=reply_msg)

async def comp__duration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info("User %s set a comp duration.", user.username)

    try:
        context.user_data["comp_duration"] = update.message.text.split(" ", 1)[0]
        print(update.message.text, context.user_data["comp_duration"])

        reply_msg = f"<b>🔰 You have successfully set your competiton's duration to <i>${update.message.text}</i>.</b>"
        await update.message.reply_html(text=reply_msg)
    except Exception as e:
        logging.error(f"An error has occurred: {e}")

        reply_msg = "<b>🚨 An error occured while using the bot.</b>"
        await update.message.reply_html(text=reply_msg)

async def first_prize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    try:
        reply_msg = "<b>🔰 Enter your competiton's first prize in BNB ie: 1st: 0.05</b>"
        await query.message.reply_html(text=reply_msg)
    except Exception as e:
        logging.error(f"An error has occurred: {e}")

        reply_msg = "<b>🚨 An error occured while using the bot.</b>"
        await query.message.reply_html(text=reply_msg)

async def first__prize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info("User %s set a 1st prize for comp.", user.username)

    try:
        context.user_data["first_prize"] = update.message.text.split(" ", 1)[0]
        print(update.message.text, context.user_data["first_prize"])

        reply_msg = f"<b>🔰 You have successfully set the first prize for your competiton to be <i>${update.message.text}</i>.</b>"
        await update.message.reply_html(text=reply_msg)
    except Exception as e:
        logging.error(f"An error has occurred: {e}")

        reply_msg = "<b>🚨 An error occured while using the bot.</b>"
        await update.message.reply_html(text=reply_msg)

async def second_prize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    try:
        reply_msg = "<b>🔰 Enter your competiton's second prize in BNB ie: 2nd: 0.05</b>"
        await query.message.reply_html(text=reply_msg)
    except Exception as e:
        logging.error(f"An error has occurred: {e}")

        reply_msg = "<b>🚨 An error occured while using the bot.</b>"
        await query.message.reply_html(text=reply_msg)

async def second__prize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info("User %s set a 2nd prize for comp.", user.username)

    try:
        context.user_data["second_prize"] = update.message.text.split(" ", 1)[0]
        print(update.message.text, context.user_data["second_prize"])

        reply_msg = f"<b>🔰 You have successfully set the second prize for your competiton to be <i>${update.message.text}</i>.</b>"
        await update.message.reply_html(text=reply_msg)
    except Exception as e:
        logging.error(f"An error has occurred: {e}")

        reply_msg = "<b>🚨 An error occured while using the bot.</b>"
        await update.message.reply_html(text=reply_msg)

async def third_prize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    try:
        reply_msg = "<b>🔰 Enter your competiton's third prize in BNB ie: 3rd: 0.05</b>"
        await query.message.reply_html(text=reply_msg)
    except Exception as e:
        logging.error(f"An error has occurred: {e}")

        reply_msg = "<b>🚨 An error occured while using the bot.</b>"
        await query.message.reply_html(text=reply_msg)

async def third__prize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info("User %s set a 3rd prize for comp.", user.username)

    try:
        context.user_data["third_prize"] = update.message.text.split(" ", 1)[0]
        print(update.message.text, context.user_data["third_prize"])

        reply_msg = f"<b>🔰 You have successfully set the third prize for your competiton to be <i>${update.message.text}</i>.</b>"
        await update.message.reply_html(text=reply_msg)
    except Exception as e:
        logging.error(f"An error has occurred: {e}")

        reply_msg = "<b>🚨 An error occured while using the bot.</b>"
        await update.message.reply_html(text=reply_msg)

async def must_hold(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    try:
        reply_msg = "<b>🔰 Enter your competiton's must hold in hours ie: hodl: 4</b>"
        await query.message.reply_html(text=reply_msg)
    except Exception as e:
        logging.error(f"An error has occurred: {e}")

        reply_msg = "<b>🚨 An error occured while using the bot.</b>"
        await query.message.reply_html(text=reply_msg)

async def must__hold(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info("User %s set a 3rd hold for comp.", user.username)

    try:
        context.user_data["must_hold"] = update.message.text.split(" ", 1)[0]
        print(update.message.text, context.user_data["must_hold"])

        reply_msg = f"<b>🔰 You have successfully set the must hold for your competiton to be <i>${update.message.text}</i>.</b>"
        await update.message.reply_html(text=reply_msg)
    except Exception as e:
        logging.error(f"An error has occurred: {e}")

        reply_msg = "<b>🚨 An error occured while using the bot.</b>"
        await update.message.reply_html(text=reply_msg)

async def min_buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    try:
        reply_msg = "<b>🔰 Enter your competiton's min buy in BNB ie: min: 0.05</b>"
        await query.message.reply_html(text=reply_msg)
    except Exception as e:
        logging.error(f"An error has occurred: {e}")

        reply_msg = "<b>🚨 An error occured while using the bot.</b>"
        await query.message.reply_html(text=reply_msg)

async def min__buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info("User %s set a 3rd buy for comp.", user.username)

    try:
        context.user_data["min_buy"] = update.message.text.split(" ", 1)[0]
        print(update.message.text, context.user_data["min_buy"])

        reply_msg = f"<b>🔰 You have successfully set the min buy for your competiton to be <i>${update.message.text}</i>.</b>"
        await update.message.reply_html(text=reply_msg)
    except Exception as e:
        logging.error(f"An error has occurred: {e}")

        reply_msg = "<b>🚨 An error occured while using the bot.</b>"
        await update.message.reply_html(text=reply_msg)

async def start_biggest_buy_comp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        chat_id = update.message.chat_id
        comp_duration = context.user_data["comp_duration"]
        first_prize = context.user_data["first_prize"]
        second_prize = context.user_data["second_prize"]
        third_prize = context.user_data["third_prize"]
        must_hold = context.user_data["must_hold"]
        min_buy = context.user_data["min_buy"]

        value = {"chat_id": chat_id, "duration": comp_duration, "first_prize": first_prize, "second_prize": second_prize, "third_prize": third_prize, "must_hold": must_hold, "min_buy": min_buy, "type": "BBC", "timestamp": int(time.time())}
        chat = set_chat(db=db, value=value)
        print(chat)

        reply_msg = f"<b>Congratulations 🎉, You have successfully set up a biggest buy competition.</b>"
        await query.message.reply_html(text=reply_msg)
    except Exception as e:
        logging.error(f"An error has occurred: {e}")

        reply_msg = "<b>🚨 An error occured while using the bot.</b>"
        await query.message.reply_html(text=reply_msg)
    
def main() -> None:
    global db
    db = connect_db(uri=MONGO_URI)

    global web3
    web3 = Web3(Web3.HTTPProvider(endpoint_uri=MAINNET_API_URL))

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    add_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add", add)],
        states={
            START: [
                CallbackQueryHandler(start, pattern="^start$"),
                CallbackQueryHandler(chain, pattern="^(bsc|eth)$"),
                MessageHandler(filters.Regex("^0x"), token)
            ]
        },
        fallbacks=[CallbackQueryHandler(end, pattern="^end$")]
    )
    settings_handler = CommandHandler("settings", settings)
    identity_handler = CallbackQueryHandler(identity, pattern="^identity$")
    identity__handler = CallbackQueryHandler(_identity, pattern="^(emoji|photo|gif)$")
    emoji_handler = MessageHandler(filters.Regex("[^a-zA-Z0-9]"), set_emoji)
    photo_handler = MessageHandler(filters.PHOTO, set_photo)
    gif_handler = MessageHandler(filters.ANIMATION, set_gif)
    buy_comp_callback_handler = CallbackQueryHandler(buy_comp, pattern="^buy_comp$")
    last_comp_callback_handler = CallbackQueryHandler(last_comp, pattern="^last_comp$")
    comp_duration_callback_handler = CallbackQueryHandler(comp_duration, pattern="^comp_duration$")
    comp_duration_handler = MessageHandler(filters.Regex("^duration"), comp__duration)
    first_prize_callback_handler = CallbackQueryHandler(first_prize, pattern="^first_prize$")
    first_prize_handler = MessageHandler(filters.Regex("^1st"), first__prize)
    second_prize_callback_handler = CallbackQueryHandler(second_prize, pattern="^second_prize$")
    second_prize_handler = MessageHandler(filters.Regex("^2nd"), second__prize)
    third_prize_callback_handler = CallbackQueryHandler(third_prize, pattern="^third_prize$")
    third_prize_handler = MessageHandler(filters.Regex("^3rd"), third__prize)
    must_hold_callback_handler = CallbackQueryHandler(must_hold, pattern="^must_hold$")
    must_hold_handler = MessageHandler(filters.Regex("^hodl"), must__hold)
    min_buy_callback_handler = CallbackQueryHandler(min_buy, pattern="^min_buy$")
    min_buy_handler = MessageHandler(filters.Regex("^min"), min__buy)

    app.add_handler(add_conv_handler)
    app.add_handler(settings_handler)
    app.add_handler(identity_handler)
    app.add_handler(identity__handler)
    app.add_handler(emoji_handler)
    app.add_handler(photo_handler)
    app.add_handler(gif_handler)
    app.add_handler(buy_comp_callback_handler)
    app.add_handler(last_comp_callback_handler)
    app.add_handler(comp_duration_callback_handler)
    app.add_handler(comp_duration_handler)
    app.add_handler(first_prize_callback_handler)
    app.add_handler(first_prize_handler)
    app.add_handler(second_prize_callback_handler)
    app.add_handler(second_prize_handler)
    app.add_handler(third_prize_callback_handler)
    app.add_handler(third_prize_handler)
    app.add_handler(must_hold_callback_handler)
    app.add_handler(must_hold_handler)
    app.add_handler(min_buy_callback_handler)
    app.add_handler(min_buy_handler)

    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()