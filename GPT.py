import telebot
from GPT_token import *
import requests

# Токен вашего бота от BotFather
TOKEN = '6909794689:AAHrYJnhlaLLgWdyyvq0fxoxhADC6mHereI'

# IAM-токен и ID папки для доступа к Yandex SpeechKit
IAM_TOKEN = f'{iam_token}'
FOLDER_ID = 'b1gh7qec08g3hugo7d7g'

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
def GPT():
	def generate_text(query):
		headers = {
			'Authorization': f'Bearer {IAM_TOKEN}',
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

	# Обработчик команды /start
	@bot.message_handler(commands=['start'])
	def start(message):
		bot.reply_to(message, 'Привет! Для начала работы введите /generate для генерации истории.')

	# Обработчик текстовых сообщений
	@bot.message_handler(func=lambda message: True)
	def handle_text(message):
		query = message.text
		generated_text = generate_text(query)
		bot.reply_to(message, generated_text)


# Функция для преобразования голосового сообщения в текст с помощью SpeechKit
@bot.message_handler(content_types=['voice'])
def voice_to_text(message):
	# Получаем информацию о голосовом сообщении
	file_info = bot.get_file(message.voice.file_id)
	file_path = file_info.file_path

	# Скачиваем аудиофайл
	file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
	audio_file = requests.get(file_url)

	# Отправляем "набирает сообщение" в чат
	bot.send_chat_action(message.chat.id, 'typing')

	# Параметры запроса к SpeechKit
	headers = {'Authorization': f'Bearer {IAM_TOKEN}'}
	files = {'file': audio_file.content}
	params = {'folderId': FOLDER_ID, 'lang': 'ru-RU'}  # Язык текста (русский)

	# Отправка запроса на распознавание речи
	response = requests.post('https://stt.api.cloud.yandex.net/speech/v1/stt:recognize', headers=headers, files=files,
							 params=params)

	# Обработка ответа
	if response.status_code == 200:
		text = response.json()['result']
		bot.reply_to(message, f"Распознанный текст:\n{text}")
	else:
		bot.reply_to(message, "Ошибка распознавания аудио")

# Функция для преобразования текста в голос с помощью SpeechKit
def text_to_voice(text):
	@bot.message_handler(commands=['tts'])
	def request_text(message):
		bot.send_message(message.chat.id, "Я готов к работе с вашим текстом. Пожалуйста, отправьте текст для озвучки.")

	# Функция для обработки текстовых сообщений после команды /tts
	@bot.message_handler(func=lambda message: True, content_types=['text'])
	def text_to_speech(message):
		# Отправляем "набирает сообщение" в чат
		bot.send_chat_action(message.chat.id, 'typing')

		# Получаем текст из сообщения пользователя
		text = message.text

		# Параметры запроса к SpeechKit
		data = {
			'text': text,
			'speed': 1.1,  # Скорость речи
			'emotion': 'good',  # Эмоциональная окраска
			'lang': 'ru-RU',  # Язык текста (русский)
			'voice': 'jane',  # Голос Джейн
			'folderId': FOLDER_ID,
		}
		headers = {'Authorization': f'Bearer {IAM_TOKEN}'}

		# Отправка запроса к SpeechKit
		response = requests.post('https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize', headers=headers,
								 data=data)

		# Обработка ответа
		if response.status_code == 200:
			# Отправка аудиосообщения пользователю
			bot.send_voice(message.chat.id, response.content)
		else:
			# Сообщение об ошибке, если запрос к SpeechKit завершился неудачно
			bot.reply_to(message, "При преобразовании текста в речь возникла ошибка")
# Запуск бота
bot.polling()