/**
 * === JAVASCRIPT ДЛЯ ДАШБОРДА ===
 * static/js/dashboard.js
 */

// === ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ===
let revenueChart = null;
let statsUpdateInterval = null;
let currentPeriod = 'current_month';

// === ИНИЦИАЛИЗАЦИЯ ===
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
});

/**
 * Инициализация дашборда
 */
function initializeDashboard() {
    initializeChart();
    initializePeriodSelector();
    initializeStatsUpdates();
    initializeAnimations();
    initializeNotifications();
    
    // Загружаем начальные данные
    updateDashboardStats();
    updateChart();
    
    console.log('Dashboard initialized successfully');
}

// === ИНИЦИАЛИЗАЦИЯ ГРАФИКА ===
function initializeChart() {
    const ctx = document.getElementById('revenueChart');
    if (!ctx) return;

    // Градиент для фона графика
    const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(0, 0, 0, 0.1)');
    gradient.addColorStop(1, 'rgba(0, 0, 0, 0.01)');

    revenueChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн'],
            datasets: [{
                label: 'Доходы',
                data: [120000, 135000, 118000, 142000, 155000, 168000],
                borderColor: '#000000',
                backgroundColor: gradient,
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#000000',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointRadius: 6,
                pointHoverRadius: 8,
                pointHoverBackgroundColor: '#000000',
                pointHoverBorderColor: '#ffffff',
                pointHoverBorderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.9)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: '#000000',
                    borderWidth: 1,
                    cornerRadius: 8,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return formatCurrency(context.parsed.y);
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    border: {
                        display: false
                    },
                    ticks: {
                        color: '#666666',
                        font: {
                            size: 12,
                            weight: '500'
                        }
                    }
                },
                y: {
                    grid: {
                        color: '#e0e0e0',
                        borderDash: [2, 4]
                    },
                    border: {
                        display: false
                    },
                    ticks: {
                        color: '#666666',
                        font: {
                            size: 12,
                            weight: '500'
                        },
                        callback: function(value) {
                            return formatCurrency(value, false);
                        }
                    }
                }
            },
            elements: {
                point: {
                    hoverRadius: 8
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
            }
        }
    });
}

// === ОБНОВЛЕНИЕ ГРАФИКА ===
async function updateChart(period = currentPeriod) {
    if (!revenueChart) return;
    
    try {
        const response = await fetch(`/api/dashboard/chart/?period=${period}`);
        const data = await response.json();
        
        if (data.success) {
            // Обновляем данные графика с анимацией
            revenueChart.data.labels = data.labels;
            revenueChart.data.datasets[0].data = data.values;
            revenueChart.update('active');
        }
    } catch (error) {
        console.error('Ошибка обновления графика:', error);
    }
}

// === ИНИЦИАЛИЗАЦИЯ СЕЛЕКТОРА ПЕРИОДА ===
function initializePeriodSelector() {
    const periodItems = document.querySelectorAll('[data-period]');
    const periodDropdown = document.getElementById('periodDropdown');
    
    periodItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const period = this.dataset.period;
            const periodText = this.textContent;
            
            currentPeriod = period;
            periodDropdown.innerHTML = `
                <i class="fas fa-calendar me-2"></i>
                ${periodText}
                <i class="fas fa-chevron-down ms-2"></i>
            `;
            
            // Обновляем данные
            updateDashboardStats(period);
            updateChart(period);
            
            // Закрываем dropdown
            document.querySelector('.dropdown-menu').classList.remove('show');
        });
    });
    
    // Toggle dropdown
    periodDropdown?.addEventListener('click', function() {
        const menu = document.querySelector('.dropdown-menu');
        menu.classList.toggle('show');
    });
    
    // Закрытие dropdown при клике вне его
    document.addEventListener('click', function(e) {
        const dropdown = document.querySelector('.dropdown');
        if (dropdown && !dropdown.contains(e.target)) {
            document.querySelector('.dropdown-menu')?.classList.remove('show');
        }
    });
}

// === ОБНОВЛЕНИЕ СТАТИСТИКИ ===
async function updateDashboardStats(period = currentPeriod) {
    const statElements = {
        totalOrders: document.getElementById('totalOrders'),
        totalClients: document.getElementById('totalClients'),
        monthRevenue: document.getElementById('monthRevenue'),
        conversionRate: document.getElementById('conversionRate')
    };
    
    // Показываем loading состояние
    Object.values(statElements).forEach(el => {
        if (el) el.classList.add('loading-skeleton');
    });
    
    try {
        const response = await fetch(`/api/dashboard/stats/?period=${period}`);
        const stats = await response.json();
        
        if (stats.success) {
            // Анимированное обновление счетчиков
            if (statElements.totalOrders) {
                animateCounter(statElements.totalOrders, stats.data.total_orders);
            }
            if (statElements.totalClients) {
                animateCounter(statElements.totalClients, stats.data.total_clients);
            }
            if (statElements.monthRevenue) {
                animateCounter(statElements.monthRevenue, stats.data.month_revenue, true);
            }
            if (statElements.conversionRate) {
                animateCounter(statElements.conversionRate, stats.data.conversion_rate, false, '%');
            }
        }
    } catch (error) {
        console.error('Ошибка обновления статистики:', error);
        showAlert('error', 'Ошибка загрузки статистики');
    } finally {
        // Убираем loading состояние
        setTimeout(() => {
            Object.values(statElements).forEach(el => {
                if (el) el.classList.remove('loading-skeleton');
            });
        }, 1000);
    }
}

