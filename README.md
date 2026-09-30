# 🤖 Telegram Bot for Miro Lesson Transfer

Автоматичний бот для переносу уроків на Miro дошку.

## 📋 Функціональність

✅ Отримує інформацію про урок від викладача  
✅ Парсить структуру: Група / Учень / Дата / Тема  
✅ Завантажує файли (картинки, PDF, текст)  
✅ Створює окремий фрейм на Miro для кожного уроку  
✅ Додає всі матеріали в фрейм  
✅ Відправляє підтвердження  

## 🚀 Быстрий старт

1. **Отримай токени**:
   - Telegram: `8810628323:AAFdxOn8CLTy6QniMChKd-o_Fb84Q5EVba4`
   - Miro: https://miro.com/app/settings/account/security → Create token

2. **Розгорни на Railway**:
   - GitHub repo
   - Railway integration
   - Environment variables

3. **Вжайся в боту**:
   ```
   B2 Group / Ірина / 29.09.2026 / Present Perfect
   ```
   
   Потім надішли файли + `/done`

## 📖 Докладна інструкція

Дивись `ІНСТРУКЦІЯ_RAILWAY.md`

## 🛠 Структура проекту

```
lesson-bot/
├── bot_v2.py              # Основний скрипт бота
├── requirements.txt       # Залежності Python
├── Procfile              # Конфіг для Railway
├── .gitignore            # Файли для Git
├── README.md             # Цей файл
└── ІНСТРУКЦІЯ_RAILWAY.md # Докладна інструкція
```

## 🔐 Переменные окружения

```
TELEGRAM_TOKEN = <твій токен бота>
MIRO_TOKEN = <твій Miro API токен>
```

## 📊 Конфіг

```python
MIRO_BOARD_ID = "uXjVH8UqCc4"  # Дошка для уроків
MIRO_API_URL = "https://api.miro.com/v2"
```

## 🆘 Проблеми?

Перевір логи в Railway:
- Railway Dashboard → Logs
- Ищи ошибки в TELEGRAM_TOKEN або MIRO_TOKEN

## 📝 Ліцензія

Використовується тільки для Maryna Kovalenko (@marinakovalenko_EDM)

---

**Потрібна допомога?** Напиши в боту `/start`
