/**
 * === JAVASCRIPT ДЛЯ СТРАНИЦ АВТОРИЗАЦИИ ===
 * static/js/auth.js
 */

// === СТРАНИЦА ВХОДА ===

/**
 * Заполнение полей демо-аккаунта
 * @param {string} username - Логин
 * @param {string} password - Пароль
 */
function fillCredentials(username, password) {
    const usernameField = document.getElementById('username');
    const passwordField = document.getElementById('password');
    
    if (!usernameField || !passwordField) return;
    
    usernameField.value = username;
    passwordField.value = password;
    
    // Визуальная обратная связь
    [usernameField, passwordField].forEach(field => {
        field.style.transform = 'scale(1.02)';
        field.style.borderColor = 'var(--border-color-focus)';
        field.style.boxShadow = '0 0 0 3px rgba(0, 0, 0, 0.1)';
        
        setTimeout(() => {
            field.style.transform = 'scale(1)';
            field.style.borderColor = 'var(--border-color)';
            field.style.boxShadow = 'none';
        }, 200);
    });
    
    // Очищаем предыдущие ошибки
    const alertsContainer = document.getElementById('alerts-container');
    if (alertsContainer) {
        alertsContainer.innerHTML = '';
    }
}

/**
 * Валидация формы входа
 * @returns {boolean}
 */
function validateLoginForm() {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();
    
    if (!username) {
        showAlert('Пожалуйста, введите логин', 'error');
        document.getElementById('username').focus();
        return false;
    }
    
    if (!password) {
        showAlert('Пожалуйста, введите пароль', 'error');
        document.getElementById('password').focus();
        return false;
    }
    
    if (username.length < 3) {
        showAlert('Логин должен содержать минимум 3 символа', 'error');
        document.getElementById('username').focus();
        return false;
    }
    
    if (password.length < 6) {
        showAlert('Пароль должен содержать минимум 6 символов', 'error');
        document.getElementById('password').focus();
        return false;
    }
    
    return true;
}

/**
 * Обработка отправки формы входа
 * @param {Event} e - Событие отправки формы
 */
