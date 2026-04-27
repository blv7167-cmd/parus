#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kindle Chat Handler - для встраивания в WSGI приложение
Оптимизирован для Kindle 4 (светлая тема, автообновление, защита от дублирования)
ФИКС: ответы теперь точно сохраняются в истории
"""

import json
import urllib.request
import urllib.parse
import urllib.error
import time
import os
import sys
import logging
import threading
from datetime import datetime

# ========== НАСТРОЙКИ ЛОГГИРОВАНИЯ ==========
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger('kindle_chat')
logger.setLevel(logging.INFO)

log_file = os.path.join(LOG_DIR, f'kindle_chat_{datetime.now().strftime("%Y%m%d")}.log')
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# ========== НАСТРОЙКИ OPENROUTER ==========
OPENROUTER_API_KEY = "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"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# АКТУАЛЬНЫЕ БЕСПЛАТНЫЕ МОДЕЛИ (апрель 2026)
MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "deepseek/deepseek-r1:free",
    "qwen/qwen3-next-80b-a3b-instruct:free",
    "google/gemma-3-27b-it:free",
    "microsoft/phi-3-mini-128k-instruct",
]

current_model_index = 0
current_model = MODELS[current_model_index]

SYSTEM_PROMPT = "Ты помощник для Kindle 4. Отвечай максимально кратко: 1-2 коротких предложения, максимум 200 символов."

MAX_HISTORY_MESSAGES = 6
conversations = {}
error_counts = {model: 0 for model in MODELS}
MAX_ERRORS_PER_MODEL = 3
blocked_models = {}

# Хранилище обработанных сообщений (защита от дублирования)
processed_messages = {}

# ========== ТРАНСЛИТЕРАЦИЯ (ПОЛНЫЙ РУССКИЙ АЛФАВИТ - 33 БУКВЫ) ==========
TRANSLIT_MAP = {
    'a': 'а', 'b': 'б', 'v': 'в', 'g': 'г', 'd': 'д',
    'e': 'е', 'yo': 'ё', 'zh': 'ж', 'z': 'з', 'i': 'и',
    'y': 'й', 'k': 'к', 'l': 'л', 'm': 'м', 'n': 'н',
    'o': 'о', 'p': 'п', 'r': 'р', 's': 'с', 't': 'т',
    'u': 'у', 'f': 'ф', 'kh': 'х', 'ts': 'ц', 'ch': 'ч',
    'sh': 'ш', 'shch': 'щ', '"': 'ъ', 'ui': 'ы', 'y_i': 'ы',
    "'": 'ь', '`': 'ь', "''": 'ь', 'eh': 'э', 'e`': 'э',
    "e'": 'э', 'ye': 'э', 'yu': 'ю', 'ya': 'я',

    'A': 'А', 'B': 'Б', 'V': 'В', 'G': 'Г', 'D': 'Д',
    'E': 'Е', 'Yo': 'Ё', 'Zh': 'Ж', 'Z': 'З', 'I': 'И',
    'Y': 'Й', 'K': 'К', 'L': 'Л', 'M': 'М', 'N': 'Н',
    'O': 'О', 'P': 'П', 'R': 'Р', 'S': 'С', 'T': 'Т',
    'U': 'У', 'F': 'Ф', 'Kh': 'Х', 'Ts': 'Ц', 'Ch': 'Ч',
    'Sh': 'Ш', 'Shch': 'Щ', '"': 'Ъ', 'Ui': 'Ы', 'Y_i': 'Ы',
    "'": 'Ь', '`': 'Ь', "''": 'Ь', 'Eh': 'Э', 'E`': 'Э',
    "E'": 'Э', 'Ye': 'Э', 'Yu': 'Ю', 'Ya': 'Я',
}

TRANSLIT_KEYS = sorted(TRANSLIT_MAP.keys(), key=len, reverse=True)


def translit_to_cyrillic(text):
    result = []
    i = 0
    while i < len(text):
        matched = False
        for key in TRANSLIT_KEYS:
            if text[i:i + len(key)] == key:
                result.append(TRANSLIT_MAP[key])
                i += len(key)
                matched = True
                break
        if not matched:
            result.append(text[i])
            i += 1
    return ''.join(result)


def get_translit_table_html():
    """Возвращает HTML-код таблицы транслитерации для Kindle"""
    return """
    <details class="translit-details">
        <summary>📖 Таблица транслитерации (нажмите, чтобы открыть)</summary>
        <div class="translit-table-container">
            <table class="translit-table">
                <thead><tr><th>Транслит</th><th>→</th><th>Буква</th><th></th><th>Транслит</th><th>→</th><th>Буква</th></tr></thead>
                <tbody>
                    <tr><td>a</td><td>→</td><td><b>а</b></td><td></td><td>o</td><td>→</td><td><b>о</b></td></tr>
                    <tr><td>b</td><td>→</td><td><b>б</b></td><td></td><td>p</td><td>→</td><td><b>п</b></td></tr>
                    <tr><td>v</td><td>→</td><td><b>в</b></td><td></td><td>r</td><td>→</td><td><b>р</b></td></tr>
                    <tr><td>g</td><td>→</td><td><b>г</b></td><td></td><td>s</td><td>→</td><td><b>с</b></td></tr>
                    <tr><td>d</td><td>→</td><td><b>д</b></td><td></td><td>t</td><td>→</td><td><b>т</b></td></tr>
                    <tr><td>e</td><td>→</td><td><b>е</b></td><td></td><td>u</td><td>→</td><td><b>у</b></td></tr>
                    <tr><td>yo</td><td>→</td><td><b>ё</b></td><td></td><td>f</td><td>→</td><td><b>ф</b></td></tr>
                    <tr><td>zh</td><td>→</td><td><b>ж</b></td><td></td><td>kh</td><td>→</td><td><b>х</b></td></tr>
                    <tr><td>z</td><td>→</td><td><b>з</b></td><td></td><td>ts</td><td>→</td><td><b>ц</b></td></tr>
                    <tr><td>i</td><td>→</td><td><b>и</b></td><td></td><td>ch</td><td>→</td><td><b>ч</b></td></tr>
                    <tr><td>y</td><td>→</td><td><b>й</b></td><td></td><td>sh</td><td>→</td><td><b>ш</b></td></tr>
                    <tr><td>k</td><td>→</td><td><b>к</b></td><td></td><td>shch</td><td>→</td><td><b>щ</b></td></tr>
                    <tr><td>l</td><td>→</td><td><b>л</b></td><td></td><td>"</td><td>→</td><td><b>ъ</b></td></tr>
                    <tr><td>m</td><td>→</td><td><b>м</b></td><td></td><td>ui</td><td>→</td><td><b>ы</b></td></tr>
                    <tr><td>n</td><td>→</td><td><b>н</b></td><td></td><td>'</td><td>→</td><td><b>ь</b></td></tr>
                    <tr><td>eh</td><td>→</td><td><b>э</b></td><td></td><td>yu</td><td>→</td><td><b>ю</b></td></tr>
                    <tr><td>ya</td><td>→</td><td><b>я</b></td><td></td><td></td><td></td><td></td></tr>
                </tbody>
            </table>
        </div>
        <div class="translit-note">
            💡 <b>Совет:</b> Пишите транслитом — бот сам переведёт в кириллицу<br>
            📝 <b>Примеры:</b> "privet" → "привет", "mal'chik" → "мальчик", "pod"ezd" → "подъезд"
        </div>
    </details>
    """


def switch_to_next_model():
    global current_model_index, current_model
    while True:
        current_model_index = (current_model_index + 1) % len(MODELS)
        candidate = MODELS[current_model_index]
        if candidate in blocked_models:
            if time.time() < blocked_models[candidate]:
                continue
            else:
                del blocked_models[candidate]
                error_counts[candidate] = 0
        current_model = candidate
        break
    logger.error(f"Переключение на модель: {current_model}")
    return current_model


def is_model_blocked(model):
    if model in blocked_models:
        if time.time() < blocked_models[model]:
            return True
        else:
            del blocked_models[model]
            error_counts[model] = 0
    return False


def handle_api_error(model, error_code, error_msg=""):
    error_counts[model] = error_counts.get(model, 0) + 1
    logger.error(f"Ошибка модели {model}: код={error_code}")

    if error_code in [404, 429, 401, 403, 402]:
        return True
    elif error_counts[model] >= MAX_ERRORS_PER_MODEL:
        logger.error(f"Модель {model} превысила лимит ошибок, блокируем на 5 минут...")
        blocked_models[model] = time.time() + 300
        return True
    return False


def ask_api_sync(user_message, session_id):
    """Синхронный запрос к API (выполняется в фоновом потоке)"""
    global current_model

    russian_message = translit_to_cyrillic(user_message)
    logger.info(f"Сообщение от {session_id}: {russian_message}")

    # Сохраняем сообщение пользователя
    if session_id not in conversations:
        conversations[session_id] = []

    conversations[session_id].append({
        "role": "user",
        "content": russian_message,
        "time": datetime.now().strftime("%H:%M:%S")
    })

    # Получаем историю
    history = conversations[session_id][-MAX_HISTORY_MESSAGES:]
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    request_data = {
        "model": current_model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 300
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://your-site.com",
        "X-Title": "Kindle Chat"
    }

    for retry in range(3):
        try:
            logger.debug(f"Запрос к модели {current_model}, попытка {retry + 1}")

            req = urllib.request.Request(
                OPENROUTER_API_URL,
                data=json.dumps(request_data).encode('utf-8'),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                bot_response = response_data['choices'][0]['message']['content']

                logger.info(f"Ответ от {current_model}: {bot_response[:100]}...")

                error_counts[current_model] = 0

                # Сохраняем ответ бота
                conversations[session_id].append({
                    "role": "assistant",
                    "content": bot_response,
                    "time": datetime.now().strftime("%H:%M:%S")
                })

                # Обрезаем историю
                if len(conversations[session_id]) > MAX_HISTORY_MESSAGES * 2:
                    conversations[session_id] = conversations[session_id][-MAX_HISTORY_MESSAGES * 2:]

                return

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            error_code = e.code

            logger.error(f"HTTPError {error_code}: {error_body[:100]}")

            if handle_api_error(current_model, error_code):
                switch_to_next_model()
                request_data["model"] = current_model

        except Exception as e:
            logger.error(f"Exception: {str(e)}")
            if retry == 2:
                # Добавляем сообщение об ошибке в историю
                conversations[session_id].append({
                    "role": "assistant",
                    "content": "Сервер временно недоступен. Попробуйте позже.",
                    "time": datetime.now().strftime("%H:%M:%S")
                })
                return
            time.sleep(1)


def background_ask(message, session_id):
    """Фоновая задача для API запроса"""
    ask_api_sync(message, session_id)


def format_history(session_id):
    """Форматирует историю для отображения (светлая тема)"""
    if session_id not in conversations or not conversations[session_id]:
        return '<div class="history"><div class="msg system">💡 Напишите первое сообщение (транслитом)</div></div>'

    html = '<div class="history">'
    for msg in conversations[session_id]:
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            html += f'<div class="msg user"><strong>👤 ВЫ:</strong><br>{content}</div>'
        elif role == "assistant":
            html += f'<div class="msg bot"><strong>🤖 БОТ:</strong><br>{content}</div>'
    html += '</div>'
    return html


def handle_kindle_chat(environ, start_response):
    """Обработчик скрытой страницы /kindle-chat - ОПТИМИЗИРОВАН ДЛЯ KINDLE 4"""

    query_string = environ.get('QUERY_STRING', '')
    params = urllib.parse.parse_qs(query_string)

    session_id = environ.get('REMOTE_ADDR', '0.0.0.0')

    # Очистка истории
    if params.get('clear'):
        conversations[session_id] = []
        processed_messages.pop(session_id, None)
        start_response('302 Found', [('Location', '/kindle-chat')])
        return [b'']

    message = params.get('msg', [''])[0]

    # Обработка нового сообщения
    if message and message.strip():
        last_processed = processed_messages.get(session_id, ('', 0))
        current_time = time.time()

        if last_processed[0] == message and (current_time - last_processed[1]) < 30:
            logger.debug(f"Игнорируем повторное сообщение от {session_id}: {message}")
        else:
            processed_messages[session_id] = (message, current_time)
            logger.info(f"Новое сообщение от {session_id}: {message}")

            # Запускаем фоновый запрос
            thread = threading.Thread(
                target=background_ask,
                args=(message.strip(), session_id)
            )
            thread.daemon = True
            thread.start()

            # Показываем страницу с индикатором загрузки
            history_html = format_history(session_id)
            msg_count = len(conversations.get(session_id, [])) // 2

            loading_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="10">
    <title>Kindle Chat</title>
    <style>
        body {{ background: white; color: black; font-family: monospace; padding: 10px; margin: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; }}
        h1 {{ color: black; font-size: 1.3em; text-align: center; background: #e0e0e0; padding: 8px; margin: 0 0 10px 0; border: 1px solid #ccc; }}
        .info {{ background: #f0f0f0; padding: 5px; margin: 5px 0; font-size: 0.7em; text-align: center; display: flex; justify-content: space-between; border: 1px solid #ccc; }}
        .history {{ max-height: 400px; overflow-y: auto; margin: 10px 0; padding: 5px; background: #fafafa; border: 1px solid #ccc; }}
        .msg {{ padding: 8px; margin: 5px 0; border-left: 3px solid; word-wrap: break-word; }}
        .user {{ color: #0055cc; border-left-color: #0055cc; background: #e8f0fe; }}
        .bot {{ color: #008800; border-left-color: #008800; background: #f0fff0; }}
        .loading {{ color: #cc6600; text-align: center; padding: 10px; margin: 10px 0; background: #fff3e0; border: 1px solid #cc6600; }}
        .footer {{ font-size: 0.6em; text-align: center; color: #666; margin-top: 10px; }}
        .clear-btn a {{ color: #cc0000; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 Kindle Chat</h1>
        <div class="info">
            <span>🤖 ОТПРАВЛЕНО</span>
            <span>💾 {msg_count}</span>
            <span class="clear-btn"><a href="/kindle-chat?clear=1">🗑️</a></span>
        </div>
        {history_html}
        <div class="loading">⏳ Ожидайте ответ... (обновление через 10 сек)</div>
        <div class="footer">💡 Страница обновится автоматически</div>
    </div>
</body>
</html>"""

            start_response('200 OK', [
                ('Content-Type', 'text/html; charset=utf-8'),
                ('Content-Length', str(len(loading_html.encode('utf-8'))))
            ])
            return [loading_html.encode('utf-8')]

    # Обычный показ страницы (нет нового сообщения или ответ уже в истории)
    history_html = format_history(session_id)

    model_name = current_model.split(':')[0].split('/')[-1][:20]
    msg_count = len(conversations.get(session_id, [])) // 2

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kindle Chat</title>
    <style>
        body {{
            background: white;
            color: black;
            font-family: monospace;
            padding: 10px;
            margin: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
        }}
        h1 {{
            color: black;
            font-size: 1.3em;
            text-align: center;
            background: #e0e0e0;
            padding: 8px;
            margin: 0 0 10px 0;
            border: 1px solid #ccc;
        }}
        .info {{
            background: #f0f0f0;
            padding: 5px;
            margin: 5px 0;
            font-size: 0.7em;
            text-align: center;
            display: flex;
            justify-content: space-between;
            border: 1px solid #ccc;
        }}
        .history {{
            max-height: 400px;
            overflow-y: auto;
            margin: 10px 0;
            padding: 5px;
            background: #fafafa;
            border: 1px solid #ccc;
        }}
        .msg {{
            padding: 8px;
            margin: 5px 0;
            border-left: 3px solid;
            word-wrap: break-word;
        }}
        .user {{
            color: #0055cc;
            border-left-color: #0055cc;
            background: #e8f0fe;
        }}
        .bot {{
            color: #008800;
            border-left-color: #008800;
            background: #f0fff0;
        }}
        form {{
            margin: 15px 0;
        }}
        input {{
            width: 100%;
            padding: 10px;
            background: white;
            color: black;
            border: 2px solid #999;
            font-family: monospace;
            font-size: 1em;
            box-sizing: border-box;
        }}
        button {{
            width: 100%;
            padding: 10px;
            margin-top: 10px;
            background: #333;
            color: white;
            border: none;
            font-weight: bold;
            font-size: 1em;
        }}
        .footer {{
            font-size: 0.6em;
            text-align: center;
            color: #666;
            margin-top: 10px;
        }}
        .clear-btn a {{
            color: #cc0000;
            text-decoration: none;
        }}
        .translit-details {{
            background: #f5f5f5;
            border: 1px solid #ccc;
            border-radius: 5px;
            margin: 15px 0;
        }}
        .translit-details summary {{
            padding: 10px;
            cursor: pointer;
            background: #e0e0e0;
            font-weight: bold;
        }}
        .translit-table-container {{
            padding: 10px;
            overflow-x: auto;
        }}
        .translit-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9em;
        }}
        .translit-table th {{
            background: #333;
            color: white;
            padding: 8px;
            text-align: center;
        }}
        .translit-table td {{
            padding: 5px 8px;
            border-bottom: 1px solid #ddd;
            text-align: center;
        }}
        .translit-table td b {{
            color: #0055cc;
        }}
        .translit-note {{
            background: #e8f0fe;
            padding: 10px;
            margin: 5px 10px;
            border-left: 3px solid #0055cc;
            font-size: 0.85em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 Kindle Chat</h1>
        <div class="info">
            <span>🤖 {model_name}</span>
            <span>💾 {msg_count}</span>
            <span class="clear-btn"><a href="/kindle-chat?clear=1">🗑️</a></span>
        </div>

        {history_html}

        <form method="GET" action="/kindle-chat">
            <input type="text" name="msg" placeholder="napishi soobshchenie..." autofocus>
            <button type="submit">📤 OTPABUTb</button>
        </form>

        {get_translit_table_html()}

        <div class="footer">
            💡 Пишите транслитом (privet, kak dela)<br>
            ⏳ После отправки подождите 10-15 секунд
        </div>
    </div>
</body>
</html>"""

    start_response('200 OK', [
        ('Content-Type', 'text/html; charset=utf-8'),
        ('Content-Length', str(len(html.encode('utf-8'))))
    ])
    return [html.encode('utf-8')]


def run_local_server(host='0.0.0.0', port=8000):
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class KindleChatHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)

            if parsed.path == '/kindle-chat':
                environ = {
                    'REQUEST_METHOD': 'GET',
                    'PATH_INFO': parsed.path,
                    'QUERY_STRING': parsed.query,
                    'REMOTE_ADDR': self.client_address[0],
                }

                def start_response(status, headers):
                    self.send_response(int(status.split()[0]))
                    for name, value in headers:
                        self.send_header(name, value)
                    self.end_headers()

                response = handle_kindle_chat(environ, start_response)
                for chunk in response:
                    self.wfile.write(chunk)
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'404 Not Found')

        def log_message(self, format, *args):
            if self.path != '/favicon.ico':
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")

    server = HTTPServer((host, port), KindleChatHandler)
    print(f"✅ Kindle Chat сервер запущен на http://{host}:{port}/kindle-chat")
    print(f"📝 Логи: {LOG_DIR}")
    print("⏹️ Нажми Ctrl+C для остановки\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⚠️ Сервер остановлен")
        server.shutdown()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Kindle Chat Server')
    parser.add_argument('--port', type=int, default=8000, help='Порт')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Хост')
    args = parser.parse_args()
    run_local_server(host=args.host, port=args.port)