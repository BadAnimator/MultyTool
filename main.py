from utils import Database, Logger, Utils

import requests
import telebot

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

import time
import os

CLOSE_BUTTON = InlineKeyboardButton("❌ Закрыть", callback_data="CLOSE")
CLOSE_KB = InlineKeyboardMarkup(); CLOSE_KB.add(CLOSE_BUTTON)


LAST_UPDATE_PROXIES_TIME = time.time()
ACTUALY_PROXIES = None

BOT_TOKEN = "8621117455:AAH2qqGqCgxECUsQ1xymeFdwgctJVS2f_ho" # BOT TOKEN !!!!

bot = telebot.TeleBot(BOT_TOKEN)

Log = Logger("Logs.log", end_function=lambda t: print(t))

PROXY_GITHUB_URL = "https://raw.githubusercontent.com/SoliSpirit/mtproto/refs/heads/master/all_proxies.txt"

DEFAULT_ADMINS_IDS = [7925361356, -1003677686279] # And groups/channels*

def FormateProxiesForHTML(text_with_HTML_tag="*Тык*") -> list:
    proxy_format=f'<a href="https://t.me/proxy?server=%HOST%&port=%PORT%&secret=%SECRET%">{text_with_HTML_tag}</a>'
    return [proxy_format.replace(
        "%HOST%",
        proxy["server"]
    ).replace(
        "%PORT%",
        proxy["PORT"]
    ).replace(
        "%SECRET",
        proxy["secret"]
    ) for proxt in ACTUALY_PROXIES]

def UpdateProxies():
    try:
        data = requests.get(PROXY_GITHUB_URL)
        if data:
            global ACTUALY_PROXIES
            FormattedProxies = Utils.formatProxies(data.text.split("\n"))
            ACTUALY_PROXIES = FormattedProxies
            Log.log(f"Successfull collection proxies data. Status code: {data.status_code}; Worked proxies count: {len(FormattedProxies)}")
        else:
            Log.log(f"Unsuccessfull collection proxies data. Error code: {data.status_code}")
    except Exception as e:
        Log.log(f"Error collection proxies data. Error: {e}")


@bot.message_handler(content_types=['text'])
def handle_message(message):
    """
    Обработка сообщений
    """
    Log.log(f"New message: {message.text}")
    cid = message.chat.id
    mid = message.id
    txt = message.text
    if cid in DEFAULT_ADMINS_IDS:
        if txt.lower() == "/proxies":
            EditFlag = False
            if LAST_UPDATE_PROXIES_TIME < time.time() - 60*60*24:
                EditFlag = bot.send_message(cid, "Подождите, обновление прокси... ⏳")
                UpdateProxies()
            if EditFlag:
                bot.edit_message_text(' '.join(FormateProxiesForHTML()), cid, EditFlag.id, parse_mode="HTML", reply_markup=CLOSE_KB)
            else:
                bot.send_message(cid, ' '.join(FormateProxiesForHTML()), parse_mode="HTML", reply_markup=CLOSE_KB)

Log.log("Program has been started...")

if __name__ == '__main__':
    try:
        Log.log("Bot started...")
        bot.infinity_polling()
    except Exception as e:
        Log.log(f"Bot stopped his work for error: {e}")