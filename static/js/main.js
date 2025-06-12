// Основной JavaScript для Universal Service CRM

class CRMApp {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeComponents();
        this.setupTooltips();
        this.setupDropdowns();
        this.setupSearch();
        this.setupFilters();
    }

    setupEventListeners() {
        // Мобильное меню
        document.addEventListener('click', (e) => {
            if (e.target.closest('.mobile-menu-toggle')) {
                this.toggleMobileMenu();
            }
        });

        // Закрытие дропдаунов при клике вне
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.dropdown')) {
                this.closeAllDropdowns();
            }
        });

        // Обработка форм
        document.addEventListener('submit', (e) => {
            if (e.target.classList.contains('ajax-form')) {
                e.preventDefault();
                this.handleAjaxForm(e.target);
            }
        });

        // Автосохранение черновиков
        document.addEventListener('input', (e) => {
            if (e.target.classList.contains('auto-save')) {
                this.autoSave(e.target);
            }
        });
    }

    initializeComponents() {
        // Инициализация графиков
        this.initCharts();
        
        // Инициализация таблиц
        this.initTables();
        
        // Инициализация уведомлений
        this.initNotifications();
        
        // Инициализация канбан доски
        if (document.querySelector('.kanban-board')) {
            this.initKanban();
        }
    }

    setupTooltips() {
        const tooltips = document.querySelectorAll('[data-tooltip]');
        tooltips.forEach(element => {
            element.addEventListener('mouseenter', (e) => {
                this.showTooltip(e.target);
            });
            element.addEventListener('mouseleave', () => {
                this.hideTooltip();
            });
        });
    }

    setupDropdowns() {
        const dropdowns = document.querySelectorAll('.dropdown-toggle');
        dropdowns.forEach(dropdown => {
            dropdown.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.toggleDropdown(dropdown);
            });
        });
    }

    setupSearch() {
        const searchInputs = document.querySelectorAll('.search-input');
        searchInputs.forEach(input => {
            input.addEventListener('input', (e) => {
                this.debounce(() => {
                    this.performSearch(e.target.value, e.target.dataset.target);
                }, 300);
            });
        });
    }

    setupFilters() {
        const filterSelects = document.querySelectorAll('.filter-select');
        filterSelects.forEach(select => {
            select.addEventListener('change', (e) => {
                this.applyFilter(e.target.name, e.target.value);
            });
        });
    }

    // Мобильное меню
    toggleMobileMenu() {
        const sidebar = document.querySelector('.sidebar');
        const overlay = document.querySelector('.mobile-overlay');
        
        sidebar.classList.toggle('show');
        
        if (!overlay) {
            const newOverlay = document.createElement('div');
            newOverlay.className = 'mobile-overlay';
            newOverlay.addEventListener('click', () => this.closeMobileMenu());
            document.body.appendChild(newOverlay);
        }
    }

    closeMobileMenu() {
        const sidebar = document.querySelector('.sidebar');
        const overlay = document.querySelector('.mobile-overlay');
        
        sidebar.classList.remove('show');
        if (overlay) {
            overlay.remove();
        }
    }

    // Дропдауны
    toggleDropdown(trigger) {
        const dropdown = trigger.closest('.dropdown');
        const menu = dropdown.querySelector('.dropdown-menu');
        
        // Закрываем другие дропдауны
        this.closeAllDropdowns();
        
        // Переключаем текущий
        dropdown.classList.toggle('show');
        menu.classList.toggle('show');
    }

    closeAllDropdowns() {
        const dropdowns = document.querySelectorAll('.dropdown.show');
        dropdowns.forEach(dropdown => {
            dropdown.classList.remove('show');
            dropdown.querySelector('.dropdown-menu').classList.remove('show');
        });
    }

    // Тултипы
    showTooltip(element) {
        const text = element.dataset.tooltip;
        if (!text) return;

        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = text;
        
        document.body.appendChild(tooltip);
        
        const rect = element.getBoundingClientRect();
        tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
        tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
        
        setTimeout(() => tooltip.classList.add('show'), 10);
    }

    hideTooltip() {
        const tooltip = document.querySelector('.tooltip');
        if (tooltip) {
            tooltip.remove();
        }
    }

    // AJAX формы
    async handleAjaxForm(form) {
        const formData = new FormData(form);
        const url = form.action || window.location.href;
        
        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCookie('csrftoken')
                }
            });

            const data = await response.json();
            
            if (data.success) {
                this.showNotification('success', data.message || 'Операция выполнена успешно');
                if (data.redirect) {
                    window.location.href = data.redirect;
                } else if (data.reload) {
                    window.location.reload();
                }
            } else {
                this.showNotification('error', data.error || 'Произошла ошибка');
            }
        } catch (error) {
            this.showNotification('error', 'Ошибка сети');
            console.error('AJAX Error:', error);
        }
    }

    // Поиск
    performSearch(query, target) {
        if (!target) return;
        
        const elements = document.querySelectorAll(target);
        
        elements.forEach(element => {
            const text = element.textContent.toLowerCase();
            const isVisible = text.includes(query.toLowerCase());
            element.style.display = isVisible ? '' : 'none';
        });
    }

    // Фильтры
    applyFilter(filterName, filterValue) {
        const url = new URL(window.location);
        
        if (filterValue) {
            url.searchParams.set(filterName, filterValue);
        } else {
            url.searchParams.delete(filterName);
        }
        
        window.location.href = url.toString();
    }

    // Графики
    initCharts() {
        // Инициализация графиков Chart.js
        const chartElements = document.querySelectorAll('[data-chart]');
        
        chartElements.forEach(element => {
            const type = element.dataset.chart;
            const data = JSON.parse(element.dataset.chartData || '{}');
            
            this.createChart(element, type, data);
        });
    }

    createChart(element, type, data) {
        const ctx = element.getContext('2d');
        
        const config = {
            type: type,
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        };

        new Chart(ctx, config);
    }

    // Таблицы
    initTables() {
        const tables = document.querySelectorAll('.data-table');
        
        tables.forEach(table => {
            this.setupTableSorting(table);
            this.setupTablePagination(table);
        });
    }

    setupTableSorting(table) {
        const headers = table.querySelectorAll('th[data-sort]');
        
        headers.forEach(header => {
            header.addEventListener('click', () => {
                const column = header.dataset.sort;
                const direction = header.classList.contains('asc') ? 'desc' : 'asc';
                
                this.sortTable(table, column, direction);
                
                // Обновляем классы
                headers.forEach(h => h.classList.remove('asc', 'desc'));
                header.classList.add(direction);
            });
        });
    }

    sortTable(table, column, direction) {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        
        rows.sort((a, b) => {
            const aValue = a.querySelector(`[data-value="${column}"]`)?.textContent || '';
            const bValue = b.querySelector(`[data-value="${column}"]`)?.textContent || '';
            
            if (direction === 'asc') {
                return aValue.localeCompare(bValue, 'ru', { numeric: true });
            } else {
                return bValue.localeCompare(aValue, 'ru', { numeric: true });
            }
        });
        
        rows.forEach(row => tbody.appendChild(row));
    }

    // Канбан доска
    initKanban() {
        const kanbanBoard = document.querySelector('.kanban-board');
        if (!kanbanBoard) return;

        this.setupDragAndDrop();
        this.updateKanbanStats();
    }

    setupDragAndDrop() {
        const cards = document.querySelectorAll('.kanban-card');
        const columns = document.querySelectorAll('.kanban-column');

        cards.forEach(card => {
            card.draggable = true;
            
            card.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('text/plain', card.dataset.orderId);
                card.classList.add('dragging');
            });
            
            card.addEventListener('dragend', () => {
                card.classList.remove('dragging');
            });
        });

        columns.forEach(column => {
            column.addEventListener('dragover', (e) => {
                e.preventDefault();
                column.classList.add('drag-over');
            });
            
            column.addEventListener('dragleave', () => {
                column.classList.remove('drag-over');
            });
            
            column.addEventListener('drop', (e) => {
                e.preventDefault();
                column.classList.remove('drag-over');
                
                const orderId = e.dataTransfer.getData('text/plain');
                const newStatus = column.dataset.status;
                
                this.moveCard(orderId, newStatus);
            });
        });
    }

    async moveCard(orderId, newStatus) {
        try {
            const response = await fetch(`/quick/orders/${orderId}/status/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: `status=${newStatus}`
            });

            const data = await response.json();
            
            if (data.success) {
                this.showNotification('success', data.message);
                this.updateKanbanStats();
                
                // Перемещаем карточку в новую колонку
                const card = document.querySelector(`[data-order-id="${orderId}"]`);
                const targetColumn = document.querySelector(`[data-status="${newStatus}"] .kanban-cards`);
                
                if (card && targetColumn) {
                    targetColumn.appendChild(card);
                    card.className = `kanban-card ${newStatus}`;
                }
            } else {
                this.showNotification('error', data.error);
            }
        } catch (error) {
            this.showNotification('error', 'Ошибка обновления статуса');
            console.error('Move card error:', error);
        }
    }

    updateKanbanStats() {
        const columns = document.querySelectorAll('.kanban-column');
        
        columns.forEach(column => {
            const cards = column.querySelectorAll('.kanban-card');
            const countElement = column.querySelector('.kanban-count');
            
            if (countElement) {
                countElement.textContent = cards.length;
            }
        });
    }

    // Уведомления
    initNotifications() {
        // Проверяем новые уведомления каждые 30 секунд
        setInterval(() => {
            this.checkNotifications();
        }, 30000);
    }

    async checkNotifications() {
        try {
            const response = await fetch('/api/notifications/unread/', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCookie('csrftoken')
                }
            });

            const data = await response.json();
            
            if (data.count > 0) {
                this.updateNotificationBadge(data.count);
            }
        } catch (error) {
            console.error('Notification check error:', error);
        }
    }

    updateNotificationBadge(count) {
        const badge = document.querySelector('.notification-badge');
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'block' : 'none';
        }
    }

    showNotification(type, message) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="notification-icon fas fa-${this.getNotificationIcon(type)}"></i>
                <span class="notification-message">${message}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        const container = this.getNotificationContainer();
        container.appendChild(notification);

        // Автоматическое удаление через 5 секунд
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);

        // Анимация появления
        setTimeout(() => notification.classList.add('show'), 10);
    }

    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    getNotificationContainer() {
        let container = document.querySelector('.notification-container');
        
        if (!container) {
            container = document.createElement('div');
            container.className = 'notification-container';
            document.body.appendChild(container);
        }
        
        return container;
    }

    // Автосохранение
    autoSave(input) {
        const key = `autosave_${input.name}_${input.form?.id || 'form'}`;
        localStorage.setItem(key, input.value);
        
        // Показываем индикатор сохранения
        this.showSaveIndicator(input);
    }

    showSaveIndicator(input) {
        let indicator = input.parentElement.querySelector('.save-indicator');
        
        if (!indicator) {
            indicator = document.createElement('span');
            indicator.className = 'save-indicator';
            indicator.innerHTML = '<i class="fas fa-check"></i> Сохранено';
            input.parentElement.appendChild(indicator);
        }
        
        indicator.classList.add('show');
        
        setTimeout(() => {
            indicator.classList.remove('show');
        }, 2000);
    }

    // Утилиты
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

    debounce(func, wait) {
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

    formatCurrency(amount) {
        return new Intl.NumberFormat('ru-RU', {
            style: 'currency',
            currency: 'RUB'
        }).format(amount);
    }

    formatDate(date) {
        return new Intl.DateTimeFormat('ru-RU').format(new Date(date));
    }

    formatDateTime(date) {
        return new Intl.DateTimeFormat('ru-RU', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        }).format(new Date(date));
    }
}

// Глобальные функции для совместимости
window.CRM = new CRMApp();

// Дополнительные утилиты
window.utils = {
    formatCurrency: (amount) => window.CRM.formatCurrency(amount),
    formatDate: (date) => window.CRM.formatDate(date),
    formatDateTime: (date) => window.CRM.formatDateTime(date),
    showNotification: (type, message) => window.CRM.showNotification(type, message),
    getCookie: (name) => window.CRM.getCookie(name)
};

// Быстрые действия
window.quickActions = {
    async updateOrderStatus(orderId, status) {
        try {
            const response = await fetch(`/quick/orders/${orderId}/status/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': utils.getCookie('csrftoken')
                },
                body: `status=${status}`
            });

            const data = await response.json();
            
            if (data.success) {
                utils.showNotification('success', data.message);
                setTimeout(() => location.reload(), 1000);
            } else {
                utils.showNotification('error', data.error);
            }
        } catch (error) {
            utils.showNotification('error', 'Ошибка обновления статуса');
        }
    },

    async assignExecutor(orderId, executorId) {
        try {
            const response = await fetch(`/quick/orders/${orderId}/assign/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': utils.getCookie('csrftoken')
                },
                body: `executor_id=${executorId}`
            });

            const data = await response.json();
            
            if (data.success) {
                utils.showNotification('success', data.message);
                setTimeout(() => location.reload(), 1000);
            } else {
                utils.showNotification('error', data.error);
            }
        } catch (error) {
            utils.showNotification('error', 'Ошибка назначения исполнителя');
        }
    }
};

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', function() {
    console.log('CRM App initialized');
});