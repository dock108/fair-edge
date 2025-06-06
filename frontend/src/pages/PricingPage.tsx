import React, { useState } from 'react';

const PricingPage: React.FC = () => {
  const [openFaqIndex, setOpenFaqIndex] = useState<number | null>(null);

  const toggleFaq = (index: number) => {
    setOpenFaqIndex(openFaqIndex === index ? null : index);
  };

  return (
    <div className="pricing-page">
      <div className="pricing-container">
        {/* Header */}
        <div className="pricing-header">
          <h1 className="pricing-title">Choose Your Plan</h1>
          <p className="pricing-subtitle">Get the betting insights you need to make informed decisions</p>
        </div>

        {/* Pricing Cards */}
        <div className="pricing-cards">
          {/* Free Tier */}
          <div className="pricing-card">
            <div className="pricing-card-header">
              <h3 className="plan-title">Free</h3>
              <p className="plan-subtitle">Main Lines Only</p>
              <div className="price">
                <span className="price-amount">$0</span>
                <span className="price-period">/month</span>
              </div>
            </div>
            <div className="pricing-card-body">
              <ul className="features-list">
                <li className="feature-item">
                  <i className="fas fa-check feature-icon"></i>
                  <strong>Main lines:</strong> Moneyline, Spreads, Totals
                </li>
                <li className="feature-item">
                  <i className="fas fa-check feature-icon"></i>
                  Basic EV analysis
                </li>
                <li className="feature-item">
                  <i className="fas fa-check feature-icon"></i>
                  5-minute data refresh
                </li>
                <li className="feature-item">
                  <i className="fas fa-check feature-icon"></i>
                  Educational resources
                </li>
                <li className="feature-item">
                  <i className="fas fa-check feature-icon"></i>
                  Search and filter tools
                </li>
                <li className="feature-item disabled">
                  <i className="fas fa-times feature-icon"></i>
                  <span>No player props</span>
                </li>
                <li className="feature-item disabled">
                  <i className="fas fa-times feature-icon"></i>
                  <span>No alternate lines</span>
                </li>
                <li className="feature-item disabled">
                  <i className="fas fa-times feature-icon"></i>
                  <span>No advanced analytics</span>
                </li>
              </ul>
            </div>
            <div className="pricing-card-footer">
              <a href="/login" className="btn btn-outline">
                Get Started Free
              </a>
            </div>
          </div>

          {/* Premium Tier */}
          <div className="pricing-card premium">
            <div className="popular-badge">Most Popular</div>
            <div className="pricing-card-header">
              <h3 className="plan-title">Premium Access</h3>
              <p className="plan-subtitle">All Markets + Advanced Features</p>
              <div className="price">
                <span className="price-amount">$4.99</span>
                <span className="price-period">/month</span>
              </div>
            </div>
            <div className="pricing-card-body">
              <ul className="features-list">
                <li className="feature-item">
                  <i className="fas fa-check feature-icon"></i>
                  <strong>Main lines:</strong> Moneyline, Spreads, Totals
                </li>
                <li className="feature-item">
                  <i className="fas fa-star feature-icon"></i>
                  <strong>Player props:</strong> Points, Assists, Rebounds, etc.
                </li>
                <li className="feature-item">
                  <i className="fas fa-star feature-icon"></i>
                  <strong>Alternate lines:</strong> Spreads, Totals variations
                </li>
                <li className="feature-item">
                  <i className="fas fa-star feature-icon"></i>
                  <strong>Live markets:</strong> In-game betting opportunities
                </li>
                <li className="feature-item">
                  <i className="fas fa-star feature-icon"></i>
                  Advanced EV analysis
                </li>
                <li className="feature-item">
                  <i className="fas fa-star feature-icon"></i>
                  Export capabilities
                </li>
                <li className="feature-item">
                  <i className="fas fa-star feature-icon"></i>
                  Priority customer support
                </li>
                <li className="feature-item">
                  <i className="fas fa-star feature-icon"></i>
                  7-day free trial
                </li>
              </ul>
            </div>
            <div className="pricing-card-footer">
              <button className="btn btn-primary" onClick={() => alert('Premium upgrade functionality will be available soon. Please contact support for early access.')}>
                Start Free Trial
              </button>
              <small className="trial-note">7-day free trial • Credit card required • Cancel anytime</small>
            </div>
          </div>
        </div>

        {/* Feature Comparison */}
        <div className="feature-comparison">
          <h3 className="comparison-title">Feature Comparison</h3>
          <div className="comparison-table-container">
            <table className="comparison-table">
              <thead>
                <tr>
                  <th>Feature</th>
                  <th>Free</th>
                  <th>Premium Access</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Main Lines (Moneyline, Spreads, Totals)</td>
                  <td><i className="fas fa-check text-success"></i></td>
                  <td><i className="fas fa-check text-success"></i></td>
                </tr>
                <tr>
                  <td>Player Props</td>
                  <td><i className="fas fa-times text-muted"></i></td>
                  <td><i className="fas fa-check text-success"></i></td>
                </tr>
                <tr>
                  <td>Alternate Lines</td>
                  <td><i className="fas fa-times text-muted"></i></td>
                  <td><i className="fas fa-check text-success"></i></td>
                </tr>
                <tr>
                  <td>Live Markets</td>
                  <td><i className="fas fa-times text-muted"></i></td>
                  <td><i className="fas fa-check text-success"></i></td>
                </tr>
                <tr>
                  <td>Data Refresh Rate</td>
                  <td>5 minutes</td>
                  <td>5 minutes</td>
                </tr>
                <tr>
                  <td>Advanced Analytics</td>
                  <td><i className="fas fa-times text-muted"></i></td>
                  <td><i className="fas fa-check text-success"></i></td>
                </tr>
                <tr>
                  <td>Export Capabilities</td>
                  <td><i className="fas fa-times text-muted"></i></td>
                  <td><i className="fas fa-check text-success"></i></td>
                </tr>
                <tr>
                  <td>Support Level</td>
                  <td>Community</td>
                  <td>Email Priority</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* FAQ Section */}
        <div className="faq-section">
          <h3 className="faq-title">Frequently Asked Questions</h3>
          <div className="faq-container">
            {[
              {
                question: "Can I cancel my subscription anytime?",
                answer: "Yes, you can cancel your subscription at any time. Your access will continue until the end of your current billing period."
              },
              {
                question: "Is there a free trial for Premium Access?",
                answer: "Yes! We offer a 7-day free trial for Premium Access. A credit card is required to start your trial, but you won't be charged until after the trial period ends."
              },
              {
                question: "What's the difference between Free and Premium Access?",
                answer: "Free users get access to main betting lines (moneyline, spreads, totals). Premium subscribers get access to all markets including player props, alternate lines, and live markets, plus advanced analytics and export features."
              },
              {
                question: "How accurate are the EV calculations?",
                answer: "Our models are based on comprehensive market analysis and statistical modeling. While we strive for accuracy, all betting involves risk and no system guarantees profits."
              },
              {
                question: "Is this for educational purposes only?",
                answer: "Yes, our platform is designed for educational and research purposes to help users understand betting markets and EV analysis. Always gamble responsibly."
              }
            ].map((faq, index) => (
              <div key={index} className="faq-item">
                <div 
                  className="faq-question" 
                  onClick={() => toggleFaq(index)}
                  style={{ cursor: 'pointer' }}
                >
                  <h4>{faq.question}</h4>
                  <i className={`fas fa-chevron-${openFaqIndex === index ? 'up' : 'down'}`}></i>
                </div>
                <div className="faq-answer" style={{ display: openFaqIndex === index ? 'block' : 'none' }}>
                  <p>{faq.answer}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PricingPage; 