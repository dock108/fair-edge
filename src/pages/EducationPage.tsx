import React, { useEffect } from 'react';

const EducationPage: React.FC = () => {
  useEffect(() => {
    document.title = 'Education - How Our Analysis Works | Sports Betting +EV Analyzer';
  }, []);

  return (
    <div className="content-wrap">
      <div className="education-container">
        <header className="education-header text-center py-5">
          <h1 className="education-title">
            <i className="fas fa-graduation-cap me-3"></i>
            How Our Analysis Works
          </h1>
          <p className="education-subtitle lead">
            Understanding Expected Value (EV) in Sports Betting
          </p>
        </header>

        <div className="row justify-content-center">
          <div className="col-lg-10">
            
            {/* Introduction Section */}
            <section className="education-section mb-5">
              <div className="card">
                <div className="card-body">
                  <h2 className="card-title">
                    <i className="fas fa-lightbulb text-warning me-2"></i>
                    What is Expected Value (EV)?
                  </h2>
                  <p className="card-text">
                    Expected Value is a mathematical concept that helps determine the long-term profitability 
                    of a bet. A positive EV (+EV) indicates that a bet is mathematically profitable over time, 
                    while a negative EV (-EV) suggests the bet will lose money in the long run.
                  </p>
                  <div className="alert alert-info">
                    <strong>Formula:</strong> EV = (Probability of Winning × Amount Won) - (Probability of Losing × Amount Lost)
                  </div>
                </div>
              </div>
            </section>

            {/* How We Calculate EV */}
            <section className="education-section mb-5">
              <div className="card">
                <div className="card-body">
                  <h2 className="card-title">
                    <i className="fas fa-calculator text-primary me-2"></i>
                    How We Calculate EV
                  </h2>
                  <div className="row">
                    <div className="col-md-6">
                      <h4>Step 1: Data Collection</h4>
                      <ul>
                        <li>Real-time odds from multiple sportsbooks</li>
                        <li>Historical performance data</li>
                        <li>Market movement analysis</li>
                        <li>Sharp money indicators</li>
                      </ul>
                    </div>
                    <div className="col-md-6">
                      <h4>Step 2: True Probability Estimation</h4>
                      <ul>
                        <li>Remove sportsbook margins (vig)</li>
                        <li>Weight odds by market efficiency</li>
                        <li>Apply statistical models</li>
                        <li>Account for market biases</li>
                      </ul>
                    </div>
                  </div>
                  <div className="mt-3">
                    <h4>Step 3: EV Calculation</h4>
                    <p>
                      We compare the true probability against the implied probability of each sportsbook's odds 
                      to identify discrepancies that represent betting value.
                    </p>
                  </div>
                </div>
              </div>
            </section>

            {/* EV Classifications */}
            <section className="education-section mb-5">
              <div className="card">
                <div className="card-body">
                  <h2 className="card-title">
                    <i className="fas fa-chart-line text-success me-2"></i>
                    EV Classifications
                  </h2>
                  <div className="row">
                    <div className="col-md-4">
                      <div className="ev-example ev-high p-3 rounded mb-3">
                        <h4 className="text-success">High EV (4.5%+)</h4>
                        <p>Excellent betting opportunities with significant edge over the market.</p>
                      </div>
                    </div>
                    <div className="col-md-4">
                      <div className="ev-example ev-medium p-3 rounded mb-3">
                        <h4 className="text-warning">Medium EV (2.5-4.4%)</h4>
                        <p>Good betting opportunities with moderate edge over the market.</p>
                      </div>
                    </div>
                    <div className="col-md-4">
                      <div className="ev-example ev-low p-3 rounded mb-3">
                        <h4 className="text-info">Low EV (0.1-2.4%)</h4>
                        <p>Small but positive edge opportunities for conservative bettors.</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Market Types */}
            <section className="education-section mb-5">
              <div className="card">
                <div className="card-body">
                  <h2 className="card-title">
                    <i className="fas fa-list text-info me-2"></i>
                    Market Types We Analyze
                  </h2>
                  <div className="row">
                    <div className="col-md-6">
                      <h4>Main Markets (Free Tier)</h4>
                      <ul>
                        <li><strong>Moneyline:</strong> Straight win/loss bets</li>
                        <li><strong>Point Spreads:</strong> Handicap betting</li>
                        <li><strong>Totals (Over/Under):</strong> Combined score bets</li>
                      </ul>
                    </div>
                    <div className="col-md-6">
                      <h4>Premium Markets (Subscribers)</h4>
                      <ul>
                        <li><strong>Player Props:</strong> Individual player statistics</li>
                        <li><strong>Team Props:</strong> Team-specific outcomes</li>
                        <li><strong>Alternative Lines:</strong> Non-standard spreads/totals</li>
                        <li><strong>Live Betting:</strong> In-game opportunities</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Risk Management */}
            <section className="education-section mb-5">
              <div className="card">
                <div className="card-body">
                  <h2 className="card-title">
                    <i className="fas fa-shield-alt text-danger me-2"></i>
                    Risk Management & Bankroll
                  </h2>
                  <div className="alert alert-warning">
                    <strong>Important:</strong> Even positive EV bets can lose. Proper bankroll management is crucial.
                  </div>
                  <div className="row">
                    <div className="col-md-6">
                      <h4>Kelly Criterion</h4>
                      <p>
                        A mathematical formula for determining optimal bet sizing based on your edge and bankroll.
                      </p>
                      <code>Bet Size = (bp - q) / b</code>
                      <small className="d-block mt-1">
                        Where: b = odds, p = win probability, q = lose probability
                      </small>
                    </div>
                    <div className="col-md-6">
                      <h4>General Guidelines</h4>
                      <ul>
                        <li>Never bet more than 5% of bankroll on single bet</li>
                        <li>Track all bets and results</li>
                        <li>Be prepared for losing streaks</li>
                        <li>Only bet what you can afford to lose</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Limitations */}
            <section className="education-section mb-5">
              <div className="card">
                <div className="card-body">
                  <h2 className="card-title">
                    <i className="fas fa-exclamation-triangle text-warning me-2"></i>
                    Limitations & Considerations
                  </h2>
                  <ul>
                    <li><strong>No Guarantee:</strong> EV is a long-term concept. Individual bets can still lose.</li>
                    <li><strong>Market Efficiency:</strong> Some markets are more efficient than others.</li>
                    <li><strong>Line Movement:</strong> Odds change rapidly; act quickly on identified opportunities.</li>
                    <li><strong>Betting Limits:</strong> Sportsbooks may limit successful bettors.</li>
                    <li><strong>Variance:</strong> Short-term results may not reflect long-term expectations.</li>
                  </ul>
                </div>
              </div>
            </section>

            {/* Educational Purpose */}
            <section className="education-section mb-5">
              <div className="card border-info">
                <div className="card-body">
                  <h2 className="card-title text-info">
                    <i className="fas fa-info-circle me-2"></i>
                    Educational Purpose Only
                  </h2>
                  <p className="card-text">
                    This tool is designed for educational purposes to help users understand sports betting 
                    mathematics and market analysis. We do not encourage gambling and recommend that users:
                  </p>
                  <ul>
                    <li>Only bet in jurisdictions where it's legal</li>
                    <li>Never bet more than they can afford to lose</li>
                    <li>Seek help if gambling becomes a problem</li>
                    <li>Use this information for research and learning</li>
                  </ul>
                  <div className="mt-3">
                    <a href="/disclaimer" className="btn btn-outline-info">
                      <i className="fas fa-file-alt me-1"></i>
                      Read Full Disclaimer
                    </a>
                  </div>
                </div>
              </div>
            </section>

          </div>
        </div>
      </div>
    </div>
  );
};

export default EducationPage; 