// Loading spinner management
class LoadingSpinner {
    constructor() {
        this.activeSpinners = new Set();
        this.createSpinnerElements();
    }

    createSpinnerElements() {
        // Create global spinner overlay
        if (!document.getElementById('global-spinner')) {
            const spinnerOverlay = document.createElement('div');
            spinnerOverlay.id = 'global-spinner';
            spinnerOverlay.className = 'spinner-overlay hidden';
            spinnerOverlay.innerHTML = `
                <div class="spinner-container">
                    <div class="spinner"></div>
                    <div class="spinner-text">Loading...</div>
                </div>
            `;
            document.body.appendChild(spinnerOverlay);
        }
    }

    show(spinnerId = 'global', message = 'Loading...') {
        this.activeSpinners.add(spinnerId);

        if (spinnerId === 'global') {
            const spinner = document.getElementById('global-spinner');
            const text = spinner.querySelector('.spinner-text');
            if (text) text.textContent = message;
            spinner.classList.remove('hidden');
        } else {
            // Show specific spinner
            const targetSpinner = document.getElementById(spinnerId);
            if (targetSpinner) {
                targetSpinner.classList.remove('hidden');
                targetSpinner.classList.add('active');
            } else {
                // Create inline spinner
                this.createInlineSpinner(spinnerId, message);
            }
        }
    }

    hide(spinnerId = 'global') {
        this.activeSpinners.delete(spinnerId);

        if (spinnerId === 'global') {
            const spinner = document.getElementById('global-spinner');
            spinner.classList.add('hidden');
        } else {
            const targetSpinner = document.getElementById(spinnerId);
            if (targetSpinner) {
                targetSpinner.classList.add('hidden');
                targetSpinner.classList.remove('active');
            }
        }
    }

    createInlineSpinner(spinnerId, message) {
        const spinner = document.createElement('div');
        spinner.id = spinnerId;
        spinner.className = 'inline-spinner active';
        spinner.innerHTML = `
            <div class="mini-spinner"></div>
            <span class="spinner-message">${message}</span>
        `;
        
        // Try to find a container or add to body
        const container = document.querySelector('.spinner-container') || document.body;
        container.appendChild(spinner);
    }

    // Show spinner for form submissions
    showForForm(formElement, message = 'Processing...') {
        const submitButton = formElement.querySelector('button[type="submit"], input[type="submit"]');
        if (submitButton) {
            const originalText = submitButton.textContent || submitButton.value;
            submitButton.disabled = true;
            submitButton.setAttribute('data-original-text', originalText);
            submitButton.innerHTML = `
                <span class="mini-spinner"></span>
                ${message}
            `;
        }
        this.show('form-spinner', message);
    }

    hideForForm(formElement) {
        const submitButton = formElement.querySelector('button[type="submit"], input[type="submit"]');
        if (submitButton) {
            const originalText = submitButton.getAttribute('data-original-text');
            submitButton.disabled = false;
            submitButton.innerHTML = originalText || 'Submit';
            submitButton.removeAttribute('data-original-text');
        }
        this.hide('form-spinner');
    }

    // Show spinner for AJAX requests
    showForAjax(containerId, message = 'Loading...') {
        const container = document.getElementById(containerId);
        if (container) {
            const spinner = document.createElement('div');
            spinner.className = 'ajax-spinner';
            spinner.innerHTML = `
                <div class="spinner"></div>
                <div class="spinner-text">${message}</div>
            `;
            container.appendChild(spinner);
        }
    }

    hideForAjax(containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            const spinner = container.querySelector('.ajax-spinner');
            if (spinner) {
                spinner.remove();
            }
        }
    }

    // Utility method to wrap async operations
    async wrapAsync(asyncFunction, spinnerId = 'global', message = 'Loading...') {
        try {
            this.show(spinnerId, message);
            const result = await asyncFunction();
            return result;
        } finally {
            this.hide(spinnerId);
        }
    }

    // Check if any spinners are active
    isActive() {
        return this.activeSpinners.size > 0;
    }

    // Hide all active spinners
    hideAll() {
        this.activeSpinners.forEach(spinnerId => this.hide(spinnerId));
        this.activeSpinners.clear();
    }
}

// Auto-attach to common form submissions
document.addEventListener('DOMContentLoaded', () => {
    window.loadingSpinner = new LoadingSpinner();
    
    // Auto-handle form submissions
    document.addEventListener('submit', (e) => {
        const form = e.target;
        if (form.classList.contains('auto-spinner') || form.id === 'resume-form') {
            const message = form.getAttribute('data-spinner-message') || 'Processing...';
            window.loadingSpinner.showForForm(form, message);
        }
    });

    // Auto-handle AJAX requests with fetch
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        const showSpinner = args[1]?.showSpinner !== false;
        if (showSpinner) {
            window.loadingSpinner.show('ajax-spinner', 'Loading...');
        }
        
        return originalFetch.apply(this, args)
            .finally(() => {
                if (showSpinner) {
                    window.loadingSpinner.hide('ajax-spinner');
                }
            });
    };
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LoadingSpinner;
}