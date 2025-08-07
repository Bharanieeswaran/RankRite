// Theme toggle functionality
class ThemeToggler {
    constructor() {
        this.init();
    }

    init() {
        // Get stored theme or default to 'dark'
        this.currentTheme = localStorage.getItem('theme') || 'dark';
        this.applyTheme(this.currentTheme);
        this.setupEventListeners();
    }

    setupEventListeners() {
        const toggleBtn = document.getElementById('theme-toggle');
        const themeSelect = document.getElementById('theme-select');
        
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggleTheme());
        }
        
        if (themeSelect) {
            themeSelect.addEventListener('change', (e) => {
                this.setTheme(e.target.value);
            });
        }
    }

    toggleTheme() {
        const themes = ['light', 'dark', 'neon'];
        const currentIndex = themes.indexOf(this.currentTheme);
        const nextIndex = (currentIndex + 1) % themes.length;
        this.setTheme(themes[nextIndex]);
    }

    setTheme(theme) {
        this.currentTheme = theme;
        this.applyTheme(theme);
        localStorage.setItem('theme', theme);
        
        // Update theme selector if exists
        const themeSelect = document.getElementById('theme-select');
        if (themeSelect) {
            themeSelect.value = theme;
        }
        
        // Trigger custom event for other components
        document.dispatchEvent(new CustomEvent('themeChanged', { 
            detail: { theme } 
        }));
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        document.body.className = `theme-${theme}`;
        
        // Update theme toggle button icon/text
        this.updateToggleButton(theme);
    }

    updateToggleButton(theme) {
        const toggleBtn = document.getElementById('theme-toggle');
        if (!toggleBtn) return;
        
        const icons = {
            light: '☀️',
            dark: '🌙',
            neon: '⚡'
        };
        
        const names = {
            light: 'Light',
            dark: 'Dark',
            neon: 'Neon'
        };
        
        toggleBtn.innerHTML = `${icons[theme]} ${names[theme]}`;
        toggleBtn.setAttribute('aria-label', `Switch to ${names[theme]} theme`);
    }

    getCurrentTheme() {
        return this.currentTheme;
    }
}

// Initialize theme toggler when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.themeToggler = new ThemeToggler();
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeToggler;
}