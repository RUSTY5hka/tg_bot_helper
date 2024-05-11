import requests

import config
from creds import get_creds  # модуль для получения токенов

class gpt:
    def __init__(self):
        self.URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        self.HEADERS = {"Content-Type": "application/json"}
        self.MAX_MODEL_TOKENS = config.MAX_MODEL_TOKENS
        self.iam_token, self.folder_id=get_creds()
    def process_resp(self, response):
        # Проверка статус кода
        if response.status_code == 200:
            # достаём ответ YandexGPT
            text = response.json()["result"]["alternatives"][0]["message"]["text"]
            return text
        else:
            raise RuntimeError(
                'Invalid response received: code: {}, message: {}'.format(
                    {response.status_code}, {response.text}))

    # Подсчитывает количество токенов в тексте
    # Подсчитывает количество токенов в сессии
    # messages - все промты из указанной сессии
    def count_tokens_in_dialog(self, messages):
        headers = {
            'Authorization': f'Bearer {self.iam_token}',
            'Content-Type': 'application/json'
        }
        data = {
            "modelUri": f"gpt://{self.folder_id}/yandexgpt/latest",
            "maxTokens": self.MAX_MODEL_TOKENS,
            "messages": []
        }
        # Проходимся по всем сообщениям и добавляем их в список
        for row in messages:
            data["messages"].append(
                {
                    "role": row["role"],
                    "text": row["text"]
                }
            )
        return len(requests.post(
                "https://llm.api.cloud.yandex.net/foundationModels/v1/tokenizeCompletion",
                json=data,
                headers=headers
            ).json()
                   )

    def make_headers(self):
        headers = {
            'Authorization': f'Bearer {self.iam_token}',
            'Content-Type': 'application/json'
        }
        return headers
    def make_json(self, messages):
        data = {
            "modelUri": f"gpt://{self.folder_id}/yandexgpt/latest",  # Адрес модели GPT
            "completionOptions": {  # Опции генерации текста
                "stream": False,  # Отключение потоковой передачи
                "temperature": 0.6,  # Температура для вариативности ответов
                "maxTokens": self.MAX_MODEL_TOKENS  # Максимальное количество токенов в ответе
            },
            "messages": []  # Список сообщений для истории
        }

        # Добавление сообщений из collection в данные запроса
        for row in messages:

            # Формирование сообщения для отправки
            data["messages"].append({
                "role": row["role"],  # Роль отправителя (пользователь или система)
                "text": row['text']  # Текст сообщения
            })
        return data
        # Отправка запроса
    def send_request(self, headers, data):
        response = requests.post(self.URL,
                                 headers=headers,
                                 json=data)
        return response