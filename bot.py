# -*- coding: utf-8 -*-
import yaml
from datetime import datetime

import telebot
import openai

# Global variables
bot = None
chatgpt_model = None
bot_token = None
chatgpt_config_file = None
admin_chat = None
upload_time = datetime.now()

users_in_que = 0
conversations = {}

# Global constants
KEYWORDS = ("игорь,", "igor,", "пес,", "@igorva_dev_bot", "@igorva_bot")

CONVERSATION_LENGTH = 10
CHAT_GPT_MODEL_NAME = "gpt-3.5-turbo"
ERROR_MESSAGE = ''
BOT_VERSION = '2.1.1'
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
ERROR_MESSAGE = cfg['error_message']

# let's init the bot
bot = telebot.TeleBot(bot_token)
openai.api_key = chatgpt_token


class ChatGPT:
    """
    class for chatgpt model
    """    

    def ask(self, message, dialog_messages=[]) -> str:
        """
        Ask the chatgpt model

        Args:
            message (_type_): _description_
            dialog_messages (list, optional): _description_. Defaults to [].

        Raises:
            ValueError: _description_

        Returns:
            _type_: _description_
        """        

        answer = None

        while answer is None:

            try:

                messages = self._generate_prompt_messages_for_chatgpt_api(message, dialog_messages)
                r = openai.ChatCompletion.create(
                    model=CHAT_GPT_MODEL_NAME,
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

        prompt = "As an advanced chatbot named Igor, your primary goal is to assist users to the best of your ability. This may involve answering questions, providing helpful information, or completing tasks based on user input. In order to effectively assist users, it is important to be detailed and thorough in your responses. Use examples and evidence to support your points and justify your recommendations or solutions. Remember to always prioritize the needs and satisfaction of the user. Your ultimate goal is to provide a helpful and enjoyable experience for the user. If user asks you about programming or asks to write code do it for him."
        messages = [{"role": "system", "content": prompt}]

        for dialog_message in dialog_messages:
            messages.append({"role": "user", "content": dialog_message["user"]})
            messages.append({"role": "assistant", "content": dialog_message["bot"]})

        messages.append({"role": "user", "content": message})

        return messages

    def _postprocess_answer(self, answer):
        answer = answer.strip()
        return answer


def is_message_to_bot(message):

    chat_title = message.chat.title

    for word in message.text.split():

        if (word.lower() in KEYWORDS) or (chat_title is None):

            return True

    return False


def strip_message_text(message):

    message = message.lower()

    for word in KEYWORDS:
        message = message.replace(word, '')

    return message.strip()


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


@bot.message_handler(commands=['help', 'info'])
def help_command_message(message):

    if message.text.find('help') > 0:

        bot.send_message(message.chat.id,
                         "Igor bot version " + BOT_VERSION + '\n' + 
                         "Author: Denis Afanasev (@shamansw)" + '\n\n' +
                         'Command list:' + '\n' +
                         '/info - General information and status' + '\n' +
                         '/help - Help' + '\n\n' +
                         "Igor bot is a chatbot that uses the ChatGPT model to answer questions and carry on a conversation." + "\n" +
                         "Could be added to chats and groups and support context of the conversation." + "\n" +
                         "You can address the bot by typing @igor_bot or by typing Igor in the begining of message on English or Russian language.")

    if message.text.find('info') > 0:

        status = ""

        if users_in_que > 0:
            status = "In use"
        else:
            status = "Idle"

        bot.send_message(message.chat.id,
                        "Author: Denis Afanasev (@shamansw)" + '\n' +
                        "Igor bot version " + 
                        BOT_VERSION + '\n' + 
                        "ChatGPT model version: " + CHAT_GPT_MODEL_NAME + '\n\n' +
                        "Upload time: " + upload_time.strftime("%Y-%m-%d %H:%M:%S") + '\n' +
                        "Conversation count: " + str(len(conversations)) + '\n' +
                        "Users in que: " + str(users_in_que) + '\n' +
                         "Status: " + status)


@bot.message_handler(content_types=["text"])
def response_for_message(message):

    global users_in_que
    global conversations

    message_id = message.id
    chat = message.chat.id
    chat_title = message.chat.title
    user_full_name = message.from_user.full_name
    message_text = strip_message_text(message.text)
    response = ""
    conversation = conversations[chat] if chat in conversations else []

    if is_message_to_bot(message):

        '''
        if users_in_que > 0:
            
            try:
                bot.send_message(chat, user_full_name + ", я занят, задайте ваш вопрос попозже плз...")
            except Exception as e:
                pass

            break
        '''

        users_in_que += 1

        if chat_title is None:
            chat_title = "Private chat"

        try:

            bot.send_message(chat, user_full_name + ", вопрос принят, мне надо немного подумать...")
            bot.send_message(admin_chat, "Вопрос от " + user_full_name + " в чате " + chat_title + ": " + message_text)

            bot.send_chat_action(chat, 'typing')
            response = chatgpt_model.ask(message_text, conversation)

            bot.send_chat_action(chat, 'typing')
            bot.send_message(chat, response)

        except Exception as e:
            try:

                bot.send_message(chat, ERROR_MESSAGE)
                bot.send_message(admin_chat, str(e))

            except Exception as e:
                pass

        users_in_que -= 1

    conversation.append({"user": message_text, "bot": response})

    if len(conversation) > CONVERSATION_LENGTH:
        conversation.pop(0)

    conversations[chat] = conversation


if __name__ == '__main__':

    # init the bot
    init()

    bot.polling(none_stop=True)
