/**
 * Google Analytics Configuration for FacultyFinder
 * This script initializes Google Analytics (GA4) tracking
 */

// Configuration - will be loaded from server-side endpoint
const GOOGLE_ANALYTICS_CONFIG = {
    // This will be loaded from /static/js/ga-config.js
    trackingId: window.GOOGLE_ANALYTICS_CONFIG?.trackingId || window.GOOGLE_ANALYTICS_ID || 'G-XXXXXXXXXX',
    
    // Check if enabled from server config, default to not on localhost
    enabled: window.GOOGLE_ANALYTICS_CONFIG?.enabled !== false,
    
    // Only track in production (not localhost) unless explicitly enabled
    enableOnLocalhost: false,
    
    // Additional configuration
    config: {
        send_page_view: true,
        anonymize_ip: true,
        allow_google_signals: false,
        cookie_flags: 'SameSite=None;Secure'
    }
};

/**
 * Initialize Google Analytics
 */
function initializeGoogleAnalytics() {
    // Check if we should track (not localhost unless explicitly enabled)
    const isLocalhost = window.location.hostname === 'localhost' || 
                       window.location.hostname === '127.0.0.1' ||
                       window.location.hostname.includes('192.168.') ||
                       window.location.hostname.includes('local');
    
    // Check if Google Analytics is disabled
    if (!GOOGLE_ANALYTICS_CONFIG.enabled) {
        console.log('Google Analytics disabled via server configuration');
        return;
    }
    
    if (isLocalhost && !GOOGLE_ANALYTICS_CONFIG.enableOnLocalhost) {
        console.log('Google Analytics disabled on localhost');
        return;
    }
    
    // Check if tracking ID is set and valid
    if (!GOOGLE_ANALYTICS_CONFIG.trackingId || 
        GOOGLE_ANALYTICS_CONFIG.trackingId === 'G-XXXXXXXXXX' ||
        GOOGLE_ANALYTICS_CONFIG.trackingId === '') {
        console.log('Google Analytics tracking ID not configured');
        return;
    }
    
    // Initialize Google Analytics
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    
    // Load the gtag script with the actual tracking ID if available
    if (GOOGLE_ANALYTICS_CONFIG.trackingId !== 'G-XXXXXXXXXX') {
        const script = document.createElement('script');
        script.async = true;
        script.src = `https://www.googletagmanager.com/gtag/js?id=${GOOGLE_ANALYTICS_CONFIG.trackingId}`;
        document.head.appendChild(script);
    }
    
    // Configure tracking
    gtag('config', GOOGLE_ANALYTICS_CONFIG.trackingId, {
        page_title: document.title,
        page_location: window.location.href,
        ...GOOGLE_ANALYTICS_CONFIG.config
    });
    
    console.log('Google Analytics initialized with ID:', GOOGLE_ANALYTICS_CONFIG.trackingId);
    
    // Track page type for better analytics
    trackPageType();
}

/**
 * Determine and track page type based on URL
 */
function trackPageType() {
    const path = window.location.pathname;
    let pageType = 'other';
    
    if (path === '/' || path === '/index.html') {
        pageType = 'homepage';
    } else if (path.includes('/professor/')) {
        pageType = 'faculty_profile';
        // Track faculty view if professor ID available
        const professorId = extractProfessorId(path);
        if (professorId) {
            setTimeout(() => trackFacultyView(professorId, ''), 1000);
        }
    } else if (path.includes('/university/')) {
        pageType = 'university_profile';
        // Track university view if university code available
        const universityCode = extractUniversityCode(path);
        if (universityCode) {
            setTimeout(() => trackUniversityView(universityCode), 1000);
        }
    } else if (path.includes('/faculties')) {
        pageType = 'faculty_search';
    } else if (path.includes('/universities')) {
        pageType = 'university_search';
    } else if (path.includes('/countries')) {
        pageType = 'countries';
    } else if (path.includes('/admin')) {
        pageType = 'admin';
    }
    
    // Track page type as custom event
    trackEvent('page_view_by_type', {
        page_type: pageType,
        event_category: 'navigation'
    });
}

/**
 * Extract professor ID from URL path
 * @param {string} path - URL path
 * @returns {string|null} - Professor ID or null
 */
function extractProfessorId(path) {
    const match = path.match(/\/professor\/([A-Z]+-[A-Z]+-\d+-\d+)/);
    return match ? match[1] : null;
}

/**
 * Extract university code from URL path
 * @param {string} path - URL path
 * @returns {string|null} - University code or null
 */
function extractUniversityCode(path) {
    const match = path.match(/\/university\/([A-Z]+-[A-Z]+-\d+)/);
    return match ? match[1] : null;
}

/**
 * Track custom events
 * @param {string} eventName - Event name
 * @param {object} parameters - Event parameters
 */
function trackEvent(eventName, parameters = {}) {
    if (typeof gtag !== 'undefined') {
        gtag('event', eventName, parameters);
    }
}

/**
 * Track page views manually (for SPAs)
 * @param {string} pageTitle - Page title
 * @param {string} pagePath - Page path
 */
function trackPageView(pageTitle, pagePath) {
    if (typeof gtag !== 'undefined') {
        gtag('config', GOOGLE_ANALYTICS_CONFIG.trackingId, {
            page_title: pageTitle,
            page_path: pagePath
        });
    }
}

/**
 * Track faculty profile views
 * @param {string} professorId - Professor ID
 * @param {string} university - University code
 */
function trackFacultyView(professorId, university) {
    trackEvent('faculty_view', {
        professor_id: professorId,
        university_code: university,
        event_category: 'engagement'
    });
}

/**
 * Track university profile views
 * @param {string} universityCode - University code
 */
function trackUniversityView(universityCode) {
    trackEvent('university_view', {
        university_code: universityCode,
        event_category: 'engagement'
    });
}

/**
 * Track search queries
 * @param {string} query - Search query
 * @param {string} searchType - Type of search (faculty, university, etc.)
 * @param {number} resultCount - Number of results
 */
function trackSearch(query, searchType, resultCount) {
    trackEvent('search', {
        search_term: query,
        search_type: searchType,
        result_count: resultCount,
        event_category: 'search'
    });
}

// Auto-initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeGoogleAnalytics);
} else {
    initializeGoogleAnalytics();
}

// Export functions for use in other scripts
window.FacultyFinderAnalytics = {
    trackEvent,
    trackPageView,
    trackFacultyView,
    trackUniversityView,
    trackSearch
}; 