# Universal Service CRM

Гибкая CRM-система для малого и среднего бизнеса в сфере услуг с поддержкой мультитенантности.

## Основные возможности

- ✅ **Мультитенантность** - поддержка нескольких компаний в одной системе
- ✅ **Управление заказами** - создание, отслеживание, назначение исполнителей
- ✅ **Управление клиентами** - база клиентов с историей заказов
- ✅ **Управление сотрудниками** - роли, зарплаты, комиссии
- ✅ **Финансовый модуль** - учет доходов, расходов, расчет зарплат
- ✅ **Гранулярные права доступа** - владелец, менеджер, исполнитель
- ✅ **Responsive веб-интерфейс** - адаптивный дизайн
- ✅ **REST API** - для интеграций и мобильных приложений

## Роли пользователей

### Владелец (Owner)
- Полный доступ ко всем функциям
- Управление сотрудниками
- Настройки компании
- Финансовая отчетность

### Менеджер (Manager)
- Управление заказами и клиентами
- Просмотр отчетов
- Назначение исполнителей
- Расчет зарплат

### Исполнитель (Executor)
- Просмотр только назначенных заказов
- Обновление статуса работ
- Просмотр своей зарплаты

## Установка и запуск

### Требования
- Python 3.8+
- Django 4.2+
- SQLite (для разработки) или PostgreSQL (для продакшена)

### Быстрый старт

1. **Клонирование и настройка окружения**
```bash
git clone <repository-url>
cd universal-service-crm
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

2. **Настройка базы данных**
```bash
python manage.py makemigrations
python manage.py migrate
```

3. **Создание демо-данных**
```bash
python manage.py setup_demo_data
```

4. **Запуск сервера разработки**
```bash
python manage.py runserver
```

5. **Доступ к системе**
- Веб-интерфейс: http://127.0.0.1:8000/
- Админ-панель: http://127.0.0.1:8000/admin/

### Демо-аккаунты
- **admin/admin123** - суперпользователь
- **owner1/password123** - владелец компании
- **manager1/password123** - менеджер
- **executor1/password123** - исполнитель

## Структура проекта

```
universal_crm/
├── manage.py
├── requirements.txt
├── universal_crm/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── crm/
│   ├── __init__.py
│   ├── models.py          # Модели данных
│   ├── views.py           # Представления
│   ├── forms.py           # Формы
│   ├── admin.py           # Админ-панель
│   ├── urls.py            # URL-маршруты
│   ├── api_urls.py        # API маршруты
│   ├── permissions.py     # Права доступа
│   ├── middleware.py      # Мидлвары
│   ├── utils.py           # Утилиты
│   └── management/
│       └── commands/      # Команды управления
├── templates/             # HTML шаблоны
│   ├── base.html
│   ├── auth/
│   └── crm/
└── static/               # Статические файлы
    ├── css/
    ├── js/
    └── img/
```

## API Endpoints

### Основные API маршруты
```
GET    /api/services/                    # Список услуг компании
GET    /api/clients/?q=<search>          # Поиск клиентов
POST   /api/orders/<id>/status/          # Обновление статуса заказа
GET    /api/orders/<id>/executors/       # Исполнители заказа
POST   /api/salary/calculate/            # Расчет зарплаты
GET    /api/dashboard/stats/             # Статистика для дашборда
```

### Примеры использования API
```javascript
// Получить услуги компании
fetch('/api/services/')
  .then(response => response.json())
  .then(data => console.log(data));

