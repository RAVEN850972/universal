/**
 * === ОБЩИЕ JAVASCRIPT УТИЛИТЫ ===
 * static/js/common.js
 */

// === ГЛОБАЛЬНЫЕ УТИЛИТЫ ===

/**
 * Показать уведомление
 * @param {string} message - Текст сообщения
 * @param {string} type - Тип: 'error', 'success', 'warning', 'info'
 * @param {number} duration - Длительность в мс (0 = не скрывать автоматически)
 * @param {string} container - ID контейнера
 */
function showAlert(message, type = 'error', duration = 5000, container = 'alerts-container') {
    const alertContainer = document.getElementById(container);
    if (!alertContainer) {
        console.warn(`Контейнер ${container} не найден`);
        return;
    }
    
    // Удаляем предыдущие уведомления если нужно
    alertContainer.innerHTML = '';
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible`;
    
    const icons = {
        error: 'fas fa-exclamation-triangle',
        success: 'fas fa-check-circle',
        warning: 'fas fa-exclamation-circle',
        info: 'fas fa-info-circle'
    };
    
    alert.innerHTML = `
        <i class="${icons[type] || icons.error}"></i>
        ${message}
        <button type="button" class="alert-dismiss" onclick="dismissAlert(this)">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    alertContainer.appendChild(alert);
    
    // Автоматически скрываем
    if (duration > 0) {
        setTimeout(() => {
            dismissAlert(alert.querySelector('.alert-dismiss'));
        }, duration);
    }
    
    return alert;
}

/**
 * Закрыть уведомление
 * @param {Element} button - Кнопка закрытия
 */
function dismissAlert(button) {
    const alert = button.closest('.alert');
    if (alert) {
        alert.style.animation = 'fadeOut 0.3s ease-out';
        setTimeout(() => {
            alert.remove();
        }, 300);
    }
}

/**
 * Установить состояние загрузки для элемента
 * @param {Element} element - Элемент (обычно кнопка)
 * @param {boolean} loading - Состояние загрузки
 */
function setLoading(element, loading = true) {
    if (loading) {
        element.classList.add('loading');
        element.disabled = true;
        element.setAttribute('data-original-text', element.innerHTML);
    } else {
        element.classList.remove('loading');
        element.disabled = false;
        const originalText = element.getAttribute('data-original-text');
        if (originalText) {
            element.innerHTML = originalText;
            element.removeAttribute('data-original-text');
        }
    }
}

/**
 * Валидация формы
 * @param {HTMLFormElement} form - Форма для валидации
 * @param {Object} rules - Правила валидации
 * @returns {Object} - Результат валидации
 */
function validateForm(form, rules = {}) {
    const errors = {};
    const formData = new FormData(form);
    
    for (const [fieldName, fieldRules] of Object.entries(rules)) {
        const value = formData.get(fieldName);
        const field = form.querySelector(`[name="${fieldName}"]`);
        
        // Очищаем предыдущие ошибки
        if (field) {
            field.classList.remove('error');
            const errorMsg = field.parentNode.querySelector('.form-error');
            if (errorMsg) errorMsg.remove();
        }
        
        // Проверяем правила
        for (const rule of fieldRules) {
            let isValid = true;
            let errorMessage = '';
            
            switch (rule.type) {
                case 'required':
                    isValid = value && value.trim() !== '';
                    errorMessage = rule.message || 'Поле обязательно для заполнения';
                    break;
                    
                case 'minLength':
                    isValid = !value || value.length >= rule.value;
                    errorMessage = rule.message || `Минимум ${rule.value} символов`;
                    break;
                    
                case 'maxLength':
                    isValid = !value || value.length <= rule.value;
                    errorMessage = rule.message || `Максимум ${rule.value} символов`;
                    break;
                    
                case 'email':
                    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    isValid = !value || emailRegex.test(value);
                    errorMessage = rule.message || 'Неверный формат email';
                    break;
                    
                case 'pattern':
                    isValid = !value || rule.value.test(value);
                    errorMessage = rule.message || 'Неверный формат';
                    break;
                    
                case 'custom':
                    isValid = rule.validator(value, formData);
                    errorMessage = rule.message || 'Неверное значение';
                    break;
            }
            
            if (!isValid) {
                errors[fieldName] = errorMessage;
                
                if (field) {
                    field.classList.add('error');
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'form-error';
                    errorDiv.textContent = errorMessage;
                    field.parentNode.appendChild(errorDiv);
                }
                
                break; // Останавливаемся на первой ошибке
            }
        }
    }
    
    return {
        isValid: Object.keys(errors).length === 0,
        errors
    };
}

/**
 * Отправка AJAX запроса
 * @param {string} url - URL для запроса
 * @param {Object} options - Опции запроса
 * @returns {Promise}
 */
async function makeRequest(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    };
    
    // Добавляем CSRF токен для POST запросов
    if (options.method && options.method.toUpperCase() !== 'GET') {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfToken) {
            defaultOptions.headers['X-CSRFToken'] = csrfToken.value;
        }
    }
    
    const finalOptions = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(url, finalOptions);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || `HTTP ${response.status}`);
        }
        
        return { success: true, data };
    } catch (error) {
        console.error('Request failed:', error);
        return { success: false, error: error.message };
    }
}

/**
 * Форматирование числа как валюты
 * @param {number} amount - Сумма
 * @param {string} currency - Валюта
 * @returns {string}
 */
