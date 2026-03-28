import os
os.system("pip install requests PyTelegramBot phonenumbers ipinfo")
os.system("pip install phonenumbers")
os.system("pip install ipinfo")

from utils import Database, Logger, Utils

import requests
import telebot
import phonenumbers
import ipinfo

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from phonenumbers import geocoder, carrier, timezone, PhoneNumberType, PhoneNumberFormat

import re
import time
# import os

CLOSE_BUTTON = InlineKeyboardButton("❌ Закрыть", callback_data="CLOSE")
CLOSE_KB = InlineKeyboardMarkup(); CLOSE_KB.add(CLOSE_BUTTON)

START = "\n".join([
	f"• <b>Поиск по IP</b>: <code>/ip</code> <i>*Ipv4/Ipv6*</i>",
	f"• <b>Поиск по номеру</b>: <code>/num</code> <i>*Number*</i>",
	f"• <b>Получить прокси</b>: <code>/proxies</code>",
	"",
	f"<b><i>Удачного использования!</i></b>"
])

LAST_UPDATE_PROXIES_TIME = time.time()
ACTUALY_PROXIES = None

BOT_TOKEN = "8621117455:AAH2qqGqCgxECUsQ1xymeFdwgctJVS2f_ho" # BOT TOKEN !!!!
IPINFO_TOKEN = "2140c2c5e9e680" # IP INFO TOKEN !!!!

bot = telebot.TeleBot(BOT_TOKEN)

USERNAME = bot.get_me().username

Log = Logger("Logs.log", end_function=lambda t: print(t))
IPINFO_HANDLER=ipinfo.getHandlerLite(access_token=IPINFO_TOKEN)

PROXY_GITHUB_URL = "https://raw.githubusercontent.com/SoliSpirit/mtproto/refs/heads/master/all_proxies.txt"

DEFAULT_ADMINS_IDS = [7925361356, -1003677686279] # And groups/channels*

