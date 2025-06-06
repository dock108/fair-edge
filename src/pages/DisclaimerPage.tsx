import React, { useEffect } from 'react';

const DisclaimerPage: React.FC = () => {
  useEffect(() => {
    document.title = 'Disclaimer & Risk Disclosure | Sports Betting +EV Analyzer';
  }, []);

  return (
    <div className="content-wrap">
      <div className="disclaimer-container">
        
        {/* Header */}
        <header className="disclaimer-header text-center py-5">
          <h1 className="disclaimer-title">
            <i className="fas fa-exclamation-triangle text-warning me-3"></i>
            Disclaimer & Risk Disclosure
          </h1>
          <p className="disclaimer-subtitle lead text-muted">
            Important legal information and risk disclosures
          </p>
        </header>

        <div className="row justify-content-center">
          <div className="col-lg-10">
            
            {/* Educational Purpose */}
            <section className="disclaimer-section mb-5">
              <div className="card border-warning">
                <div className="card-header bg-warning text-dark">
                  <h2 className="card-title mb-0">
                    <i className="fas fa-graduation-cap me-2"></i>
                    Educational Purpose Only
                  </h2>
                </div>
                <div className="card-body">
                  <p className="card-text">
                    <strong>This tool is designed for educational and research purposes only.</strong> The Sports Betting +EV Analyzer 
                    provides mathematical analysis and market data to help users understand sports betting concepts, 
                    probability theory, and market efficiency. We do not encourage, promote, or facilitate gambling.
                  </p>
                  <div className="alert alert-warning">
                    <strong>Not Financial or Gambling Advice:</strong> Nothing on this platform constitutes financial advice, 
                    gambling advice, or recommendations to place bets. All information is provided for educational purposes only.
                  </div>
                </div>
              </div>
            </section>

            {/* Risk Disclosure */}
            <section className="disclaimer-section mb-5">
              <div className="card border-danger">
                <div className="card-header bg-danger text-white">
                  <h2 className="card-title mb-0">
                    <i className="fas fa-shield-alt me-2"></i>
                    Risk Disclosure
                  </h2>
                </div>
                <div className="card-body">
                  <h4>Gambling Involves Risk</h4>
                  <ul>
                    <li><strong>Financial Loss:</strong> Sports betting involves substantial risk of financial loss. Never bet more than you can afford to lose.</li>
                    <li><strong>No Guarantees:</strong> Past performance does not guarantee future results. Even positive expected value bets can lose.</li>
                    <li><strong>Addiction Risk:</strong> Gambling can be addictive. If you have a gambling problem, seek professional help immediately.</li>
                    <li><strong>Variance:</strong> Short-term results may vary significantly from mathematical expectations due to variance and luck.</li>
                  </ul>

                  <h4 className="mt-4">Mathematical Limitations</h4>
                  <ul>
                    <li><strong>Model Accuracy:</strong> Our models are based on available data and mathematical calculations, but they are not perfect.</li>
                    <li><strong>Market Changes:</strong> Odds and market conditions change rapidly. Information may become outdated quickly.</li>
                    <li><strong>External Factors:</strong> Injuries, weather, and other unforeseen events can affect outcomes regardless of mathematical analysis.</li>
                  </ul>
                </div>
              </div>
            </section>

            {/* Legal Compliance */}
            <section className="disclaimer-section mb-5">
              <div className="card">
                <div className="card-header">
                  <h2 className="card-title mb-0">
                    <i className="fas fa-gavel me-2"></i>
                    Legal Compliance
                  </h2>
                </div>
                <div className="card-body">
                  <h4>User Responsibility</h4>
                  <p>
                    It is your responsibility to ensure that your use of this tool and any related activities 
                    comply with all applicable laws and regulations in your jurisdiction. Sports betting laws 
                    vary significantly by location.
                  </p>

                  <h4>Age Restrictions</h4>
                  <p>
                    You must be at least 18 years old (or the legal age of majority in your jurisdiction) 
                    to use this service. We do not knowingly collect information from minors.
                  </p>

                  <h4>Prohibited Jurisdictions</h4>
                  <p>
                    This service may not be available in all jurisdictions. Users are responsible for 
                    determining whether their use of this service is legal in their location.
                  </p>
                </div>
              </div>
            </section>

            {/* Data Accuracy */}
            <section className="disclaimer-section mb-5">
              <div className="card">
                <div className="card-header">
                  <h2 className="card-title mb-0">
                    <i className="fas fa-database me-2"></i>
                    Data Accuracy & Reliability
                  </h2>
                </div>
                <div className="card-body">
                  <h4>Third-Party Data</h4>
                  <p>
                    Our analysis relies on odds data from third-party sources. While we strive for accuracy, 
                    we cannot guarantee the completeness, accuracy, or timeliness of this data.
                  </p>

                  <h4>Technical Issues</h4>
                  <p>
                    Technical issues, server downtime, or data feed interruptions may affect the availability 
                    and accuracy of information. We are not responsible for losses resulting from such issues.
                  </p>

                  <h4>User Verification</h4>
                  <p>
                    Users should always verify odds and information independently before making any decisions. 
                    Do not rely solely on our analysis.
                  </p>
                </div>
              </div>
            </section>

            {/* Limitation of Liability */}
            <section className="disclaimer-section mb-5">
              <div className="card">
                <div className="card-header">
                  <h2 className="card-title mb-0">
                    <i className="fas fa-balance-scale me-2"></i>
                    Limitation of Liability
                  </h2>
                </div>
                <div className="card-body">
                  <p>
                    <strong>To the maximum extent permitted by law, we disclaim all liability for any direct, 
                    indirect, incidental, special, or consequential damages arising from:</strong>
                  </p>
                  <ul>
                    <li>Use of this service or reliance on any information provided</li>
                    <li>Financial losses from gambling or betting activities</li>
                    <li>Technical issues, errors, or interruptions in service</li>
                    <li>Inaccurate or outdated information</li>
                    <li>Third-party actions or data</li>
                  </ul>
                  
                  <div className="alert alert-info mt-3">
                    <strong>Your use of this service is at your own risk.</strong> We provide this tool "as is" 
                    without any warranties, express or implied.
                  </div>
                </div>
              </div>
            </section>

            {/* Responsible Gambling */}
            <section className="disclaimer-section mb-5">
              <div className="card border-info">
                <div className="card-header bg-info text-white">
                  <h2 className="card-title mb-0">
                    <i className="fas fa-heart me-2"></i>
                    Responsible Gambling Resources
                  </h2>
                </div>
                <div className="card-body">
                  <p>
                    If you or someone you know has a gambling problem, help is available. Contact these resources:
                  </p>
                  
                  <div className="row">
                    <div className="col-md-6">
                      <h5>United States</h5>
                      <ul>
                        <li><strong>National Problem Gambling Helpline:</strong> 1-800-522-4700</li>
                        <li><strong>Gamblers Anonymous:</strong> <a href="https://www.gamblersanonymous.org" target="_blank" rel="noopener noreferrer">gamblersanonymous.org</a></li>
                        <li><strong>National Council on Problem Gambling:</strong> <a href="https://www.ncpgambling.org" target="_blank" rel="noopener noreferrer">ncpgambling.org</a></li>
                      </ul>
                    </div>
                    <div className="col-md-6">
                      <h5>International</h5>
                      <ul>
                        <li><strong>GamCare (UK):</strong> <a href="https://www.gamcare.org.uk" target="_blank" rel="noopener noreferrer">gamcare.org.uk</a></li>
                        <li><strong>Gambling Therapy:</strong> <a href="https://www.gamblingtherapy.org" target="_blank" rel="noopener noreferrer">gamblingtherapy.org</a></li>
                        <li><strong>BeGambleAware:</strong> <a href="https://www.begambleaware.org" target="_blank" rel="noopener noreferrer">begambleaware.org</a></li>
                      </ul>
                    </div>
                  </div>

                  <div className="alert alert-warning mt-3">
                    <strong>Warning Signs of Problem Gambling:</strong>
                    <ul className="mb-0 mt-2">
                      <li>Betting more than you can afford to lose</li>
                      <li>Chasing losses with bigger bets</li>
                      <li>Lying about gambling activities</li>
                      <li>Neglecting responsibilities due to gambling</li>
                      <li>Feeling anxious or depressed about gambling</li>
                    </ul>
                  </div>
                </div>
              </div>
            </section>

            {/* Contact Information */}
            <section className="disclaimer-section mb-5">
              <div className="card">
                <div className="card-header">
                  <h2 className="card-title mb-0">
                    <i className="fas fa-envelope me-2"></i>
                    Contact & Updates
                  </h2>
                </div>
                <div className="card-body">
                  <p>
                    This disclaimer may be updated from time to time. Continued use of the service constitutes 
                    acceptance of any changes. For questions about this disclaimer, please contact us.
                  </p>
                  
                  <p className="text-muted">
                    <strong>Last Updated:</strong> {new Date().toLocaleDateString()}
                  </p>
                </div>
              </div>
            </section>

          </div>
        </div>
      </div>
    </div>
  );
};

export default DisclaimerPage; 