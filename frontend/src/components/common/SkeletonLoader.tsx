import React from 'react';

interface SkeletonLoaderProps {
  variant?: 'text' | 'rectangular' | 'circular' | 'card';
  width?: string | number;
  height?: string | number;
  lines?: number;
  className?: string;
  animate?: boolean;
}

/**
 * SkeletonLoader Component
 * 
 * Provides skeleton loading states that match the shape of content being loaded.
 * Creates a better perceived performance experience.
 */
export const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({
  variant = 'text',
  width = '100%',
  height,
  lines = 1,
  className = '',
  animate = true
}) => {
  const baseClasses = `bg-gray-200 ${animate ? 'animate-pulse' : ''}`;
  
  const getVariantClasses = () => {
    switch (variant) {
      case 'text':
        return 'rounded';
      case 'rectangular':
        return 'rounded-md';
      case 'circular':
        return 'rounded-full';
      case 'card':
        return 'rounded-lg';
      default:
        return 'rounded';
    }
  };

  const getDefaultHeight = () => {
    switch (variant) {
      case 'text':
        return '1rem';
      case 'rectangular':
        return '2rem';
      case 'circular':
        return width;
      case 'card':
        return '8rem';
      default:
        return '1rem';
    }
  };

  const finalHeight = height || getDefaultHeight();

  if (variant === 'text' && lines > 1) {
    return (
      <div className={className}>
        {Array.from({ length: lines }).map((_, index) => (
          <div
            key={index}
            className={`${baseClasses} ${getVariantClasses()} mb-2 last:mb-0`}
            style={{
              width: index === lines - 1 ? '75%' : width,
              height: finalHeight
            }}
          />
        ))}
      </div>
    );
  }

  return (
    <div
      className={`${baseClasses} ${getVariantClasses()} ${className}`}
      style={{ width, height: finalHeight }}
    />
  );
};

/**
 * OpportunityCardSkeleton Component
 * 
 * Skeleton specifically designed for betting opportunity cards
 */
export const OpportunityCardSkeleton: React.FC = () => {
  return (
    <div className="bg-white p-4 rounded-lg shadow-sm border animate-pulse">
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <SkeletonLoader variant="text" width="60%" height="1.25rem" className="mb-2" />
          <SkeletonLoader variant="text" width="80%" height="0.875rem" />
        </div>
        <SkeletonLoader variant="rectangular" width="4rem" height="2rem" />
      </div>
      
      <div className="grid grid-cols-3 gap-4 mb-3">
        <div>
          <SkeletonLoader variant="text" width="100%" height="0.75rem" className="mb-1" />
          <SkeletonLoader variant="text" width="70%" height="1rem" />
        </div>
        <div>
          <SkeletonLoader variant="text" width="100%" height="0.75rem" className="mb-1" />
          <SkeletonLoader variant="text" width="60%" height="1rem" />
        </div>
        <div>
          <SkeletonLoader variant="text" width="100%" height="0.75rem" className="mb-1" />
          <SkeletonLoader variant="text" width="80%" height="1rem" />
        </div>
      </div>
      
      <SkeletonLoader variant="text" width="40%" height="0.875rem" />
    </div>
  );
};

/**
 * DashboardSkeleton Component
 * 
 * Comprehensive skeleton for the main dashboard loading state
 */
export const DashboardSkeleton: React.FC = () => {
  return (
    <div className="main-container">
      <div className="animate-pulse">
        {/* Header section */}
        <div className="mb-6">
          <SkeletonLoader variant="text" width="300px" height="2rem" className="mb-2" />
          <SkeletonLoader variant="text" width="500px" height="1rem" />
        </div>

        {/* Filters section */}
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <div className="flex flex-wrap gap-4 items-center">
            <SkeletonLoader variant="rectangular" width="150px" height="2.5rem" />
            <SkeletonLoader variant="rectangular" width="120px" height="2.5rem" />
            <SkeletonLoader variant="rectangular" width="100px" height="2.5rem" />
            <SkeletonLoader variant="rectangular" width="80px" height="2.5rem" />
          </div>
        </div>

        {/* Stats cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {Array.from({ length: 3 }).map((_, index) => (
            <div key={index} className="bg-white p-4 rounded-lg shadow-sm border">
              <SkeletonLoader variant="text" width="80%" height="0.875rem" className="mb-2" />
              <SkeletonLoader variant="text" width="60%" height="1.5rem" />
            </div>
          ))}
        </div>

        {/* Opportunity cards */}
        <div className="space-y-4">
          {Array.from({ length: 5 }).map((_, index) => (
            <OpportunityCardSkeleton key={index} />
          ))}
        </div>
      </div>
    </div>
  );
};