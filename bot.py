from DataBase import Data
from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup
import config
from SpeechKit import Speechkit
from GPT import gpt
import random
from creds import get_bot_token  # модуль для получения bot_token



Data().create_table(['id', 'user_id', 'gpt_tokens', 'stt_blocks', 'tts_symbol', 'role', 'content'], ['INTEGER PRIMARY KEY', 'INTEGER', 'INTEGER', 'INTEGER', 'INTEGER', 'TEXT', 'TEXT'])
bot = TeleBot(get_bot_token())
system_tokens=gpt().count_tokens_in_dialog(messages = [{'role': 'system', 'text': config.system_prompt}])
def create_keyboard(buttons_list):
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*buttons_list)
    return keyboard

@bot.message_handler(commands=['salto'])
def salto(message):
    number_gif=random.randint(1,len(config.salto)-1)
    directory='GIFs/backflip'+str(number_gif)+'.gif'
    img = open(directory, 'rb')
    bot.send_video(message.chat.id, img, None, 'Text')
    img.close()

@bot.message_handler(commands=['start'])
def start(message):
    user_name = message.from_user.first_name
    bot.send_message(message.chat.id,
                     text=f"Привет, {user_name}! Я милый бот-помощник для чего-то!\n"
                          f"Ты можешь у меня что то спросить а я на это отвечу.\n"
                          "/help-тут все команды, ну и мини тутор по использованию бота",
                     reply_markup=create_keyboard(["/new_story", '/help']))


@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.from_user.id,
                     text=f"/salto-самая важная команда\n/tts-после ввода команды напиши текст а в ответ тебе пришлют озвучку,\n/stt-пришли голосовое сообщение а в ответ получи текст\nЕсли ты просто напишешь сообщение то ты начнёшь общатся с YandexGPT",
                     reply_markup=create_keyboard(["/new_story"]))

@bot.message_handler(commands=['tts'])
def tts_handler(message):
    sum_tts_symbol=Data().select_from_table(['SUM(tts_symbol)'], ['user_id'], [str(message.from_user.id)])
    if sum_tts_symbol>=config.MAX_USER_TTS_SYMBOL:
        bot.send_message(message.chat.id, "ливай отсюда")
        return
    bot.send_message(message.chat.id, "введи текст который надо превратить в  аудио")
    bot.register_next_step_handler(message, tts)

def tts(message):
    user_id = message.from_user.id
    if message.content_type != 'text':
        bot.send_message(user_id, "это no text")
    text = message.text
    Data().insert_row(['user_id', 'tts_symbol'], [user_id, len(text)])
    audio=Speechkit().text_to_speech(text)
    if audio[0]==False:
        bot.send_message(user_id, "чё-то не так")
        return
    bot.send_voice(user_id, audio[1], reply_markup=create_keyboard(["/tts"]))


@bot.message_handler(commands=['stt'])
def stt_handler(message):
    user_id = message.from_user.id
    sum_stt_blocks = Data().select_from_table(['SUM(stt_blocks)'], ['user_id'], [str(message.from_user.id)])
    if sum_stt_blocks>=config.MAX_USER_STT_BLOCKS:
        bot.send_message(user_id, 'купи блоки кирпича или ливай отсюда')
    bot.send_message(user_id, 'Отправь голосовое сообщение, чтобы я его распознал!')
    bot.register_next_step_handler(message, stt)


# Переводим голосовое сообщение в текст после команды stt
def stt(message):
    user_id = message.from_user.id
    # Проверка, что сообщение действительно голосовое
    if not message.voice:
        return
    duration=message.voice.duration
    all_blocks=Data().select_from_table(['SUM(stt_blocks)'], ['user_id'], [str(message.from_user.id)])
    audio_blocks=Speechkit().is_stt_block_limit(duration, all_blocks)
    if audio_blocks[0]:
        Data().insert_row(['user_id', 'stt_blocks'], [user_id, audio_blocks[1]])
    else:
        bot.send_message(user_id, audio_blocks[1])
        return
    file_id = message.voice.file_id  # получаем id голосового сообщения
    file_info = bot.get_file(file_id)  # получаем информацию о голосовом сообщении
    file = bot.download_file(file_info.file_path)  # скачиваем голосовое сообщение
    status, text = Speechkit().speech_to_text(file)  # преобразовываем голосовое сообщение в текст
    bot.send_message(user_id, text)

