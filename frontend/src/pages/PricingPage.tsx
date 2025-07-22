import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { apiService } from '../services/apiService';

const PricingPage: React.FC = () => {
  const [openFaqIndex, setOpenFaqIndex] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const { user, isAuthenticated } = useAuth();
  const userRole = user?.user_metadata?.role;
  const isBasicSubscriber = userRole === 'basic';
  const isPremiumSubscriber = userRole === 'premium' || userRole === 'subscriber';

  const toggleFaq = (index: number) => {
    setOpenFaqIndex(openFaqIndex === index ? null : index);
  };

  const handleStartTrial = async (plan: 'basic' | 'premium') => {
    if (!isAuthenticated) {
      // Redirect to login first
      window.location.href = `/login?redirect=pricing&plan=${plan}`;
      return;
    }

    // Check current subscription status
    const userRole = user?.user_metadata?.role;

    if (plan === 'basic') {
      if (userRole === 'basic') {
        alert('You already have Basic access!');
        return;
      }
      if (userRole === 'premium' || userRole === 'subscriber') {
        alert('You already have Premium access, which includes all Basic features.');
        return;
      }
    }

    if (plan === 'premium') {
      if (userRole === 'premium' || userRole === 'subscriber') {
        alert('You already have Premium access!');
        return;
      }
    }

    setLoading(true);
    try {
      const response = await apiService.createCheckoutSession(plan);
      // Redirect to Stripe Checkout
      window.location.href = response.checkout_url;
    } catch (error) {
      console.error('Failed to create checkout session:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      alert(`Failed to start trial: ${errorMessage}\n\nPlease try again or contact support.`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="pricing-page">
      <div className="pricing-container">
        {/* Header */}
        <div className="pricing-header">
          <h1 className="pricing-title">Simple, Transparent Pricing</h1>
          <p className="pricing-subtitle">From browsing opportunities to maximizing profits - choose your level</p>

          {/* Sports Coverage */}
          <div style={{
            background: 'rgba(16, 185, 129, 0.1)',
            padding: '1rem 2rem',
            borderRadius: '12px',
            margin: '1.5rem auto 0',
            maxWidth: '700px',
            textAlign: 'center'
          }}>
            <p style={{ margin: 0, color: '#065f46', fontWeight: '500', fontSize: '0.95rem' }}>
              <i className="fas fa-trophy" style={{ color: '#10b981', marginRight: '0.5rem' }}></i>
              <strong>Sports Covered:</strong> NFL • NBA • MLB • NHL • College Basketball • College Football
            </p>
          </div>

          <div style={{
            background: 'rgba(59, 130, 246, 0.1)',
            padding: '1rem 2rem',
            borderRadius: '12px',
            margin: '1rem auto 0',
            maxWidth: '600px',
            textAlign: 'center'
          }}>
            <p style={{ margin: 0, color: '#1e293b', fontWeight: '500' }}>
              <i className="fas fa-lightbulb" style={{ color: '#f59e0b', marginRight: '0.5rem' }}></i>
              Free users see what's available but only unprofitable bets. Start winning with Basic!
            </p>
          </div>
        </div>

        {/* Pricing Cards */}
        <div className="pricing-cards">
          {/* Free Tier */}
          <div className="pricing-card">
            <div className="pricing-card-header">
              <h3 className="plan-title">Free</h3>
              <p className="plan-subtitle">See What's Available</p>
              <div className="price">
                <span className="price-amount">$0</span>
                <span className="price-period">/forever</span>
              </div>
            </div>
            <div className="pricing-card-body">
              <ul className="features-list">
                <li className="feature-item">
                  <i className="fas fa-check feature-icon"></i>
                  <strong>10 Sample Opportunities:</strong> Fixed selection to browse
                </li>
                <li className="feature-item">
                  <i className="fas fa-check feature-icon"></i>
                  <strong>Real-time Updates:</strong> 5-minute refresh
                </li>
                <li className="feature-item disabled">
                  <i className="fas fa-times feature-icon"></i>
                  <span>No search (fixed 10 opportunities)</span>
                </li>
                <li className="feature-item" style={{ color: '#f59e0b' }}>
                  <i className="fas fa-exclamation-triangle feature-icon" style={{ color: '#f59e0b' }}></i>
                  <strong>Only unprofitable bets (-2% EV or worse)</strong>
                </li>
                <li className="feature-item disabled">
                  <i className="fas fa-times feature-icon"></i>
                  <span>No positive EV opportunities</span>
                </li>
              </ul>
            </div>
            <div className="pricing-card-footer">
              <a href="/login" className="btn btn-outline">
                <i className="fas fa-eye"></i>
                Browse Opportunities
              </a>
              <div style={{ marginTop: '0.5rem' }}>
                <small className="trial-note">No credit card required</small>
              </div>
            </div>
          </div>

          {/* Basic Tier */}
          <div className="pricing-card">
            <div className="pricing-card-header">
              <h3 className="plan-title">Basic</h3>
              <p className="plan-subtitle">All Main Line Opportunities</p>
              <div className="price">
                <span className="price-amount">$3.99</span>
                <span className="price-period">/month</span>
              </div>
            </div>
            <div className="pricing-card-body">
              <ul className="features-list">
                <li className="feature-item">
                  <i className="fas fa-check feature-icon"></i>
                  <strong>All Main Lines:</strong> Every EV value
                </li>
                <li className="feature-item">
                  <i className="fas fa-star feature-icon"></i>
                  <strong>Positive EV Opportunities:</strong> Find profitable bets
                </li>
                <li className="feature-item">
                  <i className="fas fa-check feature-icon"></i>
                  <strong>Real-time Updates:</strong> 5-minute refresh
                </li>
                <li className="feature-item">
                  <i className="fas fa-check feature-icon"></i>
                  <strong>Full Search & Filter:</strong> All tools unlocked
                </li>
                <li className="feature-item disabled">
                  <i className="fas fa-times feature-icon"></i>
                  <span>No Player Props or Alternate Lines</span>
                </li>
              </ul>
            </div>
            <div className="pricing-card-footer">
              {isBasicSubscriber ? (
                <div style={{ textAlign: 'center' }}>
                  <div className="btn btn-primary" style={{
                    background: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)',
                    cursor: 'default',
                    position: 'relative'
                  }}>
                    <i className="fas fa-check-circle"></i>
                    Current Plan
                  </div>
                  <small className="trial-note" style={{ display: 'block', marginTop: '0.5rem' }}>You're enjoying Basic features!</small>
                </div>
              ) : isPremiumSubscriber ? (
                <div style={{ textAlign: 'center' }}>
                  <button
                    className="btn btn-outline"
                    onClick={() => handleStartTrial('basic')}
                    disabled={loading}
                  >
                    <i className="fas fa-arrow-down"></i>
                    Downgrade to Basic
                  </button>
                  <small className="trial-note">Manage subscription</small>
                </div>
              ) : (
                <>
                  <button
                    className="btn btn-primary"
                    onClick={() => handleStartTrial('basic')}
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <i className="fas fa-spinner fa-spin"></i>
                        Setting up trial...
                      </>
                    ) : (
                      <>
                        <i className="fas fa-chart-line"></i>
                        Start 7-Day Free Trial
                      </>
                    )}
                  </button>
                  <small className="trial-note">No commitment • Cancel anytime</small>
                </>
              )}
            </div>
          </div>

          {/* Premium Tier */}
          <div className="pricing-card premium">
            <div className="popular-badge">🏆 Most Popular</div>
            <div className="pricing-card-header">
              <h3 className="plan-title">Premium</h3>
              <p className="plan-subtitle">Complete Market Coverage</p>
              <div className="price">
                <span className="price-amount">$9.99</span>
                <span className="price-period">/month</span>
              </div>
            </div>
            <div className="pricing-card-body">
              <ul className="features-list">
                <li className="feature-item">
                  <i className="fas fa-check feature-icon"></i>
                  <strong>Everything in Basic</strong>
                </li>
                <li className="feature-item">
                  <i className="fas fa-star feature-icon"></i>
                  <strong>Player Props:</strong> Points, Assists, Rebounds & more
                </li>
                <li className="feature-item">
                  <i className="fas fa-star feature-icon"></i>
                  <strong>Alternate Lines:</strong> All spread & total variations
                </li>
                <li className="feature-item">
                  <i className="fas fa-star feature-icon"></i>
                  <strong>5x More Opportunities:</strong> Complete market access
                </li>
              </ul>
            </div>
            <div className="pricing-card-footer">
              {isPremiumSubscriber ? (
                <div style={{ textAlign: 'center' }}>
                  <div className="btn btn-primary" style={{
                    background: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)',
                    cursor: 'default',
                    position: 'relative'
                  }}>
                    <i className="fas fa-check-circle"></i>
                    Current Plan
                  </div>
                  <small className="trial-note" style={{ display: 'block', marginTop: '0.5rem' }}>You're enjoying Premium features!</small>
                </div>
              ) : isBasicSubscriber ? (
                <div style={{ textAlign: 'center' }}>
                  <button
                    className="btn btn-primary"
                    onClick={() => handleStartTrial('premium')}
                    disabled={loading}
                    style={{ background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)' }}
                  >
                    <i className="fas fa-arrow-up"></i>
                    Upgrade to Premium
                  </button>
                  <small className="trial-note">Get player props & alternate lines</small>
                </div>
              ) : (
                <>
                  <button
                    className="btn btn-primary"
                    onClick={() => handleStartTrial('premium')}
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <i className="fas fa-spinner fa-spin"></i>
                        Setting up trial...
                      </>
                    ) : (
                      <>
                        <i className="fas fa-crown"></i>
                        Start 7-Day Free Trial
                      </>
                    )}
              </button>
                  <small className="trial-note">No commitment • Cancel anytime</small>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Upgrade Path */}
        <div className="upgrade-path" style={{
          margin: '3rem 0',
          padding: '2rem',
          background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(16, 185, 129, 0.05) 100%)',
          borderRadius: '20px',
          border: '1px solid rgba(59, 130, 246, 0.1)'
        }}>
          <h3 style={{ textAlign: 'center', marginBottom: '2rem', color: '#1e293b' }}>
            <i className="fas fa-route" style={{ marginRight: '0.5rem', color: '#3b82f6' }}></i>
            Your Journey to Profitable Betting
          </h3>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '1.5rem'
          }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{
                background: '#f3f4f6',
                borderRadius: '50%',
                width: '60px',
                height: '60px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 1rem',
                color: '#6b7280'
              }}>
                <i className="fas fa-eye" style={{ fontSize: '1.5rem' }}></i>
              </div>
              <h4 style={{ color: '#374151', marginBottom: '0.5rem' }}>Free: Browse & Learn</h4>
              <p style={{ color: '#6b7280', fontSize: '0.9rem' }}>See negative EV bets to understand what opportunities look like</p>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{
                background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
                borderRadius: '50%',
                width: '60px',
                height: '60px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 1rem',
                color: 'white'
              }}>
                <i className="fas fa-chart-line" style={{ fontSize: '1.5rem' }}></i>
              </div>
              <h4 style={{ color: '#374151', marginBottom: '0.5rem' }}>Basic: Start Winning</h4>
              <p style={{ color: '#6b7280', fontSize: '0.9rem' }}>Unlock positive EV main lines and start making profitable bets</p>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{
                background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                borderRadius: '50%',
                width: '60px',
                height: '60px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 1rem',
                color: 'white'
              }}>
                <i className="fas fa-crown" style={{ fontSize: '1.5rem' }}></i>
              </div>
              <h4 style={{ color: '#374151', marginBottom: '0.5rem' }}>Premium: Maximize Profits</h4>
              <p style={{ color: '#6b7280', fontSize: '0.9rem' }}>Access all markets for maximum opportunities and higher returns</p>
            </div>
          </div>
        </div>

        {/* Feature Comparison */}
        <div className="feature-comparison">
          <h3 className="comparison-title">What's Included</h3>
          <div className="comparison-table-container">
            <table className="comparison-table">
              <thead>
                <tr>
                  <th>Feature</th>
                  <th>Free</th>
                  <th>Basic</th>
                  <th>Premium</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>Main Lines</strong> (Moneyline, Spreads, Totals)</td>
                  <td style={{ color: '#f59e0b' }}>-2% EV or worse only</td>
                  <td><i className="fas fa-check text-success"></i></td>
                  <td><i className="fas fa-check text-success"></i></td>
                </tr>
                <tr>
                  <td><strong>Positive EV Opportunities</strong></td>
                  <td><i className="fas fa-times text-muted"></i></td>
                  <td><i className="fas fa-check text-success"></i></td>
                  <td><i className="fas fa-check text-success"></i></td>
                </tr>
                <tr>
                  <td><strong>Data Refresh</strong></td>
                  <td>5 minutes</td>
                  <td>5 minutes</td>
                  <td>5 minutes</td>
                </tr>
                <tr>
                  <td><strong>Search & Filter</strong></td>
                  <td><i className="fas fa-times text-muted"></i></td>
                  <td><i className="fas fa-check text-success"></i></td>
                  <td><i className="fas fa-check text-success"></i></td>
                </tr>
                <tr>
                  <td><strong>Player Props</strong> (Points, Assists, etc.)</td>
                  <td><i className="fas fa-times text-muted"></i></td>
                  <td><i className="fas fa-times text-muted"></i></td>
                  <td><i className="fas fa-check text-success"></i></td>
                </tr>
                <tr>
                  <td><strong>Alternate Lines</strong> (All variations)</td>
                  <td><i className="fas fa-times text-muted"></i></td>
                  <td><i className="fas fa-times text-muted"></i></td>
                  <td><i className="fas fa-check text-success"></i></td>
                </tr>
                <tr>
                  <td><strong>EV Range</strong></td>
                  <td style={{ color: '#ef4444' }}>-2% and below</td>
                  <td style={{ color: '#10b981' }}>All EV values</td>
                  <td style={{ color: '#10b981' }}>All EV values</td>
                </tr>
                <tr>
                  <td><strong>Opportunities Shown</strong></td>
                  <td style={{ color: '#f59e0b' }}>10 real opportunities (sample)</td>
                  <td>All profitable main lines</td>
                  <td>All markets & lines</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Value Proposition */}
        <div className="feature-comparison" style={{ marginTop: '2rem' }}>
          <h3 className="comparison-title">Why Upgrade?</h3>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '1.5rem',
            padding: '2rem 0'
          }}>
            <div style={{
              background: 'rgba(59, 130, 246, 0.05)',
              border: '1px solid rgba(59, 130, 246, 0.2)',
              borderRadius: '12px',
              padding: '1.5rem',
              textAlign: 'center'
            }}>
              <i className="fas fa-chart-line" style={{ fontSize: '2rem', color: '#3b82f6', marginBottom: '1rem' }}></i>
              <h4 style={{ color: '#1e293b', marginBottom: '1rem', fontSize: '1.1rem' }}>Unlock Positive EV</h4>
              <p style={{ color: '#64748b', fontSize: '0.9rem' }}><strong>Basic ($3.99):</strong> See profitable main line opportunities instead of just losing bets. Start making money!</p>
            </div>
            <div style={{
              background: 'rgba(245, 158, 11, 0.05)',
              border: '1px solid rgba(245, 158, 11, 0.2)',
              borderRadius: '12px',
              padding: '1.5rem',
              textAlign: 'center'
            }}>
              <i className="fas fa-expand-arrows-alt" style={{ fontSize: '2rem', color: '#f59e0b', marginBottom: '1rem' }}></i>
              <h4 style={{ color: '#1e293b', marginBottom: '1rem', fontSize: '1.1rem' }}>5x More Markets</h4>
              <p style={{ color: '#64748b', fontSize: '0.9rem' }}><strong>Premium ($9.99):</strong> Player props and alternate lines provide significantly more opportunities daily.</p>
            </div>
            <div style={{
              background: 'rgba(16, 185, 129, 0.05)',
              border: '1px solid rgba(16, 185, 129, 0.2)',
              borderRadius: '12px',
              padding: '1.5rem',
              textAlign: 'center'
            }}>
              <i className="fas fa-dollar-sign" style={{ fontSize: '2rem', color: '#10b981', marginBottom: '1rem' }}></i>
              <h4 style={{ color: '#1e293b', marginBottom: '1rem', fontSize: '1.1rem' }}>Higher EV Potential</h4>
              <p style={{ color: '#64748b', fontSize: '0.9rem' }}>Props often have higher margins due to less efficient sportsbook pricing across multiple markets.</p>
            </div>
          </div>
        </div>

        {/* FAQ Section */}
        <div className="faq-section">
          <h3 className="faq-title">Frequently Asked Questions</h3>
          <div className="faq-container">
            {[
              {
                question: "What's the difference between the plans?",
                answer: "Free shows main lines with -2% EV or worse (unprofitable bets). Basic ($3.99) unlocks all main lines including positive EV opportunities. Premium ($9.99) adds player props and alternate lines for 5x more opportunities."
              },
              {
                question: "Can I cancel my subscription anytime?",
                answer: "Yes, you can cancel your subscription at any time. Your access will continue until the end of your current billing period."
              },
              {
                question: "Is there a free trial?",
                answer: "Yes! We offer a 7-day free trial for both Basic and Premium plans. You can cancel anytime during the trial without being charged."
              },
              {
                question: "Can I upgrade from Basic to Premium?",
                answer: "Absolutely! You can upgrade to Premium at any time to access player props and alternate lines. You'll be charged the difference prorated for your current billing period."
              },
              {
                question: "Why do free users only see negative EV bets?",
                answer: "This shows you what opportunities exist while incentivizing upgrades. Seeing profitable bets requires at least the Basic plan to help fund the platform's development."
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
