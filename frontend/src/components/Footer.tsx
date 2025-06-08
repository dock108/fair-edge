import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="site-footer">
      <div className="footer-container">
        <div className="footer-content">
          <div className="footer-section">
            <div className="footer-logo">
              <img src="/icons/fairedge_logo_64.png" alt="FairEdge logo" className="footer-brand-logo" />
              <span className="footer-brand-text">FairEdge</span>
            </div>
            <p className="footer-description">
              Advanced sports betting analytics for profitable decision-making.
            </p>
          </div>
          
          <div className="footer-section">
            <h4 className="footer-title">Quick Links</h4>
            <ul className="footer-links">
              <li><a href="/">Dashboard</a></li>
              <li><a href="/education">Education</a></li>
              <li><a href="/pricing">Pricing</a></li>
              <li><a href="/disclaimer">Disclaimer</a></li>
            </ul>
          </div>
          
          <div className="footer-section">
            <h4 className="footer-title">Support</h4>
            <div className="support-info">
              <div className="support-item">
                <i className="fas fa-envelope"></i>
                <div>
                  <strong>Technical Support</strong>
                  <a href="mailto:support@fairedge.com" className="support-email">
                    support@fairedge.com
                  </a>
                </div>
              </div>
              <div className="support-item">
                <i className="fas fa-question-circle"></i>
                <div>
                  <strong>General Inquiries</strong>
                  <span className="support-note">Access, billing, or site issues</span>
                </div>
              </div>
              <div className="support-item">
                <i className="fas fa-clock"></i>
                <div>
                  <strong>Response Time</strong>
                  <span className="support-note">Within 24 hours</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div className="footer-bottom">
          <div className="footer-legal">
            <p>&copy; 2024 FairEdge. All rights reserved.</p>
            <p className="footer-disclaimer">
              Gambling involves risk. Please bet responsibly and within your means.
            </p>
          </div>
          <div className="footer-version">
            <span className="version-tag">v1.0</span>
          </div>
        </div>
      </div>
    </footer>
  );
}; 