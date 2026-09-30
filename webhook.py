import os
import json
import logging
import requests
import re
from flask import Flask, request, jsonify
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import tempfile
from io import BytesIO

# Логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# Токени та конфіг
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8810628323:AAFdxOn8CLTy6QniMChKd-o_Fb84Q5EVba4")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "16oJlHbtLKXIHd9slr2ph-_Hb1L75r94s")
GOOGLE_SERVICE_ACCOUNT = os.getenv("GOOGLE_SERVICE_ACCOUNT")

# Google Drive API
def get_drive_service():
    """Отримує Google Drive сервіс"""
    try:
        service_account_info = json.loads(GOOGLE_SERVICE_ACCOUNT)
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        return build('drive', 'v3', credentials=credentials)
    except Exception as e:
        logger.error(f"Помилка при підключенні до Google Drive: {e}")
        return None

def upload_to_drive(file_name, file_content, mime_type):
    """Завантажує файл на Google Drive"""
    try:
        drive_service = get_drive_service()
        if not drive_service:
            return None

        file_metadata = {
            'name': file_name,
            'parents': [GOOGLE_DRIVE_FOLDER_ID]
        }

        # Зберігаємо файл тимчасово
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file_content)
            temp_path = temp_file.name

        try:
            media = MediaFileUpload(temp_path, mimetype=mime_type)
            file = drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()

            logger.info(f"✅ Файл завантажено на Google Drive: {file.get('id')}")
            return file.get('webViewLink')

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as e:
        logger.error(f"Помилка при завантаженні файлу: {e}")
        return None

def send_telegram_message(chat_id, message_text, parse_mode="HTML"):
    """Відправляє повідомлення в Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message_text,
            "parse_mode": parse_mode
        }
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            logger.info(f"✅ Повідомлення відправлено в Telegram")
            return True
        else:
            logger.error(f"❌ Помилка Telegram: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Помилка при відправці Telegram: {e}")
        return False

def download_telegram_file(file_path):
    """Завантажує файл з Telegram"""
    try:
        url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.content
        else:
            logger.error(f"Помилка завантаження файлу: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Помилка при завантаженні файлу: {e}")
        return None

@app.route('/webhook', methods=['POST'])
def webhook():
    """Основний webhook для обробки Zapier запитів"""

    try:
        data = request.json
        logger.info(f"Отримано запит від Zapier: {json.dumps(data, indent=2)}")

        # Парсимо дані від Zapier
        chat_id = data.get('chat_id')
        message_text = data.get('message_text', '')
        files = data.get('files', [])

        if not chat_id:
            return jsonify({'error': 'Немає chat_id'}), 400

        # Парсимо структуру: Група / Учень / Дата / Тема
        pattern = r"^(.+?)\s*\/\s*(.+?)\s*\/\s*(.+?)\s*\/\s*(.+?)$"
        match = re.match(pattern, message_text.strip())

        if not match:
            send_telegram_message(
                chat_id,
                "❌ Невірний формат!\n\n"
                "Використовуй:\n"
                "<code>Група / Учень / Дата / Тема</code>"
            )
            return jsonify({'error': 'Невірний формат'}), 400

        group, student, date_str, topic = match.groups()
        group = group.strip()
        student = student.strip()
        date_str = date_str.strip()
        topic = topic.strip()

        # Створюємо папку на Google Drive для цього уроку
        folder_name = f"{topic} | {date_str} | {student}"

        try:
            drive_service = get_drive_service()
            if drive_service:
                folder_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [GOOGLE_DRIVE_FOLDER_ID]
                }
                folder = drive_service.files().create(
                    body=folder_metadata,
                    fields='id, webViewLink'
                ).execute()
                folder_id = folder.get('id')
                folder_link = folder.get('webViewLink')
                logger.info(f"✅ Папка створена на Google Drive: {folder_id}")
            else:
                folder_link = None
        except Exception as e:
            logger.error(f"Помилка при створенні папки: {e}")
            folder_link = None

        # Завантажуємо файли
        uploaded_files = []
        for file_data in files:
            try:
                file_name = file_data.get('file_name', 'unknown_file')
                file_path = file_data.get('file_path')
                mime_type = file_data.get('mime_type', 'application/octet-stream')

                # Завантажуємо файл з Telegram
                file_content = download_telegram_file(file_path)
                if file_content:
                    # Завантажуємо на Google Drive
                    drive_link = upload_to_drive(file_name, file_content, mime_type)
                    if drive_link:
                        uploaded_files.append({
                            'name': file_name,
                            'link': drive_link
                        })
                        logger.info(f"✅ Файл завантажено: {file_name}")

            except Exception as e:
                logger.error(f"Помилка при обробці файлу {file_name}: {e}")

        # Формуємо відповідь
        response_message = (
            f"✅ <b>Урок успішно завантажено!</b>\n\n"
            f"📚 <b>Група:</b> {group}\n"
            f"👤 <b>Учень:</b> {student}\n"
            f"📅 <b>Дата:</b> {date_str}\n"
            f"📝 <b>Тема:</b> {topic}\n\n"
            f"📁 <b>Файлів завантажено:</b> {len(uploaded_files)}\n"
        )

        if folder_link:
            response_message += f"\n🔗 <a href='{folder_link}'>Перейти до папки на Google Drive</a>"

        # Відправляємо відповідь у Telegram
        send_telegram_message(chat_id, response_message)

        return jsonify({
            'status': 'success',
            'group': group,
            'student': student,
            'date': date_str,
            'topic': topic,
            'files_uploaded': len(uploaded_files),
            'folder_link': folder_link
        }), 200

    except Exception as e:
        logger.error(f"Помилка в webhook: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    # Railway використовує PORT змінну
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
