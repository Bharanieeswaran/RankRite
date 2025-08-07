// Toast notification system
class ToastManager {
    constructor() {
        this.toasts = [];
        this.container = null;
        this.init();
    }

    init() {
        this.createContainer();
        this.setupStyles();
    }

    createContainer() {
        if (document.getElementById('toast-container')) return;
        
        this.container = document.createElement('div');
        this.container.id = 'toast-container';
        this.container.className = 'toast-container';
        document.body.appendChild(this.container);
    }

    setupStyles() {
        if (document.getElementById('toast-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'toast-styles';
        styles.textContent = `
            .toast-container {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                max-width: 400px;
            }
            
            .toast {
                background: var(--toast-bg, #333);
                color: var(--toast-text, #fff);
                padding: 12px 16px;
                margin-bottom: 10px;
                border-radius: 6px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                transform: translateX(100%);
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: space-between;
                min-width: 300px;
                word-wrap: break-word;
            }
            
            .toast.show {
                transform: translateX(0);
            }
            
            .toast.success {
                background: var(--success-color, #10b981);
                border-left: 4px solid var(--success-border, #059669);
            }
            
            .toast.error {
                background: var(--error-color, #ef4444);
                border-left: 4px solid var(--error-border, #dc2626);
            }
            
            .toast.warning {
                background: var(--warning-color, #f59e0b);
                border-left: 4px solid var(--warning-border, #d97706);
                color: var(--warning-text, #1f2937);
            }
            
            .toast.info {
                background: var(--info-color, #3b82f6);
                border-left: 4px solid var(--info-border, #2563eb);
            }
            
            .toast-content {
                flex: 1;
                margin-right: 10px;
            }
            
            .toast-title {
                font-weight: 600;
                margin-bottom: 4px;
            }
            
            .toast-message {
                font-size: 14px;
                opacity: 0.9;
            }
            
            .toast-close {
                background: none;
                border: none;
                color: inherit;
                cursor: pointer;
                font-size: 18px;
                padding: 0;
                width: 20px;
                height: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                opacity: 0.7;
                transition: opacity 0.2s;
            }
            
            .toast-close:hover {
                opacity: 1;
            }
            
            .toast-icon {
                margin-right: 8px;
                font-size: 16px;
            }
            
            @media (max-width: 480px) {
                .toast-container {
                    left: 10px;
                    right: 10px;
                    top: 10px;
                }
                
                .toast {
                    min-width: auto;
                    width: 100%;
                }
            }
        `;
        document.head.appendChild(styles);
    }

    show(message, type = 'info', options = {}) {
        const toastId = 'toast-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
        
        const defaultOptions = {
            duration: 4000,
            closable: true,
            title: null,
            icon: this.getIcon(type),
            position: 'top-right'
        };
        
        const config = { ...defaultOptions, ...options };
        
        const toast = this.createToastElement(toastId, message, type, config);
        this.container.appendChild(toast);
        
        // Trigger animation
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });
        
        // Auto-remove after duration
        if (config.duration > 0) {
            setTimeout(() => {
                this.remove(toastId);
            }, config.duration);
        }
        
        // Store toast reference
        this.toasts.push({
            id: toastId,
            element: toast,
            type: type
        });
        
        return toastId;
    }

    createToastElement(id, message, type, config) {
        const toast = document.createElement('div');
        toast.id = id;
        toast.className = `toast ${type}`;
        
        const content = document.createElement('div');
        content.className = 'toast-content';
        
        if (config.title) {
            const title = document.createElement('div');
            title.className = 'toast-title';
            title.textContent = config.title;
            content.appendChild(title);
        }
        
        const messageEl = document.createElement('div');
        messageEl.className = 'toast-message';
        
        if (config.icon) {
            const icon = document.createElement('span');
            icon.className = 'toast-icon';
            icon.innerHTML = config.icon;
            messageEl.appendChild(icon);
        }
        
        const messageText = document.createElement('span');
        messageText.textContent = message;
        messageEl.appendChild(messageText);
        
        content.appendChild(messageEl);
        toast.appendChild(content);
        
        if (config.closable) {
            const closeBtn = document.createElement('button');
            closeBtn.className = 'toast-close';
            closeBtn.innerHTML = '×';
            closeBtn.setAttribute('aria-label', 'Close notification');
            closeBtn.addEventListener('click', () => this.remove(id));
            toast.appendChild(closeBtn);
        }
        
        return toast;
    }

    remove(toastId) {
        const toastIndex = this.toasts.findIndex(t => t.id === toastId);
        if (toastIndex === -1) return;
        
        const toast = this.toasts[toastIndex];
        toast.element.classList.remove('show');
        
        setTimeout(() => {
            if (toast.element && toast.element.parentNode) {
                toast.element.parentNode.removeChild(toast.element);
            }
            this.toasts.splice(toastIndex, 1);
        }, 300);
    }

    getIcon(type) {
        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };
        return icons[type] || icons.info;
    }

    // Convenience methods
    success(message, options = {}) {
        return this.show(message, 'success', options);
    }

    error(message, options = {}) {
        return this.show(message, 'error', { ...options, duration: 6000 });
    }

    warning(message, options = {}) {
        return this.show(message, 'warning', options);
    }

    info(message, options = {}) {
        return this.show(message, 'info', options);
    }

    // Clear all toasts
    clear() {
        this.toasts.forEach(toast => {
            this.remove(toast.id);
        });
    }

    // Show toast from Flask flash messages
    showFlashMessages() {
        const flashMessages = document.querySelectorAll('.flash-message');
        flashMessages.forEach(flash => {
            const message = flash.textContent.trim();
            const type = flash.getAttribute('data-category') || 'info';
            this.show(message, type);
            flash.remove();
        });
    }
}

// Initialize toast manager and handle Flask flash messages
document.addEventListener('DOMContentLoaded', () => {
    window.toast = new ToastManager();
    
    // Show any Flask flash messages
    window.toast.showFlashMessages();
    
    // Listen for custom toast events
    document.addEventListener('showToast', (e) => {
        const { message, type, options } = e.detail;
        window.toast.show(message, type, options);
    });
});

// Global helper functions
window.showToast = (message, type = 'info', options = {}) => {
    if (window.toast) {
        return window.toast.show(message, type, options);
    } else {
        console.error('Toast manager not initialized');
        return null;
    }
};

window.showSuccess = (message, options = {}) => {
    return window.showToast(message, 'success', options);
};

window.showError = (message, options = {}) => {
    return window.showToast(message, 'error', { ...options, duration: 6000 });
};

window.showWarning = (message, options = {}) => {
    return window.showToast(message, 'warning', options);
};

window.showInfo = (message, options = {}) => {
    return window.showToast(message, 'info', options);
};

// Standardized error handler for fetch/ajax requests
window.handleRequestError = (error, defaultMessage = 'An error occurred') => {
    console.error('Request error:', error);
    
    let errorMessage = defaultMessage;
    
    if (error.response && error.response.data && error.response.data.message) {
        // Axios-style error
        errorMessage = error.response.data.message;
    } else if (error.responseJSON && error.responseJSON.message) {
        // jQuery ajax error
        errorMessage = error.responseJSON.message;
    } else if (error.message) {
        // Standard Error object
        errorMessage = error.message;
    } else if (typeof error === 'string') {
        // String error
        errorMessage = error;
    }
    
    window.showError(errorMessage);
    return errorMessage;
};

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ToastManager;
}