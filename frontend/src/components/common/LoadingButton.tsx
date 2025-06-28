import React from 'react';

interface LoadingButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  loading?: boolean;
  loadingText?: string;
  variant?: 'primary' | 'secondary' | 'outline' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
}

/**
 * LoadingButton Component
 * 
 * A button component with built-in loading state handling.
 * Automatically disables the button and shows a spinner when loading.
 */
export const LoadingButton: React.FC<LoadingButtonProps> = ({
  loading = false,
  loadingText,
  variant = 'primary',
  size = 'md',
  children,
  disabled,
  className = '',
  ...props
}) => {
  const baseClasses = 'btn d-flex align-items-center justify-content-center gap-2';
  
  const variantClasses = {
    primary: 'btn-primary',
    secondary: 'btn-secondary', 
    outline: 'btn-outline-primary',
    danger: 'btn-danger'
  };
  
  const sizeClasses = {
    sm: 'btn-sm',
    md: '',
    lg: 'btn-lg'
  };

  const buttonClasses = [
    baseClasses,
    variantClasses[variant],
    sizeClasses[size],
    className
  ].filter(Boolean).join(' ');

  return (
    <button
      {...props}
      className={buttonClasses}
      disabled={loading || disabled}
    >
      {loading && (
        <i className="fas fa-spinner fa-spin" style={{ fontSize: '0.875rem' }} />
      )}
      {loading ? (loadingText || children) : children}
    </button>
  );
};