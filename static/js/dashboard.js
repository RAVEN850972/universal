/**
 * === JAVASCRIPT ДЛЯ ДАШБОРДА ===
 * static/js/dashboard.js
 */

// === ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ===
let dashboardInterval;
let notificationTimeout;

// === ИНИЦИАЛИЗАЦИЯ ДАШБОРДА ===
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    startAutoRefresh();
    initializeCharts();
    bindEventHandlers();
});

/**
 * Инициализация дашборда
 */
function initializeDashboard() {
    // Анимация счетчиков в статистических карточках
    animateCounters();
    
    // Инициализация всплывающих подсказок
    initializeTooltips();
    
    // Проверка новых уведомлений
    checkNewNotifications();
    
    console.log('Dashboard initialized');
}

/**
 * Анимация счетчиков
 */
function animateCounters() {
    const counters = document.querySelectorAll('.stats-value');
    
    counters.forEach(counter => {
        const target = parseInt(counter.textContent.replace(/[^\d]/g, ''));
        if (isNaN(target)) return;
        
        let current = 0;
        const increment = target / 30; // Анимация за 30 кадров
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            
            // Форматируем число с сохранением валютных символов
            if (counter.textContent.includes('₽')) {
                counter.textContent = Math.floor(current).toLocaleString() + '₽';
            } else {
                counter.textContent = Math.floor(current).toLocaleString();
            }
        }, 16); // ~60fps
    });
}

/**
 * Инициализация графиков
 */
function initializeCharts() {
    // График активности уже инициализируется в шаблоне
    // Здесь можем добавить дополнительные графики
    
    // Мини-график для трендов в статистических карточках
    initializeTrendCharts();
}

/**
 * Мини-графики трендов
 */
function initializeTrendCharts() {
    const trendElements = document.querySelectorAll('[data-trend]');
    
    trendElements.forEach(element => {
        const data = JSON.parse(element.getAttribute('data-trend'));
        createTrendChart(element, data);
    });
}

/**
 * Создание мини-графика тренда
 */
function createTrendChart(container, data) {
    const canvas = document.createElement('canvas');
    canvas.width = 60;
    canvas.height = 20;
    container.appendChild(canvas);
    
    const ctx = canvas.getContext('2d');
    const points = data.map((value, index) => ({
        x: (index / (data.length - 1)) * 60,
        y: 20 - ((value - Math.min(...data)) / (Math.max(...data) - Math.min(...data))) * 20
    }));
    
    ctx.strokeStyle = data[data.length - 1] > data[0] ? '#059669' : '#dc2626';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    
    points.forEach(point => {
        ctx.lineTo(point.x, point.y);
    });
    
    ctx.stroke();
}

/**
 * Автообновление данных
 */
function startAutoRefresh() {
    dashboardInterval = setInterval(() => {
        updateDashboardStats();
        checkNewNotifications();
    }, 30000); // Каждые 30 секунд
}

/**
 * Обновление статистики дашборда
 */
async function updateDashboardStats() {
    try {
        const response = await makeRequest('/api/dashboard/stats/');
        if (response.success) {
            updateStatsCards(response.data);
        }
    } catch (error) {
        console.error('Failed to update dashboard stats:', error);
    }
}

/**
 * Обновление статистических карточек
 */
function updateStatsCards(data) {
    // Обновляем значения без анимации если изменения небольшие
    Object.keys(data).forEach(key => {
        const element = document.querySelector(`[data-stat="${key}"]`);
        if (element) {
            const currentValue = parseInt(element.textContent.replace(/[^\d]/g, ''));
            const newValue = data[key];
            
            if (Math.abs(newValue - currentValue) > currentValue * 0.1) {
                // Большое изменение - показываем анимацию
                animateValueChange(element, newValue);
            } else {
                // Маленькое изменение - обновляем плавно
                element.textContent = formatStatValue(newValue, key);
            }
        }
    });
}

/**
 * Анимация изменения значения
 */
function animateValueChange(element, newValue) {
    element.classList.add('loading-skeleton');
    
    setTimeout(() => {
        element.classList.remove('loading-skeleton');
        element.textContent = formatStatValue(newValue, element.getAttribute('data-stat'));
        element.style.animation = 'pulse 0.5s ease-out';
        
        setTimeout(() => {
            element.style.animation = '';
        }, 500);
    }, 300);
}

/**
 * Форматирование значений статистики
 */