async function handleLoginSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const loginBtn = document.getElementById('loginBtn');
    
    // Валидация
    if (!validateLoginForm()) {
        return;
    }
    
    // Показываем состояние загрузки
    setLoading(loginBtn, true);
    
    try {
        // Получаем данные формы
        const formData = new FormData(form);
        
        // Отправляем запрос
        const response = await fetch(form.action || window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (response.ok) {
            // Успешный вход
            showAlert('Вход выполнен успешно! Перенаправление...', 'success');
            
            // Перенаправление
            setTimeout(() => {
                window.location.href = response.url || '/dashboard/';
            }, 1000);
        } else {
            // Ошибка входа
            const text = await response.text();
            
            // Пытаемся извлечь сообщение об ошибке из HTML
            const parser = new DOMParser();
            const doc = parser.parseFromString(text, 'text/html');
            const errorMessages = doc.querySelectorAll('.alert-error, .errorlist li');
            
            let errorText = 'Неверный логин или пароль';
            if (errorMessages.length > 0) {
                errorText = errorMessages[0].textContent.trim();
            }
            
            showAlert(errorText, 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showAlert('Произошла ошибка при входе. Попробуйте еще раз.', 'error');
    } finally {
        setLoading(loginBtn, false);
    }
}

// === СТРАНИЦА ВЫБОРА КОМПАНИИ ===

/**
 * Выбор компании
 * @param {string} companyId - ID компании
 */
function selectCompany(companyId) {
    const companyItems = document.querySelectorAll('.company-item');
    
    // Убираем выделение со всех элементов
    companyItems.forEach(item => item.classList.remove('selected'));
    
    // Выделяем выбранную компанию
    const selectedItem = document.querySelector(`[data-company-id="${companyId}"]`);
    if (selectedItem) {
        selectedItem.classList.add('selected');
    }
    
    // Обновляем скрытое поле
    const companyInput = document.getElementById('company_id');
    if (companyInput) {
        companyInput.value = companyId;
    }
}

/**
 * Обработка отправки формы выбора компании
 * @param {Event} e - Событие отправки формы
 */
async function handleCompanySelectSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const companyId = document.getElementById('company_id').value;
    
    if (!companyId) {
        showAlert('Пожалуйста, выберите компанию', 'error');
        return;
    }
    
    setLoading(submitBtn, true);
    
    try {
        const formData = new FormData(form);
        
        const response = await fetch(form.action || window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (response.ok) {
            showAlert('Компания выбрана! Перенаправление...', 'success');
            setTimeout(() => {
                window.location.href = response.url || '/dashboard/';
            }, 1000);
        } else {
            showAlert('Ошибка при выборе компании', 'error');
        }
    } catch (error) {
        console.error('Company select error:', error);
        showAlert('Произошла ошибка. Попробуйте еще раз.', 'error');
    } finally {
        setLoading(submitBtn, false);
    }
}

// === ОБЩИЕ ФУНКЦИИ ===

/**
 * Переключение видимости пароля
 * @param {string} passwordFieldId - ID поля пароля
 * @param {string} toggleButtonId - ID кнопки переключения
 */
function togglePasswordVisibility(passwordFieldId = 'password', toggleButtonId = 'passwordToggle') {
    const passwordField = document.getElementById(passwordFieldId);
    const toggleButton = document.getElementById(toggleButtonId);
    
    if (!passwordField || !toggleButton) return;
    
    if (passwordField.type === 'password') {
        passwordField.type = 'text';
        toggleButton.classList.remove('fa-eye');
        toggleButton.classList.add('fa-eye-slash');
    } else {
        passwordField.type = 'password';
        toggleButton.classList.remove('fa-eye-slash');
        toggleButton.classList.add('fa-eye');
    }
}

/**
 * Обработка ошибок полей формы
 * @param {Object} errors - Объект с ошибками
 */
function handleFieldErrors(errors) {
    // Очищаем предыдущие ошибки
    document.querySelectorAll('.form-control').forEach(field => {
        field.classList.remove('error');
    });
    document.querySelectorAll('.form-error').forEach(error => {
        error.remove();
    });
    
    // Показываем новые ошибки
    for (const [fieldName, errorMessage] of Object.entries(errors)) {
        const field = document.querySelector(`[name="${fieldName}"]`);
        if (field) {
            field.classList.add('error');
            
            const errorDiv = document.createElement('div');
            errorDiv.className = 'form-error';
            errorDiv.textContent = errorMessage;
            
            field.parentNode.appendChild(errorDiv);
        }
    }
}

// === ИНИЦИАЛИЗАЦИЯ ===

ready(function() {
    // Обработка формы входа
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLoginSubmit);
        
        // Очистка ошибок при вводе
        ['username', 'password'].forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.addEventListener('input', function() {
                    this.classList.remove('error');
                    const errorMsg = this.parentNode.querySelector('.form-error');
                    if (errorMsg) errorMsg.remove();
                    
                    // Очищаем общие уведомления
                    const alertsContainer = document.getElementById('alerts-container');
                    if (alertsContainer && alertsContainer.children.length > 0) {
                        alertsContainer.innerHTML = '';
                    }
                });
            }
        });
        
        // Обработка Enter в полях
        loginForm.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.dispatchEvent(new Event('submit'));
            }
        });
    }
    
    // Обработка формы выбора компании
    const companyForm = document.getElementById('companyForm');
    if (companyForm) {
        companyForm.addEventListener('submit', handleCompanySelectSubmit);
        
        // Обработка клика по элементам компаний
        const companyItems = document.querySelectorAll('.company-item');
        companyItems.forEach(item => {
            item.addEventListener('click', function() {
                const companyId = this.getAttribute('data-company-id');
                selectCompany(companyId);
            });
        });
    }
    
    // Кнопка переключения видимости пароля
    const passwordToggle = document.getElementById('passwordToggle');
    if (passwordToggle) {
        passwordToggle.addEventListener('click', function(e) {
            e.preventDefault();
            togglePasswordVisibility();
        });
    }
    
    // Автоматическое заполнение демо-аккаунтов
    const demoAccounts = document.querySelectorAll('.demo-account');
    demoAccounts.forEach(account => {
        account.addEventListener('click', function() {
            const credentials = this.getAttribute('data-credentials');
            if (credentials) {
                const [username, password] = credentials.split(':');
                fillCredentials(username, password);
            }
        });
    });
    
    // Анимация появления элементов
    const animatedElements = document.querySelectorAll('.login-card, .company-card');
    animatedElements.forEach((element, index) => {
        element.style.animationDelay = `${index * 0.1}s`;
    });
    
    // Обработка изменения размера окна для мобильных устройств
    let viewport = document.querySelector('meta[name=viewport]');
    function handleViewportChange() {
        if (window.innerWidth < 768) {
            if (viewport) {
                viewport.setAttribute('content', 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no');
            }
        } else {
            if (viewport) {
                viewport.setAttribute('content', 'width=device-width, initial-scale=1.0');
            }
        }
    }
    
    handleViewportChange();
    window.addEventListener('resize', debounce(handleViewportChange, 250));
});

// === ЭКСПОРТ ДЛЯ МОДУЛЬНЫХ СИСТЕМ ===
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        fillCredentials,
        validateLoginForm,
        handleLoginSubmit,
        selectCompany,
        handleCompanySelectSubmit,
        togglePasswordVisibility,
        handleFieldErrors
    };
}