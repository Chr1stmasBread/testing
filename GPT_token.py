import requests
import json
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(filename='token_refresh.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def get_iam_token():
    metadata_url = "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token"
    headers = {'Metadata-Flavor': 'Google'}

    try:
        response = requests.get(metadata_url, headers=headers)
        if response.status_code == 200:
            token_data = response.json()
            return token_data
        else:
            logging.error("Ошибка при получении IAM токена. Статус код: %d", response.status_code)
            return None
    except Exception as e:
        logging.error("Произошла ошибка при получении IAM токена:", e)
        return None


def check_and_refresh_token():
    # Инициализируем переменную iam_token
    iam_token = None

    token_data = get_iam_token()
    if token_data:
        expires_at = datetime.fromtimestamp(token_data.get('expires_at', 0))  # Проверка наличия ключа
        current_time = datetime.now()
        time_remaining = expires_at - current_time

        logging.info("Время до истечения токена: %s", time_remaining)

        if time_remaining.total_seconds() < 60:
            logging.info("Токен истек или истекает в течение минуты. Обновляем токен.")
            iam_token = refresh_token()
    else:
        logging.error("Не удалось получить IAM токен.")

    # Возвращаем значение переменной iam_token, даже если оно равно None
    return iam_token


def refresh_token():
    new_token_data = get_iam_token()
    if new_token_data and 'access_token' in new_token_data:  # Проверка наличия ключа 'access_token'
        logging.info("Токен успешно обновлен.")
        return new_token_data['access_token']
    else:
        logging.error("Не удалось обновить токен.")
        return None


# Обновляем IAM токен
iam_token = check_and_refresh_token()