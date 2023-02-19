# -*- coding: utf-8 -*-
import config
import telebot
import json

from chatterbot.trainers import ListTrainer
from chatterbot.trainers import ChatterBotCorpusTrainer
from chatterbot import ChatBot

import codecs

chatbot = ChatBot("Igor")
chatbot.set_trainer(ChatterBotCorpusTrainer)

bot = telebot.TeleBot(config.token)

ACCOST_KEYWORDS = ("игорь", "игорек", "игоречек", "igor", "игорю", "игоря",
                   "игорь,", "игорек,", "игоречек,", "igor,", "игорю,", "игоря,", "игорь!", "игорь?", )

ERROR_MESSAGE = 'Ops, something went wrong :( Pls Ask Denis to check asap!'
BOT_VERSION = '2.2'

#initial list for training
conversation = []
chat_mode = {}

#system defs

def get_chat_mode(id):
    return chat_mode.get(id, False)

def set_chat_mode(id, mode = False):
    chat_mode[id] = mode

def init(message):
    bot.send_message(message.chat.id, 'Starting initial conversation training ...')
    try:
        chatbot.train('./' + config.initial_conversation_base_name)
        bot.send_message(message.chat.id, 'Initial training completed')
    except:
        bot.send_message(message.chat.id, ERROR_MESSAGE)

def dump(message):
    bot.send_message(message.chat.id, 'Starting dumping ...')
    try:
        chatbot.trainer.export_for_training('./'+config.dump_file_name)
    except:
        bot.send_message(message.chat.id, ERROR_MESSAGE)

def force(message):
    bot.send_message(message.chat.id, 'under construction ...')
    # try:
    #     #тут надо переделать логику формирования диалогов, тк нельзя весь лог рассматривать как один диалог
    #     bot.send_message(message.chat.id, 'conversation log converting...')
    #     conversation_log = codecs.open(config.conversation_log_name, "r", encoding='utf-8')
    #     lines = conversation_log.read().splitlines()
    #     lines_count = 0
    #     conversation = []
    #
    #     for line in lines:
    #         try:
    #             words = line.split(";")
    #             conversation.append(words[3])
    #             lines_count = lines_count+1
    #         except:
    #             pass
    #
    #     export = {'conversations': conversation}
    #     with open(config.conversation_log_json_name, 'w', encoding='utf-8') as jsonfile:
    #         json.dump(export, jsonfile, ensure_ascii=False)
    #     bot.send_message(message.chat.id, 'uploaded ' + str(lines_count) + ' lines from the conversation log')
    #
    #     bot.send_message(message.chat.id, 'model training...')
    #     chatbot.train('./' + config.conversation_log_json_name)
    #     bot.send_message(message.chat.id, 'training done')
    #
    # except:
    #     bot.send_message(message.chat.id, ERROR_MESSAGE)

def log_message(message, text, if_user = True):
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
    except:
        bot.send_message(message.chat.id, ERROR_MESSAGE)

#message handlers

@bot.message_handler(commands=['help', 'force', 'group_mode', 'info', 'init', 'dump'])
def help_command_message(message):

    if message.text.find('help') > 0:
        bot.send_message(message.chat.id, '\n'+ "Igor bot version " + BOT_VERSION +'\n'+'Command list:' +'\n'+
                         '/info - general information' +'\n'+
                         '/help - Help' +'\n'+
                         '/force - Force education by the real conversation log' +'\n'+
                         '/group_mode - switch group chat mode conversation' +'\n'+
                         '/init - initial conversation training'+'\n'+
                         '/dump - dump the current DB')

    if message.text.find('info') > 0:
        if get_chat_mode(message.chat.id):
	        bot.send_message(message.chat.id, "Igor bot version " + BOT_VERSION +'\n'+"Group chat mode " + 'ON')
        else:
            bot.send_message(message.chat.id, "Igor bot version " + BOT_VERSION + '\n' + "Group chat mode " + 'OFF')

    if message.text.find('init') > 0:
        init(message)

    if message.text.find('dump') > 0:
        dump(message)

    if message.text.find('force') > 0:
        force(message)

    if message.text.find('group_mode') > 0:
        if get_chat_mode(message.chat.id):
            set_chat_mode(message.chat.id, False)
            bot.send_message(message.chat.id, 'Group chat mode OFF')
        else:
            set_chat_mode(message.chat.id, True)
            bot.send_message(message.chat.id, 'Group chat mode ON')

@bot.message_handler(content_types=["text"])
def response_for_message(message):

    if get_chat_mode(message.chat.id):
        to_log_message = True
        for word in message.text.split():
            if word.lower() in ACCOST_KEYWORDS:
                to_log_message = False
                message_text = message.text.replace(word, '').strip()
                response = chatbot.get_response(message_text)
                bot.send_message(message.chat.id, response)

                break
        if to_log_message:
            log_message(message, message.text)

    else:
        log_message(message, message.text)

        response = chatbot.get_response(message.text)
        bot.send_message(message.chat.id, response)
        log_message(message, response.text, False)

if __name__ == '__main__':
    bot.polling(none_stop=True)