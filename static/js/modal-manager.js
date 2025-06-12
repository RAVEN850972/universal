// static/js/modal-manager.js

/**
 * Универсальная система управления модальными окнами для CRM
 */

class ModalManager {
    constructor() {
        this.currentModal = null;
        this.modalContainer = null;
        this.init();
    }

    init() {
        // Создаем контейнер для модальных окон если его нет
        if (!document.getElementById('modalContainer')) {
            this.modalContainer = document.createElement('div');
            this.modalContainer.id = 'modalContainer';
            document.body.appendChild(this.modalContainer);
        } else {
            this.modalContainer = document.getElementById('modalContainer');
        }
        
        // Добавляем обработчики событий
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Обработчик для кнопок с data-modal-url
        document.addEventListener('click', (e) => {
            const modalTrigger = e.target.closest('[data-modal-url]');
            if (modalTrigger) {
                e.preventDefault();
                const url = modalTrigger.dataset.modalUrl;
                const title = modalTrigger.dataset.modalTitle || 'Модальное окно';
                const size = modalTrigger.dataset.modalSize || 'lg';
                this.loadModal(url, title, size);
            }
        });

        // Обработчик для закрытия модального окна
        document.addEventListener('hidden.bs.modal', (e) => {
            if (e.target.id === 'dynamicModal') {
                this.cleanup();
            }
        });
    }