// === АНИМАЦИЯ СЧЕТЧИКОВ ===
function animateCounter(element, targetValue, isCurrency = false, suffix = '') {
    if (!element) return;
    
    const startValue = parseFloat(element.textContent.replace(/[^\d.-]/g, '')) || 0;
    const duration = 1000;
    const steps = 60;
    const increment = (targetValue - startValue) / steps;
    
    let currentStep = 0;
    const timer = setInterval(() => {
        currentStep++;
        const currentValue = startValue + (increment * currentStep);
        
        if (isCurrency) {
            element.textContent = formatCurrency(currentValue);
        } else {
            element.textContent = Math.round(currentValue) + suffix;
        }
        
        if (currentStep >= steps) {
            clearInterval(timer);
            if (isCurrency) {
                element.textContent = formatCurrency(targetValue);
            } else {
                element.textContent = Math.round(targetValue) + suffix;
            }
        }
    }, duration / steps);
}

// === АВТОМАТИЧЕСКОЕ ОБНОВЛЕНИЕ ===
function initializeStatsUpdates() {
    // Обновляем статистику каждые 30 секунд
    statsUpdateInterval = setInterval(() => {
        updateDashboardStats();
    }, 30000);
    
    // Останавливаем обновления при скрытии вкладки
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            if (statsUpdateInterval) {
                clearInterval(statsUpdateInterval);
                statsUpdateInterval = null;
            }
        } else {
            if (!statsUpdateInterval) {
                statsUpdateInterval = setInterval(() => {
                    updateDashboardStats();
                }, 30000);
            }
        }
    });
}

// === АНИМАЦИИ ПОЯВЛЕНИЯ ===
function initializeAnimations() {
    // Наблюдатель для анимации элементов при скролле
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });
    
    // Применяем анимации к карточкам
    const cards = document.querySelectorAll('.dashboard-card, .stat-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'all 0.6s ease-out';
        card.style.transitionDelay = `${index * 0.1}s`;
        
        observer.observe(card);
    });
}

// === УПРАВЛЕНИЕ УВЕДОМЛЕНИЯМИ ===
function initializeNotifications() {
    loadNotifications();
    
    // Обновляем уведомления каждые 60 секунд
    setInterval(loadNotifications, 60000);
}

async function loadNotifications() {
    try {
        const response = await fetch('/api/notifications/recent/');
        const data = await response.json();
        
        if (data.success) {
            renderNotifications(data.notifications);
        }
    } catch (error) {
        console.error('Ошибка загрузки уведомлений:', error);
    }
}

