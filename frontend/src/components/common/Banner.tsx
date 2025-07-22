import React from 'react';

export type BannerVariant = 'info' | 'success' | 'warning' | 'error' | 'premium' | 'upgrade';

interface BannerProps {
  variant?: BannerVariant;
  title?: string;
  children: React.ReactNode;
  icon?: string;
  action?: {
    text: string;
    href?: string;
    onClick?: () => void;
    variant?: 'primary' | 'secondary' | 'outline';
  };
  dismissible?: boolean;
  onDismiss?: () => void;
  className?: string;
}

/**
 * Banner Component
 *
 * A unified component for displaying various types of messages and notifications
 * across the application with consistent styling and behavior.
 */
export const Banner: React.FC<BannerProps> = ({
  variant = 'info',
  title,
  children,
  icon,
  action,
  dismissible = false,
  onDismiss,
  className = ''
}) => {
  const getVariantStyles = () => {
    const styles = {
      info: {
        background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, rgba(16, 185, 129, 0.08) 100%)',
        border: '1px solid rgba(59, 130, 246, 0.2)',
        titleColor: '#1e40af',
        textColor: '#374151',
        iconColor: '#3b82f6'
      },
      success: {
        background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.08) 0%, rgba(16, 185, 129, 0.08) 100%)',
        border: '1px solid rgba(34, 197, 94, 0.2)',
        titleColor: '#059669',
        textColor: '#374151',
        iconColor: '#10b981'
      },
      warning: {
        background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(251, 191, 36, 0.1) 100%)',
        border: '1px solid rgba(245, 158, 11, 0.3)',
        titleColor: '#d97706',
        textColor: '#92400e',
        iconColor: '#f59e0b'
      },
      error: {
        background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.08) 0%, rgba(220, 38, 38, 0.08) 100%)',
        border: '1px solid rgba(239, 68, 68, 0.2)',
        titleColor: '#dc2626',
        textColor: '#991b1b',
        iconColor: '#ef4444'
      },
      premium: {
        background: 'linear-gradient(135deg, var(--brand-50) 0%, var(--brand-100) 100%)',
        border: '1px solid var(--brand-200)',
        titleColor: 'var(--brand-700)',
        textColor: 'var(--brand-600)',
        iconColor: 'var(--brand-600)'
      },
      upgrade: {
        background: 'linear-gradient(135deg, rgba(147, 51, 234, 0.08) 0%, rgba(79, 70, 229, 0.08) 100%)',
        border: '1px solid rgba(147, 51, 234, 0.2)',
        titleColor: '#7c3aed',
        textColor: '#5b21b6',
        iconColor: '#8b5cf6'
      }
    };
    return styles[variant];
  };

  const getDefaultIcon = () => {
    const icons = {
      info: 'fas fa-info-circle',
      success: 'fas fa-check-circle',
      warning: 'fas fa-exclamation-triangle',
      error: 'fas fa-exclamation-circle',
      premium: 'fas fa-crown',
      upgrade: 'fas fa-star'
    };
    return icons[variant];
  };

  const getActionButtonStyle = () => {
    if (!action) return {};

    const actionVariant = action.variant || 'primary';
    const variantStyles = getVariantStyles();

    if (actionVariant === 'primary') {
      return {
        background: variant === 'premium' || variant === 'upgrade'
          ? 'linear-gradient(135deg, #3b82f6 0%, #10b981 100%)'
          : variantStyles.iconColor,
        color: 'white',
        border: 'none'
      };
    } else if (actionVariant === 'outline') {
      return {
        background: 'transparent',
        color: variantStyles.titleColor,
        border: `1px solid ${variantStyles.titleColor}`
      };
    }

    return {
      background: 'rgba(255, 255, 255, 0.9)',
      color: variantStyles.titleColor,
      border: `1px solid ${variantStyles.titleColor}`
    };
  };

  const variantStyles = getVariantStyles();
  const iconClass = icon || getDefaultIcon();

  return (
    <div
      className={`rounded-md p-4 mb-4 d-flex align-items-center justify-content-between flex-wrap gap-2 ${className}`}
      style={{
        background: variantStyles.background,
        border: variantStyles.border
      }}
      role={variant === 'error' ? 'alert' : 'status'}
      aria-live={variant === 'error' ? 'assertive' : 'polite'}
    >
      <div className="d-flex align-items-start gap-3 flex-1" style={{ minWidth: '300px' }}>
        {iconClass && (
          <i
            className={iconClass}
            style={{
              color: variantStyles.iconColor,
              fontSize: '1.1rem',
              marginTop: '2px',
              flexShrink: 0
            }}
          />
        )}

        <div className="flex-1">
          {title && (
            <div
              className="fw-bold mb-1"
              style={{
                color: variantStyles.titleColor,
                fontSize: '0.95rem'
              }}
            >
              {title}
            </div>
          )}

          <div
            style={{
              color: variantStyles.textColor,
              fontSize: title ? '0.85rem' : '0.95rem',
              lineHeight: '1.4'
            }}
          >
            {children}
          </div>
        </div>
      </div>

      <div className="d-flex align-items-center gap-2">
        {action && (
          <a
            href={action.href}
            onClick={action.onClick}
            className="btn btn-sm text-decoration-none"
            style={{
              ...getActionButtonStyle(),
              padding: '8px 16px',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.85rem',
              fontWeight: '500',
              whiteSpace: 'nowrap',
              transition: 'all 0.2s ease',
              ...(!action.href ? { cursor: 'pointer' } : {})
            }}
          >
            {action.text}
          </a>
        )}

        {dismissible && (
          <button
            onClick={onDismiss}
            className="btn btn-sm p-1"
            style={{
              background: 'transparent',
              border: 'none',
              color: variantStyles.textColor,
              opacity: 0.7,
              fontSize: '0.875rem'
            }}
            aria-label="Dismiss banner"
          >
            <i className="fas fa-times" />
          </button>
        )}
      </div>
    </div>
  );
};
