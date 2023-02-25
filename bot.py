# -*- coding: utf-8 -*-
import config
import json

import telebot
from revChatGPT.V1 import Chatbot


bot = telebot.TeleBot(config.token)
chatbot = Chatbot(config={
    "email": "@10xt.tech",
    "password": "!"
})

ACCOST_KEYWORDS = ("игорь", "игорек", "игоречек", "igor", "игорю", "игоря",
                   "игорь,", "игорек,", "игоречек,", "igor,", "игорю,", "игоря,", "игорь!", "игорь?", )

ERROR_MESSAGE = 'Ops, something went wrong :( Pls Ask Denis to check asap!'
BOT_VERSION = '1.0'


def init(message):
    bot.send_message(message.chat.id, 'Starting initial conversation training ...')
    try:

        bot.send_message(message.chat.id, 'Initial training completed')

    except Exception as e:
        bot.send_message(message.chat.id, ERROR_MESSAGE)


def log_message(message, text, if_user=True):
    # log a message
    try:
        if if_user:
            user_first_name = message.from_user.first_name
            user_last_name = message.from_user.last_name
        else:
            user_first_name = 'Igor'
            user_last_name = 'Bot'

        conversation_log = open(config.conversation_log_name, 'a', encoding='utf-8')
        conversation_log.write(str(message.date) + ';' + str(user_first_name) + ';' + str(
            user_last_name) + ';' + text + '\n')
        conversation_log.close()

    except Exception as e:
        bot.send_message(message.chat.id, ERROR_MESSAGE)


@bot.message_handler(commands=['help', 'info', 'init'])
def help_command_message(message):

    if message.text.find('help') > 0:

        bot.send_message(message.chat.id, '\n' + "Igor bot version " + BOT_VERSION + '\n' + 'Command list:' + '\n' +
                         '/info - general information' + '\n' +
                         '/help - Help' + '\n' +
                         '/init - initial conversation training' + '\n')

    if message.text.find('info') > 0:
        bot.send_message(message.chat.id, "Igor bot version " + BOT_VERSION + '\n' + "Status: " + "Active" + '\n')

    if message.text.find('init') > 0:
        init(message)


@bot.message_handler(content_types=["text"])
def response_for_message(message):

    for word in message.text.split():

        if word.lower() in ACCOST_KEYWORDS:

            message_id = message.id
            chat = message.chat.id
            chat_title = message.chat.title
            user_full_name = message.from_user.full_name

            bot.send_message(message.chat.id, user_full_name + " спасибо тебе за вопрос, мне надо немного подумать...")

            message_text = message.text.replace(word, '').strip()

            response = ""

            for data in chatbot.ask(message_text):
                response = data["message"]

            bot.send_message(message.chat.id, response)

            break


if __name__ == '__main__':
    bot.polling(none_stop=True)
