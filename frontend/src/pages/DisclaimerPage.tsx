import React from 'react';

const DisclaimerPage: React.FC = () => {
  return (
    <div className="disclaimer-page">
      <div className="disclaimer-container">
        {/* Header */}
        <header className="disclaimer-header">
          <h1 className="disclaimer-title">⚠️ Important Disclaimer</h1>
          <p className="disclaimer-subtitle">Sports Betting +EV Analyzer - Terms & Risk Disclosure</p>
        </header>

        {/* Main Warning */}
        <div className="warning-box">
          <div className="warning-title">🚨 GAMBLING INVOLVES SUBSTANTIAL RISK</div>
          <p>This tool provides analysis for entertainment and educational purposes only. <span className="highlight">Gambling can result in significant financial losses</span> and should never be undertaken with money you cannot afford to lose.</p>
        </div>

        {/* Purpose & Limitations */}
        <section className="disclaimer-section">
          <h2 className="section-title">🎯 Purpose & Limitations</h2>
          <div className="disclaimer-content">
            <p>The Sports Betting +EV Analyzer is designed to:</p>
            <div className="risk-list">
              <ul>
                <li><strong>Provide educational analysis</strong> of betting market inefficiencies</li>
                <li><strong>Display mathematical calculations</strong> of expected value (EV)</li>
                <li><strong>Aggregate odds data</strong> from multiple sources for comparison</li>
                <li><strong>Demonstrate analytical techniques</strong> used in sports betting research</li>
              </ul>
            </div>
            <p><strong>This tool does NOT:</strong></p>
            <div className="risk-list">
              <ul>
                <li>Guarantee profits or positive outcomes</li>
                <li>Provide investment or financial advice</li>
                <li>Account for all market factors that may affect outcomes</li>
                <li>Replace professional gambling counseling or support</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Legal Considerations */}
        <section className="disclaimer-section">
          <h2 className="section-title">⚖️ Legal Considerations</h2>
          <div className="disclaimer-content">
            <p><strong>Age Requirement:</strong> You must be <span className="highlight">21 years or older</span> (or the legal gambling age in your jurisdiction) to use sports betting services.</p>
            
            <p><strong>Jurisdictional Compliance:</strong> Sports betting laws vary by location. It is your responsibility to ensure that:</p>
            <div className="risk-list">
              <ul>
                <li>Sports betting is legal in your jurisdiction</li>
                <li>You comply with all local, state, and federal laws</li>
                <li>You understand the tax implications of any winnings</li>
                <li>You use only licensed and regulated betting platforms</li>
              </ul>
            </div>
            
            <div className="legal-text">
              <p><em>This application does not facilitate betting transactions and is not affiliated with any gambling operators. All betting activities are conducted through third-party platforms subject to their own terms and conditions.</em></p>
            </div>
          </div>
        </section>

        {/* Data & Analysis Disclaimers */}
        <section className="disclaimer-section">
          <h2 className="section-title">📊 Data & Analysis Disclaimers</h2>
          <div className="disclaimer-content">
            <p><strong>Data Accuracy:</strong> While we strive for accuracy, odds data may be:</p>
            <div className="risk-list">
              <ul>
                <li>Delayed or outdated</li>
                <li>Subject to rapid changes</li>
                <li>Different from live market conditions</li>
                <li>Incomplete or temporarily unavailable</li>
              </ul>
            </div>
            
            <p><strong>Analysis Limitations:</strong> Our calculations are based on mathematical models that:</p>
            <div className="risk-list">
              <ul>
                <li>Cannot predict actual game outcomes</li>
                <li>May not account for all relevant factors</li>
                <li>Are subject to market volatility and changes</li>
                <li>Assume rational market behavior (which may not occur)</li>
              </ul>
            </div>
            
            <p><span className="highlight">Past performance does not guarantee future results.</span> Expected value calculations are theoretical and may not reflect actual betting outcomes.</p>
          </div>
        </section>

        {/* Risk Management */}
        <section className="disclaimer-section">
          <h2 className="section-title">🛡️ Risk Management</h2>
          <div className="disclaimer-content">
            <p>If you choose to engage in sports betting, please:</p>
            <div className="risk-list">
              <ul>
                <li><strong>Set strict limits</strong> on the amount you can afford to lose</li>
                <li><strong>Never chase losses</strong> with larger bets</li>
                <li><strong>Take regular breaks</strong> from betting activities</li>
                <li><strong>Seek help</strong> if gambling becomes problematic</li>
                <li><strong>Use bankroll management</strong> strategies appropriate to your situation</li>
                <li><strong>Consider the house edge</strong> and long-term statistical disadvantages</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Problem Gambling Resources */}
        <section className="disclaimer-section">
          <h2 className="section-title">🆘 Problem Gambling Resources</h2>
          <div className="disclaimer-content">
            <p>If you or someone you know has a gambling problem, help is available:</p>
            <div className="contact-info">
              <p><strong>National Problem Gambling Helpline:</strong> 1-800-522-4700</p>
              <p><strong>Online Resources:</strong></p>
              <ul>
                <li>National Council on Problem Gambling: <a href="https://www.ncpgambling.org" target="_blank" rel="noopener noreferrer">ncpgambling.org</a></li>
                <li>Gamblers Anonymous: <a href="https://www.gamblersanonymous.org" target="_blank" rel="noopener noreferrer">gamblersanonymous.org</a></li>
                <li>Responsible Gambling Council: <a href="https://www.responsiblegambling.org" target="_blank" rel="noopener noreferrer">responsiblegambling.org</a></li>
              </ul>
            </div>
          </div>
        </section>

        {/* Terms of Use */}
        <section className="disclaimer-section">
          <h2 className="section-title">📝 Terms of Use</h2>
          <div className="disclaimer-content">
            <p>By using this application, you acknowledge that:</p>
            <div className="risk-list">
              <ul>
                <li>You understand the risks associated with sports betting</li>
                <li>You will not hold the developers liable for any losses</li>
                <li>You will use this tool responsibly and legally</li>
                <li>You agree to these terms and applicable laws</li>
                <li>You understand this is for educational purposes only</li>
              </ul>
            </div>
            
            <div className="legal-text">
              <p><em>The developers, contributors, and hosts of this application disclaim all liability for any losses, damages, or negative outcomes resulting from the use of this tool or any betting activities undertaken based on its analysis.</em></p>
            </div>
          </div>
        </section>

        {/* Back Link */}
        <div className="disclaimer-footer">
          <a href="/" className="back-link">← Return to Dashboard</a>
        </div>
        
        <div className="legal-footer">
          <p>Last Updated: {new Date().toLocaleDateString()}</p>
          <p>Sports Betting +EV Analyzer v2.1.0</p>
        </div>
      </div>
    </div>
  );
};

export default DisclaimerPage; 