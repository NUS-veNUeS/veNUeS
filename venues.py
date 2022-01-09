#!/usr/bin/env python3

import os
import math
import heapq
import re

import telebot
from telebot.types import (
    BotCommand,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)

from datetime import datetime, timedelta
from pytz import timezone
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

import difflib
from venues_store import LOCATIONS, VENUES_LIST, LOCATIONKEYS

load_dotenv()

# Config for NUS_veNUeSBot
API_KEY = os.getenv('API_KEY')
bot = telebot.TeleBot(API_KEY)

# Config database
cert = {
    "type": os.getenv('type'),
    "project_id": os.getenv('project_id'),
    "private_key_id": os.getenv('private_key_id'),
    "private_key": os.environ.get('private_key').replace('\\n', '\n'),
    "client_email": os.getenv('client_email'),
    "client_id": os.getenv('client_id'),
    "auth_uri": os.getenv('auth_uri'),
    "token_uri": os.getenv('token_uri'),
    "auth_provider_x509_cert_url": os.getenv('auth_provider_x509_cert_url'),
    "client_x509_cert_url": os.getenv('client_x509_cert_url')
}
if not firebase_admin._apps:
    cred = credentials.Certificate(cert)
    firebase_admin.initialize_app(cred, {
        'databaseURL': os.getenv('databaseURL')
    })

NUM_RESULTS = 10

docs = db.reference("/venues")
VENUES = docs.get()

for v in VENUES:
    VENUES_LIST.append(v)
    location = VENUES[v]["location"]
    if location in LOCATIONS:
        LOCATIONS[location].append(v)


def euclidean_distance(lat, long, other_lat, other_long):
    """Calculates the euclidean distance between two points"""
    return math.sqrt(math.pow(lat - other_lat, 2)
                     + math.pow(long - other_long, 2))


# Commands available
bot.set_my_commands([
    BotCommand('start', 'Starts the bot'),
    BotCommand('help', 'Lists all commands'),
    BotCommand('room', 'Venue availability in next 1h'),
    BotCommand('locations', 'Currently available venues in specified location'),
    BotCommand('availability', 'Find available venues at a given time period'),
    BotCommand('nearme', 'Nearest 10 available locations in given time period')
])


@bot.message_handler(commands=['start'])
def start(message):
    """
    Command that welcomes the user and configures the required initial setup
    """

    if message.chat.type == 'private':
        chat_user = message.chat.first_name
    else:
        chat_user = message.chat.title

    message_text = f'Hi {chat_user}!! I can help you find empty rooms in NUS for you to make use of! :) Need a quiet room to study? No worries, We got you! Simply use any of my functions to get started! 🚀'

    bot.reply_to(message, message_text)


@bot.message_handler(commands=['help'])
def help(message):
    """
    Command that returns a list of available commands and a short description of their function
    """
    chat_id = message.chat.id
    message = "Here is a list of my commands\!\n" + "\n/start: Starts the bot" + "\n/room: Checks whether veNUeS are available in the next hour" + "\n/locations: Lists veNUeS that are currently available in the specified location/faculty" + \
        "\n/avail or /availability: Check which veNUeS are available at a specific location/faculty and given time period" + \
        "\n/nearme: List nearest 10 veNUeS that are available in a given time period\n\n_Note: Above commands assume queries for the current day_"

    bot.send_message(chat_id=chat_id, text=message, parse_mode="MarkdownV2")
    return


@bot.message_handler(commands=['room'])
def room(message):
    """
    Command that returns whether a room is available
    """
    chat_id = message.chat.id

    reply = "Please type a classroom venue below:"
    msg = bot.send_message(chat_id=chat_id, text=reply)

    bot.register_next_step_handler(msg, process_room)
    return


