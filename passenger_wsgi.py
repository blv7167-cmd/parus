#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import smtplib
import urllib.parse

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

# Импортируем Kindle Chat хендлер
from kindle_chat_handler import handle_kindle_chat

# Конфигурация
SMTP_SERVER = "smtp.yandex.ru"
SMTP_PORT = 465
SMTP_USERNAME = "blv716@yandex.ru"
SMTP_PASSWORD = "ggzcnbgtyttreusy"
TARGET_EMAIL = "blv716@yandex.ru"


def send_email(data, form_type="callback"):
    """Отправка письма с данными формы"""
    try:
        msg = MIMEMultipart("alternative")
        
        if form_type == "callback":
            msg["Subject"] = Header("🔔 Новая заявка с сайта (обратный звонок)", "utf-8")
            text_template = f"""
Новая заявка на обратный звонок!

Имя: {data.get('name', 'Не указано')}
Телефон: {data.get('phone', 'Не указан')}
Вопрос: {data.get('question', 'Без вопроса')}
Страница: {data.get('page', 'Неизвестно')}
Время: {data.get('timestamp', 'Неизвестно')}

---
Это автоматическое сообщение, отвечать на него не нужно.
            """
            html_template = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif;">
    <h2>🔔 Новая заявка на обратный звонок!</h2>
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
        else:  # review
            msg["Subject"] = Header("📝 Новый отзыв с сайта", "utf-8")
            text_template = f"""
Новый отзыв с сайта!

Имя: {data.get('name', 'Аноним')}
Контакт: {data.get('contact', 'Не указан')}
Роль: {data.get('role', 'Не указана')}
Оценка: {data.get('rating', 'Нет')} ★
Текст отзыва:
{data.get('message', 'Без текста')}

Страница: {data.get('page', 'Неизвестно')}
Время: {data.get('timestamp', 'Неизвестно')}

---
Это автоматическое сообщение, отвечать на него не нужно.
            """
            html_template = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif;">
    <h2>📝 Новый отзыв с сайта!</h2>
    <table style="border-collapse: collapse; width: 100%; max-width: 500px;">
        <tr style="background-color: #f0f7fc;">
            <td style="padding: 8px; border: 1px solid #ccc;"><strong>👤 Имя</strong></td>
            <td style="padding: 8px; border: 1px solid #ccc;">{data.get('name', 'Аноним')}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ccc;"><strong>📧 Контакт</strong></td>
            <td style="padding: 8px; border: 1px solid #ccc;">{data.get('contact', 'Не указан')}</td>
        </tr>
        <tr style="background-color: #f0f7fc;">
            <td style="padding: 8px; border: 1px solid #ccc;"><strong>👥 Роль</strong></td>
            <td style="padding: 8px; border: 1px solid #ccc;">{data.get('role', 'Не указана')}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ccc;"><strong>⭐ Оценка</strong></td>
            <td style="padding: 8px; border: 1px solid #ccc;">{'★' * int(data.get('rating', 0)) if data.get('rating', '').isdigit() else data.get('rating', 'Нет')}</td>
        </tr>
        <tr style="background-color: #f0f7fc;">
            <td style="padding: 8px; border: 1px solid #ccc;"><strong>💬 Текст отзыва</strong></td>
            <td style="padding: 8px; border: 1px solid #ccc;">{data.get('message', 'Без текста')}</td>
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

        msg["From"] = SMTP_USERNAME
        msg["To"] = TARGET_EMAIL

        part_text = MIMEText(text_template, "plain", "utf-8")
        part_html = MIMEText(html_template, "html", "utf-8")

        msg.attach(part_text)
        msg.attach(part_html)

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

    # ========== СКРЫТАЯ СТРАНИЦА ДЛЯ KINDLE ==========
    # Доступна по адресу: /kindle-chat
    if path == "/kindle-chat":
        return handle_kindle_chat(environ, start_response)

    headers = [
        ("Access-Control-Allow-Origin", "*"),
        ("Access-Control-Allow-Methods", "POST, OPTIONS"),
        ("Access-Control-Allow-Headers", "Content-Type"),
    ]

    # Обработка preflight-запроса OPTIONS
    if method == "OPTIONS":
        start_response("204 No Content", headers)
        return [b""]

    # Обработка обратных звонков
    if method == "POST" and path == "/send_message":
        post_data = parse_post_data(environ)
        
        data = {
            "name": post_data.get("name", [""])[0],
            "phone": post_data.get("phone", [""])[0],
            "question": post_data.get("question", [""])[0],
            "page": post_data.get("page", [""])[0],
            "timestamp": post_data.get("timestamp", [""])[0],
        }

        success, result = send_email(data, "callback")

        if success:
            response_body = {"status": "success", "message": "Заявка отправлена"}
            status = "200 OK"
        else:
            response_body = {"status": "error", "message": result}
            status = "500 Internal Server Error"

        response_json = json.dumps(response_body, ensure_ascii=False).encode("utf-8")
        headers.append(("Content-Type", "application/json; charset=utf-8"))
        headers.append(("Content-Length", str(len(response_json))))

        start_response(status, headers)
        return [response_json]

    # Обработка отзывов
    if method == "POST" and path == "/send_review":
        post_data = parse_post_data(environ)
        
        data = {
            "name": post_data.get("name", [""])[0],
            "contact": post_data.get("contact", [""])[0],
            "role": post_data.get("role", [""])[0],
            "rating": post_data.get("rating", [""])[0],
            "message": post_data.get("message", [""])[0],
            "page": post_data.get("page", [""])[0],
            "timestamp": post_data.get("timestamp", [""])[0],
        }

        success, result = send_email(data, "review")

        if success:
            response_body = {"status": "success", "message": "Отзыв отправлен"}
            status = "200 OK"
        else:
            response_body = {"status": "error", "message": result}
            status = "500 Internal Server Error"

        response_json = json.dumps(response_body, ensure_ascii=False).encode("utf-8")
        headers.append(("Content-Type", "application/json; charset=utf-8"))
        headers.append(("Content-Length", str(len(response_json))))

        start_response(status, headers)
        return [response_json]

    # 404 для всех остальных путей
    start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
    return [b"404 Not Found"]