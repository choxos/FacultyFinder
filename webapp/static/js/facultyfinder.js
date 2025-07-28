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

// Theme management
FacultyFinder.theme = {
    current: localStorage.getItem('facultyfinder-theme') || 'light',
    
    init: function() {
        // Set initial theme
        document.documentElement.setAttribute('data-theme', this.current);
        this.updateToggleButton();
        
        // Add theme toggle button
        this.createToggleButton();
    },
    
    createToggleButton: function() {
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'theme-toggle';
        toggleBtn.id = 'themeToggle';
        toggleBtn.innerHTML = '<i class="fas fa-moon"></i>';
        toggleBtn.title = 'Toggle Dark Mode';
        toggleBtn.setAttribute('aria-label', 'Toggle Dark Mode');
        
        // Add click event
        toggleBtn.addEventListener('click', () => {
            this.toggle();
        });
        
        document.body.appendChild(toggleBtn);
    },
    
    toggle: function() {
        const newTheme = this.current === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);
    },
    
    setTheme: function(theme) {
        this.current = theme;
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('facultyfinder-theme', theme);
        this.updateToggleButton();
        
        // Trigger custom event for other components
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme } }));
    },
    
    updateToggleButton: function() {
        const toggleBtn = document.getElementById('themeToggle');
        if (!toggleBtn) return;
        
        if (this.current === 'dark') {
            toggleBtn.innerHTML = '<i class="fas fa-sun"></i>';
            toggleBtn.className = 'theme-toggle dark-mode';
            toggleBtn.title = 'Switch to Light Mode';
            toggleBtn.setAttribute('aria-label', 'Switch to Light Mode');
        } else {
            toggleBtn.innerHTML = '<i class="fas fa-moon"></i>';
            toggleBtn.className = 'theme-toggle light-mode';
            toggleBtn.title = 'Switch to Dark Mode';
            toggleBtn.setAttribute('aria-label', 'Switch to Dark Mode');
        }
    }
};

