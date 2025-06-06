import React from 'react';
import { Link } from 'react-router-dom';

interface PremiumPromptProps {
  featureName?: string;
  children?: React.ReactNode;
}

export const PremiumPrompt: React.FC<PremiumPromptProps> = ({ 
  featureName = "this feature", 
  children 
}) => {
  return (
    <div className="premium-prompt" style={{
      background: 'linear-gradient(135deg, var(--brand-50) 0%, var(--brand-100) 100%)',
      border: '1px solid var(--brand-200)',
      borderRadius: 'var(--radius-lg)',
      padding: 'var(--space-6)',
      textAlign: 'center',
      margin: 'var(--space-4) 0'
    }}>
      <div className="premium-icon" style={{ marginBottom: 'var(--space-4)' }}>
        <i className="fas fa-crown" style={{ 
          fontSize: '2rem', 
          color: 'var(--brand-600)',
          filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.1))'
        }}></i>
      </div>
      
      <h3 style={{ 
        color: 'var(--brand-700)', 
        marginBottom: 'var(--space-3)',
        fontSize: '1.25rem',
        fontWeight: '600'
      }}>
        Premium Feature
      </h3>
      
      <p style={{ 
        color: 'var(--brand-600)', 
        marginBottom: 'var(--space-5)',
        lineHeight: '1.5'
      }}>
        {children || `Upgrade to Premium Access to unlock ${featureName} including player props, alternate lines, and advanced analytics.`}
      </p>
      
      <div style={{ 
        display: 'flex', 
        gap: 'var(--space-3)', 
        justifyContent: 'center',
        flexWrap: 'wrap'
      }}>
        <Link 
          to="/pricing" 
          className="btn btn-primary"
          style={{ textDecoration: 'none' }}
        >
          <i className="fas fa-star" style={{ marginRight: 'var(--space-2)' }}></i>
          Upgrade to Premium
        </Link>
        
        <Link 
          to="/login" 
          className="btn btn-outline"
          style={{ textDecoration: 'none' }}
        >
          Sign In
        </Link>
      </div>
      
      <div style={{ 
        marginTop: 'var(--space-4)',
        fontSize: '0.875rem',
        color: 'var(--brand-500)'
      }}>
        <i className="fas fa-info-circle" style={{ marginRight: 'var(--space-1)' }}></i>
        7-day free trial • Cancel anytime
      </div>
    </div>
  );
};

export default PremiumPrompt; 
 
 