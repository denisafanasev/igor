# -*- coding: utf-8 -*-
import json
import yaml

import telebot
import openai
# from revChatGPT.V1 import Chatbot
# from revChatGPT.V3 import Chatbot

# Global variables
bot = None
chatgpt_model = None
bot_token = None
chatgpt_config_file = None
admin_chat = None

users_in_que = 0
conversations = {}

# Global constants
KEYWORDS = ("игорь,", "igor,", "пес,", "@igorva_dev_bot", "@igorva_bot")

ERROR_MESSAGE = 'Ops, something went wrong :( Pls Ask Denis to check asap!'
BOT_VERSION = '2.1.0'
CONFIG_FILE_NAME = "../config.yaml"

OPENAI_COMPLETION_OPTIONS = {
    "temperature": 0.7,
    "max_tokens": 1000,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0
}

# read config file
with open(CONFIG_FILE_NAME, "r") as f:
    cfg = yaml.safe_load(f)

bot_token = cfg['bot_token']
admin_chat = cfg['admin_chat']
chatgpt_token = cfg['chatgpt_token']

# let's init the bot
bot = telebot.TeleBot(bot_token)
openai.api_key = chatgpt_token


class ChatGPT:

    def ask(self, message, dialog_messages=[]):

        answer = None

        while answer is None:
            
            try:
                
                messages = self._generate_prompt_messages_for_chatgpt_api(message, dialog_messages)
                r = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    **OPENAI_COMPLETION_OPTIONS
                )
                answer = r.choices[0].message["content"]
            
            except openai.error.InvalidRequestError as e:  # too many tokens
                if len(dialog_messages) == 0:
                    raise ValueError("Dialog messages is reduced to zero, but still has too many tokens to make completion") from e

                # forget first message in dialog_messages
                dialog_messages = dialog_messages[1:]

        answer = self._postprocess_answer(answer)

        return answer

    def _generate_prompt_messages_for_chatgpt_api(self, message, dialog_messages):

        prompt = "As an advanced chatbot named Igor, your primary goal is to assist users to the best of your ability. This may involve answering questions, providing helpful information, or completing tasks based on user input. In order to effectively assist users, it is important to be detailed and thorough in your responses. Use examples and evidence to support your points and justify your recommendations or solutions. Remember to always prioritize the needs and satisfaction of the user. Your ultimate goal is to provide a helpful and enjoyable experience for the user. If user asks you about programming or asks to write code do not answer his question"
        messages = [{"role": "system", "content": prompt}]

        for dialog_message in dialog_messages:
            messages.append({"role": "user", "content": dialog_message["user"]})
            messages.append({"role": "assistant", "content": dialog_message["bot"]})

        messages.append({"role": "user", "content": message})

        return messages

    def _postprocess_answer(self, answer):
        answer = answer.strip()
        return answer


def init(message=None):
    """
    Init the bot and the chatgpt model

    Args:
        message (message, optional): message from user. Defaults to None.
    """

    global chatgpt_model
    global conversations

    conversations = {}

    if message is None:
        chat_id = admin_chat
    else:
        chat_id = message.chat.id

    bot.send_message(chat_id, 'ChatGPT initialization ...')

    try:
        chatgpt_model = ChatGPT()
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
                         '/ help - Help' + '\n')

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
    global conversations

    for word in message.text.split():

        message_id = message.id
        chat = message.chat.id
        chat_title = message.chat.title
        user_full_name = message.from_user.full_name

        if (word.lower() in KEYWORDS) or (chat_title is None):

            '''
            if users_in_que > 0:
                
                try:
                    bot.send_message(chat, user_full_name + ", я занят, задайте ваш вопрос попозже плз...")
                except Exception as e:
                    pass

                break
            '''

            users_in_que += 1

            if word.lower() in KEYWORDS:
                message_text = message.text.replace(word, '').strip()
            else:
                message_text = message.text.strip()

            response = ""

            if chat_title is None:
                chat_title = "Private chat"

            try:

                bot.send_chat_action(chat, 'typing')
                bot.send_message(chat, user_full_name + ", вопрос принят, мне надо немного подумать...")
                bot.send_message(admin_chat, "Вопрос от " + user_full_name + " в чате " + chat_title + ": " + message_text)
                
                conversation = conversations[chat] if chat in conversations else []
                
                response = chatgpt_model.ask(message_text, conversation)

                conversation.append({"user": message_text, "bot": response})

                if len(conversation) > 10:
                    conversation.pop(0)
                
                conversations[chat] = conversation

                bot.send_chat_action(chat, 'typing')
                bot.send_message(chat, response)

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
