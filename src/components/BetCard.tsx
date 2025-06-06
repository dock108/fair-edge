import React from 'react';
import { BetCardProps } from '../types';

const BetCard: React.FC<BetCardProps> = ({ opportunity, index }) => {
  const handleBetClick = () => {
    if (opportunity.action_link) {
      window.open(opportunity.action_link, '_blank', 'noopener,noreferrer');
    }
  };

  return (
    <article 
      className={`odds-card ev-${opportunity.ev_classification}`} 
      role="listitem" 
      aria-labelledby={`card-${index}-title`}
      aria-describedby={`card-${index}-recommended`}
    >
      {/* Card Header */}
      <header className="odds-card__header">
        <h2 id={`card-${index}-title`} className="odds-card__title">
          {opportunity.event}
        </h2>
        <p className="odds-card__subtitle">
          {opportunity.bet_description}
        </p>
        {opportunity.sport && (
          <span className={`badge bg-secondary sport-badge`}>
            {opportunity.sport}
          </span>
        )}
      </header>

      {/* Card Body */}
      <div className="odds-card__body">
                {/* Recommended Odds Section */}
        {opportunity.recommended_posting_odds && (
          <div className="odds-card__recommended" id={`card-${index}-recommended`}>
            <div className="recommended-section">
              <h3 className="recommended-title">
                <i className="fas fa-star text-warning me-1"></i>
                Recommended
              </h3>
              <div className="recommended-odds">
                <span className="odds-value">
                  {opportunity.recommended_posting_odds}
                </span>
                <span className="odds-book">
                  at {opportunity.recommended_book}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Additional Details */}
        <div className="odds-card__details">
          {opportunity.bet_type && (
            <div className="detail-row">
              <span className="detail-label">Market:</span>
              <span className="detail-value">{opportunity.bet_type}</span>
            </div>
          )}
          
          <div className="detail-row">
            <span className="detail-label">Expected Value:</span>
            <span className={`detail-value ev-value ev-${opportunity.ev_classification}`}>
              {opportunity.ev_percentage > 0 ? '+' : ''}{opportunity.ev_percentage.toFixed(1)}%
            </span>
          </div>

          {opportunity.fair_odds && opportunity.fair_odds !== 'N/A' && (
            <div className="detail-row">
              <span className="detail-label">Fair Odds:</span>
              <span className="detail-value">{opportunity.fair_odds}</span>
            </div>
          )}
        </div>

        {/* Odds Comparison */}
        {opportunity.available_odds && opportunity.available_odds.length > 1 && (
          <div className="odds-comparison">
            <h4 className="comparison-title">Other Sportsbooks</h4>
            <div className="comparison-list">
              {opportunity.available_odds.slice(1).map((odds, idx) => (
                <div key={idx} className="comparison-item">
                  <span className="sportsbook-name">{odds.bookmaker}</span>
                  <span className="sportsbook-odds">{odds.odds}</span>
                  {odds.link && (
                    <a 
                      href={odds.link} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="btn btn-outline-primary btn-sm"
                    >
                      <i className="fas fa-external-link-alt me-1"></i>
                      Bet
                    </a>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Card Footer / Actions */}
      <footer className="odds-card__footer">
        {opportunity.available_odds && opportunity.available_odds[0] && (
          <button 
            onClick={handleBetClick}
            className="odds-card__action-btn btn btn-primary"
            title={`Place bet at ${opportunity.available_odds[0].sportsbook}`}
          >
            <i className="fas fa-external-link-alt me-1"></i>
            Bet Now at {opportunity.available_odds[0].sportsbook}
          </button>
        )}
        
        <div className="card-meta">
          <small className="text-muted">
            <i className="fas fa-chart-line me-1"></i>
            EV Classification: {opportunity.ev_classification.toUpperCase()}
          </small>
        </div>
      </footer>
    </article>
  );
};

export default BetCard; 