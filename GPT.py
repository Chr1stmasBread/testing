import telebot
import requests
from GPT_token import iam_token
from config_last import TOKEN, FOLDER_ID

# Инициализация бота
bot = telebot.TeleBot(TOKEN)

# Словарь для хранения сообщений переписки с каждым пользователем
message_history = {}

# Лимиты на использование ресурсов
resource_limits = {
    'gpt_tokens_limit': 1000,          # Лимит токенов для GPT
    'speechkit_characters_limit': 30000  # Лимит символов для SpeechKit
}

# Функция для отправки текста в Yandex GPT и получения ответа
def generate_text(query):
    try:
        headers = {
            'Authorization': f'Bearer {iam_token}',
            'Content-Type': 'application/json'
        }
        data = {
            "modelUri": f"gpt://{FOLDER_ID}/yandexgpt/latest",
            "completionOptions": {
                "stream": False,
                "temperature": 0.8,
                "maxTokens": "2000"
            },
            "messages": [
                {
                    "role": "user",
                    "text": query
                }
            ]
        }

        response = requests.post("https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                                 headers=headers,
                                 json=data)

        if response.status_code == 200:
            text = response.json()["result"]["alternatives"][0]["message"]["text"]
            return text
        else:
            error_message = 'Invalid response received: code: {}, message: {}'.format(response.status_code,
                                                                                      response.text)
            return error_message
    except Exception as e:
        return str(e)

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 'Привет! Для начала работы введите /tts, если Вы хотите перевести текст в аудио формат. Либо /generate, чтобы начать работу с обычным GPT.')

# Обработчик текстовых сообщений
@bot.message_handler(commands=['generate'])
def handle_text(message):
    bot.reply_to(message, "Введите текст для обработки GPT")
    bot.register_next_step_handler(message, process_text)

def process_text(message):
    query = message.text
    generated_text = generate_text(query)
    bot.reply_to(message, generated_text)

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    bot.reply_to(message, "Распознаю голосовое сообщение...")
    bot.register_next_step_handler(message, voice_to_text)

# Функция для преобразования голосового сообщения в текст с помощью SpeechKit
@bot.message_handler(content_types=['voice'])
def voice_to_text(message):
    try:
        file_info = bot.get_file(message.voice.file_id)
        file_url = file_info.file_path

        response = requests.get(f"https://api.telegram.org/file/bot{TOKEN}/{file_url}")

        if response.status_code == 200:
            headers = {'Authorization': f'Bearer {iam_token}'}
            files = {'file': response.content}
            params = {'folderId': FOLDER_ID, 'lang': 'ru-RU'}
            response = requests.post('https://stt.api.cloud.yandex.net/speech/v1/stt:recognize',
                                     headers=headers,
                                     files=files,
                                     params=params)

            if response.status_code == 200:
                text = response.json()['result']
                bot.reply_to(message, f"Распознанный текст:\n{text}")
            else:
                bot.reply_to(message, "Ошибка распознавания аудио")
        else:
            bot.reply_to(message, "Ошибка загрузки аудиофайла")
    except Exception as e:
        bot.reply_to(message, f"Ошибка при обработке голосового сообщения: {str(e)}")

# Функция для преобразования текста в голос с помощью SpeechKit
@bot.message_handler(commands=['tts'])
def request_text(message):
    bot.send_message(message.chat.id, "Я готов к работе с вашим текстом. Пожалуйста, отправьте текст для озвучки.")
    bot.register_next_step_handler(message, text_to_speech)

def text_to_speech(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        text = message.text
        data = {
            'text': text,
            'speed': 1.1,
            'emotion': 'good',
            'lang': 'ru-RU',
            'voice': 'jane',
            'folderId': FOLDER_ID,
        }
        headers = {'Authorization': f'Bearer {iam_token}'}
        response = requests.post('https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize',
                                 headers=headers,
                                 data=data)

        if response.status_code == 200:
            bot.send_voice(message.chat.id, response.content)
        else:
            bot.reply_to(message, "При преобразовании текста в речь возникла ошибка")
    except Exception as e:
        bot.reply_to(message, f"Ошибка при преобразовании текста в речь: {str(e)}")

# Запуск бота
bot.polling()