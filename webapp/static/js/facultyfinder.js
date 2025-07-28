/**
 * FacultyFinder JavaScript
 * Main application logic and interactions
 */

// Global application object
const FacultyFinder = {
    init: function() {
        this.initSearchFunctionality();
        this.initNavigationEnhancements();
        this.initCardInteractions();
        this.initTooltips();
    },

    initSearchFunctionality: function() {
        // Enhanced search input behavior
        const searchInputs = document.querySelectorAll('input[type="text"], input[type="search"]');
        
        searchInputs.forEach(input => {
            // Add loading state on form submission
            const form = input.closest('form');
            if (form) {
                form.addEventListener('submit', function() {
                    const submitBtn = form.querySelector('button[type="submit"]');
                    if (submitBtn) {
                        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Searching...';
                        submitBtn.disabled = true;
                    }
                });
            }

            // Auto-submit on enter for search inputs
            input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && form) {
                    form.submit();
                }
            });
        });

        // Search suggestions (placeholder for future implementation)
        this.initSearchSuggestions();
    },

    initSearchSuggestions: function() {
        // TODO: Implement search suggestions
        // This would connect to an API endpoint for autocomplete functionality
    },

    initNavigationEnhancements: function() {
        // Smooth scrolling for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });

        // Active navigation highlighting
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
        
        navLinks.forEach(link => {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
    },

    initCardInteractions: function() {
        // Enhanced card hover effects
        const cards = document.querySelectorAll('.facultyfinder-card');
        
        cards.forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-4px)';
            });
            
            card.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
            });
        });

        // Research area tag interactions
        const researchTags = document.querySelectorAll('.research-area-tag');
        
        researchTags.forEach(tag => {
            tag.addEventListener('click', function() {
                const tagText = this.textContent.trim();
                // Redirect to faculty search with this research area
                window.location.href = `/faculties?research_area=${encodeURIComponent(tagText)}`;
            });
            
            // Make tags look clickable
            tag.style.cursor = 'pointer';
            tag.title = `Search faculty in: ${tag.textContent.trim()}`;
        });
    },

    initTooltips: function() {
        // Initialize Bootstrap tooltips if available
        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }
    },

    // Utility functions
    utils: {
        // Show loading state
        showLoading: function(element) {
            element.classList.add('loading');
        },

        // Hide loading state
        hideLoading: function(element) {
            element.classList.remove('loading');
        },

        // Format numbers with commas
        formatNumber: function(num) {
            return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        },

        // Debounce function for search inputs
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        // Copy text to clipboard
        copyToClipboard: function(text) {
            if (navigator.clipboard) {
                navigator.clipboard.writeText(text).then(() => {
                    this.showToast('Copied to clipboard!', 'success');
                });
            } else {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                this.showToast('Copied to clipboard!', 'success');
            }
        },

        // Show toast notification
        showToast: function(message, type = 'info') {
            // Create toast element
            const toast = document.createElement('div');
            toast.className = `toast align-items-center text-white bg-${type} border-0`;
            toast.setAttribute('role', 'alert');
            toast.innerHTML = `
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            `;

            // Add to page
            let toastContainer = document.querySelector('.toast-container');
            if (!toastContainer) {
                toastContainer = document.createElement('div');
                toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
                document.body.appendChild(toastContainer);
            }
            
            toastContainer.appendChild(toast);

            // Show toast
            if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
                const bsToast = new bootstrap.Toast(toast);
                bsToast.show();
                
                // Remove after it's hidden
                toast.addEventListener('hidden.bs.toast', () => {
                    toast.remove();
                });
            } else {
                // Fallback without Bootstrap
                setTimeout(() => {
                    toast.remove();
                }, 3000);
            }
        }
    },

    // Statistics and analytics
    analytics: {
        // Track search queries
        trackSearch: function(query, filters) {
            // TODO: Implement analytics tracking
            console.log('Search tracked:', { query, filters });
        },

        // Track profile views
        trackProfileView: function(professorId) {
            // TODO: Implement analytics tracking
            console.log('Profile view tracked:', professorId);
        }
    }
};

// Page-specific functionality
const PageSpecific = {
    // Home page functionality
    home: function() {
        // Auto-focus main search input
        const mainSearch = document.querySelector('input[name="search"]');
        if (mainSearch) {
            mainSearch.focus();
        }

        // Animate statistics on scroll
        const statNumbers = document.querySelectorAll('.stat-number');
        if (statNumbers.length > 0 && 'IntersectionObserver' in window) {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.animateNumber(entry.target);
                        observer.unobserve(entry.target);
                    }
                });
            });

            statNumbers.forEach(stat => observer.observe(stat));
        }
    },

    // Faculty page functionality
    faculties: function() {
        // View toggle functionality
        const gridBtn = document.querySelector('[data-view="grid"]');
        const listBtn = document.querySelector('[data-view="list"]');
        const resultsContainer = document.getElementById('faculty-grid');

        if (gridBtn && listBtn && resultsContainer) {
            gridBtn.addEventListener('click', () => {
                resultsContainer.className = 'row';
                gridBtn.classList.add('active');
                listBtn.classList.remove('active');
                localStorage.setItem('faculty-view', 'grid');
            });

            listBtn.addEventListener('click', () => {
                resultsContainer.className = 'list-group';
                listBtn.classList.add('active');
                gridBtn.classList.remove('active');
                localStorage.setItem('faculty-view', 'list');
            });

            // Restore saved view preference
            const savedView = localStorage.getItem('faculty-view');
            if (savedView === 'list') {
                listBtn.click();
            }
        }
    },

    // Animate number counting
    animateNumber: function(element) {
        const target = parseInt(element.textContent.replace(/,/g, ''));
        let current = 0;
        const increment = target / 30; // 30 frames
        
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            element.textContent = FacultyFinder.utils.formatNumber(Math.floor(current));
        }, 50);
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    FacultyFinder.init();
    
    // Page-specific initialization
    const path = window.location.pathname;
    if (path === '/' || path === '/index.html') {
        PageSpecific.home();
    } else if (path === '/faculties') {
        PageSpecific.faculties();
    }
});

// Export for module usage if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FacultyFinder;
} 