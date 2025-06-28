import React from 'react';
import { Link } from 'react-router-dom';

/**
 * UpgradeSuccessPage Component
 * 
 * Displays a confirmation page after successful subscription upgrade.
 * Provides clear feedback to users about their new premium access.
 */
const UpgradeSuccessPage: React.FC = () => {
  return (
    <div className="main-container">
      <div className="text-center" style={{ padding: '4rem 2rem' }}>
        
        {/* Success Icon */}
        <div style={{ marginBottom: '2rem' }}>
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 mb-4">
            <svg 
              className="w-8 h-8 text-green-600" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M5 13l4 4L19 7" 
              />
            </svg>
          </div>
          <div className="text-4xl text-green-600 mb-4" role="img" aria-label="Crown icon">
            👑
          </div>
        </div>

        {/* Success Message */}
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Welcome to Premium!
        </h1>
        
        <p className="text-lg text-gray-600 mb-8 max-w-2xl mx-auto">
          Your subscription is now active. You have access to all premium features including 
          player props, alternate lines, and advanced analytics.
        </p>

        {/* Feature Highlights */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 max-w-4xl mx-auto">
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="text-blue-600 text-2xl mb-3">📊</div>
            <h3 className="font-semibold text-gray-900 mb-2">Advanced Analytics</h3>
            <p className="text-sm text-gray-600">
              Access detailed market analysis and trends
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="text-purple-600 text-2xl mb-3">🎯</div>
            <h3 className="font-semibold text-gray-900 mb-2">Player Props</h3>
            <p className="text-sm text-gray-600">
              Unlock player prop betting opportunities
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="text-green-600 text-2xl mb-3">💾</div>
            <h3 className="font-semibold text-gray-900 mb-2">Data Export</h3>
            <p className="text-sm text-gray-600">
              Export raw data for your own analysis
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <Link 
            to="/" 
            className="btn btn-primary inline-flex items-center px-6 py-3 text-white bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors"
          >
            <svg 
              className="w-5 h-5 mr-2" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" 
              />
            </svg>
            View Premium Opportunities
          </Link>
          
          <Link 
            to="/education" 
            className="btn btn-outline inline-flex items-center px-6 py-3 text-blue-600 border border-blue-600 hover:bg-blue-50 rounded-lg font-medium transition-colors"
          >
            <svg 
              className="w-5 h-5 mr-2" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" 
              />
            </svg>
            Learn Premium Features
          </Link>
        </div>

        {/* Support Information */}
        <div className="mt-12 p-6 bg-gray-50 rounded-lg max-w-2xl mx-auto">
          <h3 className="font-semibold text-gray-900 mb-2">Need Help Getting Started?</h3>
          <p className="text-sm text-gray-600 mb-4">
            Check out our education section to learn how to maximize your premium features, 
            or contact support if you have any questions.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link 
              to="/education" 
              className="text-blue-600 hover:text-blue-700 text-sm font-medium"
            >
              View Tutorials →
            </Link>
            <span className="hidden sm:inline text-gray-400">•</span>
            <a 
              href="mailto:support@fair-edge.com" 
              className="text-blue-600 hover:text-blue-700 text-sm font-medium"
            >
              Contact Support →
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UpgradeSuccessPage;