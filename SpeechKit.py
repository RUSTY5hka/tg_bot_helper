import requests
import config
import math
from creds import get_creds  # модуль для получения токенов

class Speechkit():
    def __init__(self):
        self.iam_token, self.folder_id=get_creds()

    def text_to_speech(self, text):
        # iam_token, folder_id для доступа к Yandex SpeechKit

        # Аутентификация через IAM-токен
        headers = {
            'Authorization': f'Bearer {self.iam_token}',
        }
        data = {
            'text': text,  # текст, который нужно преобразовать в голосовое сообщение
            'lang': 'ru-RU',  # язык текста - русский
            'voice': 'filipp',  # мужской голос Филиппа
            'folderId': self.folder_id,
        }
        # Выполняем запрос
        response = requests.post(
            'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize',
            headers=headers,
            data=data
        )
        if response.status_code == 200:
            return True, response.content  # возвращаем статус и аудио
        else:
            return False, "При запросе в SpeechKit возникла ошибка"


    def speech_to_text(self, data):
        # Указываем параметры запроса
        params = "&".join([
            "topic=general",  # используем основную версию модели
            f"folderId={self.folder_id}",
            "lang=ru-RU"  # распознаём голосовое сообщение на русском языке
        ])

        # Аутентификация через IAM-токен
        headers = {
            'Authorization': f'Bearer {self.iam_token}',
        }

        # Выполняем запрос
        response = requests.post(
            f"https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?{params}",
            headers=headers,
            data=data
        )

        # Читаем json в словарь
        decoded_data = response.json()
        # Проверяем, не произошла ли ошибка при запросе
        if decoded_data.get("error_code") is None:
            return True, decoded_data.get("result")  # Возвращаем статус и текст из аудио
        else:
            return False, "При запросе в SpeechKit возникла ошибка"

    def is_stt_block_limit(self, duration, all_blocks):

        # Переводим секунды в аудиоблоки
        audio_blocks = math.ceil(duration / 15)  # округляем в большую сторону
        # Функция из БД для подсчёта всех потраченных пользователем аудиоблоков
        all_blocks += audio_blocks

        # Проверяем, что аудио длится меньше 30 секунд
        if duration >= 30:
            msg = "SpeechKit STT работает с голосовыми сообщениями меньше 30 секунд"
            return False, msg

        # Сравниваем all_blocks с количеством доступных пользователю аудиоблоков
        if all_blocks >= config.MAX_USER_STT_BLOCKS:
            msg = f"Превышен общий лимит SpeechKit STT {config.MAX_USER_STT_BLOCKS}. Использовано {all_blocks} блоков. Доступно: {config.MAX_USER_STT_BLOCKS - all_blocks}"
            return False, msg

        return True, audio_blocks