// Load more functionality
FacultyFinder.loadMore = {
    // Load more publications for professor profile
    publications: {
        currentOffset: 5, // First 5 are already loaded
        loading: false,
        
        async load(professorId) {
            if (this.loading) return;
            
            this.loading = true;
            const loadBtn = document.getElementById('loadMorePublications');
            const originalContent = loadBtn.innerHTML;
            
            // Show loading state
            loadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
            loadBtn.disabled = true;
            
            try {
                const response = await fetch(`/api/v1/professor/${professorId}/publications?limit=10&offset=${this.currentOffset}`);
                const data = await response.json();
                
                if (data.success && data.publications.length > 0) {
                    this.appendPublications(data.publications);
                    this.currentOffset += data.publications.length;
                    
                    // Hide button if no more publications
                    if (!data.has_more) {
                        loadBtn.style.display = 'none';
                    }
                } else {
                    loadBtn.style.display = 'none';
                }
            } catch (error) {
                console.error('Error loading more publications:', error);
                FacultyFinder.utils.showToast('Error loading publications', 'error');
                loadBtn.style.display = 'none';
            } finally {
                this.loading = false;
                loadBtn.innerHTML = originalContent;
                loadBtn.disabled = false;
            }
        },
        
        appendPublications(publications) {
            const container = document.querySelector('.publications-list');
            const loadMoreContainer = container.querySelector('.text-center');
            
            publications.forEach(pub => {
                const pubElement = this.createPublicationElement(pub);
                container.insertBefore(pubElement, loadMoreContainer);
            });
        },
        
        createPublicationElement(pub) {
            const div = document.createElement('div');
            div.className = 'publication-item';
            
            let authorsHtml = pub.authors ? `<p class="publication-authors">${pub.authors}</p>` : '';
            let journalInfo = '';
            
            if (pub.journal_name || pub.publication_year || pub.volume || pub.issue) {
                journalInfo = '<p class="publication-journal">';
                if (pub.journal_name) journalInfo += `<em>${pub.journal_name}</em>`;
                if (pub.publication_year) journalInfo += ` (${pub.publication_year})`;
                if (pub.volume || pub.issue) {
                    journalInfo += ` - Vol. ${pub.volume || ''}`;
                    if (pub.issue) journalInfo += `, No. ${pub.issue}`;
                }
                journalInfo += '</p>';
            }
            
            let linksHtml = '';
            if (pub.pmid || pub.doi) {
                linksHtml = '<small class="text-muted">';
                if (pub.pmid) {
                    linksHtml += `PMID: <a href="https://pubmed.ncbi.nlm.nih.gov/${pub.pmid}/" target="_blank">${pub.pmid}</a>`;
                }
                if (pub.doi) {
                    if (pub.pmid) linksHtml += ' | ';
                    linksHtml += `DOI: <a href="https://doi.org/${pub.doi}" target="_blank">${pub.doi}</a>`;
                }
                linksHtml += '</small>';
            }
            
            div.innerHTML = `
                <h6 class="publication-title">${pub.title}</h6>
                ${authorsHtml}
                ${journalInfo}
                ${linksHtml}
            `;
            
            return div;
        }
    },
    
    // Load more faculty for faculty listing page
    faculty: {
        currentOffset: 0,
        loading: false,
        currentParams: {},
        
        init() {
            const resultsContainer = document.getElementById('faculty-grid');
            if (resultsContainer) {
                this.currentOffset = resultsContainer.children.length;
                this.extractCurrentParams();
            }
        },
        
        extractCurrentParams() {
            const urlParams = new URLSearchParams(window.location.search);
            this.currentParams = {
                search: urlParams.get('search') || '',
                university: urlParams.get('university') || '',
                department: urlParams.get('department') || '',
                research_area: urlParams.get('research_area') || '',
                degree: urlParams.get('degree') || '',
                sort: urlParams.get('sort') || 'publication_count'
            };
        },
        
        async load() {
            if (this.loading) return;
            
            this.loading = true;
            const loadBtn = document.getElementById('loadMoreFaculty');
            const originalContent = loadBtn.innerHTML;
            
            // Show loading state
            loadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading more faculty...';
            loadBtn.disabled = true;
            
            try {
                const params = new URLSearchParams({
                    ...this.currentParams,
                    limit: '20',
                    offset: this.currentOffset.toString()
                });
                
                const response = await fetch(`/api/v1/faculties/search?${params}`);
                const data = await response.json();
                
                if (data.success && data.faculty.length > 0) {
                    this.appendFaculty(data.faculty);
                    this.currentOffset += data.faculty.length;
                    
                    // Hide button if no more faculty
                    if (!data.has_more) {
                        loadBtn.style.display = 'none';
                    }
                    
                    // Update result count
                    this.updateResultCount(data.total);
                } else {
                    loadBtn.style.display = 'none';
                }
            } catch (error) {
                console.error('Error loading more faculty:', error);
                FacultyFinder.utils.showToast('Error loading faculty', 'error');
                loadBtn.style.display = 'none';
            } finally {
                this.loading = false;
                loadBtn.innerHTML = originalContent;
                loadBtn.disabled = false;
            }
        },
        
        appendFaculty(facultyList) {
            const container = document.getElementById('faculty-grid');
            
            facultyList.forEach(faculty => {
                const facultyElement = this.createFacultyElement(faculty);
                container.appendChild(facultyElement);
            });
        },
        
        createFacultyElement(faculty) {
            const div = document.createElement('div');
            div.className = 'col-lg-6 col-xl-4 mb-4';
            
            let degreesHtml = '';
            if (faculty.degrees && faculty.degrees.length > 0) {
                degreesHtml = faculty.degrees.map(degree => 
                    `<a href="/faculties?degree=${encodeURIComponent(degree.degree_type)}" 
                       class="badge bg-secondary text-decoration-none me-1 mb-1" 
                       title="Filter by ${degree.degree_type}">${degree.degree_type}</a>`
                ).join('');
            }
            
            div.innerHTML = `
                <div class="card faculty-card h-100">
                    <div class="card-body">
                        <div class="d-flex align-items-start mb-3">
                            <div class="faculty-avatar me-3">
                                <i class="fas fa-user-graduate fa-2x text-primary"></i>
                            </div>
                            <div class="flex-grow-1">
                                <h5 class="card-title mb-1">
                                    <a href="/professor/${faculty.id}" class="text-decoration-none">${faculty.name}</a>
                                </h5>
                                <p class="card-subtitle text-muted mb-2">${faculty.position || 'Faculty Member'}</p>
                                <div class="university-info mb-2">
                                    <div>
                                        <a href="/faculties?department=${encodeURIComponent(faculty.department)}" 
                                           class="department-link text-decoration-none">
                                            <i class="fas fa-building me-1"></i>${faculty.department}
                                        </a>
                                    </div>
                                    <div>
                                        <a href="/faculties?university=${encodeURIComponent(faculty.university_name)}" 
                                           class="university-link text-decoration-none">
                                            <i class="fas fa-university me-1"></i>${faculty.university_name}
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        ${faculty.research_areas ? `
                        <div class="research-areas mb-3">
                            <small class="text-muted d-block mb-1">Research Areas:</small>
                            <div class="research-tags">
                                ${faculty.research_areas.split(',').slice(0, 3).map(area => 
                                    `<span class="badge bg-light text-dark me-1 mb-1">${area.trim()}</span>`
                                ).join('')}
                            </div>
                        </div>
                        ` : ''}
                        
                        ${degreesHtml ? `
                        <div class="degrees-section mb-3">
                            <small class="text-muted d-block mb-1">Degrees:</small>
                            <div class="degrees-list">
                                ${degreesHtml}
                            </div>
                        </div>
                        ` : ''}
                        
                        <div class="faculty-stats">
                            <div class="row text-center">
                                <div class="col-4">
                                    <small class="text-muted d-block">Publications</small>
                                    <strong>${faculty.publication_count || 0}</strong>
                                </div>
                                <div class="col-4">
                                    <small class="text-muted d-block">Citations</small>
                                    <strong>${faculty.total_citations || 0}</strong>
                                </div>
                                <div class="col-4">
                                    <small class="text-muted d-block">H-Index</small>
                                    <strong>${faculty.h_index || 0}</strong>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card-footer bg-transparent">
                        <div class="d-flex justify-content-between align-items-center">
                            <a href="/professor/${faculty.id}" class="btn btn-primary btn-sm">
                                <i class="fas fa-user me-1"></i>View Profile
                            </a>
                            ${faculty.email ? `
                            <a href="mailto:${faculty.email}" class="btn btn-outline-secondary btn-sm">
                                <i class="fas fa-envelope"></i>
                            </a>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
            
            return div;
        },
        
        updateResultCount(total) {
            const countElement = document.querySelector('h3:contains("Faculty Members")');
            if (countElement) {
                const currentShowing = document.getElementById('faculty-grid').children.length;
                countElement.textContent = `Faculty Members (${currentShowing} of ${total} shown)`;
            }
        }
    }
};

