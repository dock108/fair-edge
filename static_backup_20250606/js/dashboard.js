/**
 * Sports Betting Dashboard - Enhanced JavaScript
 * Phase 5: Accessibility and User Experience Enhancements
 */

(function() {
    'use strict';

    // Wait for DOM to be ready
    document.addEventListener('DOMContentLoaded', function() {
        initializeAccessibility();
        initializeTooltips();
        initializeCardAnimations();
        initializeKeyboardNavigation();
        initializeFormEnhancements();
        announcePageLoad();
    });

    /**
     * Initialize accessibility features
     */
    function initializeAccessibility() {
        // Add skip link functionality
        const skipLink = document.querySelector('.skip-link');
        if (skipLink) {
            skipLink.addEventListener('click', function(e) {
                e.preventDefault();
                const target = document.getElementById('main-content');
                if (target) {
                    target.focus();
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            });
        }

        // Enhance focus visibility for better accessibility
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Tab') {
                document.body.classList.add('using-keyboard');
            }
        });

        document.addEventListener('mousedown', function() {
            document.body.classList.remove('using-keyboard');
        });

        // Add proper ARIA labels to dynamic content
        updateAriaLabels();
    }

    /**
     * Initialize tooltip functionality
     */
    function initializeTooltips() {
        const tooltipTriggers = document.querySelectorAll('.help-icon');
        
        tooltipTriggers.forEach(function(trigger) {
            let tooltip = trigger.parentElement.querySelector('.tooltip');
            if (!tooltip) return;

            // Show tooltip on hover/focus
            trigger.addEventListener('mouseenter', showTooltip);
            trigger.addEventListener('focus', showTooltip);
            
            // Hide tooltip on leave/blur
            trigger.addEventListener('mouseleave', hideTooltip);
            trigger.addEventListener('blur', hideTooltip);

            // Toggle tooltip on click/enter/space
            trigger.addEventListener('click', toggleTooltip);
            trigger.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    toggleTooltip();
                }
            });

            function showTooltip() {
                tooltip.setAttribute('aria-hidden', 'false');
                tooltip.style.visibility = 'visible';
                tooltip.style.opacity = '1';
            }

            function hideTooltip() {
                if (!tooltip.classList.contains('tooltip-pinned')) {
                    tooltip.setAttribute('aria-hidden', 'true');
                    tooltip.style.visibility = 'hidden';
                    tooltip.style.opacity = '0';
                }
            }

            function toggleTooltip() {
                if (tooltip.style.visibility === 'visible') {
                    tooltip.classList.remove('tooltip-pinned');
                    hideTooltip();
                } else {
                    tooltip.classList.add('tooltip-pinned');
                    showTooltip();
                }
            }
        });

        // Close pinned tooltips when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.tooltip-container')) {
                document.querySelectorAll('.tooltip-pinned').forEach(function(tooltip) {
                    tooltip.classList.remove('tooltip-pinned');
                    tooltip.setAttribute('aria-hidden', 'true');
                    tooltip.style.visibility = 'hidden';
                    tooltip.style.opacity = '0';
                });
            }
        });
    }

    /**
     * Initialize card animations
     */
    function initializeCardAnimations() {
        const cards = document.querySelectorAll('.bet-card');
        
        // Add intersection observer for progressive card loading
        if ('IntersectionObserver' in window) {
            const cardObserver = new IntersectionObserver(function(entries) {
                entries.forEach(function(entry) {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('card-visible');
                        cardObserver.unobserve(entry.target);
                    }
                });
            }, {
                threshold: 0.1,
                rootMargin: '50px'
            });

            cards.forEach(function(card) {
                card.classList.add('card-loading');
                cardObserver.observe(card);
            });
        } else {
            // Fallback for browsers without IntersectionObserver
            cards.forEach(function(card) {
                card.classList.add('card-visible');
            });
        }

        // Enhanced hover effects
        cards.forEach(function(card) {
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-4px)';
            });

            card.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
            });
        });
    }

    /**
     * Initialize keyboard navigation enhancements
     */
    function initializeKeyboardNavigation() {
        // Enhanced filter form navigation
        const filterForm = document.querySelector('.filters-form');
        if (filterForm) {
            const selects = filterForm.querySelectorAll('select');
            
            selects.forEach(function(select) {
                select.addEventListener('keydown', function(e) {
                    // Allow Enter to submit form
                    if (e.key === 'Enter') {
                        filterForm.submit();
                    }
                });
            });
        }

        // Add keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            // Alt + F to focus filter form
            if (e.altKey && e.key === 'f') {
                e.preventDefault();
                const firstSelect = document.querySelector('.filter-select');
                if (firstSelect) {
                    firstSelect.focus();
                }
            }

            // Alt + M to focus main content
            if (e.altKey && e.key === 'm') {
                e.preventDefault();
                const mainContent = document.getElementById('main-content');
                if (mainContent) {
                    mainContent.focus();
                    mainContent.scrollIntoView({ behavior: 'smooth' });
                }
            }

            // Escape to close tooltips
            if (e.key === 'Escape') {
                document.querySelectorAll('.tooltip-pinned').forEach(function(tooltip) {
                    tooltip.classList.remove('tooltip-pinned');
                    tooltip.setAttribute('aria-hidden', 'true');
                    tooltip.style.visibility = 'hidden';
                    tooltip.style.opacity = '0';
                });
            }
        });
    }

    /**
     * Initialize form enhancements
     */
    function initializeFormEnhancements() {
        const filterForm = document.querySelector('.filters-form');
        if (!filterForm) return;

        // Auto-submit on select change for better UX
        const selects = filterForm.querySelectorAll('select');
        selects.forEach(function(select) {
            select.addEventListener('change', function() {
                // Add small delay to allow for multiple quick selections
                clearTimeout(this.submitTimeout);
                this.submitTimeout = setTimeout(function() {
                    filterForm.submit();
                }, 300);
            });
        });

        // Enhanced loading state
        filterForm.addEventListener('submit', function() {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Loading...';
            }
        });
    }

    /**
     * Update ARIA labels for dynamic content
     */
    function updateAriaLabels() {
        // Update card count for screen readers
        const cards = document.querySelectorAll('.bet-card');
        const cardCount = cards.length;
        
        // Create or update live region
        let liveRegion = document.getElementById('cards-count-live');
        if (!liveRegion) {
            liveRegion = document.createElement('div');
            liveRegion.id = 'cards-count-live';
            liveRegion.className = 'sr-only';
            liveRegion.setAttribute('aria-live', 'polite');
            document.body.appendChild(liveRegion);
        }
        
        if (cardCount > 0) {
            liveRegion.textContent = `${cardCount} betting opportunities displayed`;
        }

        // Add numbering to cards for screen readers
        cards.forEach(function(card, index) {
            const cardNumber = index + 1;
            card.setAttribute('aria-label', `Betting opportunity ${cardNumber} of ${cardCount}`);
        });
    }

    /**
     * Announce page load for screen readers
     */
    function announcePageLoad() {
        // Create announcement for page load
        const announcement = document.createElement('div');
        announcement.className = 'sr-only';
        announcement.setAttribute('aria-live', 'assertive');
        announcement.setAttribute('aria-atomic', 'true');
        document.body.appendChild(announcement);

        // Announce page content after a brief delay
        setTimeout(function() {
            const cardCount = document.querySelectorAll('.bet-card').length;
            if (cardCount > 0) {
                announcement.textContent = `Sports betting dashboard loaded with ${cardCount} opportunities. Use Tab to navigate or Alt+F to access filters.`;
            } else {
                announcement.textContent = 'Sports betting dashboard loaded. No opportunities currently available.';
            }
            
            // Remove announcement after it's been read
            setTimeout(function() {
                announcement.remove();
            }, 3000);
        }, 1000);
    }

    /**
     * Add performance optimizations
     */
    function optimizePerformance() {
        // Lazy load images if any
        const images = document.querySelectorAll('img[data-src]');
        if ('IntersectionObserver' in window && images.length) {
            const imageObserver = new IntersectionObserver(function(entries) {
                entries.forEach(function(entry) {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        imageObserver.unobserve(img);
                    }
                });
            });

            images.forEach(function(img) {
                imageObserver.observe(img);
            });
        }
    }

    // Initialize performance optimizations
    optimizePerformance();

    // Export functions for testing if needed
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = {
            initializeAccessibility,
            initializeTooltips,
            initializeCardAnimations,
            initializeKeyboardNavigation
        };
    }

})();


// ===== UTILITY FUNCTIONS =====

/**
 * Format EV percentage with color coding
 */
function formatEVDisplay(percentage) {
    const formattedValue = percentage >= 0 ? `+${percentage.toFixed(1)}%` : `${percentage.toFixed(1)}%`;
    
    if (percentage >= 4.5) {
        return `<span class="text-success fw-bold">${formattedValue}</span>`;
    } else if (percentage > 0) {
        return `<span class="text-warning fw-bold">${formattedValue}</span>`;
    } else {
        return `<span class="text-muted">${formattedValue}</span>`;
    }
}

/**
 * Simple toast notifications (if needed in future phases)
 */
function showToast(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
    // Future implementation: Bootstrap toast or custom notification
} 