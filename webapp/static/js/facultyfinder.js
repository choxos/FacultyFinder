/**
 * FacultyFinder JavaScript
 * Optimized for performance with caching, debouncing, and efficient DOM operations
 */

const FacultyFinder = {
    // Configuration
    config: {
        CACHE_DURATION: 5 * 60 * 1000, // 5 minutes
        DEBOUNCE_DELAY: 300,
        REQUEST_TIMEOUT: 10000
    },

    // Performance optimizations
    cache: new Map(),
    requestController: null,
    performanceMonitor: {
        requests: [],
        logRequest: function(url, duration) {
            this.requests.push({
                url,
                duration,
                timestamp: Date.now()
            });
            
            // Keep only last 50 requests
            if (this.requests.length > 50) {
                this.requests = this.requests.slice(-50);
            }
            
            // Log slow requests
            if (duration > 1000) {
                console.warn(`Slow request: ${url} took ${duration}ms`);
            }
        }
    },

    // Utility functions
    utils: {
        // Debounce function for search inputs
        debounce: function(func, delay) {
            let timeoutId;
            return function(...args) {
                clearTimeout(timeoutId);
                timeoutId = setTimeout(() => func.apply(this, args), delay);
            };
        },

        // Throttle function for scroll events
        throttle: function(func, delay) {
            let inThrottle;
            return function(...args) {
                if (!inThrottle) {
                    func.apply(this, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, delay);
                }
            };
        },

        // Generate cache key from URL and params
        generateCacheKey: function(url, params = {}) {
            const paramString = Object.keys(params)
                .sort()
                .map(key => `${key}=${params[key]}`)
                .join('&');
            return `${url}?${paramString}`;
        },

        // Check if cache entry is valid
        isCacheValid: function(entry) {
            return entry && (Date.now() - entry.timestamp) < FacultyFinder.config.CACHE_DURATION;
        },

        // Efficient DOM element creation
        createElement: function(tag, attributes = {}, content = '') {
            const element = document.createElement(tag);
            
            Object.entries(attributes).forEach(([key, value]) => {
                if (key === 'className') {
                    element.className = value;
                } else if (key === 'innerHTML') {
                    element.innerHTML = value;
                } else {
                    element.setAttribute(key, value);
                }
            });
            
            if (content && typeof content === 'string') {
                element.textContent = content;
            }
            
            return element;
        },

        // Batch DOM updates using DocumentFragment
        batchDOMUpdates: function(container, elements) {
            const fragment = document.createDocumentFragment();
            elements.forEach(element => fragment.appendChild(element));
            container.appendChild(fragment);
        }
    },

    // API functions
    api: {
        // Generic fetch with error handling and caching
        fetch: async function(url, options = {}) {
            const cacheKey = FacultyFinder.utils.generateCacheKey(url, options.params || {});
            
            // Check cache first
            const cachedResult = FacultyFinder.cache.get(cacheKey);
            if (FacultyFinder.utils.isCacheValid(cachedResult)) {
                return cachedResult.data;
            }
            
            // Cancel previous request if still pending
            if (FacultyFinder.requestController) {
                FacultyFinder.requestController.abort();
            }
            
            FacultyFinder.requestController = new AbortController();
            
            const startTime = Date.now();
            
            try {
                const response = await fetch(url, {
                    ...options,
                    signal: FacultyFinder.requestController.signal,
                    timeout: FacultyFinder.config.REQUEST_TIMEOUT
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                const duration = Date.now() - startTime;
                
                // Log performance
                FacultyFinder.performanceMonitor.logRequest(url, duration);
                
                // Cache result
                FacultyFinder.cache.set(cacheKey, {
                    data,
                    timestamp: Date.now()
                });
                
                return data;
                
            } catch (error) {
                if (error.name !== 'AbortError') {
                    console.error('API request failed:', error);
                    throw error;
                }
            }
        }
    },

    // UI helper functions
    ui: {
        // Show loading spinner
        showLoading: function(container) {
            if (typeof container === 'string') {
                container = document.getElementById(container);
            }
            
            if (container) {
                container.innerHTML = `
                    <div class="d-flex justify-content-center align-items-center p-4">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <span class="ms-3">Loading...</span>
                    </div>
                `;
            }
        },

        // Show error message
        showError: function(container, message) {
            if (typeof container === 'string') {
                container = document.getElementById(container);
            }
            
            if (container) {
                container.innerHTML = `
                    <div class="alert alert-danger d-flex align-items-center" role="alert">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        <div>${message}</div>
                    </div>
                `;
            }
        },

        // Create notification
        createNotification: function(message, type = 'info', duration = 5000) {
            const notification = FacultyFinder.utils.createElement('div', {
                className: `alert alert-${type} alert-dismissible fade show position-fixed`,
                style: 'top: 20px; right: 20px; z-index: 1060; min-width: 300px;'
            });
            
            notification.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            document.body.appendChild(notification);
            
            // Auto-remove after duration
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, duration);
            
            return notification;
        }
    },

    // Theme management
    theme: {
        init: function() {
            const savedTheme = localStorage.getItem('ff-theme') || 'light';
            this.setTheme(savedTheme);
            this.createToggleButton();
        },

        setTheme: function(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem('ff-theme', theme);
            
            // Update toggle button icon if exists
            this.updateToggleIcon(theme);
        },

        updateToggleIcon: function(theme) {
            const toggleBtn = document.getElementById('theme-toggle');
            if (toggleBtn) {
                const icon = toggleBtn.querySelector('i');
                if (icon) {
                    // Clear all existing Font Awesome classes
                    icon.className = '';
                    // Add the correct icon based on current theme
                    // Show moon when in light theme (to switch to dark)
                    // Show sun when in dark theme (to switch to light)
                    if (theme === 'dark') {
                        icon.className = 'fas fa-sun';
                        toggleBtn.title = 'Switch to light theme';
                        toggleBtn.setAttribute('aria-label', 'Switch to light theme');
                    } else {
                        icon.className = 'fas fa-moon';
                        toggleBtn.title = 'Switch to dark theme';
                        toggleBtn.setAttribute('aria-label', 'Switch to dark theme');
                    }
                }
            }
        },

        toggle: function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            this.setTheme(newTheme);
        },

        createToggleButton: function() {
            // Remove existing button if it exists
            const existingButton = document.getElementById('theme-toggle');
            if (existingButton) {
                existingButton.remove();
            }

            const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
            
            // Create button element with improved styling
            const button = FacultyFinder.utils.createElement('button', {
                id: 'theme-toggle',
                className: 'btn btn-outline-secondary position-fixed',
                style: 'bottom: 20px; right: 20px; z-index: 1050; border-radius: 50%; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); transition: all 0.3s ease;'
            });
            
            // Create icon element with proper initial icon
            const icon = document.createElement('i');
            // Show moon when in light theme (to switch to dark)
            // Show sun when in dark theme (to switch to light)
            if (currentTheme === 'dark') {
                icon.className = 'fas fa-sun';
                button.title = 'Switch to light theme';
                button.setAttribute('aria-label', 'Switch to light theme');
            } else {
                icon.className = 'fas fa-moon';
                button.title = 'Switch to dark theme';
                button.setAttribute('aria-label', 'Switch to dark theme');
            }
            
            button.appendChild(icon);
            
            // Add click event listener
            button.addEventListener('click', () => {
                this.toggle();
                // Add a small animation effect
                button.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    button.style.transform = 'scale(1)';
                }, 150);
            });
            
            // Add hover effects
            button.addEventListener('mouseenter', () => {
                button.style.transform = 'scale(1.1)';
            });
            
            button.addEventListener('mouseleave', () => {
                button.style.transform = 'scale(1)';
            });
            
            document.body.appendChild(button);
            
            // Ensure the icon is correct for the current theme
            this.updateToggleIcon(currentTheme);
        }
    },

    // Search functionality with debouncing
    search: {
        init: function() {
            const searchInputs = document.querySelectorAll('input[type="search"], input[name="search"]');
            searchInputs.forEach(input => {
                input.addEventListener('input', 
                    FacultyFinder.utils.debounce(this.handleSearch.bind(this), 
                    FacultyFinder.config.DEBOUNCE_DELAY)
                );
            });
        },

        handleSearch: function(event) {
            const query = event.target.value.trim();
            const searchType = event.target.getAttribute('data-search-type') || 'general';
            
            if (query.length >= 2) {
                this.performSearch(query, searchType);
            } else if (query.length === 0) {
                this.clearSearchResults();
            }
        },

        performSearch: function(query, type) {
            // Implementation would depend on the specific search requirements
            console.log(`Performing ${type} search for: ${query}`);
        },

        clearSearchResults: function() {
            // Clear any search result displays
            const resultsContainers = document.querySelectorAll('.search-results');
            resultsContainers.forEach(container => {
                container.innerHTML = '';
                container.style.display = 'none';
            });
        }
    },

    // Table sorting functionality
    table: {
        init: function() {
            const sortableHeaders = document.querySelectorAll('th.sortable');
            sortableHeaders.forEach(header => {
                header.style.cursor = 'pointer';
                header.addEventListener('click', this.handleSort.bind(this));
            });
        },

        handleSort: function(event) {
            const header = event.currentTarget;
            const table = header.closest('table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const columnIndex = Array.from(header.parentNode.children).indexOf(header);
            const sortDirection = header.getAttribute('data-sort-direction') === 'asc' ? 'desc' : 'asc';
            
            // Clear all sort indicators
            table.querySelectorAll('th.sortable').forEach(th => {
                th.removeAttribute('data-sort-direction');
                const icon = th.querySelector('.fas');
                if (icon) {
                    icon.className = 'fas fa-sort ms-1';
                }
            });
            
            // Set current sort direction
            header.setAttribute('data-sort-direction', sortDirection);
            const icon = header.querySelector('.fas');
            if (icon) {
                icon.className = `fas fa-sort-${sortDirection === 'asc' ? 'up' : 'down'} ms-1`;
            }
            
            // Sort rows
            rows.sort((a, b) => {
                const aText = a.children[columnIndex].textContent.trim();
                const bText = b.children[columnIndex].textContent.trim();
                
                // Try to parse as numbers first
                const aNum = parseFloat(aText);
                const bNum = parseFloat(bText);
                
                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return sortDirection === 'asc' ? aNum - bNum : bNum - aNum;
                } else {
                    return sortDirection === 'asc' 
                        ? aText.localeCompare(bText)
                        : bText.localeCompare(aText);
                }
            });
            
            // Reappend sorted rows
            rows.forEach(row => tbody.appendChild(row));
        }
    },

    // Filter functionality
    filters: {
        init: function() {
            const filterSelects = document.querySelectorAll('select[data-filter]');
            filterSelects.forEach(select => {
                select.addEventListener('change', this.handleFilterChange.bind(this));
            });
        },

        handleFilterChange: function(event) {
            const select = event.target;
            const filterType = select.getAttribute('data-filter');
            const value = select.value;
            
            this.applyFilter(filterType, value);
        },

        applyFilter: function(type, value) {
            // Implementation would depend on the specific filtering requirements
            console.log(`Applying ${type} filter with value: ${value}`);
        }
    },

    // Initialize all modules
    init: function() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initModules());
        } else {
            this.initModules();
        }
    },

    initModules: function() {
        console.log('🚀 FacultyFinder JavaScript initialized');
        
        // Initialize all modules
        this.theme.init();
        this.search.init();
        this.table.init();
        this.filters.init();
        
        // Performance monitoring
        if (window.performance && window.performance.mark) {
            window.performance.mark('facultyfinder-js-loaded');
        }
        
        console.log('✅ All FacultyFinder modules loaded');
    }
};

// Auto-initialize
FacultyFinder.init(); 