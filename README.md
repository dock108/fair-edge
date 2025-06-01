# Sports Betting +EV Analyzer 📊

A comprehensive FastAPI application for identifying positive expected value (EV) betting opportunities across multiple sportsbooks and exchanges.

## 🚀 Features

### Real-time Odds Integration
- **Live data** from 5 major platforms: Pinnacle, DraftKings, FanDuel, Novig, ProphetX
- **24-hour filtering** for upcoming events
- **Auto-refresh** every 30 seconds
- **Multi-sport support** (NBA, NFL, and more)

### Advanced Analytics
- **Fair odds calculation** using anchor book methodology
- **EV analysis** with 4.5% threshold classification
- **Market filtering** requiring 2+ major books for liquidity
- **Vig removal** and probability normalization

### Smart Recommendations
- **🟢 Take @ [Book]**: EV ≥ 4.5% (Strong opportunities)
- **🟡 Good, but Try Better**: 0% < EV < 4.5% (Marginal opportunities)  
- **⚪ No +EV to Take**: EV ≤ 0% (Post-only scenarios)
- **Exchange posting suggestions** with optimal platform selection

### Interactive Dashboard
- **Sortable table** with real-time updates
- **Color-coded opportunities** for quick identification
- **Complete market analysis** (H2H, Spreads, Totals)
- **Action links** for immediate betting/posting

### SaaS Infrastructure (New!)
- **Supabase Integration** for user management and data persistence
- **PostgreSQL database** for scalable data storage
- **User authentication** ready for implementation
- **Database monitoring** and health checks

## 📋 Requirements

- Python 3.8+
- The Odds API key (free tier available)
- Supabase project (for database and auth)
- Internet connection for real-time data

## 🛠️ Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd bet-intel
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up Supabase** (New!)
   - Create a project at [supabase.com](https://supabase.com)
   - Note your project URL and API keys
   - Create the profiles table and trigger (see Database Setup section)

4. **Configure environment variables**
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your credentials
ODDS_API_KEY=your_api_key_here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
DB_CONNECTION_STRING=postgresql+asyncpg://postgres.your-project:password@aws-region.pooler.supabase.com:5432/postgres
```

5. **Initialize the database**
```bash
python setup_database.py
```

6. **Get your API key**
   - Visit [The Odds API](https://the-odds-api.com/)
   - Sign up for a free account (500 requests/month)
   - Copy your API key to the `.env` file

## 🗄️ Database Setup

### Supabase Configuration

1. **Create profiles table**:
```sql
create table profiles (
  id uuid primary key references auth.users(id),
  email text,
  role text default 'free',
  subscription_status text default 'none',
  stripe_customer_id text,
  stripe_subscription_id text,
  created_at timestamp default timezone('utc'::text, now()),
  updated_at timestamp default timezone('utc'::text, now())
);
```

2. **Set up user creation trigger**:
```sql
create function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, email)
  values (new.id, new.email);
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
```

3. **Run the setup script**:
```bash
python setup_database.py
```

### Database Verification

After setup, test your database connection:

```bash
# Start the application
python app.py

# Test endpoints:
curl http://localhost:8000/health
curl http://localhost:8000/debug/database-status
curl http://localhost:8000/debug/profiles
curl http://localhost:8000/debug/supabase
```

### Common Issues

**❌ "asyncio extension requires an async driver" Error:**
- Your `DB_CONNECTION_STRING` must use `postgresql+asyncpg://` not `postgresql://`
- Correct format: `postgresql+asyncpg://postgres.your-project:password@aws-region.pooler.supabase.com:5432/postgres`
- Run `python test_env.py` to validate your connection string format

**❌ "Database not properly configured" Error:**
- Check that all Supabase environment variables are set in your `.env` file
- Ensure your `.env` file is in the project root directory
- Verify your Supabase credentials are correct

## 🎮 Usage

### Quick Start - Dashboard
```bash
python run_dashboard.py
```

The dashboard will launch at `http://localhost:8501` with:
- Real-time betting opportunities table
- Auto-refresh functionality
- Sortable columns and filtering
- Summary statistics

### Command Line Testing
```bash
# Test API connection
python odds_api.py

# Test fair odds calculation
python test_fair_odds.py

# Test complete EV analysis
python test_ev_analysis.py

# Test full system integration
python test_complete_system.py
```

## 📊 Dashboard Interface

### Main Table Columns
- **Event**: Game matchup with date/time
- **Bet Description**: Type of bet (Moneyline, Spread, Total)
- **All Available Odds**: Odds from all 5 platforms
- **Fair Odds**: Calculated no-vig fair value
- **Best Available Odds**: Highest payout available
- **Expected Value %**: Color-coded EV percentage
- **Proposed Posting Odds**: Exchange posting recommendation
- **Recommended Action**: Take vs Post decision
- **Links**: Direct action buttons

