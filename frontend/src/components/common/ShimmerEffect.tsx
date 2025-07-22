import React from 'react';

interface ShimmerEffectProps {
  className?: string;
  children?: React.ReactNode;
}

/**
 * ShimmerEffect Component
 *
 * Provides a shimmer/wave effect that can be applied to any container.
 * Creates a more engaging loading experience with a moving gradient.
 */
export const ShimmerEffect: React.FC<ShimmerEffectProps> = ({
  className = '',
  children
}) => {
  return (
    <div className={`relative overflow-hidden ${className}`}>
      {children}
      <div className="absolute inset-0 -translate-x-full animate-[shimmer_2s_infinite] bg-gradient-to-r from-transparent via-white/60 to-transparent" />
    </div>
  );
};

/**
 * TableLoadingSkeleton Component
 *
 * Skeleton specifically for table/list loading states
 */
export const TableLoadingSkeleton: React.FC<{ rows?: number }> = ({ rows = 5 }) => {
  return (
    <div className="space-y-2">
      {Array.from({ length: rows }).map((_, index) => (
        <ShimmerEffect key={index} className="bg-gray-200 h-12 rounded">
          <div className="flex items-center space-x-4 p-3">
            <div className="w-8 h-8 bg-gray-300 rounded-full" />
            <div className="flex-1 space-y-2">
              <div className="h-3 bg-gray-300 rounded w-3/4" />
              <div className="h-2 bg-gray-300 rounded w-1/2" />
            </div>
            <div className="w-16 h-4 bg-gray-300 rounded" />
          </div>
        </ShimmerEffect>
      ))}
    </div>
  );
};

/**
 * CardGridSkeleton Component
 *
 * Skeleton for grid-based card layouts
 */
export const CardGridSkeleton: React.FC<{
  cards?: number;
  columns?: 1 | 2 | 3 | 4;
}> = ({
  cards = 6,
  columns = 3
}) => {
  const gridClass = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 md:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4'
  }[columns];

  return (
    <div className={`grid ${gridClass} gap-4`}>
      {Array.from({ length: cards }).map((_, index) => (
        <ShimmerEffect key={index} className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded w-3/4" />
            <div className="h-3 bg-gray-200 rounded w-full" />
            <div className="h-3 bg-gray-200 rounded w-5/6" />
            <div className="flex justify-between items-center pt-2">
              <div className="h-3 bg-gray-200 rounded w-1/3" />
              <div className="h-6 bg-gray-200 rounded w-16" />
            </div>
          </div>
        </ShimmerEffect>
      ))}
    </div>
  );
};

/**
 * InlineLoader Component
 *
 * Small loading indicator for inline use (buttons, form fields, etc.)
 */
export const InlineLoader: React.FC<{
  size?: 'xs' | 'sm' | 'md';
  text?: string;
  className?: string;
}> = ({
  size = 'sm',
  text,
  className = ''
}) => {
  const sizeClasses = {
    xs: 'w-3 h-3',
    sm: 'w-4 h-4',
    md: 'w-5 h-5'
  };

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <div className={`${sizeClasses[size]} border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin`} />
      {text && (
        <span className="text-sm text-gray-600">{text}</span>
      )}
    </div>
  );
};
