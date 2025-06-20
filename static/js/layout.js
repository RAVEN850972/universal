/**
 * === JAVASCRIPT ДЛЯ КАРКАСА ПРИЛОЖЕНИЯ ===
 * static/js/layout.js
 */

// === СОСТОЯНИЕ ИНТЕРФЕЙСА ===
let sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
let sidebarOpen = false;
let darkMode = localStorage.getItem('darkMode') === 'true';

// === УПРАВЛЕНИЕ САЙДБАРОМ ===

/**
 * Переключение мобильного сайдбара
 */
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    
    if (!sidebar) return;
    
    sidebarOpen = !sidebarOpen;
    
    if (sidebarOpen) {
        sidebar.classList.add('open');
        overlay?.classList.add('show');
        document.body.style.overflow = 'hidden';
    } else {
        sidebar.classList.remove('open');
        overlay?.classList.remove('show');
        document.body.style.overflow = '';
    }
}

/**
 * Закрытие мобильного сайдбара
 */
function closeSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    
    if (!sidebar) return;
    
    sidebarOpen = false;
    sidebar.classList.remove('open');
    overlay?.classList.remove('show');
    document.body.style.overflow = '';
}

/**
 * Сворачивание/разворачивание сайдбара (десктоп)
 */
function collapseSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;
    
    sidebarCollapsed = !sidebarCollapsed;
    
    if (sidebarCollapsed) {
        sidebar.classList.add('collapsed');
    } else {
        sidebar.classList.remove('collapsed');
    }
    
    // Сохраняем состояние
    localStorage.setItem('sidebarCollapsed', sidebarCollapsed.toString());
    
    // Диспатчим событие для других компонентов
    window.dispatchEvent(new CustomEvent('sidebarToggle', {
        detail: { collapsed: sidebarCollapsed }
    }));
}

/**
 * Инициализация состояния сайдбара
 */
function initSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;
    
    // Восстанавливаем состояние сворачивания
    if (sidebarCollapsed) {
        sidebar.classList.add('collapsed');
    }
    
    // Обработчики для подменю
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        const link = item.querySelector('.nav-link');
        const submenu = item.querySelector('.nav-submenu');
        const arrow = item.querySelector('.nav-arrow');
        
        if (submenu && arrow) {
            link.addEventListener('click', function(e) {
                // Только для ссылок с подменю без href
                if (this.getAttribute('href') === '#') {
                    e.preventDefault();
                    
                    const isOpen = item.classList.contains('open');
                    
                    // Закрываем все другие подменю
                    navItems.forEach(otherItem => {
                        if (otherItem !== item) {
                            otherItem.classList.remove('open');
                        }
                    });
                    
                    // Переключаем текущее
                    item.classList.toggle('open', !isOpen);
                }
            });
        }
    });
}

// === УПРАВЛЕНИЕ ТЕМОЙ ===

/**
 * Переключение темной темы
 */
function toggleDarkMode() {
    darkMode = !darkMode;
    
    if (darkMode) {
        document.body.classList.add('dark-theme');
    } else {
        document.body.classList.remove('dark-theme');
    }
    
    // Сохраняем состояние
    localStorage.setItem('darkMode', darkMode.toString());
    
    // Обновляем иконку
    const themeBtn = document.querySelector('[onclick="toggleDarkMode()"]');
    if (themeBtn) {
        const icon = themeBtn.querySelector('i');
        if (icon) {
            icon.className = darkMode ? 'fas fa-sun' : 'fas fa-moon';
        }
    }
    
    // Диспатчим событие
    window.dispatchEvent(new CustomEvent('themeChange', {
        detail: { darkMode }
    }));
}

/**
 * Инициализация темы
 */
function initTheme() {
    if (darkMode) {
        document.body.classList.add('dark-theme');
    }
    
    // Обновляем иконку
    const themeBtn = document.querySelector('[onclick="toggleDarkMode()"]');
    if (themeBtn) {
        const icon = themeBtn.querySelector('i');
        if (icon) {
            icon.className = darkMode ? 'fas fa-sun' : 'fas fa-moon';
        }
    }
}

