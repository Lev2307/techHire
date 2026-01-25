import uuid

from django.shortcuts import get_object_or_404

import requests
from celery import shared_task

from config.settings import TELEGRAM_BOT_TOKEN, PROXY_URL

@shared_task
def send_telegram_message(text: str, applicant_id: uuid.UUID):
    '''Таска для отправки уведомления пользователю в телеграм'''
    from .models import Applicant
    applicant = get_object_or_404(Applicant, id=applicant_id)
    chat_id = applicant.linked_telegram.chat_id
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, payload, proxies={'http': PROXY_URL})
    except Exception as e:
        print(f"Error sending message: {e}")