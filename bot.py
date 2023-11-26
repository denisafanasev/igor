# -*- coding: utf-8 -*-
import os
import yaml
import pickle
from datetime import datetime, timedelta

import telebot

from chatgpt_adapter import ChatGPTAdapter
from article_adapter import ArticleAdapter
from utility_adapter import UtilityAdapter
from donater_adapter import DonaterAdapter
import config

# Global variables
bot = None
bot_token = None

chatgpt_model = None
admin_chat = None
upload_time = datetime.now()

users_in_que = 0
error_message = ""
donate_message_link = ""
conversations = {}
tokens_counter = {}
questions_counter = {}
donate_messages_count = 0
spam_interval = 0
max_conversation_length = 0

# let's init the bot
with open(config.CONFIG_FILE_NAME, "r") as f:
    cfg = yaml.safe_load(f)

bot_token = cfg['bot_token']
bot = telebot.TeleBot(bot_token)
utility_adapter = UtilityAdapter()
donater_adapter = DonaterAdapter()


def save_state():
    """
    Save state of the bot to a dump file
    """

    file_name = config.SYSTEM_STATE_FILE_NAME

    with open(file_name, 'wb') as f:
        pickle.dump({'conversations': conversations,
                     'tokens_counter': tokens_counter,
                     'questions_counter': questions_counter,
                     'donate_messages_count': donate_messages_count}, f)


def load_state():
    """
    Load state of the bot from a dump file
    """

    global conversations
    global tokens_counter
    global questions_counter
    global donate_messages_count

    file_name = config.SYSTEM_STATE_FILE_NAME
    
    if os.path.exists(file_name):
        with open(file_name, 'rb') as f:
            system_state = pickle.load(f)
        
        conversations = system_state['conversations']
        tokens_counter = system_state['tokens_counter']
        questions_counter = system_state['questions_counter']
        donate_messages_count = system_state['donate_messages_count']


def should_donate_remind(tokens, questions):
    """
    Check if we should remind about donation

    Args:
        tokens (_type_): _description_
        questions (_type_): _description_

    Returns:
        boolean: True or False
    """

    interval = 100 / (1 + (tokens/max_conversation_length) * 9 + (questions/10000) * 0.9)
    return questions % interval < 1


def send_donate_remind(chat_id):
    """
    Send donate remind message
    """

    global donate_messages_count

    utility_adapter = UtilityAdapter()

    bot.send_message(chat_id, 'Дорогой друг, я для тебя ответил уже на ' + utility_adapter.format_number(questions_counter[chat_id]) + 
                     ' вопросов и истратил на это ' + utility_adapter.format_number(tokens_counter[chat_id]) + 
                     ' токенов. Поддержи развитие проекта, подпишись на канал и не забывай про донаты на оплату инфраструктуры: ' + donate_message_link)

    donate_messages_count += 1


def force_message(message_text):
    """
    Force message to all conversations

    Args:
        message_text (str): message text

    Returns:
        int: number of messages sent
    """

    messages_sent = 0

    for conversation in conversations:
        bot.send_message(conversation, message_text)
        messages_sent += 1

    return messages_sent


def init():
    """
    Init the bot and the chatgpt model
    """

    global chatgpt_model

    global conversations
    global tokens_counter
    global questions_counter
    global error_message
    global donate_message_link
    global spam_interval
    global max_conversation_length

    global admin_chat

    conversations = {}
    tokens_counter = {}
    questions_counter = {}

    # read config file
    with open(config.CONFIG_FILE_NAME, "r") as f:
        cfg = yaml.safe_load(f)

    admin_chat = cfg['admin_chat']
    chatgpt_token = cfg['chatgpt_token']
    error_message = cfg['error_message']
    donate_message_link = cfg['donate_message_link']
    spam_interval = cfg['spam_interval']
    max_conversation_length = cfg['max_conversation_length']

    chat_id = admin_chat

    bot.send_message(chat_id, 'Config loaded')

    load_state()
    bot.send_message(chat_id, 'System state loaded')

    bot.send_message(chat_id, 'ChatGPT initialization ...')

    try:
        chatgpt_model = ChatGPTAdapter(chatgpt_token)
        bot.send_message(chat_id, 'ChatGPT initialization completed')
        bot.send_message(chat_id, 'Bot initialization completed')

    except Exception as error:
        bot.send_message(chat_id, error)


def converation_tokens(conversation):
    """
    Get number of tokens from conversation

    Returns:
        int: number of tokens
    """

    conversation_tokens = 0

    for message in conversation:
        conversation_tokens += utility_adapter.num_tokens_from_string(message["user"], chatgpt_model.get_model_name())
        conversation_tokens += utility_adapter.num_tokens_from_string(message["bot"], chatgpt_model.get_model_name())

    return conversation_tokens


