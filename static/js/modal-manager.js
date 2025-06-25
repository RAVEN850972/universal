/**
 * Modal Manager for Universal CRM
 * Handles dynamic modal loading and management
 */

class ModalManager {
    constructor() {
        this.currentModal = null;
        this.modalContainer = document.getElementById('modalContainer');
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Auto-bind modal triggers
        document.addEventListener('click', (e) => {
            const trigger = e.target.closest('[data-modal-url]');
            if (trigger) {
                e.preventDefault();
                const url = trigger.dataset.modalUrl;
                const title = trigger.dataset.modalTitle || 'Modal Window';
                const size = trigger.dataset.modalSize || 'lg';
                this.loadModal(url, title, size);
            }
        });

        // Close modal on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.currentModal) {
                this.closeModal();
            }
        });
    }

    async loadModal(url, title = '', size = 'lg') {
        try {
            // Show loading state
            this.showLoading();

            // Fetch modal content
            const response = await fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success === false) {
                throw new Error(data.error || 'Failed to load modal');
            }

            // Create and show modal
            this.createModal(data.html || data, title, size);

        } catch (error) {
            console.error('Modal loading error:', error);
            this.showError(error.message);
        }
    }

    createModal(content, title, size) {
        // Close existing modal if any
        this.closeModal();

        // Create modal structure
        const modalId = 'dynamicModal';
        const modalHtml = `
            <div class="modal fade" id="${modalId}" tabindex="-1">
                ${content}
            </div>
        `;

        // Add to container
        this.modalContainer.innerHTML = modalHtml;

        // Get modal element
        const modalElement = document.getElementById(modalId);
        
        // Initialize Bootstrap modal
        this.currentModal = new bootstrap.Modal(modalElement, {
            backdrop: 'static',
            keyboard: true
        });

        // Show modal
        this.currentModal.show();

        // Setup form handlers
        this.initModalComponents(modalElement);

        // Cleanup on hide
        modalElement.addEventListener('hidden.bs.modal', () => {
            this.cleanup();
        });
    }

    initModalComponents(modal) {
        // Handle forms in modal
        const forms = modal.querySelectorAll('form');
        forms.forEach(form => {
            // Skip if form already has submit handler
            if (form.dataset.initialized) return;
            
            form.dataset.initialized = 'true';
            form.addEventListener('submit', (e) => {
                // Check if form has its own handler
                if (form.onsubmit) return;
                
                e.preventDefault();
                this.handleFormSubmit(form);
            });
        });

        // Initialize tooltips
        const tooltips = modal.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltips.forEach(el => new bootstrap.Tooltip(el));

        // Initialize popovers
        const popovers = modal.querySelectorAll('[data-bs-toggle="popover"]');
        popovers.forEach(el => new bootstrap.Popover(el));

        // Re-initialize any charts if present
        if (window.Chart) {
            const canvases = modal.querySelectorAll('canvas');
            canvases.forEach(canvas => {
                // Trigger chart initialization if needed
                if (canvas.id && window[`init${canvas.id}`]) {
                    window[`init${canvas.id}`]();
                }
            });
        }
    }

    async handleFormSubmit(form) {
        const formData = new FormData(form);
        const submitButton = form.querySelector('[type="submit"]');
        
        // Disable submit button
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Отправка...';
        }

        try {
            const response = await fetch(form.action || window.location.href, {
                method: form.method || 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (data.success) {
                this.notify(data.message || 'Операция выполнена успешно', 'success');
                this.closeModal();

                // Handle redirect
                if (data.redirect_url) {
                    setTimeout(() => {
                        window.location.href = data.redirect_url;
                    }, 500);
                } else if (data.reload) {
                    setTimeout(() => {
                        window.location.reload();
                    }, 500);
                }

                // Trigger custom event
                document.dispatchEvent(new CustomEvent('modalFormSuccess', { 
                    detail: data 
                }));
            } else {
                this.notify(data.error || 'Произошла ошибка', 'danger');
                
                // Show field errors if any
                if (data.errors) {
                    this.showFieldErrors(form, data.errors);
                }
            }
        } catch (error) {
            console.error('Form submission error:', error);
            this.notify('Произошла ошибка при отправке формы', 'danger');
        } finally {
            // Re-enable submit button
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.innerHTML = submitButton.dataset.originalText || 'Сохранить';
            }
        }
    }

    showFieldErrors(form, errors) {
        // Clear previous errors
        form.querySelectorAll('.is-invalid').forEach(el => {
            el.classList.remove('is-invalid');
        });
        form.querySelectorAll('.invalid-feedback').forEach(el => {
            el.remove();
        });

        // Show new errors
        Object.entries(errors).forEach(([field, messages]) => {
            const input = form.querySelector(`[name="${field}"]`);
            if (input) {
                input.classList.add('is-invalid');
                const feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                feedback.textContent = Array.isArray(messages) ? messages[0] : messages;
                input.parentNode.appendChild(feedback);
            }
        });
    }

    showLoading() {
        const loadingHtml = `
            <div class="modal fade show" style="display: block; background: rgba(0,0,0,0.5);">
                <div class="modal-dialog modal-sm modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-body text-center py-4">
                            <div class="spinner-border text-primary mb-3" role="status">
                                <span class="visually-hidden">Загрузка...</span>
                            </div>
                            <p class="mb-0">Загрузка...</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        this.modalContainer.innerHTML = loadingHtml;
    }

    showError(message) {
        const errorHtml = `
            <div class="modal fade show" style="display: block;">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header bg-danger text-white">
                            <h5 class="modal-title">Ошибка</h5>
                            <button type="button" class="btn-close btn-close-white" onclick="modalManager.closeModal()"></button>
                        </div>
                        <div class="modal-body">
                            <div class="alert alert-danger mb-0">
                                <i class="fas fa-exclamation-circle me-2"></i>
                                ${message}
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" onclick="modalManager.closeModal()">Закрыть</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        this.modalContainer.innerHTML = errorHtml;
    }

    closeModal() {
        if (this.currentModal) {
            this.currentModal.hide();
        } else {
            this.cleanup();
        }
    }

    cleanup() {
        this.modalContainer.innerHTML = '';
        this.currentModal = null;
        
        // Remove backdrop if stuck
        document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
        
        // Restore body scroll
        document.body.classList.remove('modal-open');
        document.body.style.removeProperty('overflow');
        document.body.style.removeProperty('padding-right');
    }

    notify(message, type = 'info') {
        // Use the global showAlert function if available
        if (window.showAlert) {
            window.showAlert(type, message);
        } else {
            // Fallback notification
            const alertHtml = `
                <div class="alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3" style="z-index: 9999;">
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', alertHtml);
            
            // Auto remove after 5 seconds
            setTimeout(() => {
                const alert = document.querySelector('.alert.position-fixed');
                if (alert) alert.remove();
            }, 5000);
        }
    }

    confirm(message, onConfirm, onCancel) {
        const confirmHtml = `
            <div class="modal fade show" style="display: block;">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Подтверждение</h5>
                        </div>
                        <div class="modal-body">
                            <p>${message}</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" id="confirmCancel">Отмена</button>
                            <button type="button" class="btn btn-primary" id="confirmOk">Подтвердить</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        this.modalContainer.innerHTML = confirmHtml;
        
        document.getElementById('confirmOk').onclick = () => {
            this.closeModal();
            if (onConfirm) onConfirm();
        };
        
        document.getElementById('confirmCancel').onclick = () => {
            this.closeModal();
            if (onCancel) onCancel();
        };
    }
}

// Initialize modal manager
const modalManager = new ModalManager();

// Global functions for backward compatibility
function loadModal(url, title, size, callback) {
    modalManager.loadModal(url, title, size).then(() => {
        if (callback) callback();
    });
}

function closeModal() {
    modalManager.closeModal();
}

// Utility functions
const utils = {
    formatCurrency(amount, currency = 'RUB') {
        return new Intl.NumberFormat('ru-RU', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 0,
            maximumFractionDigits: 2
        }).format(amount);
    },

    formatDate(date, options = {}) {
        const defaultOptions = {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        };
        const finalOptions = { ...defaultOptions, ...options };
        const dateObj = typeof date === 'string' ? new Date(date) : date;
        return new Intl.DateTimeFormat('ru-RU', finalOptions).format(dateObj);
    },

    debounce(func, delay) {
        let timeoutId;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    }
};

// Export for use in other scripts
window.modalManager = modalManager;
window.utils = utils;