# 🪟 Модальные окна для Universal Service CRM

## Обзор реализации

Реализована комплексная система модальных окон для CRM, которая обеспечивает:

- ✅ **Универсальный менеджер модальных окон** (JavaScript)
- ✅ **Серверные представления** для загрузки контента через AJAX
- ✅ **Готовые шаблоны** для основных операций
- ✅ **Интеграцию с формами** и валидацией
- ✅ **Быстрые действия** без перезагрузки страницы

## 📁 Структура файлов

### Новые файлы
```
crm/
├── modal_views.py          # Представления для модальных окон
├── modal_urls.py           # URL-маршруты для модальных окон
templates/crm/modals/
├── base_modal.html         # Базовый шаблон модального окна
├── order_detail_modal.html # Детали заказа
├── order_create_modal.html # Создание заказа
├── client_create_modal.html # Создание клиента
├── assign_executor_modal.html # Назначение исполнителя
└── orders_report_modal.html # Отчет по заказам
static/js/
└── modal-manager.js        # JavaScript для управления модальными окнами
```

### Обновленные файлы
```
universal_crm/urls.py       # Добавлены modal_urls
templates/base.html         # Подключен modal-manager.js
templates/crm/orders/list.html # Пример использования
```

## 🚀 Как использовать

### 1. Базовое использование в HTML

```html
<!-- Кнопка для открытия модального окна -->
<button type="button" class="btn btn-primary" 
        data-modal-url="{% url 'order_create_modal' %}" 
        data-modal-title="Создать заказ" 
        data-modal-size="xl">
    <i class="fas fa-plus"></i> Создать заказ
</button>

<!-- Ссылка с модальным окном -->
<a href="#" data-modal-url="{% url 'order_detail_modal' order.id %}" 
           data-modal-title="Заказ #{{ order.id }}" 
           data-modal-size="lg">
    #{{ order.id }}
</a>
```

### 2. Программное открытие

```javascript
// Простое открытие
loadModal('/modals/orders/123/detail/', 'Заказ #123', 'xl');

// С callback функцией
loadModal('/modals/clients/create/', 'Создать клиента', 'lg', function(data) {
    console.log('Модальное окно загружено', data);
});

// Закрытие модального окна
closeModal();
```

### 3. Создание нового модального представления

```python
# crm/modal_views.py
@company_required
@modal_view('crm/modals/my_modal.html')
def my_modal_view(request):
    """Мое модальное окно"""
    if request.method == 'POST':
        # Обработка POST запроса
        return JsonResponse({
            'success': True,
            'message': 'Операция выполнена успешно'
        })
    
    # GET запрос - возвращаем контекст для шаблона
    return {
        'data': 'Мои данные',
        'form': MyForm()
    }
```

### 4. Создание шаблона модального окна

```html
<!-- templates/crm/modals/my_modal.html -->
{% extends "crm/modals/base_modal.html" %}

{% block modal_title %}Заголовок модального окна{% endblock %}

{% block modal_body %}
<form id="myForm" method="post">
    {% csrf_token %}
    <!-- Содержимое формы -->
    {{ form.as_p }}
</form>
{% endblock %}

{% block modal_footer %}
<button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Отмена</button>
<button type="submit" form="myForm" class="btn btn-primary">Сохранить</button>

<script>
document.getElementById('myForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    fetch('/modals/my-url/', {
        method: 'POST',
        body: new FormData(this),
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', data.message);
            closeModal();
            location.reload();
        } else {
            showAlert('danger', data.error);
        }
    });
});
</script>
{% endblock %}
```

## 🛠 Доступные модальные окна

### Заказы
- **Детали заказа**: `/modals/orders/{id}/detail/`
- **Создание заказа**: `/modals/orders/create/`
- **Редактирование заказа**: `/modals/orders/{id}/edit/`
- **Назначение исполнителя**: `/modals/orders/{id}/assign-executor/`

### Клиенты
- **Создание клиента**: `/modals/clients/create/`
- **Редактирование клиента**: `/modals/clients/{id}/edit/`
- **Детали клиента**: `/modals/clients/{id}/detail/`

### Услуги
- **Создание услуги**: `/modals/services/create/`
- **Редактирование услуги**: `/modals/services/{id}/edit/`

### Сотрудники
- **Добавление сотрудника**: `/modals/employees/create/`
- **Детали сотрудника**: `/modals/employees/{id}/detail/`

### Финансы
- **Создание операции**: `/modals/transactions/create/`
- **Расчет зарплаты**: `/modals/salary/calculate/`

### Отчеты
- **Отчет по заказам**: `/modals/reports/orders/`
- **Моя производительность**: `/modals/my-performance/`