function renderNotifications(notifications) {
    const container = document.getElementById('dashboardNotifications');
    if (!container) return;
    
    if (notifications.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-bell-slash"></i>
                <p>Нет новых уведомлений</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = notifications.map(notification => `
        <div class="notification-item ${notification.is_read ? '' : 'unread'}" 
             onclick="markNotificationAsRead(${notification.id})">
            <div class="notification-icon">
                <i class="${notification.icon} ${notification.color}"></i>
            </div>
            <div class="notification-content">
                <div class="notification-title">${notification.title}</div>
                <div class="notification-text">${notification.message}</div>
                <div class="notification-time">${formatDate(notification.created_at)}</div>
            </div>
        </div>
    `).join('');
}

async function markNotificationAsRead(notificationId) {
    try {
        await fetch(`/api/notifications/${notificationId}/read/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        });
        
        // Обновляем интерфейс
        const notificationElement = document.querySelector(`[onclick="markNotificationAsRead(${notificationId})"]`);
        if (notificationElement) {
            notificationElement.classList.remove('unread');
        }
    } catch (error) {
        console.error('Ошибка отметки уведомления:', error);
    }
}

async function markAllAsRead() {
    try {
        await fetch('/api/notifications/mark-all-read/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        });
        
        // Убираем класс unread со всех уведомлений
        document.querySelectorAll('.notification-item.unread').forEach(item => {
            item.classList.remove('unread');
        });
        
        showAlert('success', 'Все уведомления отмечены как прочитанные');
    } catch (error) {
        console.error('Ошибка отметки всех уведомлений:', error);
        showAlert('error', 'Ошибка при отметке уведомлений');
    }
}

// === ФУНКЦИИ ГРАФИКА ===
function refreshChart() {
    if (revenueChart) {
        // Показываем индикатор загрузки
        const button = event.target.closest('button');
        const originalContent = button.innerHTML;
        button.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i>';
        button.disabled = true;
        
        // Обновляем график
        updateChart().finally(() => {
            button.innerHTML = originalContent;
            button.disabled = false;
        });
    }
}

function exportChart() {
    if (revenueChart) {
        const url = revenueChart.toBase64Image();
        const link = document.createElement('a');
        link.href = url;
        link.download = `revenue-chart-${currentPeriod}-${new Date().toISOString().split('T')[0]}.png`;
        link.click();
        
        showAlert('success', 'График экспортирован');
    }
}

// === УТИЛИТЫ ===
function formatCurrency(amount, showSymbol = true) {
    const formatted = new Intl.NumberFormat('ru-RU', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
    
    return showSymbol ? `${formatted} ₽` : formatted;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    // Если меньше часа - показываем минуты
    if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return minutes <= 1 ? 'только что' : `${minutes} мин назад`;
    }
    
    // Если меньше дня - показываем часы
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours} час${hours > 1 ? (hours < 5 ? 'а' : 'ов') : ''} назад`;
    }
    
    // Иначе показываем дату
    return new Intl.DateTimeFormat('ru-RU', {
        day: 'numeric',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

function getCookie(name) {
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

// === ОБРАБОТЧИКИ СОБЫТИЙ ===

// Обновление заказа в списке
function updateOrderInDashboard(orderId, newData) {
    const orderElement = document.querySelector(`[data-order-id="${orderId}"]`);
    if (orderElement) {
        const statusElement = orderElement.querySelector('.status-badge');
        const amountElement = orderElement.querySelector('.order-amount');
        
        if (statusElement && newData.status) {
            statusElement.className = `status-badge status-${newData.status}`;
            statusElement.textContent = newData.status_display;
        }
        
        if (amountElement && newData.total_amount) {
            amountElement.textContent = formatCurrency(newData.total_amount);
        }
        
        // Анимация обновления
        orderElement.style.transform = 'scale(1.02)';
        setTimeout(() => {
            orderElement.style.transform = 'scale(1)';
        }, 200);
    }
}

// Добавление нового заказа в список
function addOrderToDashboard(orderData) {
    const ordersList = document.querySelector('.orders-list');
    if (!ordersList) return;
    
    // Удаляем empty state если есть
    const emptyState = ordersList.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }
    
    const orderHTML = `
        <div class="order-item" data-order-id="${orderData.id}" style="opacity: 0; transform: translateX(-20px);">
            <div class="order-info">
                <div class="order-id">#${orderData.id}</div>
                <div class="order-client">${orderData.client_name}</div>
                <div class="order-date">${formatDate(orderData.created_at)}</div>
            </div>
            <div class="order-status">
                <span class="status-badge status-${orderData.status}">
                    ${orderData.status_display}
                </span>
            </div>
            <div class="order-amount">
                ${formatCurrency(orderData.total_amount)}
            </div>
            <div class="order-actions">
                <button class="btn-icon" 
                        data-modal-url="/modals/orders/${orderData.id}/detail/" 
                        data-modal-title="Заказ #${orderData.id}">
                    <i class="fas fa-eye"></i>
                </button>
            </div>
        </div>
    `;
    
    ordersList.insertAdjacentHTML('afterbegin', orderHTML);
    
    // Анимация появления
    const newOrder = ordersList.firstElementChild;
    setTimeout(() => {
        newOrder.style.opacity = '1';
        newOrder.style.transform = 'translateX(0)';
    }, 100);
    
    // Обновляем счетчики
    updateDashboardStats();
}

// === ОБРАБОТКА МОДАЛЬНЫХ ОКОН ===

// Обработка успешного создания заказа
window.addEventListener('orderCreated', function(event) {
    addOrderToDashboard(event.detail);
    showAlert('success', 'Заказ успешно создан');
});

// Обработка обновления заказа
window.addEventListener('orderUpdated', function(event) {
    updateOrderInDashboard(event.detail.id, event.detail);
    showAlert('success', 'Заказ обновлен');
});

// === PERFORMANCE MONITORING ===
if ('performance' in window) {
    window.addEventListener('load', function() {
        setTimeout(() => {
            const perfData = performance.getEntriesByType('navigation')[0];
            console.log(`Dashboard loaded in ${Math.round(perfData.loadEventEnd - perfData.loadEventStart)}ms`);
        }, 0);
    });
}

// === CLEANUP ===
window.addEventListener('beforeunload', function() {
    if (statsUpdateInterval) {
        clearInterval(statsUpdateInterval);
    }
    
    if (revenueChart) {
        revenueChart.destroy();
    }
});

// === ЭКСПОРТ ДЛЯ ГЛОБАЛЬНОГО ИСПОЛЬЗОВАНИЯ ===
window.DashboardManager = {
    updateStats: updateDashboardStats,
    updateChart: updateChart,
    refreshChart: refreshChart,
    exportChart: exportChart,
    formatCurrency: formatCurrency,
    formatDate: formatDate
};