def process_room(message):
    chat_id = message.chat.id
    room = message.text.upper()

    if room not in VENUES:
        matches = difflib.get_close_matches(
            room, VENUES_LIST, cutoff=0.5, n=NUM_RESULTS)
        buttons = []
        for match in matches:
            button = InlineKeyboardButton(
                text=match, callback_data='venue ' + match)
            buttons.append([button])

        bot.send_message(
            chat_id=chat_id,
            text="Venue not found. Did you mean:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    if isAvailable(room):
        bot.reply_to(message, f"{room} is available for the next hour! 🚀")
    else:

        bot.reply_to(
            message, f"{room} is not available in the next hour :( \nNext available time: {check_availability(room)}\n\nTry /nearme to find available veNUeS near you now!")

    return


def check_availability(room):
    day = getCurrentDay()
    t = getTimeRounded()

    if 'availability' not in VENUES[room]:
        return "Not available today :("

    if day in VENUES[room]['availability']:
        avail_info = VENUES[room]['availability'][day]
    else:
        return "Available for the whole day! :)"

    i = 0
    while t != "2130":
        timeCheck = datetime.strptime(t, "%H%M") + timedelta(minutes=i*30)
        timeCheck = datetime.strftime(timeCheck, "%H%M")
        if not avail_info.get(timeCheck):
            return f'{room} will be available at {timeCheck}!'
        i = 1
        t = timeCheck
    return "Not available today :("


# Get local time rounded up to nearest 30 mins
def getTimeRounded():
    tz = timezone('Asia/Singapore')
    t = datetime.now(tz)
    min_aware = datetime.min.replace(tzinfo=tz)
    rounded = t + (min_aware - t) % timedelta(minutes=30) - \
        timedelta(minutes=35)
    current_time = rounded.strftime("%H%M")
    return current_time


def getTimeRoundedDown(time):
    time = datetime.strptime(time, "%H%M")
    new_minute = (time.minute // 30) * 30
    time = time + timedelta(minutes=new_minute - time.minute)
    return datetime.strftime(time, "%H%M")


def getTimeRoundedUp(time):
    time = datetime.strptime(time, "%H%M")
    new_minute = math.ceil(time.minute / 30) * 30
    time = time + timedelta(minutes=new_minute - time.minute)
    return datetime.strftime(time, "%H%M")


def getCurrentDay():
    days = ["Monday", "Tuesday", "Wednesday",
            "Thursday", "Friday", "Saturday", "Sunday"]
    today = datetime.today().weekday()
    return days[today]


def getMapsString(rm):
    lat = str(VENUES[rm]['lat'])
    long = str(VENUES[rm]['long'])
    return "https://www.google.com/maps/search/?api=1&query=" + lat + "%2C" + long


@bot.message_handler(commands=['locations'])
def locations(message):
    """
    Command that returns venues that are available for the next hour in the specified location
    """
    chat_id = message.chat.id

    chat_text = 'Select the location/faculty you want!'

    buttons = []
    locationKey = []
    count = 0

    for loc in LOCATIONS.keys():
        locationKey.append(loc)

    for _ in range(4):
        row = []
        for _ in range(3):
            loc = str(locationKey[count])
            button = InlineKeyboardButton(
                text=str(LOCATIONKEYS[count]),
                callback_data='location ' + loc
            )
            count += 1
            row.append(button)
        buttons.append(row)

    bot.send_message(
        chat_id=chat_id,
        text=chat_text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return


@bot.message_handler(commands=['availability', 'avail'])
def availability(message):
    """
    Searches for the available veNUeS at a selected faculty/location during a given time period
    """
    chat_id = message.chat.id

    chat_text = 'Select the location/faculty you want:'

    buttons = []
    locationKey = []
    count = 0

    for loc in LOCATIONS.keys():
        locationKey.append(loc)

    for _ in range(4):
        row = []
        for _ in range(3):
            loc = str(locationKey[count])
            button = InlineKeyboardButton(
                text=str(LOCATIONKEYS[count]),
                callback_data='avail ' + loc
            )
            count += 1
            row.append(button)
        buttons.append(row)

    bot.send_message(
        chat_id=chat_id,
        text=chat_text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

    return


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """
    Handles the execution of the respective functions upon receipt of the callback query
    """

    chat_id = call.message.chat.id
    data = call.data
    intent, data = data.split()[0], data.split()[1:]

    if intent == 'location':
        chat_message = f"Here are some veNUeS that are available in {data[0]} 🚀"

        rooms = LOCATIONS[data[0]]
        room_dict = {}

        for rm in rooms:
            if isAvailable(rm):
                room_dict[rm] = timeAvailable(rm)

        room_dict = dict(
            sorted(room_dict.items(), key=lambda item: item[1], reverse=True))

        i = 1
        for rm in room_dict:
            msg = f'\n• [{rm}]({getMapsString(rm)}) is available for next {room_dict[rm]} hrs'
            chat_message = chat_message + msg
            i += 1
            if i > NUM_RESULTS:
                break

        bot.send_message(
            chat_id=chat_id,
            text=chat_message,
            parse_mode="Markdown"
        )
        return

    if intent == 'avail':
        chat_message = "Please enter start and end time! Time must be in 24 hour format! e.g. 0930-1450"

        msg = bot.send_message(
            chat_id=chat_id,
            text=chat_message
        )
        bot.register_next_step_handler(msg, parse_time, data)

        return

    if intent == 'venue':
        # call.message.text = "/room " + data[0]
        call.message.text = data[0]
        process_room(call.message)

        return

    print(f'{chat_id}: Callback not implemented')


def parse_time(message, location):
    chat_id = message.chat.id
    message.text = message.text.strip()
    pattern = '^(0[0-9]|1[0-9]|2[0-3])[0-5][0-9]-(0[0-9]|1[0-9]|2[0-3])[0-5][0-9]$'
    result = re.match(pattern, message.text)

    if not result:
        bot.send_message(
            chat_id=chat_id,
            text="Invalid time. Please try again! :("
        )
        return

    times = message.text.split("-")
    start_time = getTimeRoundedDown(times[0])
    end_time = getTimeRoundedUp(times[1])

    if int(end_time) < int(start_time):
        bot.send_message(
            chat_id=chat_id,
            text="End time cannot be earlier than start time. Please enter start and end time again"
        )
        return

    available_locations = []

    for venue in LOCATIONS[location[0]]:
        if isAvailableWithTime(venue, start_time, end_time):
            available_locations.append(venue)

    msg = f"These are the veNUeS that are available from {start_time} to {end_time}:"
    i = 1
    for location in available_locations:
        msg += f'\n• [{location}]({getMapsString(location)})'
        i += 1
        if i > NUM_RESULTS:
            break

    bot.send_message(
        chat_id=chat_id,
        text=msg,
        parse_mode="Markdown"
    )
    return


@bot.message_handler(commands=['nearme'])
def nearme(message):
    """
    Finds the 10 nearest available veNUeS to the user in a given time period
    """
    chat_id = message.chat.id

    button = KeyboardButton(
        text="Tap here to send your current location", request_location=True)
    markup = ReplyKeyboardMarkup()
    markup.add(button)

    bot.send_message(
        chat_id=chat_id,
        text="Please provide your location via the button below:",
        reply_markup=markup
    )

    return


@bot.message_handler(content_types=['location'])
def nearme_callback(message):
    """
    Handles the callback of the nearme function
    """
    chat_id = message.chat.id

    lat = message.location.latitude
    long = message.location.longitude

    pq = []
    heapq.heapify(pq)

    for venue in VENUES:
        dist = euclidean_distance(
            lat, long, VENUES[venue]["lat"], VENUES[venue]["long"])
        heapq.heappush(pq, (dist, venue))

    # ask for start time and end time
    chat_message = "Please enter start and end time! Time must be in 24 hour format! e.g. 0930-1450"

    msg = bot.send_message(
        chat_id=chat_id,
        text=chat_message
    )
    bot.register_next_step_handler(msg, nearest_available_venues, pq)

    return


def nearest_available_venues(message, pq):
    chat_id = message.chat.id
    message.text = message.text.strip()
    pattern = '^(0[0-9]|1[0-9]|2[0-3])[0-5][0-9]-(0[0-9]|1[0-9]|2[0-3])[0-5][0-9]$'
    result = re.match(pattern, message.text)

    if not result:
        bot.send_message(
            chat_id=chat_id,
            text="Invalid time. Please try again! :("
        )
        return

    times = message.text.split("-")
    start_time = getTimeRoundedDown(times[0])
    end_time = getTimeRoundedUp(times[1])

    if int(end_time) < int(start_time):
        bot.send_message(
            chat_id=chat_id,
            text="End time cannot be earlier than start time. Please enter start and end time again"
        )
        return

    max_results = NUM_RESULTS
    available_locations = []

    while pq and max_results > 0:
        rm_tup = heapq.heappop(pq)
        if isAvailableWithTime(rm_tup[1], start_time, end_time):
            available_locations.append(rm_tup[1])
            max_results -= 1

    msg = f"These are the veNUeS that are available from {start_time} to {end_time} near you:"
    for location in available_locations:
        msg += f'\n• [{location}]({getMapsString(location)})'

    bot.send_message(
        chat_id=chat_id,
        text=msg,
        parse_mode="Markdown"
    )
    return


def isAvailable(room):
    day = getCurrentDay()
    t = getTimeRounded()

    if 'availability' not in VENUES[room]:
        return False

    if day in VENUES[room]['availability']:
        avail_info = VENUES[room]['availability'][day]
    else:
        return True

    for i in range(2):
        timeCheck = datetime.strptime(t, "%H%M") + timedelta(minutes=i*30)
        timeCheck = datetime.strftime(timeCheck, "%H%M")
        if avail_info.get(timeCheck):
            return False
    return True


def isAvailableWithTime(room, start_time, end_time):
    day = getCurrentDay()

    if 'availability' not in VENUES[room]:
        return False

    if 'availability' in VENUES[room]:
        if day in VENUES[room]['availability']:
            avail_info = VENUES[room]['availability'][day]
        else:
            return True

    while int(start_time) < int(end_time):
        if avail_info.get(start_time):  # occupied at start_time
            return False
        start_time = datetime.strptime(
            start_time, "%H%M") + timedelta(minutes=30)
        start_time = datetime.strftime(start_time, "%H%M")

    return True

# How much time a room is available for


def timeAvailable(room):
    duration_Counter = 0
    t = getTimeRounded()
    day = getCurrentDay()
    avail_info = {}
    i = 0

    if 'availability' in VENUES[room]:
        if day in VENUES[room]['availability']:
            avail_info = VENUES[room]['availability'][day]
        while t != "2130":
            timeCheck = datetime.strptime(t, "%H%M") + timedelta(minutes=i*30)
            timeCheck = datetime.strftime(timeCheck, "%H%M")

            if avail_info.get(timeCheck):
                return duration_Counter

            duration_Counter += 0.5
            i = 1
            t = timeCheck
    return duration_Counter


@bot.message_handler(regexp="/.*")
def handle_message(message):
    bot.send_message(chat_id=message.chat.id,
                     text="Sorry, I didn't understand that command. :(")


bot.enable_save_next_step_handlers(delay=2)
bot.load_next_step_handlers()

bot.infinity_polling()
