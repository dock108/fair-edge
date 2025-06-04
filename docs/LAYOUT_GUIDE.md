# Layout System Guide

This guide documents the modern layout system implemented in Phase 2 of the UI modernization.

## Overview

The layout system uses CSS Grid and Flexbox utilities to create responsive, accessible layouts without Bootstrap dependencies. All layouts use design tokens for consistent spacing and breakpoints.

## Core Concepts

### Content Wrapper
```html
<div class="content-wrap">
  <!-- All page content goes here -->
</div>
```

**Purpose**: Provides consistent maximum width (1440px) and responsive padding across all pages.

**Features**:
- Max width: 1440px
- Auto-centering with `margin-inline: auto`
- Responsive padding: 16px mobile, 20px tablet, 24px desktop

### Grid System

#### Basic Grid
```html
<div class="grid grid-cols-1">
  <div>Item 1</div>
  <div>Item 2</div>
</div>
```

#### Responsive Grid
```html
<div class="grid grid-cols-1 grid-md-2 grid-lg-3">
  <!-- Responsive: 1 col mobile, 2 cols tablet, 3 cols desktop -->
</div>
```

#### Dashboard Grid (Specialized)
```html
<div class="grid grid-dashboard">
  <!-- Left: 260px stats sidebar -->
  <!-- Right: Flexible main content -->
</div>
```

## Available Classes

### Grid Layout Classes
- `.grid` - Base grid container
- `.grid-cols-1` to `.grid-cols-4` - Column counts
- `.grid-md-2`, `.grid-lg-3`, etc. - Responsive variants
- `.grid-dashboard` - Specialized dashboard layout

### Grid Item Classes
- `.col-span-1` to `.col-span-4` - Span multiple columns
- `.col-span-full` - Span all columns

### Flex Utilities
- `.flex`, `.flex-col`, `.flex-row`
- `.items-center`, `.items-start`, `.items-end`
- `.justify-center`, `.justify-between`, `.justify-start`, `.justify-end`
- `.flex-1`, `.flex-none`, `.flex-auto`

### Gap Utilities
- `.gap-0` to `.gap-8` - Uses design token spacing scale

## Sticky Top Shell

### Structure
```html
<header class="top-shell" id="top-shell">
  <div class="content-wrap">
    <div class="top-shell__content">
      <div class="top-shell__title">Page Title</div>
      <div class="top-shell__actions">
        <!-- Search, filters, actions -->
      </div>
    </div>
  </div>
</header>
```

### Features
- Sticky positioning with `position: sticky; top: 0`
- Height: 56px mobile, 64px desktop
- Auto-shadow on scroll (`.top-shell--scrolled`)
- Responsive content layout

### JavaScript Integration
The top shell automatically gets shadow on scroll:
```javascript
// Automatic scroll detection included in top_shell.html
window.addEventListener('scroll', onScroll, { passive: true });
```

## Stats Components

### Desktop Sidebar
```html
<aside class="stats-sidebar">
  <h2 class="stats-sidebar__title">Summary Statistics</h2>
  <div class="stats-sidebar__grid">
    <!-- Metric cards -->
  </div>
</aside>
```

### Mobile Drawer
```html
<aside class="stats-drawer" x-data="{ open: false }">
  <button class="stats-drawer__toggle" @click="open = !open">
    Summary Statistics
  </button>
  <div class="stats-drawer__content" x-show="open">
    <!-- Metric cards -->
  </div>
</aside>
```

## Responsive Breakpoints

| Breakpoint | Behavior |
|------------|----------|
| < 768px | Single column, stats drawer collapsed, mobile-first layout |
| ≥ 768px | Two-column grid: 260px stats rail + fluid right column |
| ≥ 1280px | Increased gaps for better visual hierarchy |

### Breakpoint Variables (Design Tokens)
```css
/* Use in media queries */
@media (min-width: 768px) { /* Tablet */ }
@media (min-width: 992px) { /* Desktop */ }
@media (min-width: 1280px) { /* Large desktop */ }
```

## Form Controls

### Search Input
```html
<input type="text" class="search-input" placeholder="Search...">
```

### Filter Select
```html
<select class="filter-select">
  <option value="">All Options</option>
</select>
```

### Filter Group
```html
<div class="filter-group">
  <label class="filter-label">Filter:</label>
  <select class="filter-select">...</select>
</div>
```

## Alpine.js Integration

### Requirements
- Alpine.js 3.x loaded in base template
- Used for interactive stats drawer
- Focus trapping and accessibility features included

### Example Usage
```html
<div x-data="{ open: false }">
  <button @click="open = !open">Toggle</button>
  <div x-show="open" x-transition>Content</div>
</div>
```

## Accessibility Features

### Focus Management
- Focus trapping in drawers
- Proper ARIA labels and states
- Keyboard navigation support

### Screen Reader Support
- Semantic HTML structure
- ARIA landmarks and regions
- Live regions for dynamic updates

### Keyboard Shortcuts
- Alt + F: Focus first filter
- Alt + M: Jump to main content
- Escape: Close drawers/tooltips

## Migration Guide

### From Bootstrap Containers
```html
<!-- Old -->
<div class="container-fluid">
  <div class="row">
    <div class="col-md-6">Content</div>
  </div>
</div>

<!-- New -->
<div class="content-wrap">
  <div class="grid grid-md-2">
    <div>Content</div>
  </div>
</div>
```

### Grid Updates
1. Replace `.container-fluid` with `.content-wrap`
2. Replace `.row` with `.grid` + column classes
3. Replace `.col-*` with grid utilities
4. Update JavaScript selectors if needed

## Performance Considerations

### CSS Loading Order
1. `_tokens.css` (design tokens)
2. `_layout.css` (layout utilities)
3. `bootstrap.min.css` (if needed)
4. `dashboard.css` (component styles)

### JavaScript Optimizations
- Debounced resize handlers for layout recalculation
- Intersection Observer for progressive loading
- Passive event listeners for better performance

## Debugging

### Layout Debug Mode
Add `data-layout-debug="true"` to any element to show layout outlines:
```html
<div class="content-wrap" data-layout-debug="true">
  <!-- Visual debugging outlines appear -->
</div>
```

### Common Issues
- **Horizontal scroll**: Check for fixed widths > container width
- **Layout shifts**: Ensure consistent spacing using design tokens
- **Mobile overflow**: Use `.content-wrap` for proper padding

## Best Practices

1. **Always use design tokens** for spacing, colors, and typography
2. **Mobile-first approach** - start with single column, enhance for larger screens
3. **Semantic HTML** - use proper landmarks and heading hierarchy
4. **Progressive enhancement** - ensure functionality without JavaScript
5. **Test across devices** - verify responsive behavior at all breakpoints

## Examples

### Simple Page Layout
```html
<div class="content-wrap">
  <main class="grid grid-cols-1 gap-5">
    <section>Content Section 1</section>
    <section>Content Section 2</section>
  </main>
</div>
```

### Dashboard Layout
```html
<div class="content-wrap">
  <main class="grid grid-cols-1 grid-dashboard">
    <!-- Stats sidebar/drawer -->
    {% include "partials/stats_drawer.html" %}
    
    <!-- Main content -->
    <div class="main-content">
      <section id="opportunity-grid" class="opportunity-grid">
        <!-- Cards rendered here -->
      </section>
    </div>
  </main>
</div>
``` 