@bot.message_handler(content_types=['text', 'voice'])
def get_message(message):
    user_id = message.from_user.id
    sum_tokens=Data().select_from_table(['SUM(gpt_tokens)'], ['user_id'], [str(user_id)])
    if sum_tokens>=config.MAX_GPT_TOKENS_FOR_USER - system_tokens:
        bot.send_message(user_id, 'токены закончились')
        return

    if message.voice:
        duration = message.voice.duration
        all_blocks = Data().select_from_table(['SUM(stt_blocks)'], ['user_id'], [str(user_id)])
        audio_blocks = Speechkit().is_stt_block_limit(duration, all_blocks)
        if audio_blocks[0]:
            Data().insert_row(['user_id', 'stt_blocks'], [user_id, audio_blocks[1]])
        else:
            bot.send_message(user_id, audio_blocks[1])
            return
        file_id = message.voice.file_id  # получаем id голосового сообщения
        file_info = bot.get_file(file_id)  # получаем информацию о голосовом сообщении
        file = bot.download_file(file_info.file_path)  # скачиваем голосовое сообщение
        status, text = Speechkit().speech_to_text(file)  # преобразовываем голосовое сообщение в текст
    else:
        text=message.text
    remaining_tokens=config.MAX_GPT_TOKENS_FOR_USER-sum_tokens
    messages = [{'role': 'user', 'text': text}]

    user_tokens = gpt().count_tokens_in_dialog(messages)

    messages = [{'role': 'system', 'text': config.system_prompt},
                {'role': 'user', 'text': text}]

    if user_tokens>remaining_tokens:
        bot.send_message(user_id, 'сократи запрос', reply_markup=create_keyboard(["/start"]))
        return
    headers = gpt().make_headers()
    json = gpt().make_json(messages)
    resp = gpt().send_request(headers, json)
    response = gpt().process_resp(resp)
    messages.append({'role': 'assistant', 'text': response})
    messages_gpt = [{'role': 'assistant', 'text': response}]
    assistant_tokens = gpt().count_tokens_in_dialog(messages_gpt)
    remaining_tokens = remaining_tokens - assistant_tokens - system_tokens

    Data().insert_row(['user_id','role', 'gpt_tokens', 'content'], [str(user_id), 'system', str(system_tokens), config.system_prompt])
    Data().insert_row(['user_id','role', 'gpt_tokens', 'content'], [str(user_id),'user', str(user_tokens), text])
    Data().insert_row(['user_id','role', 'gpt_tokens', 'content'], [str(user_id), 'assistant', str(assistant_tokens), response])

    if message.voice:
        Data().insert_row(['user_id', 'tts_symbol'], [user_id, len(text)])
        audio = Speechkit().text_to_speech(response)
        if audio[0] == False:
            bot.send_message(user_id, "чё-то не так")
            return
        bot.send_voice(user_id, audio[1])
    else:
        bot.send_message(user_id, response)
    bot.register_next_step_handler(message, continue_dialog, messages, remaining_tokens)





def continue_dialog(message, messages,remaining_tokens):
    user_id = message.from_user.id
    if not message.voice and not message.text:
        return
    if message.text=='Закончить':
        return
    if remaining_tokens<=0:
        bot.send_message(user_id, 'кончились токены')
        return
    if message.voice:
        duration = message.voice.duration
        all_blocks = Data().select_from_table(['SUM(stt_blocks)'], ['user_id'], [str(user_id)])
        audio_blocks = Speechkit().is_stt_block_limit(duration, all_blocks)
        if audio_blocks[0]:
            Data().insert_row(['user_id', 'stt_blocks'], [user_id, audio_blocks[1]])
        else:
            bot.send_message(user_id, audio_blocks[1])
            return
        file_id = message.voice.file_id  # получаем id голосового сообщения
        file_info = bot.get_file(file_id)  # получаем информацию о голосовом сообщении
        file = bot.download_file(file_info.file_path)  # скачиваем голосовое сообщение
        status, text = Speechkit().speech_to_text(file)  # преобразовываем голосовое сообщение в текст
    else:
        text=message.text
    user_tokens=gpt().count_tokens_in_dialog([{'role': 'user', 'text': text}])
    if remaining_tokens<gpt().count_tokens_in_dialog(messages)+ user_tokens:
        bot.send_message(user_id, 'сократи запрос')
        bot.register_next_step_handler(message, continue_dialog, messages, remaining_tokens)
        return
    messages.insert(1, {'role': 'user', 'text': text})

    headers = gpt().make_headers()
    json = gpt().make_json(messages)
    resp = gpt().send_request(headers, json)
    response = gpt().process_resp(resp)

    messages_gpt = [{'role': 'assistant', 'text': response}]
    assistant_tokens = gpt().count_tokens_in_dialog(messages_gpt)
    messages.insert(2, {'role': 'assistant', 'text': response})
    remaining_tokens = remaining_tokens - assistant_tokens - system_tokens

    Data().insert_row(['user_id', 'role', 'gpt_tokens', 'content'], [str(user_id), 'user', str(user_tokens), text])
    Data().insert_row(['user_id', 'role', 'gpt_tokens', 'content'],[str(user_id), 'assistant', str(assistant_tokens), response])

    bot.send_message(user_id, response, create_keyboard('Закончить'))
    bot.register_next_step_handler(message, continue_dialog,messages,remaining_tokens)
bot.polling()