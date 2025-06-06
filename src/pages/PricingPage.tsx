import React, { useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import apiService from '../services/api';

const PricingPage: React.FC = () => {
  const { user, isSubscriber } = useAuth();

  useEffect(() => {
    document.title = 'Pricing Plans | Sports Betting +EV Analyzer';
  }, []);

  const handleUpgrade = async () => {
    try {
      if (!user) {
        window.location.href = '/login?intent=upgrade';
        return;
      }

      if (isSubscriber) {
        alert('You are already a Premium subscriber!');
        return;
      }

      const { checkout_url } = await apiService.createCheckoutSession();
      window.location.href = checkout_url;
    } catch (error) {
      console.error('Upgrade failed:', error);
      alert('Failed to start upgrade process. Please try again.');
    }
  };

  const handleManageBilling = async () => {
    try {
      const { portal_url } = await apiService.manageBilling();
      window.location.href = portal_url;
    } catch (error) {
      console.error('Manage billing failed:', error);
      alert('Failed to open billing portal. Please try again.');
    }
  };

  return (
    <div className="content-wrap">
      <div className="pricing-container">
        
        {/* Header Section */}
        <header className="pricing-header text-center py-5">
          <h1 className="pricing-title">
            <i className="fas fa-tags me-3"></i>
            Choose Your Plan
          </h1>
          <p className="pricing-subtitle lead">
            Get access to professional-grade sports betting analysis
          </p>
        </header>

        {/* Pricing Cards */}
        <div className="row justify-content-center">
          
          {/* Free Plan */}
          <div className="col-lg-5 col-md-6 mb-4">
            <div className="card h-100 border-secondary">
              <div className="card-header bg-light text-center">
                <h3 className="card-title mb-0">Free</h3>
                <p className="text-muted mb-0">Main Lines Only</p>
                <div className="mt-3">
                  <span className="display-4 fw-bold">$0</span>
                  <span className="text-muted">/month</span>
                </div>
              </div>
              <div className="card-body">
                <ul className="list-unstyled">
                  <li className="mb-3">
                    <i className="fas fa-check text-success me-2"></i>
                    <strong>Main lines:</strong> Moneyline, Spreads, Totals
                  </li>
                  <li className="mb-3">
                    <i className="fas fa-check text-success me-2"></i>
                    <strong>Real-time odds</strong> from major sportsbooks
                  </li>
                  <li className="mb-3">
                    <i className="fas fa-check text-success me-2"></i>
                    <strong>Expected Value (EV)</strong> calculations
                  </li>
                  <li className="mb-3">
                    <i className="fas fa-check text-success me-2"></i>
                    <strong>Basic filtering</strong> by sport and search
                  </li>
                  <li className="mb-3">
                    <i className="fas fa-check text-success me-2"></i>
                    <strong>Educational resources</strong> and guides
                  </li>
                  <li className="mb-3 text-muted">
                    <i className="fas fa-times text-muted me-2"></i>
                    Player props and alternative lines
                  </li>
                  <li className="mb-3 text-muted">
                    <i className="fas fa-times text-muted me-2"></i>
                    Live betting opportunities
                  </li>
                  <li className="mb-3 text-muted">
                    <i className="fas fa-times text-muted me-2"></i>
                    Advanced analytics and insights
                  </li>
                </ul>
              </div>
              <div className="card-footer text-center">
                <button className="btn btn-outline-secondary btn-lg w-100" disabled>
                  Current Plan
                </button>
                <small className="text-muted d-block mt-2">
                  Perfect for getting started
                </small>
              </div>
            </div>
          </div>

          {/* Premium Plan */}
          <div className="col-lg-5 col-md-6 mb-4">
            <div className="card h-100 border-warning shadow-lg">
              <div className="card-header bg-warning text-dark text-center position-relative">
                <div className="position-absolute top-0 start-50 translate-middle">
                  <span className="badge bg-danger rounded-pill px-3 py-2">
                    <i className="fas fa-star me-1"></i>MOST POPULAR
                  </span>
                </div>
                <h3 className="card-title mb-0 mt-3">Premium</h3>
                <p className="text-dark mb-0">All Markets + Analytics</p>
                <div className="mt-3">
                  <span className="display-4 fw-bold">$29</span>
                  <span className="text-dark">/month</span>
                </div>
                <small className="text-dark">
                  <s className="text-muted">$49/month</s> Limited time offer!
                </small>
              </div>
              <div className="card-body">
                <ul className="list-unstyled">
                  <li className="mb-3">
                    <i className="fas fa-check text-success me-2"></i>
                    <strong>Everything in Free</strong> plus:
                  </li>
                  <li className="mb-3">
                    <i className="fas fa-star text-warning me-2"></i>
                    <strong>Player props:</strong> Points, rebounds, assists, etc.
                  </li>
                  <li className="mb-3">
                    <i className="fas fa-star text-warning me-2"></i>
                    <strong>Team props:</strong> Team totals, first half lines
                  </li>
                  <li className="mb-3">
                    <i className="fas fa-star text-warning me-2"></i>
                    <strong>Alternative lines:</strong> Non-standard spreads/totals
                  </li>
                  <li className="mb-3">
                    <i className="fas fa-star text-warning me-2"></i>
                    <strong>Live betting:</strong> In-game opportunities
                  </li>
                  <li className="mb-3">
                    <i className="fas fa-star text-warning me-2"></i>
                    <strong>Advanced analytics:</strong> Market movement, sharp money
                  </li>
                  <li className="mb-3">
                    <i className="fas fa-star text-warning me-2"></i>
                    <strong>Priority support</strong> and feature requests
                  </li>
                  <li className="mb-3">
                    <i className="fas fa-star text-warning me-2"></i>
                    <strong>Export data:</strong> CSV downloads for tracking
                  </li>
                </ul>
              </div>
              <div className="card-footer text-center">
                {isSubscriber ? (
                  <div>
                    <button className="btn btn-success btn-lg w-100 mb-2" disabled>
                      <i className="fas fa-check me-2"></i>
                      Current Plan
                    </button>
                    <button 
                      onClick={handleManageBilling}
                      className="btn btn-outline-primary btn-sm w-100"
                    >
                      <i className="fas fa-credit-card me-1"></i>
                      Manage Billing
                    </button>
                  </div>
                ) : (
                  <button 
                    onClick={handleUpgrade}
                    className="btn btn-warning btn-lg w-100"
                  >
                    <i className="fas fa-rocket me-2"></i>
                    Upgrade to Premium
                  </button>
                )}
                <small className="text-muted d-block mt-2">
                  Cancel anytime • No long-term commitment
                </small>
              </div>
            </div>
          </div>
        </div>

        {/* Features Comparison */}
        <div className="row justify-content-center mt-5">
          <div className="col-lg-10">
            <div className="card">
              <div className="card-header">
                <h3 className="card-title mb-0">
                  <i className="fas fa-list-check me-2"></i>
                  Feature Comparison
                </h3>
              </div>
              <div className="card-body">
                <div className="table-responsive">
                  <table className="table table-striped">
                    <thead>
                      <tr>
                        <th>Feature</th>
                        <th className="text-center">Free</th>
                        <th className="text-center">Premium</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td>Main Lines (ML, Spreads, Totals)</td>
                        <td className="text-center"><i className="fas fa-check text-success"></i></td>
                        <td className="text-center"><i className="fas fa-check text-success"></i></td>
                      </tr>
                      <tr>
                        <td>Real-time Odds Updates</td>
                        <td className="text-center"><i className="fas fa-check text-success"></i></td>
                        <td className="text-center"><i className="fas fa-check text-success"></i></td>
                      </tr>
                      <tr>
                        <td>Expected Value Calculations</td>
                        <td className="text-center"><i className="fas fa-check text-success"></i></td>
                        <td className="text-center"><i className="fas fa-check text-success"></i></td>
                      </tr>
                      <tr>
                        <td>Player Props</td>
                        <td className="text-center"><i className="fas fa-times text-muted"></i></td>
                        <td className="text-center"><i className="fas fa-check text-success"></i></td>
                      </tr>
                      <tr>
                        <td>Alternative Lines</td>
                        <td className="text-center"><i className="fas fa-times text-muted"></i></td>
                        <td className="text-center"><i className="fas fa-check text-success"></i></td>
                      </tr>
                      <tr>
                        <td>Live Betting Opportunities</td>
                        <td className="text-center"><i className="fas fa-times text-muted"></i></td>
                        <td className="text-center"><i className="fas fa-check text-success"></i></td>
                      </tr>
                      <tr>
                        <td>Advanced Analytics</td>
                        <td className="text-center"><i className="fas fa-times text-muted"></i></td>
                        <td className="text-center"><i className="fas fa-check text-success"></i></td>
                      </tr>
                      <tr>
                        <td>Data Export (CSV)</td>
                        <td className="text-center"><i className="fas fa-times text-muted"></i></td>
                        <td className="text-center"><i className="fas fa-check text-success"></i></td>
                      </tr>
                      <tr>
                        <td>Priority Support</td>
                        <td className="text-center"><i className="fas fa-times text-muted"></i></td>
                        <td className="text-center"><i className="fas fa-check text-success"></i></td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* FAQ Section */}
        <div className="row justify-content-center mt-5">
          <div className="col-lg-10">
            <div className="card">
              <div className="card-header">
                <h3 className="card-title mb-0">
                  <i className="fas fa-question-circle me-2"></i>
                  Frequently Asked Questions
                </h3>
              </div>
              <div className="card-body">
                <div className="accordion" id="faqAccordion">
                  
                  <div className="accordion-item">
                    <h2 className="accordion-header">
                      <button className="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#faq1">
                        Can I cancel my subscription anytime?
                      </button>
                    </h2>
                    <div id="faq1" className="accordion-collapse collapse" data-bs-parent="#faqAccordion">
                      <div className="accordion-body">
                        Yes! You can cancel your Premium subscription at any time. You'll continue to have access to Premium features until the end of your current billing period.
                      </div>
                    </div>
                  </div>

                  <div className="accordion-item">
                    <h2 className="accordion-header">
                      <button className="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#faq2">
                        How often are odds updated?
                      </button>
                    </h2>
                    <div id="faq2" className="accordion-collapse collapse" data-bs-parent="#faqAccordion">
                      <div className="accordion-body">
                        Our system updates odds every 30 seconds from multiple sportsbooks to ensure you have the most current information for your analysis.
                      </div>
                    </div>
                  </div>

                  <div className="accordion-item">
                    <h2 className="accordion-header">
                      <button className="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#faq3">
                        Is this gambling advice?
                      </button>
                    </h2>
                    <div id="faq3" className="accordion-collapse collapse" data-bs-parent="#faqAccordion">
                      <div className="accordion-body">
                        No, this tool is for educational purposes only. We provide mathematical analysis and market data to help you understand sports betting concepts. Always gamble responsibly and within your means.
                      </div>
                    </div>
                  </div>

                  <div className="accordion-item">
                    <h2 className="accordion-header">
                      <button className="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#faq4">
                        What payment methods do you accept?
                      </button>
                    </h2>
                    <div id="faq4" className="accordion-collapse collapse" data-bs-parent="#faqAccordion">
                      <div className="accordion-body">
                        We accept all major credit cards (Visa, MasterCard, American Express) and PayPal through our secure Stripe payment processing.
                      </div>
                    </div>
                  </div>

                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Call to Action */}
        <div className="text-center mt-5 mb-5">
          <div className="card bg-light">
            <div className="card-body">
              <h3>Ready to Get Started?</h3>
              <p className="text-muted">
                Join thousands of users who are already using our analysis to make smarter betting decisions.
              </p>
              {!isSubscriber && (
                <button 
                  onClick={handleUpgrade}
                  className="btn btn-warning btn-lg px-5"
                >
                  <i className="fas fa-rocket me-2"></i>
                  Start Premium Trial
                </button>
              )}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default PricingPage; 