// Global functions for template access
function loadMorePublications() {
    const professorId = window.location.pathname.split('/').pop();
    if (professorId && !isNaN(professorId)) {
        FacultyFinder.loadMore.publications.load(parseInt(professorId));
    }
}

function loadMoreFaculty() {
    FacultyFinder.loadMore.faculty.load();
}

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
    // Initialize theme management
    FacultyFinder.theme.init();
    
    const currentPage = window.location.pathname;
    
    if (currentPage === '/') {
        if (typeof initHomePage === 'function') {
            initHomePage();
        }
    } else if (currentPage === '/faculties') {
        if (typeof initFacultiesPage === 'function') {
            initFacultiesPage();
        }
    } else if (currentPage.includes('/professor/')) {
        // Initialize citation network on professor profile pages
        const professorId = currentPage.split('/').pop();
        if (professorId && !isNaN(professorId)) {
            FacultyFinder.citations.loadNetworkVisualization(parseInt(professorId));
        }
    }
    
    // Add keyboard shortcut for theme toggle (Ctrl/Cmd + Shift + D)
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'D') {
            e.preventDefault();
            FacultyFinder.theme.toggle();
        }
    });
    
    // Initialize load more functionality
    if (currentPage === '/faculties') {
        FacultyFinder.loadMore.faculty.init();
    }
});

// Export for module usage if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FacultyFinder;
} 