@bot.message_handler(commands=['help', 'info', 'load', 'save', 'force'])
def help_command_message(message):
    """
    Help command messages
    """

    chat_id = message.chat.id

    if message.text.find('help') > 0:

        bot.send_message(message.chat.id,
                         "Igor bot version " + config.BOT_VERSION + '\n' + 
                         "Author: Denis Afanasev (@shamansw)" + '\n\n' +
                         "Model name: " + chatgpt_model.get_model_name() + '\n' +
                         'Command list:' + '\n' +
                         '/info - General information and status' + '\n' +
                         '/help - Help' + '\n\n' +
                         "News and general info: https://t.me/cdo_club" + '\n' +
                         "Donations for support and development: " + donate_message_link + '\n\n' +
                         "Igor bot is a chatbot that uses the ChatGPT model to answer questions and carry on a conversation." + "\n" +
                         "Could be added to chats and groups and support context of the conversation." + "\n" +
                         "You can address the bot by typing @@IgorVA_bot or by typing Igor in the begining of message on English or Russian language.")

    if message.text.find('info') > 0:

        status = ""

        if users_in_que > 0:
            status = "In use"
        else:
            status = "Idle"

        bot.send_message(message.chat.id,
                        "Author: Denis Afanasev (@shamansw)" + '\n' +
                        "Igor bot version " + 
                        config.BOT_VERSION + '\n' + 
                        "ChatGPT model version: " + chatgpt_model.get_model_name() + '\n\n' +
                        "Upload time: " + upload_time.strftime("%Y-%m-%d %H:%M:%S") + '\n\n' +
                        "Conversation count: " + str(len(conversations)) + '\n' +
                        "Tokens count: " + str(sum(tokens_counter.values())) + '\n' +
                        "Questions count: " + str(sum(questions_counter.values())) + '\n' +
                        "Donate messages count: " + str(donate_messages_count) + '\n' +
                        "Users in que: " + str(users_in_que) + '\n' +
                        "Status: " + status)
    
    if message.text.find('load') > 0:
        if chat_id == admin_chat:
            init()
        else:
            bot.send_message(message.chat.id, "This command can be used only by the bot administrator")
    
    if message.text.find('save') > 0:
        if chat_id == admin_chat:
            save_state()
            bot.send_message(message.chat.id, "Save state completed")
        else:
            bot.send_message(message.chat.id, "This command can be used only by the bot administrator")
    
    if message.text.find('force') > 0:
        if chat_id == admin_chat:
            force_massage_text = message.text.replace('/force ', '')
            messages_sent = force_message(force_massage_text)
            bot.send_message(message.chat.id, "Number of distrubuted messages: " + str(messages_sent))
        else:
            bot.send_message(message.chat.id, "This command can be used only by the bot administrator")


@bot.message_handler(content_types=["text"])
def response_for_message(message):

    global users_in_que
    global conversations
    global tokens_counter
    global questions_counter

    chat = message.chat.id
    chat_title = message.chat.title
    user_full_name = message.from_user.full_name
    username = message.from_user.username
    message_text = utility_adapter.strip_message_text(message.text)
    response = ""

    # get conversation history and article
    conversation = conversations[chat] if chat in conversations else []
    token_counter = tokens_counter[chat] if chat in tokens_counter else 0
    question_counter = questions_counter[chat] if chat in questions_counter else 0
                

    if utility_adapter.is_message_to_bot(message):

        if chat_title is None:
            chat_title = "Private chat"
        
        bot.send_message(admin_chat, "Вопрос от " + user_full_name + " в чате " + chat_title + ": " + message_text)
        bot.send_message(chat, user_full_name + ", вопрос принят, мне надо немного подумать...")
        bot.send_chat_action(chat, 'typing')

        # check if user is donater
        if not donater_adapter.is_donater(username):

            last_conversation_time = datetime(1970, 1, 1, 0, 0, 0)

            if len(conversation) > 0:
                if "time" in conversation[-1].keys():
                    last_conversation_time = conversation[-1]["time"]

                    if (datetime.now() - last_conversation_time).total_seconds() < spam_interval:
                        bot.send_message(chat, "Дорогой " + user_full_name + ", не вижу тебя в списке пользователей, поддержавших мою работу через donats, " +
                                        "поэтому могу отвечать тебе не раньше чем один раз в " + str(spam_interval) + " секунд. Попробуй задать вопрос попозже или поддержки сервис: " + donate_message_link)
                        bot.send_message(admin_chat, "Пользователь " + user_full_name + " пытается спамить в чате " + chat_title)
                        return


        users_in_que += 1

        # if there is a link in the text, we will try to replace the link with the text of the article
        links = utility_adapter.get_links(message_text)

        for link in links:

            bot.send_chat_action(chat, 'typing')

            try:
                article_adapter = ArticleAdapter(link)
                article_text = article_adapter.article.text
            except Exception as error:
                bot.send_message(admin_chat, str(error))
                article_text = "эта статья мне не доступна, при ее получении произошла ошибка " + str(error)

            if utility_adapter.num_tokens_from_string(article_text, chatgpt_model.get_model_name()) < 8192:
                message_text = message_text.replace(link, article_text)
            else:
                message_text = message_text.replace(link, "эта статья слишком длинная (больше 8192 токенов) и ее текст я не могу обработать")

        if utility_adapter.num_tokens_from_string(message_text, chatgpt_model.get_model_name()) > max_conversation_length:
            message_text = "этот вопрос слишком длинный (больше 16384 токенов) и я не могу его обработать"
        
        bot.send_chat_action(chat, 'typing')

        message_text_tokens = utility_adapter.num_tokens_from_string(message_text, chatgpt_model.get_model_name())

        while (converation_tokens(conversation) + message_text_tokens > max_conversation_length) and (len(conversation) > 0):
            conversation = conversation[1:]

        # count tokens and questions number
        token_counter = token_counter + converation_tokens(conversation) + message_text_tokens
        question_counter += 1

        bot.send_chat_action(chat, 'typing')

        try:
            response = chatgpt_model.ask(message_text, conversation)

        except Exception as error:
            bot.send_message(chat, error_message)
            bot.send_message(admin_chat, str(error))
            
        bot.send_chat_action(chat, 'typing')

        conversation.append({"user": message_text, "bot": response, "time": datetime.now()})

        conversations[chat] = conversation
        tokens_counter[chat] = token_counter
        questions_counter[chat] = question_counter

        bot.send_message(chat, response)

        # check for donate message

        if should_donate_remind(converation_tokens(conversation), question_counter):
            send_donate_remind(chat)

        users_in_que -= 1


if __name__ == '__main__':

    # init the bot
    init()
    bot.polling(none_stop=True)
