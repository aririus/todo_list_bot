from telebot import TeleBot, types
from telebot_calendar import Calendar, CallbackData, RUSSIAN_LANGUAGE
from datetime import datetime
import time

with open('token.txt') as f:
    token = f.readline()
bot = TeleBot(token)

calendar = Calendar(language=RUSSIAN_LANGUAGE)
callback_data = CallbackData('calendar', 'action', 'year', 'month', 'day')

startText = """
Привет! Это To-Do List – бот для составления списка дел.
"""
calendarText = """
Выберите дату на предложенном ниже календаре. После этого вы сможете добавить задачи, просмотреть или удалить уже имеющиеся
"""

todo = {}
userDate = {}


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, startText)
    forCalender(message)


def forCalender(message):
    bot.send_message(message.chat.id, calendarText)
    calendar_command(message)


def calendar_command(message):
    now = datetime.now()
    bot.send_message(
        message.chat.id,
        'Выберите дату:',
        reply_markup=calendar.create_calendar(
            name=callback_data.prefix,
            year=now.year,
            month=now.month
        )
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith(callback_data.prefix))
def callback_inline(call):
    userID = call.from_user.id
    name, action, year, month, day = call.data.split(callback_data.sep)
    date = calendar.calendar_query_handler(
        bot=bot,
        call=call,
        name=name,
        action=action,
        year=year,
        month=month,
        day=day
    )

    if action == "DAY":
        if date:
            selected_date = date.strftime('%d.%m.%Y')
            userDate[userID] = selected_date
            bot.delete_message(call.message.chat.id, call.message.message_id - 1)
            actionButtons(call.message)


@bot.message_handler(commands=['action'])
def actionButtons(message):
    userID = message.chat.id
    date = userDate.get(userID)

    markup = types.InlineKeyboardMarkup()
    addButton = types.InlineKeyboardButton('Добавить задачи', callback_data='add')
    markup.row(addButton)
    showButton = types.InlineKeyboardButton('Посмотреть', callback_data='show')
    clearButton = types.InlineKeyboardButton('Удалить', callback_data='clear')
    markup.row(showButton, clearButton)
    bot.send_message(message.chat.id, f'Выбранная дата: {date}\n\nВыберите действие для этой даты:',
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data == 'add')
def callback_message(callback):
    msg = bot.send_message(callback.message.chat.id,
                           'Введите одну задачу или несколько, каждую с отдельной строки')
    bot.register_next_step_handler(msg, add_task)


def add_task(message):
    userID = message.from_user.id
    date = userDate.get(userID)
    del userDate[userID]

    task = message.text.split('\n')
    if userID not in todo:
        todo[userID] = {}
    if date not in todo[userID]:
        todo[userID][date] = []

    if len(task) == 1:
        todo[userID][date].append(task)
        bot.delete_message(message.chat.id, message.message_id - 2)
        text = ''.join(task)
        bot.send_message(message.chat.id, f'Задача "{text}" добавлена на дату {date}')
        bot.delete_message(message.chat.id, message.message_id - 1)
    else:
        todo[userID][date] = task
        bot.delete_message(message.chat.id, message.message_id - 2)
        task = ',\n'.join(task)
        bot.send_message(message.chat.id, f'Задачи\n{task}\nдобавлены на дату {date}')
        bot.delete_message(message.chat.id, message.message_id - 1)

    time.sleep(1)
    forCalender(message)


@bot.callback_query_handler(func=lambda callback: callback.data == 'show')
def callback_message(callback):
    userID = callback.from_user.id
    date = userDate.get(userID)

    if date:
        allTasks = todo.get(userID, {}).get(date, [])
        del userDate[userID]
        text = ''
        for task in allTasks:
            text += f"- {''.join(task)}\n"
        if not text:
            text = f"На дату {date} задач нет"
        else:
            text = f"Задачи на дату {date}:\n" + text
    else:
        text = f"На дату {date} задач нет"

    bot.send_message(callback.message.chat.id, text)
    time.sleep(1)
    forCalender(callback.message)


@bot.callback_query_handler(func=lambda callback: callback.data == 'clear')
def callback_message(callback):
    userID = callback.from_user.id
    date = userDate.get(userID)

    if date and userID in todo and date in todo[userID]:
        del todo[userID][date]
        del userDate[userID]
        text = f'Задачи на дату "{date}" удалены'
    else:
        text = "Задач на эту дату не было и нет :)"

    bot.send_message(callback.message.chat.id, text)
    time.sleep(1)
    forCalender(callback.message)


bot.polling(non_stop=True)