    /**
     * Загрузка содержимого модального окна
     * @param {string} url - URL для загрузки содержимого
     * @param {string} title - Заголовок модального окна
     * @param {string} size - Размер модального окна (sm, lg, xl)
     * @param {function} callback - Функция обратного вызова после загрузки
     */
    loadModal(url, title = 'Модальное окно', size = 'lg', callback = null) {
        // Показываем загрузчик
        this.showLoader();

        // Загружаем содержимое
        fetch(url, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': this.getCookie('csrftoken')
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.html) {
                this.showModal(data.html, title, size);
                if (callback) callback(data);
            } else {
                throw new Error(data.error || 'Ошибка загрузки модального окна');
            }
        })
        .catch(error => {
            this.showError('Ошибка загрузки: ' + error.message);
            console.error('Modal load error:', error);
        })
        .finally(() => {
            this.hideLoader();
        });
    }

    /**
     * Отображение модального окна с содержимым
     * @param {string} html - HTML содержимое
     * @param {string} title - Заголовок
     * @param {string} size - Размер
     */
    showModal(html, title, size) {
        // Создаем структуру модального окна
        const modalHtml = `
            <div class="modal fade" id="dynamicModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-${size}">
                    <div class="modal-content">
                        ${html}
                    </div>
                </div>
            </div>
        `;

        // Вставляем в контейнер
        this.modalContainer.innerHTML = modalHtml;
        
        // Инициализируем Bootstrap modal
        this.currentModal = new bootstrap.Modal(document.getElementById('dynamicModal'), {
            backdrop: 'static',
            keyboard: true
        });

        // Показываем модальное окно
        this.currentModal.show();

        // Инициализируем дополнительные элементы в модальном окне
        this.initModalComponents();
    }

    /**
     * Инициализация компонентов в модальном окне
     */
    initModalComponents() {
        const modal = document.getElementById('dynamicModal');
        if (!modal) return;

        // Инициализируем tooltips
        const tooltips = modal.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltips.forEach(tooltip => {
            new bootstrap.Tooltip(tooltip);
        });

        // Инициализируем popovers
        const popovers = modal.querySelectorAll('[data-bs-toggle="popover"]');
        popovers.forEach(popover => {
            new bootstrap.Popover(popover);
        });

        // Инициализируем select2 если есть
        if (window.jQuery && window.jQuery.fn.select2) {
            modal.querySelectorAll('.select2').forEach(select => {
                $(select).select2({
                    dropdownParent: $(modal)
                });
            });
        }

        // Устанавливаем фокус на первое поле ввода
        const firstInput = modal.querySelector('input:not([type="hidden"]), textarea, select');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    }

    /**
     * Закрытие текущего модального окна
     */
    closeModal() {
        if (this.currentModal) {
            this.currentModal.hide();
        }
    }

    /**
     * Очистка после закрытия модального окна
     */
    cleanup() {
        if (this.currentModal) {
            this.currentModal.dispose();
            this.currentModal = null;
        }
        this.modalContainer.innerHTML = '';
    }

    /**
     * Показать загрузчик
     */
    showLoader() {
        const loaderHtml = `
            <div class="modal fade show" id="modalLoader" style="display: block;" tabindex="-1">
                <div class="modal-dialog modal-sm">
                    <div class="modal-content">
                        <div class="modal-body text-center py-4">
                            <div class="spinner-border text-primary" role="status">
                                <span class="visually-hidden">Загрузка...</span>
                            </div>
                            <div class="mt-2">Загрузка...</div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="modal-backdrop fade show"></div>
        `;
        
        this.modalContainer.innerHTML = loaderHtml;
    }

    /**
     * Скрыть загрузчик
     */
    hideLoader() {
        const loader = document.getElementById('modalLoader');
        if (loader) {
            loader.remove();
        }
        const backdrop = this.modalContainer.querySelector('.modal-backdrop');
        if (backdrop) {
            backdrop.remove();
        }
    }

    /**
     * Показать ошибку
     * @param {string} message - Сообщение об ошибке
     */
    showError(message) {
        const errorHtml = `
            <div class="modal fade show" id="modalError" style="display: block;" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-danger text-white">
                            <h5 class="modal-title">Ошибка</h5>
                            <button type="button" class="btn-close btn-close-white" onclick="modalManager.closeError()"></button>
                        </div>
                        <div class="modal-body">
                            <div class="alert alert-danger mb-0">
                                <i class="fas fa-exclamation-triangle me-2"></i>
                                ${message}
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" onclick="modalManager.closeError()">
                                Закрыть
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            <div class="modal-backdrop fade show"></div>
        `;
        
        this.modalContainer.innerHTML = errorHtml;
    }

    /**
     * Закрыть окно ошибки
     */
    closeError() {
        const errorModal = document.getElementById('modalError');
        if (errorModal) {
            errorModal.remove();
        }
        const backdrop = this.modalContainer.querySelector('.modal-backdrop');
        if (backdrop) {
            backdrop.remove();
        }
    }

    /**
     * Получить значение cookie
     * @param {string} name - Имя cookie
     * @returns {string} Значение cookie
     */
    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    /**
     * Подтверждение действия
     * @param {string} message - Сообщение для подтверждения
     * @param {function} onConfirm - Функция при подтверждении
     * @param {function} onCancel - Функция при отмене
     */
    confirm(message, onConfirm, onCancel = null) {
        const confirmHtml = `
            <div class="modal fade show" id="confirmModal" style="display: block;" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Подтверждение</h5>
                        </div>
                        <div class="modal-body">
                            <div class="d-flex align-items-center">
                                <i class="fas fa-question-circle text-warning fa-2x me-3"></i>
                                <div>${message}</div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" onclick="modalManager.closeConfirm(false)">
                                Отмена
                            </button>
                            <button type="button" class="btn btn-primary" onclick="modalManager.closeConfirm(true)">
                                Подтвердить
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            <div class="modal-backdrop fade show"></div>
        `;
        
        this.modalContainer.innerHTML = confirmHtml;
        this.confirmCallback = onConfirm;
        this.cancelCallback = onCancel;
    }

    /**
     * Закрыть окно подтверждения
     * @param {boolean} confirmed - Подтверждено ли действие
     */
    closeConfirm(confirmed) {
        const confirmModal = document.getElementById('confirmModal');
        if (confirmModal) {
            confirmModal.remove();
        }
        const backdrop = this.modalContainer.querySelector('.modal-backdrop');
        if (backdrop) {
            backdrop.remove();
        }

        if (confirmed && this.confirmCallback) {
            this.confirmCallback();
        } else if (!confirmed && this.cancelCallback) {
            this.cancelCallback();
        }

        this.confirmCallback = null;
        this.cancelCallback = null;
    }

    /**
     * Быстрое создание уведомления
     * @param {string} message - Сообщение
     * @param {string} type - Тип (success, danger, warning, info)
     */
    notify(message, type = 'info') {
        const alertHtml = `
            <div class="modal fade show" id="notifyModal" style="display: block;" tabindex="-1">
                <div class="modal-dialog modal-sm">
                    <div class="modal-content">
                        <div class="modal-body text-center py-4">
                            <div class="alert alert-${type} mb-0">
                                <i class="fas fa-${this.getIconForType(type)} me-2"></i>
                                ${message}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="modal-backdrop fade show"></div>
        `;
        
        this.modalContainer.innerHTML = alertHtml;
        
        // Автоматически закрываем через 3 секунды
        setTimeout(() => {
            const notifyModal = document.getElementById('notifyModal');
            if (notifyModal) {
                notifyModal.remove();
            }
            const backdrop = this.modalContainer.querySelector('.modal-backdrop');
            if (backdrop) {
                backdrop.remove();
            }
        }, 3000);
    }

    /**
     * Получить иконку для типа уведомления
     * @param {string} type - Тип уведомления
     * @returns {string} Класс иконки
     */
    getIconForType(type) {
        const icons = {
            'success': 'check-circle',
            'danger': 'exclamation-triangle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
}

// Глобальные функции для совместимости
window.modalManager = new ModalManager();

// Экспорт функций для использования в шаблонах
window.loadModal = (url, title, size, callback) => modalManager.loadModal(url, title, size, callback);
window.closeModal = () => modalManager.closeModal();
window.showAlert = (type, message) => modalManager.notify(message, type);
window.getCookie = (name) => modalManager.getCookie(name);
window.confirmAction = (message, onConfirm, onCancel) => modalManager.confirm(message, onConfirm, onCancel);

// Дополнительные утилиты
window.utils = {
    /**
     * Форматирование числа как валюты
     * @param {number} amount - Сумма
     * @returns {string} Отформатированная строка
     */
    formatCurrency: (amount) => {
        return new Intl.NumberFormat('ru-RU', {
            style: 'currency',
            currency: 'RUB'
        }).format(amount);
    },

    /**
     * Форматирование даты
     * @param {Date|string} date - Дата
     * @returns {string} Отформатированная дата
     */
    formatDate: (date) => {
        const d = new Date(date);
        return d.toLocaleDateString('ru-RU');
    },

    /**
     * Форматирование даты и времени
     * @param {Date|string} date - Дата и время
     * @returns {string} Отформатированная строка
     */
    formatDateTime: (date) => {
        const d = new Date(date);
        return d.toLocaleString('ru-RU');
    },

    /**
     * Дебаунс функции
     * @param {function} func - Функция
     * @param {number} wait - Время ожидания в мс
     * @returns {function} Дебаунсенная функция
     */
    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', function() {
    console.log('Modal Manager initialized');
    
    // Добавляем стили для модальных окон если их нет
    if (!document.querySelector('#modal-styles')) {
        const styles = document.createElement('style');
        styles.id = 'modal-styles';
        styles.textContent = `
            .modal-backdrop.show {
                opacity: 0.5;
            }
            
            .service-row {
                transition: all 0.3s ease;
            }
            
            .service-row:hover {
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .modal-loader {
                z-index: 1060;
            }
            
            .modal-backdrop {
                z-index: 1055;
            }
            
            .spinner-border-sm {
                width: 1rem;
                height: 1rem;
            }
        `;
        document.head.appendChild(styles);
    }
});