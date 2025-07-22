import React from 'react';

const EducationPage: React.FC = () => {
  return (
    <div className="education-page">
      <div className="main-container">
        <div className="education-container">
        {/* Header */}
        <header className="education-header text-center" style={{ marginBottom: 'var(--space-10)' }}>
          <h1 className="type-h1 text-inverse">🧮 How Our Analysis Works</h1>
          <p className="type-body-sm text-inverse font-medium">The math and strategy behind our recommended odds</p>
        </header>

        {/* What We're Actually Doing */}
        <section className="education-section">
          <div className="prose mx-auto">
            <h2>🎯 What We're Actually Doing</h2>

            <p>Our tool isn't just comparing odds - we're trying to find situations where the market has mispriced a bet. Think of it like finding a stock that's trading below its "true" value.</p>

            <div className="strategy-box" style={{
              background: 'var(--surface-secondary)',
              border: '1px solid var(--border-light)',
              borderRadius: 'var(--radius-lg)',
              padding: 'var(--space-6)',
              marginBottom: 'var(--space-6)'
            }}>
              <h3 className="type-h4 text-brand" style={{ marginTop: 0, marginBottom: 'var(--space-3)' }}>💡 Our Core Strategy</h3>
              <p className="type-body">We identify <strong>the best valued sportsbook</strong> (not P2P exchange) for each bet - often Pinnacle due to their sharp lines and low margins, but could be DraftKings, FanDuel, or others. Then we look for other books offering significantly different odds on the same outcome. When we find big differences, there might be value.</p>
            </div>

            <p>The goal is to post odds on betting exchanges that give us a mathematical edge - similar to how a casino has an edge on every game.</p>
          </div>
        </section>

        {/* Fair Odds Calculation */}
        <section className="education-section">
          <h2 className="section-title">🔬 How We Calculate "Fair Odds"</h2>
          <div className="education-content">
            <p>Our <span className="key-term">"Fair Odds"</span> calculation uses what's called the <strong>best payout anchor method</strong>:</p>

            <div className="math-box">
              <strong>Step 1:</strong> For each outcome, find the best payout among major books (Pinnacle, DraftKings, FanDuel)<br/>
              <strong>Step 2:</strong> Use that same bookmaker's opposite side to maintain market consistency<br/>
              <strong>Step 3:</strong> Convert to probabilities and remove the bookmaker's built-in margin<br/>
              <strong>Step 4:</strong> Convert back to fair odds without any house edge
            </div>

            <div className="example-box">
              <div className="example-title">📊 Real Example: Player Props</div>
              <p><strong>Zach Eflin Over 4.5 Strikeouts</strong></p>

              <p><strong>For the OVER side:</strong></p>
              <ul>
                <li><strong>Best Over payout:</strong> DraftKings -115 (vs FanDuel -125, Pinnacle -120)</li>
                <li><strong>DraftKings Under:</strong> -105 (use same book for consistency)</li>
                <li><strong>Remove DraftKings margin:</strong> 53.5% + 51.2% = 104.7% → normalize</li>
                <li><strong>Fair Over odds:</strong> -108 (51.9% true probability)</li>
              </ul>

              <p><strong>For the UNDER side:</strong></p>
              <ul>
                <li><strong>Best Under payout:</strong> FanDuel -100 (vs DraftKings -105, Pinnacle -110)</li>
                <li><strong>FanDuel Over:</strong> -125 (use same book for consistency)</li>
                <li><strong>Remove FanDuel margin:</strong> 55.6% + 50.0% = 105.6% → normalize</li>
                <li><strong>Fair Under odds:</strong> +109 (47.8% true probability)</li>
              </ul>

              <p><strong>Final Result:</strong> We take the calculation that gives us the most conservative (worst case) fair odds for our analysis.</p>
              <p><strong>Why this works:</strong> Each outcome gets the best available pricing, and we maintain market consistency within each calculation.</p>
            </div>

            <p>This method ensures we're not mixing different bookmakers' opinions while still getting the best available odds for our calculation.</p>
          </div>
        </section>

        {/* Recommended Posting Odds */}
        <section className="education-section">
          <h2 className="section-title">💰 Why We Recommend Specific Posting Odds</h2>
          <div className="education-content">
            <p>When you see our <span className="key-term">"Recommended Posting Odds"</span>, here's the math behind it:</p>

            <div className="concept-list">
              <ul>
                <li><strong>Target:</strong> 2.5% expected value after exchange fees</li>
                <li><strong>Exchange Commission:</strong> Usually 2% on winnings</li>
                <li><strong>Safety Margin:</strong> Extra buffer for variance</li>
              </ul>
            </div>

            <div className="math-box">
              <strong>Formula:</strong><br/>
              Recommended Odds = Fair Odds × (1 + Target EV) ÷ (1 - Commission Rate)<br/><br/>
              <strong>Example:</strong><br/>
              Fair Odds: +200 (33.3% probability)<br/>
              Target EV: 2.5%<br/>
              Commission: 2%<br/>
              Recommended: +215
            </div>

            <div className="strategy-box">
              <div className="strategy-title">🎯 Why This Works</div>
              <p>By posting at these odds, you're essentially becoming the house. Other bettors take your bet, and you have the mathematical edge. Over many bets, this should be profitable even when individual bets lose.</p>
            </div>
          </div>
        </section>

        {/* EV Calculations */}
        <section className="education-section">
          <h2 className="section-title">📈 Understanding Our EV Calculations</h2>
          <div className="education-content">
            <p>When we show <span className="key-term">"Expected Value"</span>, we're comparing the best available odds against our calculated fair odds:</p>

            <div className="example-box">
              <div className="example-title">🔍 EV Breakdown Example</div>
              <p><strong>Jack Leiter Over 5.5 Hits Allowed</strong></p>
              <ul>
                <li><strong>Fair Odds:</strong> +141 (41.5% implied probability)</li>
                <li><strong>Best Available:</strong> ProphetX +148 (40.5% implied probability)</li>
                <li><strong>EV Calculation:</strong> (0.415 × 2.48) - 1 = 2.9%</li>
              </ul>
              <p><strong>Translation:</strong> If this bet were available 1000 times, you'd expect to make about 2.9% profit on average.</p>
            </div>

            <div className="warning-note">
              <strong>Important:</strong> EV only matters over large sample sizes. Individual bets can still lose even with positive EV.
            </div>
          </div>
        </section>

        {/* Good Opportunities */}
        <section className="education-section">
          <h2 className="section-title">🔍 What Makes a Good Opportunity</h2>
          <div className="education-content">
            <p>We filter opportunities based on several criteria:</p>

            <div className="concept-list">
              <ul>
                <li><strong>Market Depth:</strong> At least 2 major books offering both sides</li>
                <li><strong>Line Quality:</strong> Significant difference from fair value</li>
                <li><strong>Exchange Availability:</strong> Can actually post the opposite side</li>
                <li><strong>Liquidity:</strong> Enough betting volume to get matched</li>
              </ul>
            </div>

            <div className="strategy-box">
              <div className="strategy-title">⚡ Our Filtering Process</div>
              <p>We automatically filter out markets where only 1 major book has both sides available. This prevents us from recommending bets where there's not enough market consensus to trust our fair odds calculation.</p>
            </div>
          </div>
        </section>

        {/* Exchange Strategy */}
        <section className="education-section">
          <h2 className="section-title">🎲 The Exchange Strategy</h2>
          <div className="education-content">
            <p>The key insight is using <strong>betting exchanges</strong> to post bets like market orders or eBay "best offers":</p>

            <div className="concept-list">
              <ul>
                <li><strong>ProphetX:</strong> A peer-to-peer betting exchange where you can post odds and wait for other users to accept your bets. Charges ~2% commission on winnings.</li>
                <li><strong>Novig:</strong> Another P2P exchange platform that allows you to set your own odds and act as the "house" for other bettors. Also charges ~2% commission.</li>
              </ul>
            </div>

            <p>These platforms let you post odds instead of just taking what sportsbooks offer:</p>

            <div className="example-box">
              <div className="example-title">🔄 How It Actually Works</div>
              <p><strong>Scenario:</strong> Our analysis shows Eflin Over 4.5 K's has +3% EV at +120</p>
              <ul>
                <li><strong>Step 1:</strong> Post "Eflin Over 4.5 K's" at +120 on ProphetX</li>
                <li><strong>Step 2:</strong> Wait to see if anyone accepts your bet</li>
                <li><strong>Outcome A:</strong> No one takes it → No bet, no risk</li>
                <li><strong>Outcome B:</strong> Someone takes it → You have a bet with +3% edge (at time of posting)</li>
              </ul>
              <p><strong>Key Point:</strong> You only get action when someone thinks your posted odds are favorable to them, but you calculated you have the edge.</p>
            </div>

            <div className="strategy-box">
              <div className="strategy-title">💡 Why This Works</div>
              <p>It's like posting an item on eBay with a "Buy It Now" price. Either no one buys it (no loss) or someone buys it at your target price (profit). You're essentially saying "I'll take this bet at these odds" and waiting for a counterparty.</p>
            </div>

            <div className="warning-note">
              <strong>Important:</strong> Lines can move after you post, so your edge might disappear. But at the moment you posted, the math was in your favor.
            </div>
          </div>
        </section>

        {/* Limitations & Risks */}
        <section className="education-section">
          <h2 className="section-title">⚠️ Limitations & Risks</h2>
          <div className="education-content">
            <div className="warning-note">
              <strong>🚨 This is theoretical analysis!</strong> Real-world execution has many challenges we can't account for.
            </div>

            <div className="concept-list">
              <ul>
                <li><strong>Liquidity Risk:</strong> Your posted odds might not get matched</li>
                <li><strong>Timing Risk:</strong> Lines move before you can execute both sides</li>
                <li><strong>Limits:</strong> Sportsbooks may limit your bet sizes</li>
                <li><strong>Model Risk:</strong> Our fair odds calculation could be wrong</li>
                <li><strong>Variance:</strong> Short-term results can vary wildly from expectation</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Key Takeaways */}
        <section className="education-section">
          <h2 className="section-title">🎓 Key Takeaways</h2>
          <div className="education-content">
            <p>Our tool is designed to:</p>
            <div className="concept-list">
              <ul>
                <li>Identify market inefficiencies using statistical analysis</li>
                <li>Calculate fair odds using sharp bookmaker data</li>
                <li>Recommend profitable posting strategies on exchanges</li>
                <li>Filter out low-quality opportunities automatically</li>
                <li>Provide the math behind each recommendation</li>
              </ul>
            </div>

            <p>Think of it as a systematic approach to finding and exploiting small edges in the betting market - similar to algorithmic trading but for sports betting.</p>
          </div>
        </section>

        {/* Navigation */}
        <div className="navigation-links">
          <a href="/" className="nav-link">📊 View Live Analysis</a>
          <a href="/disclaimer" className="nav-link secondary">⚠️ Legal Disclaimer</a>
        </div>

        <div className="footer-note">
          <p>Sports Betting +EV Analyzer - Educational Tool</p>
          <p>Remember: This is for learning purposes only. Past results don't guarantee future performance.</p>
        </div>
        </div>
      </div>
    </div>
  );
};

export default EducationPage;