### Color Coding
- **🟢 Dark Green**: EV ≥ 4.5% (Strong +EV)
- **🟡 Light Green**: 0% < EV < 4.5% (Marginal +EV)
- **⚪ No Color**: EV ≤ 0% (No advantage)

## 🧮 Algorithm Details

### Fair Odds Calculation
1. **Anchor Book Selection**: Find best payout from major books (Pinnacle, DraftKings, FanDuel)
2. **Consistency Rule**: Use same bookmaker's opposite side for market integrity
3. **Vig Removal**: Convert to probabilities, normalize to sum=1.0, convert back
4. **Arbitrage Detection**: Flag when probabilities sum < 1.0

### EV Analysis
```
EV = (p_fair × odds_decimal) - 1

Where:
- p_fair = True win probability from fair odds
- odds_decimal = Market odds in decimal format
```

### Exchange Posting Strategy
- **Target**: 2.5% net EV after 2% commission
- **Method**: Shift fair probability by 4.5 percentage points
- **Exchange Selection**:
  - No markets → Default to Novig
  - One empty → Choose empty exchange
  - Both active → Choose exchange with more "room" from fair odds

## 📈 Example Output

```
🎯 COMPLETE OPPORTUNITY ANALYSIS:

📌 MINNESOTA TIMBERWOLVES
   Fair: +316 (24.0% prob)
   Best: +325 @ ProphetX
   🟡 Good, but Try Better (+2.41% EV)
   📋 POSTING OPTIONS:
   📤 Back: +249 (3.50) | Net EV: -17.7%
   📤 Lay: +410 (5.10) | Net EV: -7.6%
   📍 Post on ProphetX (More room vs fair)
```

## 🔧 Configuration

### Supported Sports
- `basketball_nba` - NBA games
- `americanfootball_nfl` - NFL games
- Easily extensible to other sports

### Markets Analyzed
- **H2H (Moneyline)**: Team A vs Team B
- **Spreads**: Point spreads with handicaps
- **Totals**: Over/Under point totals
- **Player Props**: Points, assists, rebounds (filtered)

### Bookmaker Coverage
- **Major Books**: Pinnacle, DraftKings, FanDuel
- **Exchanges**: Novig, ProphetX
- **Regions**: US, US Exchange, EU

## 🧪 Testing

The system includes comprehensive test suites:

```bash
# Test individual components
python test_fair_odds.py      # Fair odds calculation
python test_ev_analysis.py    # EV opportunity identification
python test_complete_system.py # Full integration test
```

## 📚 Architecture

### Core Components
- **`app.py`**: FastAPI web application with HTML dashboard
- **`fastapi_data_processor.py`**: Data processing with persistent caching
- **`odds_api.py`**: Real-time data fetching from The Odds API
- **`fair_odds_calculator.py`**: Anchor book methodology implementation
- **`ev_analyzer.py`**: Expected value calculations and classifications
- **`maker_odds_calculator.py`**: Exchange posting recommendations
- **`templates/`**: HTML templates for web interface

### Data Flow
1. **Fetch** → Live odds from 5 platforms (cached for 30min/3hrs)
2. **Filter** → Two-sided markets with major book coverage
3. **Calculate** → Fair odds using anchor book methodology
4. **Analyze** → EV percentages and classifications
5. **Recommend** → Take vs Post decisions with optimal exchange
6. **Display** → Real-time sortable web dashboard with admin mode

## 🚨 Important Notes

### API Usage
- Free tier: 500 requests/month
- Each sport/market combination costs ~3 requests
- Dashboard refresh uses multiple requests
- Monitor quota in dashboard

### Market Liquidity
- Requires 2+ major books for analysis
- Two-sided markets only (clear opposing outcomes)
- Filters out stale odds (>1 hour old)

### Betting Considerations
- **This is for educational/analytical purposes**
- Always verify odds before placing bets
- Consider bankroll management and responsible gambling
- Exchange fees may vary from 2% assumption

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality  
4. Submit a pull request

## 📄 License

This project is for educational purposes. Always comply with local laws and betting platform terms of service.

## 🆘 Support

For issues or questions:
1. Check the test scripts work correctly
2. Verify your `.env` file has a valid API key
3. Ensure all dependencies are installed
4. Check API quota status

---

**🎯 Ready to identify +EV opportunities? Run `uvicorn app:app --host 0.0.0.0 --port 8000 --reload` to get started!** 