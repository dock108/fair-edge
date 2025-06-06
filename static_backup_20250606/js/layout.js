/**
 * Layout System JavaScript
 * Handles responsive behavior, resize optimizations, and layout utilities
 */

(function() {
    'use strict';

    let currentBreakpoint = '';
    let resizeTimeout;
    let lastWidth = window.innerWidth;

    // Initialize layout system
    document.addEventListener('DOMContentLoaded', function() {
        initializeLayoutSystem();
        handleInitialBreakpoint();
        setupResizeHandler();
        setupIntersectionObserver();
        setupFocusManagement();
    });

    /**
     * Initialize the layout system
     */
    function initializeLayoutSystem() {
        // Add layout class to body for CSS targeting
        document.body.classList.add('layout-system-loaded');
        
        // Set up viewport meta tag optimization
        optimizeViewport();
        
        // Initialize ARIA live regions for layout changes
        createLayoutAnnouncements();
        
        console.log('Layout system initialized');
    }

    /**
     * Handle responsive breakpoint changes
     */
    function handleBreakpointChange(newBreakpoint) {
        if (newBreakpoint === currentBreakpoint) return;
        
        const oldBreakpoint = currentBreakpoint;
        currentBreakpoint = newBreakpoint;
        
        document.body.setAttribute('data-breakpoint', newBreakpoint);
        
        // Announce breakpoint change to screen readers
        announceLayoutChange(`Layout changed to ${newBreakpoint} view`);
        
        // Handle specific breakpoint changes
        switch (newBreakpoint) {
            case 'mobile':
                handleMobileLayout();
                break;
            case 'tablet':
                handleTabletLayout();
                break;
            case 'desktop':
                handleDesktopLayout();
                break;
        }
        
        // Dispatch custom event for other scripts
        window.dispatchEvent(new CustomEvent('layoutBreakpointChange', {
            detail: { oldBreakpoint, newBreakpoint }
        }));
        
        console.log(`Breakpoint changed: ${oldBreakpoint} → ${newBreakpoint}`);
    }

    /**
     * Determine current breakpoint
     */
    function getCurrentBreakpoint() {
        const width = window.innerWidth;
        
        if (width < 768) {
            return 'mobile';
        } else if (width < 1280) {
            return 'tablet';
        } else {
            return 'desktop';
        }
    }

    /**
     * Handle initial breakpoint setting
     */
    function handleInitialBreakpoint() {
        const breakpoint = getCurrentBreakpoint();
        handleBreakpointChange(breakpoint);
    }

    /**
     * Set up debounced resize handler
     */
    function setupResizeHandler() {
        window.addEventListener('resize', function() {
            clearTimeout(resizeTimeout);
            
            resizeTimeout = setTimeout(function() {
                const newBreakpoint = getCurrentBreakpoint();
                const currentWidth = window.innerWidth;
                
                // Only process if breakpoint actually changed
                if (newBreakpoint !== currentBreakpoint) {
                    handleBreakpointChange(newBreakpoint);
                }
                
                // Handle width changes that might affect layout
                if (Math.abs(currentWidth - lastWidth) > 50) {
                    handleSignificantResize(lastWidth, currentWidth);
                    lastWidth = currentWidth;
                }
                
                // Recalculate any masonry layouts if they exist
                recalculateLayoutGrids();
                
            }, 250); // Debounce resize events
        }, { passive: true });
    }

    /**
     * Handle mobile-specific layout
     */
    function handleMobileLayout() {
        // Close any open drawers on mobile if switching from larger screen
        const statsDrawer = document.querySelector('.stats-drawer[aria-expanded="true"]');
        if (statsDrawer) {
            const toggle = statsDrawer.querySelector('.stats-drawer__toggle');
            if (toggle) {
                toggle.click(); // Close drawer
            }
        }
        
        // Optimize touch targets
        optimizeTouchTargets();
    }

    /**
     * Handle tablet-specific layout
     */
    function handleTabletLayout() {
        // Adjust grid gaps and spacing for tablet
        adjustTabletSpacing();
    }

    /**
     * Handle desktop-specific layout
     */
    function handleDesktopLayout() {
        // Ensure proper focus management for desktop
        setupKeyboardShortcuts();
    }

    /**
     * Handle significant resize events
     */
    function handleSignificantResize(oldWidth, newWidth) {
        // Announce significant layout changes
        if (Math.abs(newWidth - oldWidth) > 200) {
            announceLayoutChange('Page layout has been adjusted for your screen size');
        }
        
        // Refresh any intersection observers
        refreshIntersectionObservers();
    }

    /**
     * Recalculate layout grids (for future masonry implementation)
     */
    function recalculateLayoutGrids() {
        // Future: Implement masonry layout recalculation
        const grids = document.querySelectorAll('.opportunity-grid');
        grids.forEach(grid => {
            // Trigger reflow by toggling a class
            grid.classList.add('recalculating');
            requestAnimationFrame(() => {
                grid.classList.remove('recalculating');
            });
        });
    }

    /**
     * Set up intersection observer for progressive enhancement
     */
    function setupIntersectionObserver() {
        if ('IntersectionObserver' in window) {
            const observer = new IntersectionObserver(function(entries) {
                entries.forEach(function(entry) {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('in-viewport');
                        
                        // Lazy load functionality
                        if (entry.target.hasAttribute('data-lazy-load')) {
                            loadComponent(entry.target);
                        }
                    } else {
                        entry.target.classList.remove('in-viewport');
                    }
                });
            }, {
                threshold: 0.1,
                rootMargin: '50px'
            });

            // Observe layout components
            document.querySelectorAll('.stats-drawer, .opportunity-grid, .metric-card').forEach(el => {
                observer.observe(el);
            });
        }
    }

    /**
     * Refresh intersection observers
     */
    function refreshIntersectionObservers() {
        // Re-trigger intersection observer setup
        setupIntersectionObserver();
    }

    /**
     * Set up focus management for accessibility
     */
    function setupFocusManagement() {
        // Skip to main content functionality
        const skipLinks = document.querySelectorAll('.skip-link');
        skipLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.focus();
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });
    }

    /**
     * Set up keyboard shortcuts for desktop
     */
    function setupKeyboardShortcuts() {
        if (currentBreakpoint !== 'desktop') return;
        
        document.addEventListener('keydown', function(e) {
            // Only handle shortcuts when not in form inputs
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            
            switch (e.key) {
                case 'f':
                    if (e.altKey) {
                        e.preventDefault();
                        focusFirstFilter();
                    }
                    break;
                case 'm':
                    if (e.altKey) {
                        e.preventDefault();
                        focusMainContent();
                    }
                    break;
                case 's':
                    if (e.altKey) {
                        e.preventDefault();
                        toggleStatsDrawer();
                    }
                    break;
            }
        });
    }

    /**
     * Focus management utilities
     */
    function focusFirstFilter() {
        const firstFilter = document.querySelector('.filter-select, .search-input');
        if (firstFilter) {
            firstFilter.focus();
            announceLayoutChange('Focused on filters');
        }
    }

    function focusMainContent() {
        const mainContent = document.getElementById('main-content') || document.querySelector('main');
        if (mainContent) {
            mainContent.focus();
            mainContent.scrollIntoView({ behavior: 'smooth' });
            announceLayoutChange('Focused on main content');
        }
    }

    function toggleStatsDrawer() {
        const drawer = document.querySelector('.stats-drawer');
        if (drawer) {
            const toggle = drawer.querySelector('.stats-drawer__toggle');
            if (toggle) {
                toggle.click();
            }
        }
    }

    /**
     * Optimize touch targets for mobile
     */
    function optimizeTouchTargets() {
        const buttons = document.querySelectorAll('button, .btn, a');
        buttons.forEach(button => {
            const rect = button.getBoundingClientRect();
            if (rect.height < 44) {
                button.style.minHeight = '44px';
                button.style.paddingTop = '12px';
                button.style.paddingBottom = '12px';
            }
        });
    }

    /**
     * Adjust spacing for tablet layout
     */
    function adjustTabletSpacing() {
        // Future: Implement tablet-specific spacing adjustments
    }

    /**
     * Create ARIA live regions for layout announcements
     */
    function createLayoutAnnouncements() {
        if (!document.getElementById('layout-announcements')) {
            const announcer = document.createElement('div');
            announcer.id = 'layout-announcements';
            announcer.setAttribute('aria-live', 'polite');
            announcer.setAttribute('aria-atomic', 'true');
            announcer.className = 'sr-only';
            document.body.appendChild(announcer);
        }
    }

    /**
     * Announce layout changes to screen readers
     */
    function announceLayoutChange(message) {
        const announcer = document.getElementById('layout-announcements');
        if (announcer) {
            announcer.textContent = message;
            
            // Clear after announcement
            setTimeout(() => {
                announcer.textContent = '';
            }, 1000);
        }
    }

    /**
     * Optimize viewport meta tag
     */
    function optimizeViewport() {
        let viewport = document.querySelector('meta[name="viewport"]');
        if (!viewport) {
            viewport = document.createElement('meta');
            viewport.name = 'viewport';
            document.head.appendChild(viewport);
        }
        
        // Set optimized viewport for layout system
        viewport.content = 'width=device-width, initial-scale=1.0, viewport-fit=cover';
    }

    /**
     * Load component (for lazy loading)
     */
    function loadComponent(element) {
        const src = element.getAttribute('data-lazy-load');
        if (src) {
            // Future: Implement component lazy loading
            element.removeAttribute('data-lazy-load');
        }
    }

    // Export utilities for other scripts
    window.layoutSystem = {
        getCurrentBreakpoint,
        announceLayoutChange,
        focusMainContent,
        recalculateLayoutGrids
    };

})(); 