function formatStatValue(value, type) {
    if (type.includes('revenue') || type.includes('commission')) {
        return value.toLocaleString() + '₽';
    }
    return value.toLocaleString();
}

/**
 * Привязка обработчиков событий
 */
function bindEventHandlers() {
    // Клик по заказу
    document.addEventListener('click', function(e) {
        const orderItem = e.target.closest('.order-item');
        if (orderItem && !e.target.closest('.order-actions')) {
            const orderId = orderItem.getAttribute('data-order-id');
            if (orderId) {
                openOrderDetails(orderId);
            }
        }
    });
    
    // Клик по клиенту
    document.addEventListener('click', function(e) {
        const clientItem = e.target.closest('.client-item');
        if (clientItem) {
            const clientId = clientItem.getAttribute('data-client-id');
            if (clientId) {
                openClientDetails(clientId);
            }
        }
    });
    
    // Быстрые действия
    document.addEventListener('click', function(e) {
        if (e.target.matches('[data-quick-action]')) {
            handleQuickAction(e.target.getAttribute('data-quick-action'));
        }
    });
}

/**
 * Открытие деталей заказа
 */
function openOrderDetails(orderId) {
    showModal('orderDetailsModal');
    loadOrderDetails(orderId);
}

/**
 * Загрузка деталей заказа
 */
async function loadOrderDetails(orderId) {
    try {
        const response = await makeRequest(`/api/orders/${orderId}/`);
        if (response.success) {
            renderOrderDetails(response.data);
        } else {
            showAlert('Не удалось загрузить детали заказа', 'error');
        }
    } catch (error) {
        showAlert('Ошибка при загрузке заказа', 'error');
    }
}

/**
 * Отображение деталей заказа
 */
