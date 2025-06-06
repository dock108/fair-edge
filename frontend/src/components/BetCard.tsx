import { useState } from 'react';
import type { BetCardProps } from '../types';

export const BetCard = ({ opportunity, index }: BetCardProps) => {
  // State for collapsible odds
  const [showOdds, setShowOdds] = useState(false);

  // Get EV classification class
  const getEvClass = (classification: string) => {
    switch (classification) {
      case 'positive': return 'ev-positive';
      case 'high': return 'ev-high';
      case 'excellent': return 'ev-excellent';
      default: return 'ev-neutral';
    }
  };

  // Calculate fee-adjusted odds for P2P platforms (2% fee)
  const calculateFeeAdjustedOdds = (odds: string): string => {
    if (!odds) return odds;
    
    const isNegative = odds.startsWith('-');
    const isPositive = odds.startsWith('+');
    const oddsNumber = parseInt(odds.replace(/[+-]/, ''));
    
    if (isNegative) {
      // For negative odds, add 2% to the absolute value (making it worse)
      const adjustedOdds = Math.round(oddsNumber * 1.02);
      return `-${adjustedOdds}`;
    } else if (isPositive || !isNaN(oddsNumber)) {
      // For positive odds, subtract 2% (making it worse)
      const adjustedOdds = Math.round(oddsNumber * 0.98);
      return `+${adjustedOdds}`;
    }
    
    return odds;
  };

  // Get recommended P2P platform based on best available odds
  const getRecommendedP2P = () => {
    if (!opportunity.available_odds) return 'Novig';
    
    const novigOdds = opportunity.available_odds.find(o => o.bookmaker.toLowerCase() === 'novig');
    const prophetxOdds = opportunity.available_odds.find(o => o.bookmaker.toLowerCase() === 'prophetx');
    
    if (!novigOdds && !prophetxOdds) return 'Novig';
    if (!prophetxOdds) return 'Novig';
    if (!novigOdds) return 'ProphetX';
    
    // Compare which is closer to the recommended posting odds
    const recOdds = opportunity.recommended_posting_odds;
    if (!recOdds) return 'Novig';
    
    const recNumber = parseInt(recOdds.replace(/[+-]/, ''));
    const novigNumber = parseInt(novigOdds.odds.replace(/[+-]/, ''));
    const prophetxNumber = parseInt(prophetxOdds.odds.replace(/[+-]/, ''));
    
    const novigDiff = Math.abs(novigNumber - recNumber);
    const prophetxDiff = Math.abs(prophetxNumber - recNumber);
    
    return novigDiff <= prophetxDiff ? 'Novig' : 'ProphetX';
  };

  // Sort odds properly (best to worst)
  const sortedOdds = opportunity.available_odds ? [...opportunity.available_odds].sort((a, b) => {
    const aIsNegative = a.odds.startsWith('-');
    const bIsNegative = b.odds.startsWith('-');
    const aNumber = parseInt(a.odds.replace(/[+-]/, ''));
    const bNumber = parseInt(b.odds.replace(/[+-]/, ''));
    
    // For negative odds, smaller absolute value is better
    if (aIsNegative && bIsNegative) {
      return aNumber - bNumber;
    }
    // For positive odds, larger value is better
    if (!aIsNegative && !bIsNegative) {
      return bNumber - aNumber;
    }
    // Positive odds are generally better than negative
    if (!aIsNegative && bIsNegative) return -1;
    if (aIsNegative && !bIsNegative) return 1;
    
    return 0;
  }) : [];

  const recommendedP2P = getRecommendedP2P();
  const p2pPostLink = recommendedP2P === 'ProphetX' 
    ? 'https://prophetx.com/exchange' 
    : 'https://novig.com/exchange';

  return (
    <div className={`odds-card ${getEvClass(opportunity.ev_classification)}`} id={`card-${index}`}>
      <div className="odds-card__header">
        <h2 className="odds-card__event">{opportunity.event}</h2>
        <span className="odds-card__description">{opportunity.bet_description}</span>
      </div>

      {/* Additional Details */}
      <div className="odds-card__details">
        {opportunity.fair_odds && (
          <div className="detail-row">
            <span className="detail-label">Fair Odds:</span>
            <span className="detail-value">{opportunity.fair_odds}</span>
          </div>
        )}

        {opportunity.best_available_odds && (
          <div className="detail-row">
            <span className="detail-label">Best Available:</span>
            <span className="detail-value">{opportunity.best_available_odds}</span>
          </div>
        )}

        {opportunity.ev_percentage !== undefined && (
          <div className="detail-row">
            <span className="detail-label">Expected Value:</span>
            <span className={`detail-value ev-value ${getEvClass(opportunity.ev_classification)}`}>
              {opportunity.ev_percentage > 0 ? '+' : ''}{opportunity.ev_percentage.toFixed(2)}%
            </span>
          </div>
        )}
      </div>

      {/* Recommended P2P Posting Section - moved below EV */}
      {opportunity.recommended_posting_odds && (
        <div className="odds-card__recommended" id={`card-${index}-recommended`}>
          <div className="recommended-title">
            <i className="fas fa-star me-1"></i>
            Recommended Posting Price on P2P
          </div>
          <div className="recommended-row">
            <div className="recommended-odds">
              <span className="odds-value">
                {opportunity.recommended_posting_odds}
              </span>
              <span className="odds-book">
                on {recommendedP2P}
              </span>
            </div>
            <div className="odds-card__action">
              <a 
                href={p2pPostLink}
                target="_blank"
                rel="noopener noreferrer" 
                className="btn btn-warning btn-sm"
              >
                <i className="fas fa-plus-circle me-1"></i>
                Post Bet
              </a>
            </div>
          </div>
        </div>
      )}

      {/* Collapsible Odds Comparison */}
      {sortedOdds.length > 0 && (
        <div className="odds-comparison">
          <button 
            className="btn btn-link p-0 comparison-title-button"
            onClick={() => setShowOdds(!showOdds)}
            type="button"
          >
            <h4 className="comparison-title mb-0">
              Available Odds ({sortedOdds.length})
              <i className={`fas fa-chevron-${showOdds ? 'up' : 'down'} ms-2`}></i>
            </h4>
          </button>
          
          {showOdds && (
            <div className="comparison-list mt-2">
              {sortedOdds.map((bookmaker, idx) => {
                const isP2P = ['novig', 'prophetx'].includes(bookmaker.bookmaker.toLowerCase());
                const displayOdds = isP2P 
                  ? `${bookmaker.odds} (${calculateFeeAdjustedOdds(bookmaker.odds)})`
                  : bookmaker.odds;
                
                return (
                  <div key={idx} className="comparison-item">
                    <span className="sportsbook-name">{bookmaker.bookmaker}</span>
                    <span className="sportsbook-odds">{displayOdds}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}; 