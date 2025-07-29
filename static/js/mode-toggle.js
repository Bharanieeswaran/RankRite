/**
 * Dark/Light Theme Toggle Functionality
 */

(function() {
    'use strict';

    // Theme configuration
    const THEME_KEY = 'rankrite-theme';
    const THEMES = {
        LIGHT: 'light',
        DARK: 'dark'
    };

    // DOM elements
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    const htmlElement = document.documentElement;

    // Initialize theme
    function initTheme() {
        const savedTheme = localStorage.getItem(THEME_KEY);
        const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? THEMES.DARK : THEMES.LIGHT;
        const currentTheme = savedTheme || systemTheme;
        
        setTheme(currentTheme);
    }

    // Set theme
    function setTheme(theme) {
        htmlElement.setAttribute('data-theme', theme);
        updateIcon(theme);
        localStorage.setItem(THEME_KEY, theme);
        
        // Dispatch custom event for other components
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme } }));
    }

    // Update theme icon
    function updateIcon(theme) {
        if (!themeIcon) return;
        
        themeIcon.className = theme === THEMES.DARK 
            ? 'bi bi-moon-fill' 
            : 'bi bi-sun-fill';
        
        // Update tooltip
        const tooltip = bootstrap.Tooltip.getInstance(themeToggle);
        if (tooltip) {
            const newTitle = theme === THEMES.DARK ? 'Switch to light mode' : 'Switch to dark mode';
            themeToggle.setAttribute('title', newTitle);
            tooltip.setContent({ '.tooltip-inner': newTitle });
        }
    }

    // Toggle theme
    function toggleTheme() {
        const currentTheme = htmlElement.getAttribute('data-theme');
        const newTheme = currentTheme === THEMES.DARK ? THEMES.LIGHT : THEMES.DARK;
        
        // Add transition class for smooth animation
        htmlElement.classList.add('theme-transitioning');
        
        setTheme(newTheme);
        
        // Remove transition class after animation
        setTimeout(() => {
            htmlElement.classList.remove('theme-transitioning');
        }, 300);
        
        // Show feedback toast
        if (window.showToast) {
            const message = `Switched to ${newTheme} mode`;
            window.showToast(message, 'info', 2000);
        }
    }

    // Event listeners
    function attachEventListeners() {
        if (themeToggle) {
            themeToggle.addEventListener('click', toggleTheme);
            
            // Initialize tooltip
            new bootstrap.Tooltip(themeToggle, {
                title: htmlElement.getAttribute('data-theme') === THEMES.DARK 
                    ? 'Switch to light mode' 
                    : 'Switch to dark mode'
            });
        }

        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            // Only auto-switch if user hasn't manually set a preference
            if (!localStorage.getItem(THEME_KEY)) {
                setTheme(e.matches ? THEMES.DARK : THEMES.LIGHT);
            }
        });

        // Keyboard shortcut (Ctrl/Cmd + Shift + D)
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'D') {
                e.preventDefault();
                toggleTheme();
            }
        });
    }

    // CSS transition class for smooth theme switching
    function addThemeTransitionCSS() {
        const style = document.createElement('style');
        style.textContent = `
            .theme-transitioning * {
                transition: background-color 0.3s ease, 
                           color 0.3s ease, 
                           border-color 0.3s ease !important;
            }
        `;
        document.head.appendChild(style);
    }

    // Initialize when DOM is loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            addThemeTransitionCSS();
            initTheme();
            attachEventListeners();
        });
    } else {
        addThemeTransitionCSS();
        initTheme();
        attachEventListeners();
    }

    // Export functions for external use
    window.themeManager = {
        setTheme,
        toggleTheme,
        getCurrentTheme: () => htmlElement.getAttribute('data-theme'),
        THEMES
    };

})();