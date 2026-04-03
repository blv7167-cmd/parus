#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import smtplib
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

# Конфигурация
SMTP_SERVER = "smtp.yandex.ru"
SMTP_PORT = 465
SMTP_USERNAME = "blv716@yandex.ru"  # ваш email
SMTP_PASSWORD = "ggzcnbgtyttreusy"
TARGET_EMAIL = "blv716@yandex.ru"

def send_email(data):
    """Отправка письма с данными формы"""
    try:
        # Создаем письмо
        msg = MIMEMultipart("alternative")
        msg["Subject"] = Header(f"Новая заявка с сайта", "utf-8")
        msg["From"] = SMTP_USERNAME
        msg["To"] = TARGET_EMAIL

        # Формируем тело письма
        text = f"""
Новая заявка с сайта!

Имя: {data.get('name', 'Не указано')}
Телефон: {data.get('phone', 'Не указан')}
Вопрос: {data.get('question', 'Без вопроса')}
Страница: {data.get('page', 'Неизвестно')}
Время: {data.get('timestamp', 'Неизвестно')}

---
Это автоматическое сообщение, отвечать на него не нужно.
        """

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="font-family: Arial, sans-serif;">
    <h2>🔔 Новая заявка с сайта!</h2>
    <table style="border-collapse: collapse; width: 100%; max-width: 500px;">
        <tr style="background-color: #f0f7fc;">
            <td style="padding: 8px; border: 1px solid #ccc;"><strong>👤 Имя</strong></td>
            <td style="padding: 8px; border: 1px solid #ccc;">{data.get('name', 'Не указано')}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ccc;"><strong>📞 Телефон</strong></td>
            <td style="padding: 8px; border: 1px solid #ccc;"><a href="tel:{data.get('phone', '')}">{data.get('phone', 'Не указан')}</a></td>
        </tr>
        <tr style="background-color: #f0f7fc;">
            <td style="padding: 8px; border: 1px solid #ccc;"><strong>💬 Вопрос</strong></td>
            <td style="padding: 8px; border: 1px solid #ccc;">{data.get('question', 'Без вопроса')}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ccc;"><strong>📄 Страница</strong></td>
            <td style="padding: 8px; border: 1px solid #ccc;">{data.get('page', 'Неизвестно')}</td>
        </tr>
        <tr style="background-color: #f0f7fc;">
            <td style="padding: 8px; border: 1px solid #ccc;"><strong>🕐 Время</strong></td>
            <td style="padding: 8px; border: 1px solid #ccc;">{data.get('timestamp', 'Неизвестно')}</td>
        </tr>
    </table>
    <p style="color: #666; font-size: 12px; margin-top: 20px;">---<br>Это автоматическое сообщение, отвечать на него не нужно.</p>
</body>
</html>
        """

        part_text = MIMEText(text, "plain", "utf-8")
        part_html = MIMEText(html, "html", "utf-8")

        msg.attach(part_text)
        msg.attach(part_html)

        # Отправляем письмо
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        return True, "Email sent"

    except Exception as e:
        return False, str(e)


def parse_post_data(environ):
    """Парсинг POST-данных из environ"""
    try:
        content_length = int(environ.get("CONTENT_LENGTH", 0))
    except ValueError:
        content_length = 0

    if content_length == 0:
        return {}

    body = environ["wsgi.input"].read(content_length).decode("utf-8")
    return urllib.parse.parse_qs(body, keep_blank_values=True)


def application(environ, start_response):
    """WSGI-приложение"""
    method = environ.get("REQUEST_METHOD", "")
    path = environ.get("PATH_INFO", "")

    # Отправляем CORS-заголовки для всех ответов
    headers = [
        ("Access-Control-Allow-Origin", "*"),
        ("Access-Control-Allow-Methods", "POST, OPTIONS"),
        ("Access-Control-Allow-Headers", "Content-Type"),
    ]

    # Обработка preflight-запроса OPTIONS
    if method == "OPTIONS":
        start_response("204 No Content", headers)
        return [b""]

    # Только POST-запросы на /send_message
    if method == "POST" and path == "/send_message":
        # Парсим данные
        post_data = parse_post_data(environ)
        
        # Извлекаем поля (parse_qs возвращает списки)
        data = {
            "name": post_data.get("name", [""])[0],
            "phone": post_data.get("phone", [""])[0],
            "question": post_data.get("question", [""])[0],
            "page": post_data.get("page", [""])[0],
            "timestamp": post_data.get("timestamp", [""])[0],
        }

        # Отправляем письмо
        success, result = send_email(data)

        if success:
            response_body = {"status": "success", "message": "Заявка отправлена"}
            status = "200 OK"
        else:
            response_body = {"status": "error", "message": result}
            status = "500 Internal Server Error"

        # Формируем JSON-ответ
        import json
        response_json = json.dumps(response_body, ensure_ascii=False).encode("utf-8")
        headers.append(("Content-Type", "application/json; charset=utf-8"))
        headers.append(("Content-Length", str(len(response_json))))

        start_response(status, headers)
        return [response_json]

    # 404 для всех остальных путей
    start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
    return [b"404 Not Found"]
    # def application(environ, start_response):
    # """
    # environ: словарь с:
    #     - REQUEST_METHOD: GET, POST и т.д.
    #     - PATH_INFO: путь запроса
    #     - QUERY_STRING: параметры после ?
    #     - HTTP_*: заголовки запроса
    
    # start_response: функция, принимающая (status, headers, exc_info=None)
    
    # Возвращает: итерируемый объект с байтовыми строками
    # """
    # try:
    #     if environ['PATH_INFO'] <> '/send_message':
    #         start_response('200 OK', [('Content-Type', 'text/plain')])
    #         return [environ['PATH_INFO'].encode('utf-8')]
    #     body_length = int(environ.get("CONTENT_LENGTH", 0))
    #     inbody = environ["wsgi.input"].read(body_length)
    #     import smtplib
    #     from email.mime.text import MIMEText
    #     from email.mime.multipart import MIMEMultipart
        
    #     # Настройки SMTP сервера (пример для Яндекс.Почты)
    #     SMTP_SERVER = "smtp.yandex.ru"
    #     SMTP_PORT = 465  # SSL
    #     SMTP_USER = "blv716@yandex.ru"
    #     SMTP_PASSWORD = "ggzcnbgtyttreusy"
        
    #     # Кому и от кого
    #     FROM = "blv716@yandex.ru"
    #     TO = "blv716@yandex.ru"
    #     SUBJECT = "Тестовое2 письмо из Python"
        
    #     # Создаём письмо
    #     msg = MIMEMultipart()
    #     msg["From"] = FROM
    #     msg["To"] = TO
    #     msg["Subject"] = SUBJECT
    #     # Текст письма
    #     body = inbody
    #     msg.attach(MIMEText(body, "plain", "utf-8"))
    #     # Отправка
    #     with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
    #         server.login(SMTP_USER, SMTP_PASSWORD)
    #         server.send_message(msg)
    #     #print("Письмо успешно отправлено!")
    
    #     # 1. Устанавливаем статус и заголовки
    #     start_response('200 OK', [('Content-Type', 'text/plain')])
        
    #     # 2. Возвращаем тело ответа
    #     return [b'Hello, World!\n']
    # except Exception as err:
    #     return [f'{err}']