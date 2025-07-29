/**
 * Loading Spinner Management
 */

(function() {
    'use strict';

    // Configuration
    const SPINNER_ID = 'loading-overlay';
    const MIN_SHOW_TIME = 500; // Minimum time to show spinner (prevents flashing)
    
    let spinnerElement = null;
    let showStartTime = null;
    let spinnerTimeout = null;

    // Initialize spinner
    function initSpinner() {
        spinnerElement = document.getElementById(SPINNER_ID);
        
        if (!spinnerElement) {
            createSpinnerElement();
        }
    }

    // Create spinner element if it doesn't exist
    function createSpinnerElement() {
        const spinnerHtml = `
            <div id="${SPINNER_ID}" class="loading-overlay d-none">
                <div class="spinner-container">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-3 text-center" id="spinner-message">Processing your request...</p>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', spinnerHtml);
        spinnerElement = document.getElementById(SPINNER_ID);
    }

    // Show spinner
    function showSpinner(message = 'Processing your request...') {
        if (!spinnerElement) {
            initSpinner();
        }

        // Update message
        const messageElement = spinnerElement.querySelector('#spinner-message');
        if (messageElement) {
            messageElement.textContent = message;
        }

        // Show spinner
        spinnerElement.classList.remove('d-none');
        document.body.style.overflow = 'hidden'; // Prevent scrolling
        showStartTime = Date.now();

        // Add keyboard event listener to prevent interactions
        document.addEventListener('keydown', preventInteraction, true);
        document.addEventListener('click', preventInteraction, true);
    }

    // Hide spinner
    function hideSpinner() {
        if (!spinnerElement || spinnerElement.classList.contains('d-none')) {
            return;
        }

        const elapsed = Date.now() - (showStartTime || 0);
        const remainingTime = Math.max(0, MIN_SHOW_TIME - elapsed);

        // Clear any existing timeout
        if (spinnerTimeout) {
            clearTimeout(spinnerTimeout);
        }

        // Hide after minimum show time
        spinnerTimeout = setTimeout(() => {
            spinnerElement.classList.add('d-none');
            document.body.style.overflow = ''; // Restore scrolling
            
            // Remove event listeners
            document.removeEventListener('keydown', preventInteraction, true);
            document.removeEventListener('click', preventInteraction, true);
            
            showStartTime = null;
        }, remainingTime);
    }

    // Prevent user interactions while spinner is showing
    function preventInteraction(event) {
        if (!spinnerElement || spinnerElement.classList.contains('d-none')) {
            return;
        }

        // Allow ESC key to hide spinner
        if (event.type === 'keydown' && event.key === 'Escape') {
            hideSpinner();
            return;
        }

        event.preventDefault();
        event.stopPropagation();
        return false;
    }

    // Show spinner for form submissions
    function handleFormSubmission(form, message = 'Processing your request...') {
        if (!form) return;

        form.addEventListener('submit', function(event) {
            // Only show spinner if form is valid
            if (form.checkValidity()) {
                showSpinner(message);
            }
        });
    }

    // Show spinner for AJAX requests
    function wrapAjaxWithSpinner(ajaxFunction, message = 'Loading...') {
        return function(...args) {
            showSpinner(message);
            
            const result = ajaxFunction.apply(this, args);
            
            // Handle promises
            if (result && typeof result.then === 'function') {
                result
                    .finally(() => hideSpinner())
                    .catch(() => hideSpinner());
            } else {
                // For non-promise results, hide after a short delay
                setTimeout(hideSpinner, 100);
            }
            
            return result;
        };
    }

    // Auto-attach spinner to forms with data-spinner attribute
    function autoAttachToForms() {
        const forms = document.querySelectorAll('form[data-spinner]');
        
        forms.forEach(form => {
            const message = form.getAttribute('data-spinner') || 'Processing your request...';
            handleFormSubmission(form, message);
        });
    }

    // Auto-attach spinner to links with data-spinner attribute
    function autoAttachToLinks() {
        const links = document.querySelectorAll('a[data-spinner]');
        
        links.forEach(link => {
            const message = link.getAttribute('data-spinner') || 'Loading...';
            
            link.addEventListener('click', function(event) {
                // Don't show spinner for external links or anchors
                if (this.hostname !== window.location.hostname || 
                    this.getAttribute('href').startsWith('#')) {
                    return;
                }
                
                showSpinner(message);
            });
        });
    }

    // File upload progress spinner
    function showFileUploadSpinner(files) {
        const fileCount = files.length;
        const totalSize = Array.from(files).reduce((total, file) => total + file.size, 0);
        const totalSizeMB = (totalSize / (1024 * 1024)).toFixed(1);
        
        let message = `Uploading ${fileCount} file${fileCount > 1 ? 's' : ''}`;
        if (totalSizeMB > 0) {
            message += ` (${totalSizeMB} MB)`;
        }
        
        showSpinner(message);
    }

    // Show analysis progress spinner with dynamic messages
    function showAnalysisSpinner(step = 1, totalSteps = 3) {
        const steps = [
            'Extracting text from resume...',
            'Analyzing skills and experience...',
            'Calculating match scores...',
            'Finalizing results...'
        ];
        
        const message = steps[Math.min(step - 1, steps.length - 1)];
        showSpinner(message);
        
        // Auto-advance steps for demo effect
        if (step < totalSteps) {
            setTimeout(() => showAnalysisSpinner(step + 1, totalSteps), 1500);
        }
    }

    // Initialize when DOM is loaded
    function init() {
        initSpinner();
        autoAttachToForms();
        autoAttachToLinks();
        
        // Handle page navigation
        window.addEventListener('beforeunload', hideSpinner);
        
        // Handle browser back/forward buttons
        window.addEventListener('pageshow', hideSpinner);
        window.addEventListener('pagehide', hideSpinner);
    }

    // Initialize
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Export functions for global use
    window.showSpinner = showSpinner;
    window.hideSpinner = hideSpinner;
    window.showFileUploadSpinner = showFileUploadSpinner;
    window.showAnalysisSpinner = showAnalysisSpinner;
    window.wrapAjaxWithSpinner = wrapAjaxWithSpinner;

})();