function renderOrderDetails(orderData) {
    const modal = document.getElementById('orderDetailsModal');
    if (!modal) return;
    
    // Заполняем модальное окно данными заказа
    modal.querySelector('.modal-title').textContent = `Заказ #${orderData.id}`;
    
    const bodyHTML = `
        <div class="order-details">
            <div class="row">
                <div class="col-md-6">
                    <h6>Информация о заказе</h6>
                    <p><strong>Клиент:</strong> ${orderData.client.name}</p>
                    <p><strong>Дата заказа:</strong> ${formatDate(orderData.order_date)}</p>
                    <p><strong>Статус:</strong> <span class="order-status status-${orderData.status}">${getStatusText(orderData.status)}</span></p>
                    <p><strong>Сумма:</strong> ${formatCurrency(orderData.total_amount)}</p>
                </div>
                <div class="col-md-6">
                    <h6>Описание</h6>
                    <p>${orderData.description || 'Описание не указано'}</p>
                </div>
            </div>
            
            ${orderData.services && orderData.services.length > 0 ? `
            <div class="order-services">
                <h6>Услуги</h6>
                <div class="services-list">
                    ${orderData.services.map(service => `
                        <div class="service-item">
                            <span class="service-name">${service.name}</span>
                            <span class="service-quantity">${service.quantity} ${service.unit}</span>
                            <span class="service-price">${formatCurrency(service.price)}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
            ` : ''}
        </div>
    `;
    
    modal.querySelector('.modal-body').innerHTML = bodyHTML;
}

/**
 * Получение текста статуса
 */
function getStatusText(status) {
    const statusMap = {
        'new': 'Новый',
        'in_progress': 'В работе',
        'completed': 'Завершен',
        'cancelled': 'Отменен'
    };
    return statusMap[status] || status;
}

/**
 * Открытие деталей клиента
 */
function openClientDetails(clientId) {
    window.location.href = `/clients/${clientId}/`;
}

/**
 * Обработка быстрых действий
 */
function handleQuickAction(action) {
    switch (action) {
        case 'new-order':
            showQuickOrderModal();
            break;
        case 'new-client':
            showQuickClientModal();
            break;
        case 'reports':
            window.location.href = '/reports/';
            break;
        default:
            console.warn('Unknown quick action:', action);
    }
}

/**
 * Показ модального окна быстрого создания заказа
 */
function showQuickOrderModal() {
    showModal('quickOrderModal');
    initializeQuickOrderForm();
}

/**
 * Инициализация формы быстрого создания заказа
 */
function initializeQuickOrderForm() {
    const form = document.getElementById('quickOrderForm');
    if (!form) return;
    
    // Подгружаем список клиентов для автокомплита
    loadClientsForAutocomplete();
    
    // Привязываем обработчик отправки формы
    form.addEventListener('submit', handleQuickOrderSubmit);
}

/**
 * Загрузка клиентов для автокомплита
 */
async function loadClientsForAutocomplete() {
    try {
        const response = await makeRequest('/api/clients/?limit=50');
        if (response.success) {
            setupClientAutocomplete(response.data);
        }
    } catch (error) {
        console.error('Failed to load clients for autocomplete:', error);
    }
}

/**
 * Настройка автокомплита для клиентов
 */
function setupClientAutocomplete(clients) {
    const clientInput = document.getElementById('quickOrderClient');
    if (!clientInput) return;
    
    // Простая реализация автокомплита
    let currentFocus = -1;
    
    clientInput.addEventListener('input', function() {
        const value = this.value.toLowerCase();
        closeAllLists();
        
        if (!value) return;
        
        const filtered = clients.filter(client => 
            client.name.toLowerCase().includes(value)
        );
        
        if (filtered.length === 0) return;
        
        const listDiv = document.createElement('div');
        listDiv.className = 'autocomplete-items';
        this.parentNode.appendChild(listDiv);
        
        filtered.forEach((client, index) => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'autocomplete-item';
            itemDiv.innerHTML = `<strong>${client.name}</strong>`;
            if (client.phone) {
                itemDiv.innerHTML += ` - ${client.phone}`;
            }
            
            itemDiv.addEventListener('click', function() {
                clientInput.value = client.name;
                clientInput.setAttribute('data-client-id', client.id);
                closeAllLists();
            });
            
            listDiv.appendChild(itemDiv);
        });
    });
    
    // Обработка клавиш
    clientInput.addEventListener('keydown', function(e) {
        const items = document.querySelectorAll('.autocomplete-item');
        
        if (e.keyCode === 40) { // Стрелка вниз
            currentFocus++;
            addActive(items);
        } else if (e.keyCode === 38) { // Стрелка вверх
            currentFocus--;
            addActive(items);
        } else if (e.keyCode === 13) { // Enter
            e.preventDefault();
            if (currentFocus > -1 && items[currentFocus]) {
                items[currentFocus].click();
            }
        }
    });
    
    function addActive(items) {
        if (!items) return;
        removeActive(items);
        if (currentFocus >= items.length) currentFocus = 0;
        if (currentFocus < 0) currentFocus = items.length - 1;
        items[currentFocus].classList.add('autocomplete-active');
    }
    
    function removeActive(items) {
        items.forEach(item => item.classList.remove('autocomplete-active'));
    }
    
    function closeAllLists() {
        document.querySelectorAll('.autocomplete-items').forEach(list => list.remove());
        currentFocus = -1;
    }
    
    // Закрытие при клике вне
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.autocomplete-container')) {
            closeAllLists();
        }
    });
}

/**
 * Обработка отправки формы быстрого заказа
 */
async function handleQuickOrderSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    const submitBtn = form.querySelector('button[type="submit"]');
    
    setLoading(submitBtn, true);
    
    try {
        const response = await makeRequest('/api/orders/', {
            method: 'POST',
            body: formData
        });
        
        if (response.success) {
            showAlert('Заказ успешно создан!', 'success');
            hideModal('quickOrderModal');
            form.reset();
            
            // Обновляем список заказов на дашборде
            refreshOrdersList();
        } else {
            showAlert(response.error || 'Ошибка при создании заказа', 'error');
        }
    } catch (error) {
        showAlert('Произошла ошибка при создании заказа', 'error');
    } finally {
        setLoading(submitBtn, false);
    }
}

/**
 * Обновление статуса заказа
 */
async function updateOrderStatus(orderId, newStatus, event) {
    if (event) {
        event.stopPropagation();
    }
    
    if (!confirm(`Изменить статус заказа на "${getStatusText(newStatus)}"?`)) {
        return;
    }
    
    try {
        const response = await makeRequest(`/api/orders/${orderId}/status/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: newStatus })
        });
        
        if (response.success) {
            showDashboardNotification('Статус заказа обновлен', 'success');
            refreshOrdersList();
            updateDashboardStats();
        } else {
            showAlert('Ошибка при обновлении статуса', 'error');
        }
    } catch (error) {
        showAlert('Произошла ошибка при обновлении статуса', 'error');
    }
}

/**
 * Обновление списка заказов
 */
async function refreshOrdersList() {
    try {
        const response = await makeRequest('/api/dashboard/recent-orders/');
        if (response.success) {
            renderOrdersList(response.data);
        }
    } catch (error) {
        console.error('Failed to refresh orders list:', error);
    }
}

