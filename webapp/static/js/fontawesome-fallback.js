/**
 * Font Awesome CDN Fallback System
 * Ensures icons load properly on production by trying multiple CDNs
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('🔍 Checking Font Awesome availability...');
    
    // Test if Font Awesome icons are working
    function testFontAwesome() {
        var testElement = document.createElement('i');
        testElement.className = 'fas fa-home';
        testElement.style.position = 'absolute';
        testElement.style.left = '-9999px';
        testElement.style.visibility = 'hidden';
        document.body.appendChild(testElement);
        
        var computed = window.getComputedStyle(testElement);
        var fontFamily = computed.getPropertyValue('font-family');
        
        // Clean up test element
        document.body.removeChild(testElement);
        
        // Check if Font Awesome loaded
        return fontFamily && (
            fontFamily.indexOf('Font Awesome') !== -1 || 
            fontFamily.indexOf('FontAwesome') !== -1 ||
            fontFamily.indexOf('fa') !== -1
        );
    }
    
    // Load Font Awesome from alternative CDN
    function loadFontAwesome(url, description, onSuccess, onError) {
        console.log(`📦 Loading Font Awesome from ${description}...`);
        
        var link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = url;
        link.crossOrigin = 'anonymous';
        
        link.onload = function() {
            console.log(`✅ Font Awesome loaded successfully from ${description}`);
            if (onSuccess) onSuccess();
        };
        
        link.onerror = function() {
            console.warn(`❌ Failed to load Font Awesome from ${description}`);
            if (onError) onError();
        };
        
        document.head.appendChild(link);
    }
    
    // Fallback chain
    function tryFallbacks() {
        // Try jsdelivr CDN
        loadFontAwesome(
            'https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.5.1/css/all.min.css',
            'jsdelivr CDN',
            function() {
                // Success callback - test again
                setTimeout(function() {
                    if (!testFontAwesome()) {
                        tryOfficialCDN();
                    }
                }, 100);
            },
            tryOfficialCDN
        );
    }
    
    function tryOfficialCDN() {
        // Try official FontAwesome CDN
        loadFontAwesome(
            'https://use.fontawesome.com/releases/v6.5.1/css/all.css',
            'FontAwesome official CDN',
            function() {
                setTimeout(function() {
                    if (!testFontAwesome()) {
                        tryBootstrapCDN();
                    }
                }, 100);
            },
            tryBootstrapCDN
        );
    }
    
    function tryBootstrapCDN() {
        // Try BootstrapCDN as last resort
        loadFontAwesome(
            'https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css',
            'BootstrapCDN (FA 4.7)',
            function() {
                console.log('⚠️ Using Font Awesome 4.7 - some newer icons may not display');
            },
            function() {
                console.error('❌ All Font Awesome CDNs failed. Icons will not display properly.');
                // Show user-friendly error
                showIconError();
            }
        );
    }
    
    function showIconError() {
        // Create a small notification for icon loading failure
        var notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: #f8d7da;
            color: #721c24;
            padding: 10px 15px;
            border: 1px solid #f5c6cb;
            border-radius: 5px;
            font-size: 12px;
            z-index: 9999;
            max-width: 300px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        `;
        notification.innerHTML = '⚠️ Icons failed to load. Functionality not affected.';
        
        document.body.appendChild(notification);
        
        // Auto-hide after 5 seconds
        setTimeout(function() {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
    
    // Initial test
    setTimeout(function() {
        if (!testFontAwesome()) {
            console.warn('🔄 Primary Font Awesome CDN failed, trying fallbacks...');
            tryFallbacks();
        } else {
            console.log('✅ Font Awesome loaded successfully from primary CDN');
        }
    }, 500); // Give primary CDN time to load
    
    // Additional check for mobile hamburger menu icon
    setTimeout(function() {
        var hamburger = document.querySelector('.navbar-toggler-icon');
        if (hamburger && !testFontAwesome()) {
            // Add fallback hamburger menu styling
            hamburger.style.backgroundImage = `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 30 30'%3e%3cpath stroke='rgba%2833, 37, 41, 0.75%29' stroke-linecap='round' stroke-miterlimit='10' stroke-width='2' d='m4 7h22M4 15h22M4 23h22'/%3e%3c/svg%3e")`;
        }
    }, 1000);
}); 