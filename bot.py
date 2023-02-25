# -*- coding: utf-8 -*-
import config
import json
import yaml

import telebot
from revChatGPT.V1 import Chatbot

# Global variables
bot = None
chatgpt_model = None
bot_token = None
chatgpt_config_file = None

# Global constants
KEYWORDS = ("игорь", "игорек", "игоречек", "igor", "игорю", "игоря",
            "игорь,", "игорек,", "игоречек,", "igor,", "игорю,", "игоря,", "игорь!", "игорь?", )

ERROR_MESSAGE = 'Ops, something went wrong :( Pls Ask Denis to check asap!'
BOT_VERSION = '1.0'
CONFIG_FILE_NAME = "config.yaml"


# read config file
with open(CONFIG_FILE_NAME, "r") as f:
    cfg = yaml.safe_load(f)

bot_token = cfg['CONFIG']['bot_token']
bot_admin_chat = cfg['CONFIG']['bot_admin_chat']
chatgpt_config_file = cfg['CONFIG']['chatgpt_config_file']

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
        chat_id = bot_admin_chat
    else:
        chat_id = message.chat.id

    bot.send_message(chat_id, 'ChatGPT initialization ...')

    try:
        with open(chatgpt_config_file, "r") as f:
         
            chatgpt_config = json.load(f)
            chatgpt_model = Chatbot(config=chatgpt_config)

        bot.send_message(chat_id, 'ChatGPT initialization completed')
   
    except Exception as e:
        bot.send_message(chat_id, e)
        pass

    bot.send_message(chat_id, 'Igor initialization completed')


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

        if word.lower() in KEYWORDS:

            message_id = message.id
            chat = message.chat.id
            chat_title = message.chat.title
            user_full_name = message.from_user.full_name

            bot.send_message(message.chat.id, user_full_name + " спасибо тебе за вопрос, мне надо немного подумать...")

            message_text = message.text.replace(word, '').strip()

            response = ""

            for data in chatgpt_model.ask(message_text):
                response = data["message"]

            bot.send_message(message.chat.id, response)

            break


if __name__ == '__main__':

    init()

    bot.polling(none_stop=True)
