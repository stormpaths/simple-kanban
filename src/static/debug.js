/**
 * Debug utility for controlling console logging.
 * 
 * Usage:
 * - Debug.log('message') - logs only when debug is enabled
 * - Debug.warn('message') - logs warnings only when debug is enabled
 * - Debug.error('message') - always logs errors
 * - Debug.enable() - enable debug logging
 * - Debug.disable() - disable debug logging
 */
class DebugLogger {
    constructor() {
        // Check for debug flag in localStorage or URL params
        const urlParams = new URLSearchParams(window.location.search);
        const debugFromUrl = urlParams.get('debug') === 'true';
        const debugFromStorage = localStorage.getItem('debug') === 'true';
        
        this.enabled = debugFromUrl || debugFromStorage || false;
        
        // Save debug state to localStorage if set via URL
        if (debugFromUrl) {
            localStorage.setItem('debug', 'true');
        }
    }

    enable() {
        this.enabled = true;
        localStorage.setItem('debug', 'true');
        console.log('Debug logging enabled');
    }

    disable() {
        this.enabled = false;
        localStorage.setItem('debug', 'false');
        console.log('Debug logging disabled');
    }

    log(...args) {
        if (this.enabled) {
            console.log(...args);
        }
    }

    warn(...args) {
        if (this.enabled) {
            console.warn(...args);
        }
    }

    error(...args) {
        // Always log errors regardless of debug state
        console.error(...args);
    }

    info(...args) {
        if (this.enabled) {
            console.info(...args);
        }
    }

    group(label) {
        if (this.enabled) {
            console.group(label);
        }
    }

    groupEnd() {
        if (this.enabled) {
            console.groupEnd();
        }
    }
}

// Create global debug instance
window.Debug = new DebugLogger();
