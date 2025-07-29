/**
 * Toast Notification System
 */

(function() {
    'use strict';

    // Configuration
    const TOAST_CONTAINER_ID = 'toast-container';
    const DEFAULT_DURATION = 5000; // 5 seconds
    const MAX_TOASTS = 5;
    
    let toastContainer = null;
    let toastCounter = 0;
    let activeToasts = new Map();

    // Toast types configuration
    const TOAST_TYPES = {
        success: {
            icon: 'bi-check-circle-fill',
            bgClass: 'bg-success',
            textClass: 'text-white'
        },
        error: {
            icon: 'bi-exclamation-triangle-fill',
            bgClass: 'bg-danger',
            textClass: 'text-white'
        },
        warning: {
            icon: 'bi-exclamation-triangle',
            bgClass: 'bg-warning',
            textClass: 'text-dark'
        },
        info: {
            icon: 'bi-info-circle-fill',
            bgClass: 'bg-info',
            textClass: 'text-white'
        },
        primary: {
            icon: 'bi-bell-fill',
            bgClass: 'bg-primary',
            textClass: 'text-white'
        }
    };

    // Initialize toast system
    function initToasts() {
        toastContainer = document.querySelector('.toast-container');
        
        if (!toastContainer) {
            createToastContainer();
        }
    }

    // Create toast container if it doesn't exist
    function createToastContainer() {
        const container = document.createElement('div');
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '1060';
        document.body.appendChild(container);
        toastContainer = container;
    }

    // Create toast element
    function createToastElement(message, type = 'info', duration = DEFAULT_DURATION, title = null) {
        const toastId = `toast-${++toastCounter}`;
        const typeConfig = TOAST_TYPES[type] || TOAST_TYPES.info;
        
        // Auto-generate title if not provided
        if (!title) {
            title = type.charAt(0).toUpperCase() + type.slice(1);
        }

        const toastHtml = `
            <div id="${toastId}" class="toast ${typeConfig.bgClass} ${typeConfig.textClass}" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header ${typeConfig.bgClass} ${typeConfig.textClass} border-0">
                    <i class="bi ${typeConfig.icon} me-2"></i>
                    <strong class="me-auto">${escapeHtml(title)}</strong>
                    <small class="opacity-75">${getTimeString()}</small>
                    <button type="button" class="btn-close btn-close-${typeConfig.textClass === 'text-white' ? 'white' : 'dark'}" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body">
                    ${escapeHtml(message)}
                </div>
            </div>
        `;

        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        return document.getElementById(toastId);
    }

    // Show toast notification
    function showToast(message, type = 'info', duration = DEFAULT_DURATION, title = null) {
        if (!toastContainer) {
            initToasts();
        }

        // Limit number of active toasts
        if (activeToasts.size >= MAX_TOASTS) {
            const oldestToast = activeToasts.keys().next().value;
            hideToast(oldestToast);
        }

        // Create and show toast
        const toastElement = createToastElement(message, type, duration, title);
        const bsToast = new bootstrap.Toast(toastElement, {
            autohide: duration > 0,
            delay: duration
        });

        // Store reference
        activeToasts.set(toastElement.id, {
            element: toastElement,
            bsToast: bsToast,
            type: type
        });

        // Show toast with animation
        toastElement.style.opacity = '0';
        bsToast.show();
        
        // Fade in animation
        setTimeout(() => {
            toastElement.style.transition = 'opacity 0.3s ease-in-out';
            toastElement.style.opacity = '1';
        }, 50);

        // Clean up when toast is hidden
        toastElement.addEventListener('hidden.bs.toast', () => {
            activeToasts.delete(toastElement.id);
            toastElement.remove();
        });

        // Add click-to-dismiss functionality
        toastElement.addEventListener('click', (e) => {
            if (!e.target.closest('.btn-close')) {
                bsToast.hide();
            }
        });

        return toastElement.id;
    }

    // Hide specific toast
    function hideToast(toastId) {
        const toastData = activeToasts.get(toastId);
        if (toastData) {
            toastData.bsToast.hide();
        }
    }

    // Hide all toasts
    function hideAllToasts() {
        activeToasts.forEach((toastData) => {
            toastData.bsToast.hide();
        });
    }

    // Convenience methods for different toast types
    function showSuccess(message, duration = DEFAULT_DURATION, title = 'Success') {
        return showToast(message, 'success', duration, title);
    }

    function showError(message, duration = 8000, title = 'Error') {
        return showToast(message, 'error', duration, title);
    }

    function showWarning(message, duration = 6000, title = 'Warning') {
        return showToast(message, 'warning', duration, title);
    }

    function showInfo(message, duration = DEFAULT_DURATION, title = 'Info') {
        return showToast(message, 'info', duration, title);
    }

    // Show toast with progress bar
    function showProgressToast(message, type = 'info', title = 'Progress') {
        const toastId = showToast(message, type, 0, title); // Don't auto-hide
        const toastElement = document.getElementById(toastId);
        
        // Add progress bar
        const progressHtml = `
            <div class="progress mt-2" style="height: 4px;">
                <div class="progress-bar" role="progressbar" style="width: 0%"></div>
            </div>
        `;
        
        const toastBody = toastElement.querySelector('.toast-body');
        toastBody.insertAdjacentHTML('beforeend', progressHtml);
        
        const progressBar = toastBody.querySelector('.progress-bar');
        
        return {
            id: toastId,
            updateProgress: (percent) => {
                progressBar.style.width = `${Math.max(0, Math.min(100, percent))}%`;
            },
            updateMessage: (newMessage) => {
                const messageElement = toastBody.firstChild;
                if (messageElement.nodeType === Node.TEXT_NODE) {
                    messageElement.textContent = newMessage;
                }
            },
            complete: () => {
                progressBar.style.width = '100%';
                setTimeout(() => hideToast(toastId), 1000);
            },
            hide: () => hideToast(toastId)
        };
    }

    // Show toast for form validation errors
    function showFormErrors(errors) {
        if (Array.isArray(errors)) {
            errors.forEach((error, index) => {
                setTimeout(() => {
                    showError(error, 6000);
                }, index * 200); // Stagger the display
            });
        } else if (typeof errors === 'string') {
            showError(errors);
        } else if (typeof errors === 'object') {
            Object.entries(errors).forEach(([field, error], index) => {
                setTimeout(() => {
                    showError(`${field}: ${error}`, 6000);
                }, index * 200);
            });
        }
    }

    // Show toast for file upload status
    function showFileUploadToast(fileName, status = 'uploading') {
        const messages = {
            uploading: `Uploading ${fileName}...`,
            success: `${fileName} uploaded successfully`,
            error: `Failed to upload ${fileName}`
        };
        
        const types = {
            uploading: 'info',
            success: 'success',
            error: 'error'
        };
        
        return showToast(messages[status], types[status]);
    }

    // Utility functions
    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, (m) => map[m]);
    }

    function getTimeString() {
        return new Date().toLocaleTimeString('en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    // Auto-show toasts for flash messages
    function handleFlashMessages() {
        const flashMessages = document.querySelectorAll('.alert[data-toast]');
        
        flashMessages.forEach((alert) => {
            const message = alert.textContent.trim();
            const type = alert.classList.contains('alert-success') ? 'success' :
                        alert.classList.contains('alert-danger') ? 'error' :
                        alert.classList.contains('alert-warning') ? 'warning' : 'info';
            
            showToast(message, type);
            alert.remove(); // Remove the original alert
        });
    }

    // Keyboard shortcuts
    function handleKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + Shift + H to hide all toasts
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'H') {
                e.preventDefault();
                hideAllToasts();
            }
            
            // ESC to hide the newest toast
            if (e.key === 'Escape' && activeToasts.size > 0) {
                const newestToastId = Array.from(activeToasts.keys()).pop();
                hideToast(newestToastId);
            }
        });
    }

    // Initialize when DOM is loaded
    function init() {
        initToasts();
        handleFlashMessages();
        handleKeyboardShortcuts();
        
        // Listen for custom toast events
        document.addEventListener('showToast', (e) => {
            const { message, type, duration, title } = e.detail;
            showToast(message, type, duration, title);
        });
    }

    // Initialize
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Export functions for global use
    window.showToast = showToast;
    window.showSuccess = showSuccess;
    window.showError = showError;
    window.showWarning = showWarning;
    window.showInfo = showInfo;
    window.showProgressToast = showProgressToast;
    window.showFormErrors = showFormErrors;
    window.showFileUploadToast = showFileUploadToast;
    window.hideToast = hideToast;
    window.hideAllToasts = hideAllToasts;

})();