// === УВЕДОМЛЕНИЯ ===

/**
 * Показать панель уведомлений
 */
function showNotifications() {
    // Будет реализовано позже с модальными окнами
    console.log('Показать уведомления');
}

/**
 * Обновление счетчика уведомлений
 */
function updateNotificationCount(count) {
    const badges = document.querySelectorAll('.action-badge, .nav-badge');
    badges.forEach(badge => {
        if (count > 0) {
            badge.textContent = count;
            badge.style.display = 'block';
        } else {
            badge.style.display = 'none';
        }
    });
}

// === БЫСТРЫЕ ДЕЙСТВИЯ ===

/**
 * Показать модальное окно быстрого создания заказа
 */
function showQuickOrderModal() {
    // Будет реализовано позже с модальными окнами
    console.log('Быстрое создание заказа');
}

// === АДАПТИВНОСТЬ ===

/**
 * Обработка изменения размера окна
 */
function handleResize() {
    const width = window.innerWidth;
    const sidebar = document.getElementById('sidebar');
    
    if (width >= 1024) {
        // Десктоп - восстанавливаем состояние сворачивания
        closeSidebar(); // Закрываем мобильное меню
        if (sidebarCollapsed) {
            sidebar?.classList.add('collapsed');
        }
    } else {
        // Мобильный - убираем сворачивание
        sidebar?.classList.remove('collapsed');
    }
}

// === НАВИГАЦИЯ ===

/**
 * Обновление активной ссылки навигации
 */
function updateActiveNavigation() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && href !== '#') {
            if (currentPath === href || (href !== '/' && currentPath.startsWith(href))) {
                link.classList.add('active');
                
                // Открываем родительское подменю если есть
                const parentItem = link.closest('.nav-item');
                const parentSubmenu = parentItem.closest('.nav-submenu');
                if (parentSubmenu) {
                    const grandParentItem = parentSubmenu.closest('.nav-item');
                    grandParentItem?.classList.add('open');
                }
            } else {
                link.classList.remove('active');
            }
        }
    });
}

// === СОСТОЯНИЕ ПОДКЛЮЧЕНИЯ ===

/**
 * Обновление статуса подключения
 */
function updateConnectionStatus(online = true) {
    const statusElement = document.querySelector('.connection-status');
    if (!statusElement) return;
    
    if (online) {
        statusElement.classList.add('online');
        statusElement.classList.remove('offline');
        statusElement.innerHTML = '<i class="fas fa-circle"></i><span>Онлайн</span>';
    } else {
        statusElement.classList.remove('online');
        statusElement.classList.add('offline');
        statusElement.innerHTML = '<i class="fas fa-circle"></i><span>Офлайн</span>';
    }
}

/**
 * Мониторинг подключения
 */
function initConnectionMonitoring() {
    // Проверяем статус подключения
    updateConnectionStatus(navigator.onLine);
    
    // Слушаем изменения статуса
    window.addEventListener('online', () => updateConnectionStatus(true));
    window.addEventListener('offline', () => updateConnectionStatus(false));
    
    // Периодическая проверка (опционально)
    setInterval(async () => {
        try {
            const response = await fetch('/api/ping/', { 
                method: 'HEAD',
                cache: 'no-cache'
            });
            updateConnectionStatus(response.ok);
        } catch {
            updateConnectionStatus(false);
        }
    }, 30000); // Каждые 30 секунд
}

// === КЛАВИАТУРНЫЕ СОКРАЩЕНИЯ ===

/**
 * Обработка клавиатурных сокращений
 */
function handleKeyboardShortcuts(e) {
    // Ctrl/Cmd + B - переключение сайдбара
    if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
        e.preventDefault();
        if (window.innerWidth >= 1024) {
            collapseSidebar();
        } else {
            toggleSidebar();
        }
    }
    
    // Ctrl/Cmd + K - поиск (если есть)
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('#globalSearch');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Ctrl/Cmd + Shift + N - быстрое создание заказа
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'N') {
        e.preventDefault();
        showQuickOrderModal();
    }
    
    // Ctrl/Cmd + Shift + D - переключение темы
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'D') {
        e.preventDefault();
        toggleDarkMode();
    }
}

