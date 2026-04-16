#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kindle Chat Handler - для встраивания в WSGI приложение
"""

import json
import urllib.request
import urllib.parse
import urllib.error
import time
from datetime import datetime

# ========== НАСТРОЙКИ OPENROUTER ==========
OPENROUTER_API_KEY = "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"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Список моделей для автоматического перебора
MODELS = [
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "qwen/qwen3.6-plus-preview:free",
    "openai/gpt-oss-120b:free",
    "z-ai/glm-4.5-air:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemma-4-26b-a4b-it:free",
    "openrouter/free",
]

current_model_index = 0
current_model = MODELS[current_model_index]

# Для Kindle 4: максимально краткие ответы
SYSTEM_PROMPT = "Ты помощник для Kindle 4. Отвечай максимально кратко: 1-2 коротких предложения, максимум 200 символов."

# ========== НАСТРОЙКИ ПАМЯТИ ==========
MAX_HISTORY_MESSAGES = 6  # Для Kindle 4 достаточно 6 сообщений
MAX_HISTORY_TOKENS = 1000

conversations = {}
error_counts = {model: 0 for model in MODELS}
MAX_ERRORS_PER_MODEL = 3
blocked_models = {}

# ========== ТРАНСЛИТЕРАЦИЯ ==========
TRANSLIT_MAP = {
    'a': 'а', 'b': 'б', 'v': 'в', 'g': 'г', 'd': 'д', 'e': 'е',
    'zh': 'ж', 'z': 'з', 'i': 'и', 'y': 'й', 'k': 'к', 'l': 'л',
    'm': 'м', 'n': 'н', 'o': 'о', 'p': 'п', 'r': 'р', 's': 'с',
    't': 'т', 'u': 'у', 'f': 'ф', 'kh': 'х', 'ts': 'ц', 'ch': 'ч',
    'sh': 'ш', 'shch': 'щ', 'yu': 'ю', 'ya': 'я',
    'A': 'А', 'B': 'Б', 'V': 'В', 'G': 'Г', 'D': 'Д', 'E': 'Е',
}

TRANSLIT_KEYS = sorted(TRANSLIT_MAP.keys(), key=len, reverse=True)

def translit_to_cyrillic(text):
    result = []
    i = 0
    while i < len(text):
        matched = False
        for key in TRANSLIT_KEYS:
            if text[i:i+len(key)] == key:
                result.append(TRANSLIT_MAP[key])
                i += len(key)
                matched = True
                break
        if not matched:
            result.append(text[i])
            i += 1
    return ''.join(result)

def estimate_tokens(text):
    return len(text) // 4

def trim_history_by_tokens(history, max_tokens):
    if not history:
        return []
    
    result = []
    total_tokens = 0
    
    for msg in reversed(history):
        msg_tokens = estimate_tokens(msg['content']) + 10
        if total_tokens + msg_tokens <= max_tokens:
            result.insert(0, msg)
            total_tokens += msg_tokens
        else:
            break
    
    if not result and history:
        result = [history[-1]]
    
    return result

def get_formatted_history(session_id):
    if session_id not in conversations:
        return []
    
    history = conversations[session_id]
    
    if len(history) > MAX_HISTORY_MESSAGES:
        history = history[-MAX_HISTORY_MESSAGES:]
    
    history = trim_history_by_tokens(history, MAX_HISTORY_TOKENS)
    
    return [{"role": msg["role"], "content": msg["content"]} for msg in history]

def format_for_display(history):
    if not history:
        return '<div class="history"><div class="msg system">💡 Напишите первое сообщение (транслитом)</div></div>'
    
    html = '<div class="history">'
    for msg in history:
        role = msg["role"]
        content = msg["content"]
        time_str = msg.get("time", "")
        
        if role == "user":
            html += f'<div class="msg user"><strong>👤 ВЫ:</strong><br>{content}</div>'
        elif role == "assistant":
            html += f'<div class="msg bot"><strong>🤖 БОТ:</strong><br>{content}</div>'
    html += '</div>'
    return html

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
    
    print(f"🔄 Переключение на модель: {current_model}")
    return current_model

def is_model_blocked(model):
    if model in blocked_models:
        if time.time() < blocked_models[model]:
            return True
        else:
            del blocked_models[model]
            error_counts[model] = 0
    return False

def handle_api_error(model, error_code):
    global error_counts
    
    error_counts[model] = error_counts.get(model, 0) + 1
    
    if error_code in [404, 429, 401, 403]:
        print(f"⚠️ Модель {model} выдала ошибку {error_code}, переключаем...")
        return True
    elif error_counts[model] >= MAX_ERRORS_PER_MODEL:
        print(f"⚠️ Модель {model} превысила лимит ошибок, блокируем на 5 минут...")
        blocked_models[model] = time.time() + 300
        return True
    
    return False

def ask_api_with_fallback(user_message, session_id, retry_count=0):
    global current_model
    
    if retry_count >= len(MODELS) * 2:
        return "Все модели недоступны. Попробуйте позже."
    
    if is_model_blocked(current_model):
        switch_to_next_model()
        return ask_api_with_fallback(user_message, session_id, retry_count + 1)
    
    russian_message = translit_to_cyrillic(user_message)
    
    if session_id not in conversations:
        conversations[session_id] = []
    
    conversations[session_id].append({
        "role": "user",
        "content": russian_message,
        "time": datetime.now().strftime("%H:%M:%S")
    })
    
    api_history = get_formatted_history(session_id)
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(api_history)
    
    request_data = {
        "model": current_model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 300  # Ограничиваем длину ответа для Kindle 4
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://your-site.com",
        "X-Title": "Kindle Chat"
    }
    
    try:
        req = urllib.request.Request(
            OPENROUTER_API_URL,
            data=json.dumps(request_data).encode('utf-8'),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            bot_response = response_data['choices'][0]['message']['content']
            
            error_counts[current_model] = 0
            
            conversations[session_id].append({
                "role": "assistant",
                "content": bot_response,
                "time": datetime.now().strftime("%H:%M:%S")
            })
            
            if len(conversations[session_id]) > MAX_HISTORY_MESSAGES * 2:
                conversations[session_id] = conversations[session_id][-MAX_HISTORY_MESSAGES:]
            
            return bot_response
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        error_code = e.code
        
        if session_id in conversations and conversations[session_id]:
            conversations[session_id].pop()
        
        if handle_api_error(current_model, error_code):
            switch_to_next_model()
            return ask_api_with_fallback(user_message, session_id, retry_count + 1)
        
        return f"Ошибка {error_code}"
        
    except Exception as e:
        if session_id in conversations and conversations[session_id]:
            conversations[session_id].pop()
        
        if handle_api_error(current_model, 500):
            switch_to_next_model()
            return ask_api_with_fallback(user_message, session_id, retry_count + 1)
        
        return f"Ошибка"

def get_kindle_chat_html(message, session_id):
    """Возвращает HTML для Kindle чата"""
    
    bot_response = ""
    user_message = ""
    if message and message.strip():
        user_message = message
        bot_response = ask_api_with_fallback(message, session_id)
    
    history_html = ""
    if session_id in conversations:
        history_html = format_for_display(conversations[session_id])
    
    model_name = current_model.split(':')[0].split('/')[-1][:20]
    msg_count = len(conversations.get(session_id, []))
    
    # Специально для Kindle 4: максимально простой HTML
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
    <title>Kindle Chat</title>
    <style>
        body {{
            background: black;
            color: white;
            font-family: monospace;
            padding: 10px;
            margin: 0;
            font-size: 1.2em;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
        }}
        h1 {{
            color: white;
            font-size: 1.3em;
            text-align: center;
            background: #222;
            padding: 8px;
            margin: 0 0 10px 0;
        }}
        .info {{
            background: #222;
            padding: 5px;
            margin: 5px 0;
            font-size: 0.7em;
            text-align: center;
            display: flex;
            justify-content: space-between;
        }}
        .history {{
            max-height: 400px;
            overflow-y: auto;
            margin: 10px 0;
            padding: 5px;
            background: #111;
            border: 1px solid #333;
        }}
        .msg {{
            padding: 8px;
            margin: 5px 0;
            border-left: 3px solid;
            word-wrap: break-word;
        }}
        .user {{
            color: #0ff;
            border-left-color: #0ff;
            background: #001;
        }}
        .bot {{
            color: #0f0;
            border-left-color: #0f0;
            background: #010;
        }}
        form {{
            margin: 15px 0;
        }}
        input {{
            width: 100%;
            padding: 10px;
            background: #222;
            color: white;
            border: 2px solid white;
            font-family: monospace;
            font-size: 1em;
            box-sizing: border-box;
        }}
        button {{
            width: 100%;
            padding: 10px;
            margin-top: 10px;
            background: white;
            color: black;
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
            color: #f66;
            text-decoration: none;
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
        
        {f'<div class="msg bot"><strong>📌 НОВОЕ:</strong><br>{bot_response}</div>' if bot_response else ''}
        
        <form method="GET" action="/kindle-chat">
            <input type="text" name="msg" placeholder="napishi soobshchenie..." autofocus>
            <button type="submit">📤 OTPABUTb</button>
        </form>
        
        <div class="footer">
            💡 Пишите транслитом (privet, kak dela)
        </div>
    </div>
</body>
</html>"""

def handle_kindle_chat(environ, start_response):
    """Обработчик скрытой страницы /kindle-chat"""
    
    # Получаем параметры из URL
    query_string = environ.get('QUERY_STRING', '')
    params = urllib.parse.parse_qs(query_string)
    
    # Очистка истории
    if params.get('clear'):
        session_id = environ.get('REMOTE_ADDR', '0.0.0.0')
        if session_id in conversations:
            conversations[session_id] = []
    
    # Получаем сообщение
    message = params.get('msg', [''])[0]
    session_id = environ.get('REMOTE_ADDR', '0.0.0.0')
    
    # Генерируем HTML
    html = get_kindle_chat_html(message, session_id)
    
    start_response('200 OK', [
        ('Content-Type', 'text/html; charset=utf-8'),
        ('Content-Length', str(len(html.encode('utf-8'))))
    ])
    return [html.encode('utf-8')]