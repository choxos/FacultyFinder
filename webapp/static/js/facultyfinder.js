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

    // Table sorting functionality
    sorting: {
        currentSort: { column: null, direction: 'asc' },
        
        init: function() {
            // Add click listeners to sortable headers
            document.addEventListener('click', (e) => {
                if (e.target.classList.contains('sortable') || e.target.closest('.sortable')) {
                    e.preventDefault();
                    const header = e.target.classList.contains('sortable') ? e.target : e.target.closest('.sortable');
                    const column = header.getAttribute('data-sort');
                    if (column) {
                        this.sortTable(header, column);
                    }
                }
            });
        },
        
        sortTable: function(header, column) {
            const table = header.closest('table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            // Determine sort direction
            let direction = 'asc';
            if (this.currentSort.column === column && this.currentSort.direction === 'asc') {
                direction = 'desc';
            }
            
            // Update current sort state
            this.currentSort = { column, direction };
            
            // Update header icons
            this.updateSortIcons(table, header, direction);
            
            // Sort rows
            rows.sort((a, b) => {
                const aCell = a.querySelector(`[data-sort-value="${column}"]`) || 
                             a.cells[this.getColumnIndex(table, column)];
                const bCell = b.querySelector(`[data-sort-value="${column}"]`) || 
                             b.cells[this.getColumnIndex(table, column)];
                
                if (!aCell || !bCell) return 0;
                
                let aValue = aCell.getAttribute('data-sort-value') || aCell.textContent.trim();
                let bValue = bCell.getAttribute('data-sort-value') || bCell.textContent.trim();
                
                // Handle numeric values
                if (this.isNumeric(aValue) && this.isNumeric(bValue)) {
                    aValue = parseFloat(aValue) || 0;
                    bValue = parseFloat(bValue) || 0;
                    return direction === 'asc' ? aValue - bValue : bValue - aValue;
                }
                
                // Handle text values
                aValue = aValue.toLowerCase();
                bValue = bValue.toLowerCase();
                
                if (direction === 'asc') {
                    return aValue.localeCompare(bValue);
                } else {
                    return bValue.localeCompare(aValue);
                }
            });
            
            // Re-append sorted rows
            rows.forEach(row => tbody.appendChild(row));
        },
        
        updateSortIcons: function(table, activeHeader, direction) {
            // Reset all sort icons
            table.querySelectorAll('.sortable i').forEach(icon => {
                icon.className = 'fas fa-sort ms-1';
            });
            
            // Update active header icon
            const icon = activeHeader.querySelector('i');
            if (icon) {
                icon.className = direction === 'asc' ? 'fas fa-sort-up ms-1' : 'fas fa-sort-down ms-1';
            }
        },
        
        getColumnIndex: function(table, column) {
            const headers = table.querySelectorAll('th[data-sort]');
            for (let i = 0; i < headers.length; i++) {
                if (headers[i].getAttribute('data-sort') === column) {
                    return i;
                }
            }
            return 0;
        },
        
        isNumeric: function(value) {
            return !isNaN(parseFloat(value)) && isFinite(value);
        }
    },

    // Enhanced theme management with proper icons
    theme: {
        init: function() {
            const savedTheme = localStorage.getItem('ff-theme') || 'light';
            this.setTheme(savedTheme);
            this.createToggleButton();
        },

        setTheme: function(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem('ff-theme', theme);

            // Update toggle button if exists
            this.updateToggleIcon(theme);
        },

        updateToggleIcon: function(theme) {
            const toggleBtn = document.getElementById('theme-toggle');
            if (toggleBtn) {
                const icon = toggleBtn.querySelector('i');
                if (icon) {
                    icon.className = ''; // Clear existing classes
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
            const existingButton = document.getElementById('theme-toggle');
            if (existingButton) {
                existingButton.remove(); // Remove existing button to prevent duplicates
            }

            const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
            const button = FacultyFinder.utils.createElement('button', {
                id: 'theme-toggle',
                className: 'btn btn-outline-secondary position-fixed',
                style: 'bottom: 20px; right: 20px; z-index: 1050; border-radius: 50%; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); transition: all 0.3s ease;'
            });

            const icon = document.createElement('i');
            button.appendChild(icon); // Append icon to button first

            button.addEventListener('click', () => {
                this.toggle();
                button.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    button.style.transform = 'scale(1)';
                }, 150);
            });

            button.addEventListener('mouseenter', () => {
                button.style.transform = 'scale(1.1)';
            });

            button.addEventListener('mouseleave', () => {
                button.style.transform = 'scale(1)';
            });

            document.body.appendChild(button);
            this.updateToggleIcon(currentTheme); // Ensure initial icon is correct
        }
    },

    // Enhanced view toggle with proper icons
    viewToggle: {
        init: function() {
            // Add icons to existing view toggle buttons
            this.updateViewToggleIcons();
        },
        
        updateViewToggleIcons: function() {
            // Update grid view buttons
            document.querySelectorAll('[data-view="grid"]').forEach(btn => {
                if (!btn.querySelector('i')) {
                    const icon = document.createElement('i');
                    icon.className = 'fas fa-th me-1';
                    btn.insertBefore(icon, btn.firstChild);
                }
                if (!btn.title) {
                    btn.title = 'Grid View';
                }
            });
            
            // Update list view buttons
            document.querySelectorAll('[data-view="list"]').forEach(btn => {
                if (!btn.querySelector('i')) {
                    const icon = document.createElement('i');
                    icon.className = 'fas fa-list me-1';
                    btn.insertBefore(icon, btn.firstChild);
                }
                if (!btn.title) {
                    btn.title = 'List View';
                }
            });
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

    // Initialize all FacultyFinder modules
    init: function() {
        console.log('🚀 FacultyFinder JavaScript initialized');
        
        // Initialize theme management
        this.theme.init();
        
        // Initialize table sorting
        this.sorting.init();
        
        // Initialize view toggles
        this.viewToggle.init();
        
        console.log('✅ All FacultyFinder modules loaded');
    }
};

// Auto-initialize
FacultyFinder.init(); 