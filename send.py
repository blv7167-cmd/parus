import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Настройки SMTP сервера (пример для Яндекс.Почты)
SMTP_SERVER = "smtp.yandex.ru"
SMTP_PORT = 465  # SSL
SMTP_USER = "blv716@yandex.ru"
SMTP_PASSWORD = "ggzcnbgtyttreusy"

# Кому и от кого
FROM = "blv716@yandex.ru"
TO = "blv716@yandex.ru"
SUBJECT = "Тестовое2 письмо из Python"

# Создаём письмо
msg = MIMEMultipart()
msg["From"] = FROM
msg["To"] = TO
msg["Subject"] = SUBJECT

# Текст письма
body = "Привет! Это тестовое письмо, отправленное из Python скрипта."
msg.attach(MIMEText(body, "plain", "utf-8"))

# Отправка
try:
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
    print("Письмо успешно отправлено!")
except Exception as e:
    print(f"Ошибка: {e}")


# import smtplib as smtp
# from getpass import getpass
# email = input('введите почту: \n')
# password = getpass('введите пароль: ')
# dest_email = input('введите адрес получателя: \n')
# subject = input('тема письма: \n')
# email_text = input('текст письма: \n' )
# message = 'From: {}\nTo: {}\nSubject: {}\n\n{}'.format(email,
#                                                        dest_email,
#                                                        subject,
#                                                        email_text)
# server = smtp.SMTP_SSL('smtp.yandex.com')
# server.set_debuglevel(1)
# server.ehlo(email)
# server.login(email, password)
# server.auth_plain()
# server.sendmail(email, dest_email, message)
# server.quit()