def GetFormattedNumInfo(number: str) -> str:
	"""
	Принимает строку с номером телефона (поддерживает международный формат с '+' 
	и российские номера в форматах 8XXX... или 7XXX...).
	Возвращает HTML‑строку с подробной информацией о номере.
	"""
	# Удаляем пробелы, дефисы, скобки и другие разделители
	original = number.strip()
	cleaned = re.sub(r'[\s\-\(\)]', '', original)

	# Эвристика для российских номеров
	if cleaned.startswith('8') and len(cleaned) == 11 and cleaned[1] in '9':
		# Российский мобильный: 8 XXX XXX XX XX → +7 XXX ...
		cleaned = '+7' + cleaned[1:]
	elif cleaned.startswith('7') and len(cleaned) == 11:
		# 7 XXX XXX XX XX → +7 XXX ...
		cleaned = '+' + cleaned
	# При необходимости здесь можно добавить аналогичные правила для других стран

	try:
		# Парсинг номера (None означает, что номер должен быть международным,
		# но наша предобработка уже позаботилась об этом для популярных случаев)
		phone_number = phonenumbers.parse(cleaned, None)
	except phonenumbers.NumberParseException as e:
		return f'Не удалось проверить номер. Пожалуйста, проверьте формат'

	phone_number

	# Валидация
	is_valid = phonenumbers.is_valid_number(phone_number)
	valid_str = "Да ✅" if is_valid else "Нет ❌"
	is_possible = phonenumbers.is_possible_number(phone_number)
	possible_str = "Да ✅" if is_possible else "Нет ❌"

	# Страна и регион (на русском)
	region = geocoder.description_for_number(phone_number, "ru")
	if not region:
		region = "Неизвестно"

	# Код страны
	country_code = f"+{phone_number.country_code}"

	# Оператор (на русском)
	operator = carrier.name_for_number(phone_number, "ru")
	if not operator:
		operator = "Не определён"

	# Тип номера
	num_type = phonenumbers.number_type(phone_number)
	type_names = {
		PhoneNumberType.FIXED_LINE: "Стационарный",
		PhoneNumberType.MOBILE: "Мобильный",
		PhoneNumberType.FIXED_LINE_OR_MOBILE: "Стационарный или мобильный",
		PhoneNumberType.TOLL_FREE: "Бесплатный вызов (toll‑free)",
		PhoneNumberType.PREMIUM_RATE: "Премиум‑номер",
		PhoneNumberType.SHARED_COST: "С разделением платы",
		PhoneNumberType.VOIP: "VoIP",
		PhoneNumberType.PERSONAL_NUMBER: "Персональный номер",
		PhoneNumberType.PAGER: "Пейджер",
		PhoneNumberType.UAN: "Универсальный номер",
		PhoneNumberType.VOICEMAIL: "Голосовая почта",
		PhoneNumberType.UNKNOWN: "Неизвестный тип"
	}
	type_str = type_names.get(num_type, "Неизвестный тип")

	# Часовой пояс
	timezones = timezone.time_zones_for_number(phone_number)
	tz_str = timezones[0] if timezones else "Не определён"

	# Форматы номера
	e164 = phonenumbers.format_number(phone_number, PhoneNumberFormat.E164)
	international = phonenumbers.format_number(phone_number, PhoneNumberFormat.INTERNATIONAL)
	national = phonenumbers.format_number(phone_number, PhoneNumberFormat.NATIONAL)

	# Формируем HTML‑ответ
	html = '\n'.join([
		f"<b>Действителен:</b> {valid_str}",
		f"<b>Возможен (валиден):</b> {possible_str}",
		f"<b>Код страны:</b> <code>{country_code}</code>",
		f"<b>Страна/Регион:</b> <i>{region}</i>",
		f"<b>Оператор:</b> <code>{operator}</code>",
		f"<b>Тип номера:</b> {type_str}",
		f"<b>Часовой пояс:</b> <b><i>Информация временно недоступна</i></b>",#<code>{tz_str}</code> (<code>{get_zone_time(tz_str)}</code>)",
		f"",
		f"<b>E.164:</b> <code>{e164}</code>",
		f"<b>Международный:</b> <code>{international}</code>",
		f"<b>Национальный:</b> <code>{national}</code>"
	])
	return html.strip()

def GetFormattedIpInfo(IP: str):
	try:
		details=IPINFO_HANDLER.getDetails(IP)
		answer = "\n".join([
			f"<b><i>Запрос:</i></b> <code>{details.ip}</code>",
			f"",
			f"<b>Код страны:</b> <code>{details.country_code}</code>",
			f"<b>Страна:</b> <code>{details.country}</code> {details.country_flag['emoji']}",
			f"<b>Код континента:</b> <code>{details.continent_code}</code>",
			f"<b>Континент:</b> <code>{details.continent['name']}</code>",
			f"<b>ASN:</b> <code>{details.asn}</code>",
			f"<b>Домен:</b> <code>{details.as_domain}</code>",
			f"<b>Компания:</b> <code>{details.as_name}</code>",
			f"",
			f"<b>ЕС:</b> <i>{'Да ✅' if details.isEU else 'Нет ❌'}</i>",
			f"<b>Валюта страны:</b> <code>{details.country_currency['code']}</code> (<code>{details.country_currency['symbol']}</code>)"
		])
		return answer, None
	except Exception as e:
		Log.log(f"Error get ip info: {e}")
		return "<b>Простите! Произошла ошибка, попробуйте ещё раз позже!</b>", e