// === АНИМАЦИИ ===

/**
 * Анимация появления элементов
 */
function animateElements() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });
    
    // Наблюдаем за элементами с классом animate-on-scroll
    document.querySelectorAll('.animate-on-scroll').forEach(el => {
        observer.observe(el);
    });
}

// === ИНИЦИАЛИЗАЦИЯ ===

/**
 * Инициализация всех компонентов каркаса
 */
function initLayout() {
    initSidebar();
    initTheme();
    updateActiveNavigation();
    initConnectionMonitoring();
    animateElements();
    
    // Обработчики событий
    window.addEventListener('resize', throttle(handleResize, 250));
    document.addEventListener('keydown', handleKeyboardShortcuts);
    
    // Обработка кликов вне сайдбара на мобильных
    document.addEventListener('click', function(e) {
        if (window.innerWidth < 1024 && sidebarOpen) {
            const sidebar = document.getElementById('sidebar');
            const sidebarToggle = document.querySelector('.sidebar-toggle');
            
            if (sidebar && !sidebar.contains(e.target) && 
                sidebarToggle && !sidebarToggle.contains(e.target)) {
                closeSidebar();
            }
        }
    });
    
    // Первоначальная настройка адаптивности
    handleResize();
    
    console.log('Layout initialized');
}

// === УТИЛИТЫ ДЛЯ ДРУГИХ КОМПОНЕНТОВ ===

/**
 * Показать loading на странице
 */
function showPageLoading() {
    const main = document.querySelector('.page-content-body');
    if (main) {
        main.classList.add('loading');
    }
}

/**
 * Скрыть loading на странице
 */
function hidePageLoading() {
    const main = document.querySelector('.page-content-body');
    if (main) {
        main.classList.remove('loading');
    }
}

/**
 * Обновить заголовок страницы
 */
function updatePageTitle(title, subtitle = '') {
    document.title = title + ' - Universal CRM';
    
    const pageTitle = document.querySelector('.page-title');
    const pageSubtitle = document.querySelector('.page-subtitle');
    
    if (pageTitle) {
        // Сохраняем иконку если есть
        const icon = pageTitle.querySelector('i');
        pageTitle.innerHTML = (icon ? icon.outerHTML + ' ' : '') + title;
    }
    
    if (pageSubtitle) {
        if (subtitle) {
            pageSubtitle.textContent = subtitle;
            pageSubtitle.style.display = 'block';
        } else {
            pageSubtitle.style.display = 'none';
        }
    }
}

/**
 * Обновить хлебные крошки
 */
function updateBreadcrumbs(breadcrumbs) {
    const container = document.querySelector('.breadcrumb-list');
    if (!container) return;
    
    container.innerHTML = breadcrumbs.map((crumb, index) => {
        const isLast = index === breadcrumbs.length - 1;
        return `
            <li class="breadcrumb-item${isLast ? ' active' : ''}">
                ${isLast || !crumb.url ? 
                    `<span>${crumb.title}</span>` : 
                    `<a href="${crumb.url}">${crumb.title}</a>`
                }
            </li>
        `;
    }).join('');
}

// === ЭКСПОРТ ДЛЯ МОДУЛЬНЫХ СИСТЕМ ===
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        toggleSidebar,
        closeSidebar,
        collapseSidebar,
        toggleDarkMode,
        showNotifications,
        updateNotificationCount,
        showQuickOrderModal,
        updateActiveNavigation,
        updateConnectionStatus,
        showPageLoading,
        hidePageLoading,
        updatePageTitle,
        updateBreadcrumbs,
        initLayout
    };
}

// === АВТОИНИЦИАЛИЗАЦИЯ ===
document.addEventListener('DOMContentLoaded', initLayout);