// Обновить статус заказа
fetch('/api/orders/123/status/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded',
    'X-CSRFToken': getCookie('csrftoken')
  },
  body: 'status=completed'
});
```

## Настройка для продакшена

### PostgreSQL
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'universal_crm',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Переменные окружения
Создайте файл `.env`:
```
SECRET_KEY=your-secret-key-here
DEBUG=False
DATABASE_URL=postgresql://user:password@localhost/dbname
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### Nginx конфигурация
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location /static/ {
        alias /path/to/your/staticfiles/;
    }
    
    location /media/ {
        alias /path/to/your/media/;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Systemd сервис
```ini
# /etc/systemd/system/universal-crm.service
[Unit]
Description=Universal CRM Django Application
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/path/to/universal-service-crm
Environment=PATH=/path/to/venv/bin
ExecStart=/path/to/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 universal_crm.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

## Управляющие команды

### Создание демо-данных
```bash
# Создать демо-данные
python manage.py setup_demo_data

# Очистить и пересоздать данные
python manage.py setup_demo_data --clear
```

### Расчет зарплат
```bash
# Рассчитать зарплаты за текущий месяц
python manage.py calculate_salaries

# За конкретный период
python manage.py calculate_salaries --year 2024 --month 12

# Для конкретной компании
python manage.py calculate_salaries --company "Строительная компания"
```

### Экспорт данных
```bash
# Экспорт заказов
python manage.py export_data --type orders --output orders.csv

# Экспорт клиентов конкретной компании
python manage.py export_data --type clients --company 1 --output clients.csv

# Экспорт финансовых операций
python manage.py export_data --type transactions --output transactions.csv
```

## Основные модели данных

### Company (Компания)
- Основа мультитенантности
- Содержит информацию о компании
- Связана с пользователями через CompanyUser

### User (Пользователь)
- Расширенная модель пользователя Django
- Может принадлежать к нескольким компаниям
- Роль определяется в CompanyUser

### Order (Заказ)
- Основная сущность для работы
- Содержит услуги через OrderService
- Назначается исполнителям через OrderExecutor

### Client (Клиент)
- Заказчики услуг
- Привязаны к конкретной компании
- Содержат историю заказов

### Service (Услуга)
- Каталог услуг компании
- Базовые цены и единицы измерения
- Используются в заказах

## Безопасность

### Мультитенантность
- Все данные фильтруются по текущей компании
- Middleware автоматически проверяет принадлежность
- Невозможен доступ к данным чужих компаний

### Права доступа
- Декораторы для проверки ролей
- Миксины для автоматической фильтрации
- Гранулярные права на уровне объектов

### Аудит
- Логирование всех действий
- Отслеживание изменений заказов
- Финансовые операции с временными метками

## Мониторинг и логирование

### Логи
```python
# Конфигурация в settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/django.log',
        },
    },
    'loggers': {
        'crm': {
            'handlers': ['file'],
            'level': 'DEBUG',
        },
    },
}
```

### Метрики
- Количество заказов по статусам
- Доходы по периодам
- Эффективность исполнителей
- Конверсия клиентов

## Планы развития (v2.0+)

### Ближайшие фичи
- [ ] Календарь и планирование задач
- [ ] Уведомления в Telegram
- [ ] Мобильное приложение (React Native)
- [ ] Интеграция с платежными системами
- [ ] Документооборот и подпись договоров

### Интеграции
- [ ] 1C:Бухгалтерия
- [ ] Яндекс.Карты для адресов
- [ ] SMS-уведомления
- [ ] Email-маркетинг
- [ ] Интеграция с банками

### Аналитика
- [ ] Машинное обучение для прогнозов
- [ ] Автоматическое ценообразование
- [ ] Анализ эффективности сотрудников
- [ ] Предиктивная аналитика по клиентам

## Поддержка

### Документация
- Подробная документация API
- Видео-инструкции для пользователей
- FAQ по настройке и использованию

### Техническая поддержка
- Система тикетов
- Telegram-чат для разработчиков
- Еженедельные вебинары

## Лицензия

MIT License - свободное использование для коммерческих и некоммерческих проектов.

## Контрибьюторы

Мы приветствуем вклад сообщества! Ознакомьтесь с CONTRIBUTING.md для получения инструкций по участию в разработке.

---

**Universal Service CRM** - современное решение для автоматизации сервисного бизнеса. 
Начните работу уже сегодня! 🚀