def FormateProxiesForHTML(text_with_HTML_tag="*Тык*") -> list:
	proxy_format=f'<a href="https://t.me/proxy?server=%HOST%&port=%PORT%&secret=%SECRET%">{text_with_HTML_tag}</a>'
	formated_proxies = [proxy_format.replace(
		"%HOST%",
		proxy["server"]
	).replace(
		"%PORT%",
		proxy["port"]
	).replace(
		"%SECRET%",
		proxy["secret"]
	) for proxy in ACTUALY_PROXIES]
	return Utils.splitList(formated_proxies, 50)
	"""
	["*Тык*", "*Тык*", "*Тык*"];
	["*Тык*", "*Тык*", "*Тык*"]
	"""

def UpdateProxies():
	try:
		data = requests.get(PROXY_GITHUB_URL)
		if data:
			global ACTUALY_PROXIES, LAST_UPDATE_PROXIES_TIME
			FormattedProxies = Utils.formatProxies(data.text.split("\n"))
			ACTUALY_PROXIES = FormattedProxies
			LAST_UPDATE_PROXIES_TIME = time.time()
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
	thread_id=message.message_thread_id
	if cid in DEFAULT_ADMINS_IDS:
		Log.log(f"User {cid} is Admin")
		if txt.lower() == "/proxies" or txt.lower() == f"/proxies@{USERNAME}":
			Log.log(f"Command: /proxies")
			EditFlag = False
			if LAST_UPDATE_PROXIES_TIME < time.time() - 60*60*24: # 100 < 200 - 10
				Log.log("Update proxies...")
				EditFlag = bot.send_message(cid, "Подождите, обновление прокси... ⏳", message_thread_id=thread_id)
				UpdateProxies()
			for text in FormateProxiesForHTML():
				if EditFlag:
					bot.edit_message_text(' '.join(text), cid, EditFlag.id, parse_mode="HTML", reply_markup=CLOSE_KB, message_thread_id=thread_id)
					EditFlag=False
				else:
					bot.send_message(cid, ' '.join(text), parse_mode="HTML", reply_markup=CLOSE_KB, message_thread_id=thread_id)
		elif txt.lower() == '/start':
			bot.send_message(cid, f"Здраствуйте, администратор! \nСписок команд:\n{START}", parse_mode="HTML", reply_markup=CLOSE_KB, message_thread_id=thread_id)

		elif txt.lower().startswith("/ip"):
			if txt.lower().strip() == '/ip':
				bot.send_message(cid, "__Использование__: `/ip` **<Ipv4/Ipv6>**", parse_mode="MarkDown", message_thread_id=thread_id); return
			Ip=txt[len("/ip "):]
			if len(Ip) < 7: # 1.1.1.1 = 7
				bot.send_message(cid, "Проверьте правильность написания айпи. Пример: <code>8.8.8.8</code>", parse_mode="HTML", message_thread_id=thread_id)
				return
			text, error = GetFormattedIpInfo(Ip)
			bot.send_message(cid, text, parse_mode="HTML", message_thread_id=thread_id, reply_markup=CLOSE_KB)
		elif txt.lower().startswith("/num"):
			if txt.lower().strip() == '/num':
				bot.send_message(cid, "__Использование__: `/num` **<number>**", parse_mode="MarkDown", message_thread_id=thread_id); return
			Num=txt[len('/num '):]
			text = GetFormattedNumInfo(Num)
			bot.send_message(cid, text, parse_mode="HTML", message_thread_id=thread_id, reply_markup=CLOSE_KB)
	else:
		bot.send_message(cid, "Простите, но вы не администратор. Обратитесь к создателю.", message_thread_id=thread_id)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
	cid = call.message.chat.id
	mid = call.message.message_id
	tid = call.message.message_thread_id
	if call.data == "CLOSE":
		bot.delete_message(cid, mid)
		bot.answer_callback_query(call.id, "Закрыто!")

Log.log("Program has been started...")
if __name__ == '__main__':
	try:
		UpdateProxies()
		Log.log("Proxies updated")
		Log.log("Bot started")
		bot.infinity_polling()
	except Exception as e:
		Log.log(f"Bot stopped his work for error: {e}")