/**
 * Отображение списка заказов
 */
function renderOrdersList(orders) {
    const container = document.querySelector('.orders-list');
    if (!container) return;
    
    if (orders.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">
                    <i class="fas fa-clipboard-list"></i>
                </div>
                <h6>Заказов пока нет</h6>
                <p class="text-muted">Создайте первый заказ для начала работы</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = orders.map(order => `
        <div class="order-item" data-order-id="${order.id}" onclick="openOrderDetails(${order.id})">
            <div class="order-main">
                <div class="order-info">
                    <div class="order-header">
                        <span class="order-number">Заказ #${order.id}</span>
                        <span class="order-status status-${order.status}">
                            ${getStatusText(order.status)}
                        </span>
                    </div>
                    <div class="order-client">
                        <i class="fas fa-user me-1"></i>
                        ${order.client.name}
                    </div>
                    <div class="order-meta">
                        <span class="order-date">
                            <i class="fas fa-calendar me-1"></i>
                            ${formatDate(order.order_date)}
                        </span>
                        ${order.total_amount ? `
                        <span class="order-amount">
                            <i class="fas fa-ruble-sign me-1"></i>
                            ${formatCurrency(order.total_amount)}
                        </span>
                        ` : ''}
                    </div>
                </div>
                ${order.description ? `
                <div class="order-description">
                    ${order.description.length > 80 ? order.description.substring(0, 80) + '...' : order.description}
                </div>
                ` : ''}
            </div>
            <div class="order-actions">
                ${order.status === 'new' ? `
                <div class="status-actions">
                    <button class="btn btn-sm btn-success" onclick="updateOrderStatus(${order.id}, 'in_progress', event)">
                        <i class="fas fa-play"></i>
                    </button>
                </div>
                ` : order.status === 'in_progress' ? `
                <div class="status-actions">
                    <button class="btn btn-sm btn-primary" onclick="updateOrderStatus(${order.id}, 'completed', event)">
                        <i class="fas fa-check"></i>
                    </button>
                </div>
                ` : ''}
                <i class="fas fa-chevron-right order-arrow"></i>
            </div>
        </div>
    `).join('');
}

/**
 * Показ уведомления в дашборде
 */
function showDashboardNotification(message, type = 'info') {
    // Удаляем предыдущее уведомление
    const existing = document.querySelector('.dashboard-notification');
    if (existing) {
        existing.remove();
    }
    
    const notification = document.createElement('div');
    notification.className = `dashboard-notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
        <button class="btn-icon-sm" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    document.body.appendChild(notification);
    
    // Автоматически скрываем через 5 секунд
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

/**
 * Проверка новых уведомлений
 */
async function checkNewNotifications() {
    try {
        const response = await makeRequest('/api/notifications/unread-count/');
        if (response.success && response.data.count > 0) {
            updateNotificationBadge(response.data.count);
        }
    } catch (error) {
        // Тихо игнорируем ошибки проверки уведомлений
    }
}

/**
 * Обновление бейджа уведомлений
 */
function updateNotificationBadge(count) {
    const badge = document.getElementById('notificationBadge');
    if (badge) {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'block' : 'none';
    }
}

/**
 * Инициализация всплывающих подсказок
 */
function initializeTooltips() {
    const elements = document.querySelectorAll('[title]');
    elements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

/**
 * Показ всплывающей подсказки
 */
function showTooltip(e) {
    const element = e.target;
    const title = element.getAttribute('title');
    if (!title) return;
    
    // Создаем tooltip
    const tooltip = document.createElement('div');
    tooltip.className = 'custom-tooltip';
    tooltip.textContent = title;
    document.body.appendChild(tooltip);
    
    // Позиционируем tooltip
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
    
    // Скрываем стандартный title
    element.setAttribute('data-original-title', title);
    element.removeAttribute('title');
    
    // Сохраняем ссылку для удаления
    element._tooltip = tooltip;
}

/**
 * Скрытие всплывающей подсказки
 */
function hideTooltip(e) {
    const element = e.target;
    if (element._tooltip) {
        element._tooltip.remove();
        element._tooltip = null;
    }
    
    // Восстанавливаем title
    const originalTitle = element.getAttribute('data-original-title');
    if (originalTitle) {
        element.setAttribute('title', originalTitle);
        element.removeAttribute('data-original-title');
    }
}

/**
 * Показ модального окна быстрого создания клиента
 */
function showQuickClientModal() {
    showModal('quickClientModal');
    initializeQuickClientForm();
}

/**
 * Инициализация формы быстрого создания клиента
 */
function initializeQuickClientForm() {
    const form = document.getElementById('quickClientForm');
    if (!form) return;
    
    form.addEventListener('submit', handleQuickClientSubmit);
}

/**
 * Обработка отправки формы быстрого создания клиента
 */
async function handleQuickClientSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    const submitBtn = form.querySelector('button[type="submit"]');
    
    setLoading(submitBtn, true);
    
    try {
        const response = await makeRequest('/api/clients/', {
            method: 'POST',
            body: formData
        });
        
        if (response.success) {
            showAlert('Клиент успешно создан!', 'success');
            hideModal('quickClientModal');
            form.reset();
            
            // Обновляем статистику
            updateDashboardStats();
        } else {
            showAlert(response.error || 'Ошибка при создании клиента', 'error');
        }
    } catch (error) {
        showAlert('Произошла ошибка при создании клиента', 'error');
    } finally {
        setLoading(submitBtn, false);
    }
}

/**
 * Обработка ошибок соединения
 */
function handleConnectionError() {
    showDashboardNotification('Потеряно соединение с сервером', 'error');
    
    // Останавливаем автообновление
    if (dashboardInterval) {
        clearInterval(dashboardInterval);
    }
    
    // Пытаемся переподключиться через 30 секунд
    setTimeout(() => {
        checkConnection();
    }, 30000);
}

/**
 * Проверка соединения
 */
async function checkConnection() {
    try {
        const response = await fetch('/api/health/', { method: 'HEAD' });
        if (response.ok) {
            showDashboardNotification('Соединение восстановлено', 'success');
            startAutoRefresh();
            updateDashboardStats();
        } else {
            throw new Error('Server not responding');
        }
    } catch (error) {
        // Повторяем попытку через 30 секунд
        setTimeout(checkConnection, 30000);
    }
}

/**
 * Обработка видимости страницы
 */
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // Страница скрыта - останавливаем обновления
        if (dashboardInterval) {
            clearInterval(dashboardInterval);
        }
    } else {
        // Страница видима - возобновляем обновления
        updateDashboardStats();
        startAutoRefresh();
    }
});

/**
 * Очистка при выходе со страницы
 */
window.addEventListener('beforeunload', function() {
    if (dashboardInterval) {
        clearInterval(dashboardInterval);
    }
    
    if (notificationTimeout) {
        clearTimeout(notificationTimeout);
    }
});

/**
 * Обработка ошибок JavaScript
 */
window.addEventListener('error', function(e) {
    console.error('Dashboard error:', e.error);
    
    // Показываем пользователю дружелюбное сообщение только для критичных ошибок
    if (e.error && e.error.message && e.error.message.includes('fetch')) {
        handleConnectionError();
    }
});

/**
 * Экспорт функций для глобального использования
 */
window.dashboardFunctions = {
    updateOrderStatus,
    openOrderDetails,
    openClientDetails,
    showQuickOrderModal,
    showQuickClientModal,
    updateDashboardStats,
    refreshOrdersList
};

// Добавляем CSS для всплывающих подсказок
const tooltipStyles = `
.custom-tooltip {
    position: absolute;
    background: var(--bg-dark);
    color: var(--text-light);
    padding: 6px 8px;
    border-radius: 4px;
    font-size: 12px;
    white-space: nowrap;
    z-index: var(--z-tooltip);
    animation: fadeIn 0.2s ease-out;
    pointer-events: none;
}

.autocomplete-items {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-top: none;
    border-radius: 0 0 var(--border-radius-small) var(--border-radius-small);
    box-shadow: var(--shadow-medium);
    max-height: 200px;
    overflow-y: auto;
    z-index: var(--z-dropdown);
}

.autocomplete-item {
    padding: 8px 12px;
    cursor: pointer;
    font-size: 14px;
    transition: var(--transition-fast);
}

.autocomplete-item:hover,
.autocomplete-item.autocomplete-active {
    background: var(--bg-light);
}

.autocomplete-container {
    position: relative;
}

.notification-content {
    display: flex;
    align-items: center;
    gap: 8px;
}
`;

// Добавляем стили в head
const styleSheet = document.createElement('style');
styleSheet.textContent = tooltipStyles;
document.head.appendChild(styleSheet);