function formatCurrency(amount, currency = 'RUB') {
    return new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    }).format(amount);
}

/**
 * Форматирование даты
 * @param {Date|string} date - Дата
 * @param {Object} options - Опции форматирования
 * @returns {string}
 */
function formatDate(date, options = {}) {
    const defaultOptions = {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    
    return new Intl.DateTimeFormat('ru-RU', finalOptions).format(dateObj);
}

/**
 * Дебаунс функции
 * @param {Function} func - Функция для дебаунса
 * @param {number} delay - Задержка в мс
 * @returns {Function}
 */
function debounce(func, delay) {
    let timeoutId;
    return function (...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

/**
 * Throttle функции
 * @param {Function} func - Функция для throttle
 * @param {number} limit - Лимит в мс
 * @returns {Function}
 */
function throttle(func, limit) {
    let inThrottle;
    return function (...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// === МОДАЛЬНЫЕ ОКНА ===

/**
 * Показать модальное окно
 * @param {string} modalId - ID модального окна
 */
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    // Создаем backdrop
    const backdrop = document.createElement('div');
    backdrop.className = 'modal-backdrop';
    backdrop.onclick = () => hideModal(modalId);
    
    document.body.appendChild(backdrop);
    modal.style.display = 'block';
    modal.classList.add('fade-in');
    
    // Блокируем скролл
    document.body.style.overflow = 'hidden';
    
    // Фокус на модальном окне
    modal.focus();
}

/**
 * Скрыть модальное окно
 * @param {string} modalId - ID модального окна
 */
function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    const backdrop = document.querySelector('.modal-backdrop');
    
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('fade-in');
    }
    
    if (backdrop) {
        backdrop.remove();
    }
    
    // Восстанавливаем скролл
    document.body.style.overflow = '';
}

// === УТИЛИТЫ ДЛЯ РАБОТЫ С DOM ===

/**
 * Готовность DOM
 * @param {Function} callback - Функция для выполнения
 */
function ready(callback) {
    if (document.readyState !== 'loading') {
        callback();
    } else {
        document.addEventListener('DOMContentLoaded', callback);
    }
}

/**
 * Создание элемента с атрибутами
 * @param {string} tag - Тег элемента
 * @param {Object} attributes - Атрибуты
 * @param {string} content - Содержимое
 * @returns {Element}
 */
function createElement(tag, attributes = {}, content = '') {
    const element = document.createElement(tag);
    
    for (const [key, value] of Object.entries(attributes)) {
        if (key === 'className') {
            element.className = value;
        } else if (key === 'style' && typeof value === 'object') {
            Object.assign(element.style, value);
        } else {
            element.setAttribute(key, value);
        }
    }
    
    if (content) {
        element.innerHTML = content;
    }
    
    return element;
}

// === УТИЛИТЫ ДЛЯ АНИМАЦИЙ ===

/**
 * Плавная прокрутка к элементу
 * @param {string|Element} target - Селектор или элемент
 * @param {number} offset - Смещение в пикселях
 */
function scrollToElement(target, offset = 0) {
    const element = typeof target === 'string' ? document.querySelector(target) : target;
    if (!element) return;
    
    const elementPosition = element.offsetTop;
    const offsetPosition = elementPosition - offset;
    
    window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth'
    });
}

/**
 * Анимация счетчика
 * @param {Element} element - Элемент для анимации
 * @param {number} target - Целевое значение
 * @param {number} duration - Длительность в мс
 */
function animateCounter(element, target, duration = 1000) {
    const start = parseInt(element.textContent) || 0;
    const increment = (target - start) / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= target) || (increment < 0 && current <= target)) {
            current = target;
            clearInterval(timer);
        }
        element.textContent = Math.floor(current);
    }, 16);
}

// === ОБРАБОТЧИКИ СОБЫТИЙ ===

// Закрытие модальных окон по Escape
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const backdrop = document.querySelector('.modal-backdrop');
        if (backdrop) {
            backdrop.click();
        }
    }
});

// Автоматическое закрытие уведомлений при клике
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('alert-dismiss')) {
        dismissAlert(e.target);
    }
});

// Инициализация подсказок и других компонентов
ready(function() {
    // Автофокус на первое поле формы
    const firstInput = document.querySelector('input:not([type="hidden"]):not([disabled])');
    if (firstInput && !document.querySelector('[autofocus]')) {
        firstInput.focus();
    }
    
    // Обработка форм с подтверждением
    const formsWithConfirm = document.querySelectorAll('[data-confirm]');
    formsWithConfirm.forEach(form => {
        form.addEventListener('submit', function(e) {
            const message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
    
    // Автоматическое скрытие флеш-сообщений
    const djangoMessages = document.querySelectorAll('#django-messages .alert');
    djangoMessages.forEach(alert => {
        setTimeout(() => {
            const dismissBtn = alert.querySelector('.alert-dismiss');
            if (dismissBtn) {
                dismissAlert(dismissBtn);
            } else {
                alert.style.animation = 'fadeOut 0.3s ease-out';
                setTimeout(() => alert.remove(), 300);
            }
        }, 5000);
    });
});

// === ЭКСПОРТ ДЛЯ МОДУЛЬНЫХ СИСТЕМ ===
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        showAlert,
        dismissAlert,
        setLoading,
        validateForm,
        makeRequest,
        formatCurrency,
        formatDate,
        debounce,
        throttle,
        showModal,
        hideModal,
        ready,
        createElement,
        scrollToElement,
        animateCounter
    };
}