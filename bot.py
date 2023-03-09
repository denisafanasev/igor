# -*- coding: utf-8 -*-
import json
import yaml

import telebot
# from revChatGPT.V1 import Chatbot
from revChatGPT.V3 import Chatbot

# Global variables
bot = None
chatgpt_model = None
bot_token = None
chatgpt_config_file = None
admin_chat = None

users_in_que = 0

# Global constants
KEYWORDS = ("игорь,", "igor,", "пес,", "@igorva_dev_bot", "@igorva_bot")

ERROR_MESSAGE = 'Ops, something went wrong :( Pls Ask Denis to check asap!'
BOT_VERSION = '2.0.1'
CONFIG_FILE_NAME = "../config.yaml"


# read config file
with open(CONFIG_FILE_NAME, "r") as f:
    cfg = yaml.safe_load(f)

bot_token = cfg['CONFIG']['bot_token']
admin_chat = cfg['CONFIG']['admin_chat']
chatgpt_token = cfg['CONFIG']['chatgpt_token']
# chatgpt_config_file = cfg['CONFIG']['chatgpt_config_file']


# let's init the bot
bot = telebot.TeleBot(bot_token)


def init(message=None):
    """
    Init the bot and the chatgpt model

    Args:
        message (message, optional): message from user. Defaults to None.
    """

    global chatgpt_model

    if message is None:
        chat_id = admin_chat
    else:
        chat_id = message.chat.id

    bot.send_message(chat_id, 'ChatGPT initialization ...')

    try:
        chatgpt_model = Chatbot(chatgpt_token)
        bot.send_message(chat_id, 'ChatGPT initialization completed')
    except Exception as e:
        bot.send_message(chat_id, e)
        pass

    bot.send_message(chat_id, 'Igor initialization completed')


@bot.message_handler(commands=['help', 'info', 'init'])
def help_command_message(message):

    if message.text.find('help') > 0:

        bot.send_message(message.chat.id, '\n' + "Igor bot version " + BOT_VERSION + '\n' + 'Command list:' + '\n' +
                         '/info - General information and status' + '\n' +
                         '/init - Init ChatGPT model' + '\n' +
                         '/help - Help' + '\n')

    if message.text.find('info') > 0:

        status = ""

        if users_in_que > 0:
            status = "In use"
        else:
            status = "Idle"

        bot.send_message(message.chat.id, "Igor bot version " + BOT_VERSION + '\n' + "Status: " + status + '\n')

    if message.text.find('init') > 0:
        init(message)


@bot.message_handler(content_types=["text"])
def response_for_message(message):

    global users_in_que

    for word in message.text.split():

        message_id = message.id
        chat = message.chat.id
        chat_title = message.chat.title
        user_full_name = message.from_user.full_name

        if (word.lower() in KEYWORDS) or (chat_title is None):

            if users_in_que > 0:
                
                try:
                    bot.send_message(chat, user_full_name + ", я занят, задайте ваш вопрос попозже плз...")
                except Exception as e:
                    pass

                break

            users_in_que += 1

            if word.lower() in KEYWORDS:
                message_text = message.text.replace(word, '').strip()
            else:
                message_text = message.text.strip()

            response = ""

            if chat_title is None:
                chat_title = "Private chat"

            try:

                bot.send_message(chat, user_full_name + ", вопрос принят, мне надо немного подумать...")
                bot.send_message(admin_chat, "Вопрос от " + user_full_name + " в чате " + chat_title + ":\n" + message_text)

                response = chatgpt_model.ask(message_text)
                
                bot.send_message(message.chat.id, response)

            except Exception as e:
                try:

                    bot.send_message(chat, ERROR_MESSAGE)
                    bot.send_message(admin_chat, str(e))

                except Exception as e:
                    pass

            users_in_que -= 1

            break


if __name__ == '__main__':

    # init the bot
    init()

    bot.polling(none_stop=True)
