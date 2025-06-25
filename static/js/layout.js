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
    let overlay = document.querySelector('.sidebar-overlay');
    
    if (!sidebar) return;
    
    // Создаем оверлей если его нет
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        overlay.onclick = closeSidebar;
        document.body.appendChild(overlay);
    }
    
    sidebarOpen = !sidebarOpen;
    
    if (sidebarOpen) {
        sidebar.classList.add('open');
        overlay.classList.add('show');
        document.body.style.overflow = 'hidden';
    } else {
        sidebar.classList.remove('open');
        overlay.classList.remove('show');
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
 * Создание кнопки мобильного меню
 */
function createMobileMenuButton() {
    // Проверяем есть ли уже кнопка
    if (document.querySelector('.mobile-menu-btn')) return;
    
    const button = document.createElement('button');
    button.className = 'mobile-menu-btn';
    button.innerHTML = '<i class="fas fa-bars"></i>';
    button.onclick = toggleSidebar;
    
    // Ищем куда вставить кнопку (в заголовок страницы)
    const pageHeader = document.querySelector('.page-header');
    if (pageHeader) {
        const headerContent = pageHeader.querySelector('.page-header-content');
        if (headerContent) {
            headerContent.insertBefore(button, headerContent.firstChild);
        }
    }
}

/**
 * Инициализация состояния сайдбара
 */
function initSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;
    
    // Восстанавливаем состояние сворачивания только на десктопе
    if (window.innerWidth >= 1024 && sidebarCollapsed) {
        sidebar.classList.add('collapsed');
    }
    
    // Создаем кнопку мобильного меню если её нет
    createMobileMenuButton();
    
    // Обработчики для подменю
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        const link = item.querySelector('.nav-link');
        const submenu = item.querySelector('.nav-submenu');
        const arrow = item.querySelector('.nav-arrow');
        
        if (submenu && arrow) {
            link.addEventListener('click', function(e) {
                if (window.innerWidth < 1024) {
                    e.preventDefault();
                    item.classList.toggle('open');
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

// === АДАПТИВНОСТЬ ===

/**
 * Обработка изменения размера окна
 */
function handleResize() {
    const width = window.innerWidth;
    const sidebar = document.getElementById('sidebar');
    
    if (width >= 1024) {
        // Десктоп - закрываем мобильное меню и восстанавливаем состояние
        closeSidebar();
        if (sidebarCollapsed) {
            sidebar?.classList.add('collapsed');
        } else {
            sidebar?.classList.remove('collapsed');
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
            } else {
                link.classList.remove('active');
            }
        }
    });
}

// === АНИМАЦИИ ===

/**
 * Анимация элементов при загрузке
 */
function animateElements() {
    const elements = document.querySelectorAll('.stat-card, .dashboard-card, .card');
    elements.forEach((element, index) => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            element.style.transition = 'all 0.6s ease-out';
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

// === ОБРАБОТЧИКИ КЛАВИАТУРЫ ===

/**
 * Обработка горячих клавиш
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
    
    // Escape - закрытие мобильного сайдбара
    if (e.key === 'Escape' && sidebarOpen) {
        closeSidebar();
    }
}

// === УВЕДОМЛЕНИЯ ===

/**
 * Показать уведомление
 */
function showAlert(type, message, duration = 5000) {
    const alertHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
            ${message}
            <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
        </div>
    `;
    
    let container = document.querySelector('.messages-container');
    if (!container) {
        container = document.querySelector('.page-content-body');
    }
    
    if (container) {
        container.insertAdjacentHTML('afterbegin', alertHTML);
        
        // Автоматическое скрытие
        if (duration > 0) {
            setTimeout(() => {
                const alert = container.querySelector('.alert');
                if (alert) {
                    alert.remove();
                }
            }, duration);
        }
    }
}

// === УТИЛИТЫ ===

/**
 * Throttle функция для оптимизации производительности
 */
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
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
 * Инициализация каркаса
 */
function initLayout() {
    initSidebar();
    initTheme();
    updateActiveNavigation();
    animateElements();
    
    // Обработчики событий
    window.addEventListener('resize', throttle(handleResize, 250));
    document.addEventListener('keydown', handleKeyboardShortcuts);
    
    // Обработка кликов вне сайдбара на мобильных
    document.addEventListener('click', function(e) {
        if (window.innerWidth < 1024 && sidebarOpen) {
            const sidebar = document.getElementById('sidebar');
            const mobileBtn = document.querySelector('.mobile-menu-btn');
            
            if (sidebar && !sidebar.contains(e.target) && 
                mobileBtn && !mobileBtn.contains(e.target)) {
                closeSidebar();
            }
        }
    });
    
    // Первоначальная настройка адаптивности
    handleResize();
    
    console.log('Layout initialized');
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', initLayout);

// Экспорт функций для глобального использования
window.toggleSidebar = toggleSidebar;
window.closeSidebar = closeSidebar;
window.collapseSidebar = collapseSidebar;
window.toggleDarkMode = toggleDarkMode;
window.showAlert = showAlert;
window.updatePageTitle = updatePageTitle;