## ⚡ Быстрые действия

### Обновление статуса заказа
```javascript
function quickStatusUpdate(orderId, newStatus) {
    fetch(`/quick/orders/${orderId}/status/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: `status=${newStatus}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', data.message);
            location.reload();
        }
    });
}
```

### Быстрое назначение исполнителя
```javascript
function quickAssignExecutor(orderId, executorId) {
    fetch(`/quick/orders/${orderId}/assign/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: `executor_id=${executorId}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', data.message);
        }
    });
}
```

## 🎨 JavaScript API модального менеджера

### Основные методы
```javascript
// Загрузка модального окна
modalManager.loadModal(url, title, size, callback);

// Закрытие модального окна
modalManager.closeModal();

// Показать уведомление
modalManager.notify(message, type); // success, danger, warning, info

// Показать подтверждение
modalManager.confirm(message, onConfirm, onCancel);

// Показать ошибку
modalManager.showError(message);
```

### Утилиты
```javascript
// Получить CSRF токен
getCookie('csrftoken');

// Показать alert
showAlert('success', 'Сообщение');

// Форматирование валюты
utils.formatCurrency(1234.56); // "1 234,56 ₽"

// Форматирование даты
utils.formatDate(new Date()); // "01.12.2024"

// Дебаунс функции
const debouncedSearch = utils.debounce(searchFunction, 300);
```

## 🔧 Настройка и кастомизация

### Размеры модальных окон
- `sm` - маленький (300px)
- `lg` - большой (800px) 
- `xl` - очень большой (1140px)
- По умолчанию - обычный (500px)

### Кастомные стили
```css
/* static/css/custom.css */
.modal-backdrop.show {
    opacity: 0.5;
}

.service-row {
    transition: all 0.3s ease;
}

.service-row:hover {
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
```

### Интеграция с внешними библиотеками
```javascript
// Инициализация Select2 в модальных окнах
modalManager.initModalComponents = function() {
    // ... существующий код ...
    
    // Добавляем кастомную инициализацию
    if (window.jQuery && window.jQuery.fn.select2) {
        modal.querySelectorAll('.select2').forEach(select => {
            $(select).select2({
                dropdownParent: $(modal)
            });
        });
    }
};
```

## 📱 Адаптивность

Все модальные окна автоматически адаптируются под мобильные устройства:
- На мобильных устройствах окна занимают почти весь экран
- Сенсорные жесты для закрытия
- Оптимизированные размеры кнопок

## 🔐 Безопасность

- ✅ Автоматическая передача CSRF токенов
- ✅ Проверка прав доступа на сервере
- ✅ Валидация данных в формах
- ✅ Фильтрация по текущей компании

## 🚀 Развертывание

### 1. Добавить URL-маршруты
```python
# universal_crm/urls.py
urlpatterns = [
    # ... существующие маршруты ...
    path('', include('crm.modal_urls')),  # Добавить эту строку
]
```

### 2. Обновить базовый шаблон
```html
<!-- В base.html добавить перед закрывающим </body> -->
<div id="modalContainer"></div>
<script src="{% static 'js/modal-manager.js' %}"></script>
```

### 3. Подключить зависимости
```html
<!-- Bootstrap 5.3+ обязательно -->
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

<!-- Chart.js для графиков -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
```

## 📊 Производительность

- **Ленивая загрузка**: Контент загружается только при открытии
- **Кэширование**: Повторные запросы к одному URL кэшируются
- **Оптимизация DOM**: Модальные окна удаляются после закрытия
- **Минимальные зависимости**: Только Bootstrap и Chart.js

## 🧪 Тестирование

```javascript
// Пример тестирования модального окна
describe('Modal Manager', () => {
    test('should load modal content', async () => {
        const modalManager = new ModalManager();
        
        // Мокаем fetch
        global.fetch = jest.fn(() =>
            Promise.resolve({
                ok: true,
                json: () => Promise.resolve({
                    success: true,
                    html: '<div>Test content</div>'
                })
            })
        );
        
        await modalManager.loadModal('/test-url/', 'Test Modal');
        
        expect(document.getElementById('dynamicModal')).toBeTruthy();
    });
});
```

## 📝 TODO / Планы развития

- [ ] Поддержка множественных модальных окон
- [ ] Анимации открытия/закрытия
- [ ] Интеграция с WebSocket для real-time обновлений
- [ ] Поддержка drag & drop в модальных окнах
- [ ] Мобильная оптимизация жестов
- [ ] Интеграция с PWA для офлайн работы

---

**Модальные окна полностью готовы к использованию!** 🎉

Теперь вы можете создавать современный пользовательский интерфейс без перезагрузки страниц.
