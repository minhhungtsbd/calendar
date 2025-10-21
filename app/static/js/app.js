// Main JavaScript for Calendar Application

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize dark mode
    initializeDarkMode();

    // Initialize HTMX event listeners
    initializeHTMX();

    // Initialize keyboard shortcuts
    initializeKeyboardShortcuts();

    // Initialize tooltips
    initializeTooltips();

    // Initialize navigation highlighting
    initializeNavigation();

    console.log('Calendar application initialized');
}

function initializeDarkMode() {
    const themeToggle = document.getElementById('theme-toggle');
    const darkIcon = document.getElementById('theme-toggle-dark-icon');
    const lightIcon = document.getElementById('theme-toggle-light-icon');

    if (!themeToggle || !darkIcon || !lightIcon) return;

    // Check for saved theme preference or default to 'light'
    const savedTheme = localStorage.getItem('theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = savedTheme || (systemPrefersDark ? 'dark' : 'light');

    // Apply theme and set correct icons
    if (theme === 'dark') {
        document.documentElement.classList.add('dark');
        darkIcon.classList.add('hidden');      // Hide moon icon (show when in light mode)
        lightIcon.classList.remove('hidden'); // Show sun icon (show when in dark mode)
    } else {
        document.documentElement.classList.remove('dark');
        darkIcon.classList.remove('hidden');  // Show moon icon (show when in light mode)
        lightIcon.classList.add('hidden');    // Hide sun icon (hide when in light mode)
    }

    // Toggle function
    themeToggle.addEventListener('click', function() {
        const isDark = document.documentElement.classList.contains('dark');

        if (isDark) {
            // Switch to light mode
            document.documentElement.classList.remove('dark');
            localStorage.setItem('theme', 'light');
            darkIcon.classList.remove('hidden');  // Show moon icon
            lightIcon.classList.add('hidden');    // Hide sun icon
        } else {
            // Switch to dark mode
            document.documentElement.classList.add('dark');
            localStorage.setItem('theme', 'dark');
            darkIcon.classList.add('hidden');     // Hide moon icon
            lightIcon.classList.remove('hidden'); // Show sun icon
        }
    });
}

function initializeHTMX() {
    // HTMX configuration
    document.body.addEventListener('htmx:configRequest', function(evt) {
        evt.detail.headers['X-Requested-With'] = 'XMLHttpRequest';
    });

    // Show loading indicator
    document.body.addEventListener('htmx:beforeRequest', function(evt) {
        const indicator = document.getElementById('loading-indicator');
        if (indicator) {
            indicator.style.display = 'block';
        }
    });

    // Hide loading indicator
    document.body.addEventListener('htmx:afterRequest', function(evt) {
        const indicator = document.getElementById('loading-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    });

    // Handle form submission success
    document.body.addEventListener('htmx:afterSwap', function(evt) {
        // Re-initialize tooltips for new content
        initializeTooltips();
        
        // Add animation to new content
        if (evt.detail.target) {
            evt.detail.target.classList.add('form-slide-in');
        }
    });

    // Handle errors
    document.body.addEventListener('htmx:responseError', function(evt) {
        showNotification('Có lỗi xảy ra. Vui lòng thử lại.', 'error');
    });

    // Handle network errors
    document.body.addEventListener('htmx:sendError', function(evt) {
        showNotification('Không thể kết nối đến máy chủ.', 'error');
    });
}

function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + N: New note
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            const newNoteButton = document.querySelector('[hx-get="/notes/new"]');
            if (newNoteButton) {
                newNoteButton.click();
            }
        }
        
        // Escape: Close forms/modals
        if (e.key === 'Escape') {
            const formContainer = document.getElementById('note-form-container');
            if (formContainer && formContainer.innerHTML.trim()) {
                formContainer.innerHTML = '';
            }
        }
        
        // Ctrl/Cmd + /: Focus search (if implemented)
        if ((e.ctrlKey || e.metaKey) && e.key === '/') {
            e.preventDefault();
            const searchInput = document.querySelector('input[type="search"]');
            if (searchInput) {
                searchInput.focus();
            }
        }
    });
}

function initializeTooltips() {
    // Simple tooltip implementation for data-tooltip attributes
    const tooltipElements = document.querySelectorAll('[data-tooltip]');

    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            showTooltip(this, this.getAttribute('data-tooltip'));
        });

        element.addEventListener('mouseleave', function() {
            hideTooltip();
        });
    });
}

function showTooltip(element, text) {
    // Remove existing tooltip
    hideTooltip();
    
    const tooltip = document.createElement('div');
    tooltip.id = 'custom-tooltip';
    tooltip.className = 'absolute z-50 px-2 py-1 text-sm text-white bg-gray-900 rounded shadow-lg pointer-events-none';
    tooltip.textContent = text;
    
    document.body.appendChild(tooltip);
    
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
}

function hideTooltip() {
    const tooltip = document.getElementById('custom-tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-50 px-4 py-3 rounded-md shadow-lg text-white max-w-sm ${
        type === 'error' ? 'bg-red-500' : 
        type === 'success' ? 'bg-green-500' : 
        'bg-blue-500'
    }`;
    
    notification.innerHTML = `
        <div class="flex items-center">
            <span class="flex-1">${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-2 text-white hover:text-gray-200">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Utility functions
function formatDate(date) {
    return new Date(date).toLocaleDateString('vi-VN');
}

function formatDateTime(datetime) {
    return new Date(datetime).toLocaleString('vi-VN');
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function initializeNavigation() {
    // Highlight active navigation based on current path
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');

    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath || (currentPath === '/' && href === '/')) {
            link.classList.add('active');
        }
    });
}

// Export functions for global use
window.CalendarApp = {
    showNotification,
    formatDate,
    formatDateTime,
    debounce
};
