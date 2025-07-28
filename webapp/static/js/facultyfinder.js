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
        },

        // Show toast notification
        showToast: function(message, type = 'info', duration = 3000) {
            const toastContainer = document.getElementById('toast-container') || 
                this.createToastContainer();
            
            const toast = this.createElement('div', {
                className: `toast toast-${type}`,
                innerHTML: `
                    <div class="toast-content">
                        <i class="fas fa-${this.getToastIcon(type)} me-2"></i>
                        ${message}
                    </div>
                    <button class="toast-close" onclick="this.parentElement.remove()">
                        <i class="fas fa-times"></i>
                    </button>
                `
            });

            toastContainer.appendChild(toast);

            // Auto-remove toast
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.remove();
                }
            }, duration);

            return toast;
        },

        createToastContainer: function() {
            const container = this.createElement('div', {
                id: 'toast-container',
                className: 'toast-container'
            });
            document.body.appendChild(container);
            return container;
        },

        getToastIcon: function(type) {
            const icons = {
                'success': 'check-circle',
                'error': 'exclamation-circle',
                'warning': 'exclamation-triangle',
                'info': 'info-circle'
            };
            return icons[type] || 'info-circle';
        }
    },

    // Network layer with caching
    network: {
        // Fetch with caching and performance monitoring
        fetchWithCache: async function(url, options = {}) {
            const startTime = performance.now();
            const cacheKey = FacultyFinder.utils.generateCacheKey(url, options.params || {});
            
            // Check cache first
            const cachedData = FacultyFinder.cache.get(cacheKey);
            if (FacultyFinder.utils.isCacheValid(cachedData)) {
                const duration = performance.now() - startTime;
                FacultyFinder.performanceMonitor.logRequest(url, duration);
                return cachedData.data;
            }

            // Cancel previous request if exists
            if (FacultyFinder.requestController) {
                FacultyFinder.requestController.abort();
            }

            // Create new AbortController
            FacultyFinder.requestController = new AbortController();

            try {
                const fetchOptions = {
                    signal: FacultyFinder.requestController.signal,
                    headers: {
                        'Content-Type': 'application/json',
                        'Cache-Control': 'no-cache'
                    },
                    ...options
                };

                const response = await fetch(url, fetchOptions);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                
                // Cache the response
                FacultyFinder.cache.set(cacheKey, {
                    data,
                    timestamp: Date.now()
                });

                const duration = performance.now() - startTime;
                FacultyFinder.performanceMonitor.logRequest(url, duration);

                return data;
            } catch (error) {
                if (error.name === 'AbortError') {
                    console.log('Request was cancelled');
                    return null;
                }
                
                console.error('Network error:', error);
                FacultyFinder.utils.showToast(`Network error: ${error.message}`, 'error');
                throw error;
            }
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
            
            // Update toggle button if exists
            const toggleBtn = document.getElementById('theme-toggle');
            if (toggleBtn) {
                const icon = toggleBtn.querySelector('i');
                if (icon) {
                    icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
                }
            }
        },

        toggle: function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            this.setTheme(newTheme);
        },

        createToggleButton: function() {
            if (document.getElementById('theme-toggle')) return;

            const currentTheme = document.documentElement.getAttribute('data-theme');
            const button = FacultyFinder.utils.createElement('button', {
                id: 'theme-toggle',
                className: 'btn btn-outline-secondary position-fixed',
                style: 'bottom: 20px; right: 20px; z-index: 1050; border-radius: 50%; width: 50px; height: 50px;',
                innerHTML: `<i class="fas fa-${currentTheme === 'dark' ? 'sun' : 'moon'}"></i>`,
                title: 'Toggle theme'
            });

            button.addEventListener('click', () => this.toggle());
            document.body.appendChild(button);
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
            const searchType = event.target.dataset.searchType || 'general';

            if (query.length >= 2) {
                this.performSearch(query, searchType);
            }
        },

        performSearch: async function(query, type) {
            try {
                const endpoint = this.getSearchEndpoint(type);
                const results = await FacultyFinder.network.fetchWithCache(
                    endpoint, 
                    { params: { q: query } }
                );

                if (results) {
                    this.displaySearchResults(results, type);
                }
            } catch (error) {
                console.error('Search error:', error);
            }
        },

        getSearchEndpoint: function(type) {
            const endpoints = {
                'faculty': '/api/v1/faculty/search',
                'university': '/api/v1/university/search',
                'general': '/api/v1/search'
            };
            return endpoints[type] || endpoints.general;
        },

        displaySearchResults: function(results, type) {
            // Implementation depends on the page type
            console.log(`Displaying ${results.length} results for ${type}:`, results);
        }
    },

    // Load more functionality
    loadMore: {
        init: function() {
            const loadMoreBtns = document.querySelectorAll('[id^="loadMore"]');
            loadMoreBtns.forEach(btn => {
                btn.addEventListener('click', this.handleLoadMore.bind(this));
            });
        },

        handleLoadMore: async function(event) {
            const button = event.target;
            const originalText = button.innerHTML;
            
            // Show loading state
            button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
            button.disabled = true;

            try {
                const contentType = button.id.replace('loadMore', '').toLowerCase();
                const container = document.getElementById(`${contentType}-grid`) || 
                               document.getElementById(`${contentType}-list`);
                
                if (!container) {
                    throw new Error('Container not found');
                }

                const currentCount = container.children.length;
                const endpoint = `/api/v1/${contentType}/load-more`;
                
                const newItems = await FacultyFinder.network.fetchWithCache(endpoint, {
                    params: { offset: currentCount, limit: 20 }
                });

                if (newItems && newItems.length > 0) {
                    this.appendItems(container, newItems, contentType);
                    FacultyFinder.utils.showToast(`Loaded ${newItems.length} more items`, 'success');
                } else {
                    button.style.display = 'none';
                    FacultyFinder.utils.showToast('No more items to load', 'info');
                }

            } catch (error) {
                console.error('Load more error:', error);
                FacultyFinder.utils.showToast('Error loading more items', 'error');
            } finally {
                // Restore button state
                button.innerHTML = originalText;
                button.disabled = false;
            }
        },

        appendItems: function(container, items, type) {
            const elements = items.map(item => this.createItemElement(item, type));
            FacultyFinder.utils.batchDOMUpdates(container, elements);
        },

        createItemElement: function(item, type) {
            // This would be implemented based on the item type
            // For now, return a placeholder
            return FacultyFinder.utils.createElement('div', {
                className: 'col-lg-4 col-md-6 mb-4',
                innerHTML: `<div class="card"><div class="card-body">${item.name || item.title}</div></div>`
            });
        }
    },

    // Image lazy loading
    lazyLoading: {
        init: function() {
            if ('IntersectionObserver' in window) {
                this.observer = new IntersectionObserver(this.handleIntersect.bind(this), {
                    rootMargin: '50px'
                });

                this.observeImages();
            } else {
                // Fallback for older browsers
                this.loadAllImages();
            }
        },

        observeImages: function() {
            const images = document.querySelectorAll('img[data-src]');
            images.forEach(img => this.observer.observe(img));
        },

        handleIntersect: function(entries) {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    this.observer.unobserve(img);
                }
            });
        },

        loadAllImages: function() {
            const images = document.querySelectorAll('img[data-src]');
            images.forEach(img => {
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
            });
        }
    },

    // Performance monitoring
    performance: {
        init: function() {
            // Monitor page load performance
            window.addEventListener('load', this.logPageLoadTime.bind(this));
            
            // Monitor long tasks
            if ('PerformanceObserver' in window) {
                this.observeLongTasks();
            }
        },

        logPageLoadTime: function() {
            const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
            console.log(`Page load time: ${loadTime}ms`);
            
            if (loadTime > 3000) {
                console.warn('Slow page load detected');
            }
        },

        observeLongTasks: function() {
            try {
                const observer = new PerformanceObserver(list => {
                    list.getEntries().forEach(entry => {
                        if (entry.duration > 50) {
                            console.warn(`Long task detected: ${entry.duration}ms`);
                        }
                    });
                });
                observer.observe({ entryTypes: ['longtask'] });
            } catch (e) {
                // longtask API not supported
            }
        }
    },

    // Initialize all components
    init: function() {
        console.log('Initializing FacultyFinder...');
        
        // Initialize components
        this.theme.init();
        this.search.init();
        this.loadMore.init();
        this.lazyLoading.init();
        this.performance.init();

        console.log('FacultyFinder initialized successfully');
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    FacultyFinder.init();
});

// Export for use in other scripts
window.FacultyFinder = FacultyFinder; 