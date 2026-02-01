/**
 * Theme Management for Simple Kanban Board
 * Handles dark/light mode toggle and persistence
 */

class ThemeManager {
    constructor() {
        this.currentTheme = localStorage.getItem('theme') || 'light';
        this.themeToggle = document.getElementById('theme-toggle');
        this.authThemeToggle = document.getElementById('auth-theme-toggle');
        
        this.init();
    }

    init() {
        // Apply saved theme
        this.applyTheme(this.currentTheme);
        
        // Bind toggle events
        if (this.themeToggle) {
            this.themeToggle.addEventListener('click', () => this.toggleTheme());
        }
        if (this.authThemeToggle) {
            this.authThemeToggle.addEventListener('click', () => this.toggleTheme());
        }
    }

    getStoredTheme() {
        return localStorage.getItem('theme');
    }

    storeTheme(theme) {
        localStorage.setItem('theme', theme);
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.currentTheme = theme;
        this.storeTheme(theme);
        this.updateToggleIcon();
    }

    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme);
    }

    updateToggleIcon() {
        const icon = this.themeToggle?.querySelector('i');
        const authIcon = this.authThemeToggle?.querySelector('i');
        
        const iconClass = this.currentTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        
        if (icon) {
            icon.className = iconClass;
        }
        if (authIcon) {
            authIcon.className = iconClass;
        }
    }

    getCurrentTheme() {
        return this.currentTheme;
    }
}

// Initialize theme manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
});
