"""
Betting Opportunities Persistence Service

Handles saving betting opportunities to the database with proper data normalization,
batch operations, and error handling that doesn't break the refresh pipeline.
"""
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists, text
from sqlalchemy.dialects.postgresql import insert

from models import Bet, BetOffer, Sport, League, Book
from db import AsyncSessionLocal
from utils.odds_utils import american_to_decimal

logger = logging.getLogger(__name__)


class BetPersistenceService:
    """Service for persisting betting opportunities to the database"""
    
    def __init__(self):
        self.refresh_cycle_id = None
    
    async def save_opportunities_batch(self, opportunities: List[Dict[str, Any]], 
                                       source: str = "refresh_task") -> Dict[str, Any]:
        """
        Save a batch of betting opportunities to the database
        
        Args:
            opportunities: List of opportunity dictionaries from the processing pipeline
            source: Source identifier for this batch (e.g., "refresh_task", "manual")
            
        Returns:
            Dict with results including counts, errors, and timing
        """
        start_time = datetime.now()
        self.refresh_cycle_id = str(uuid.uuid4())
        
        results = {
            "status": "success",
            "refresh_cycle_id": self.refresh_cycle_id,
            "source": source,
            "total_opportunities": len(opportunities),
            "bets_created": 0,
            "bets_updated": 0, 
            "offers_created": 0,
            "errors": [],
            "processing_time_ms": 0
        }
        
        if not opportunities:
            logger.warning("No opportunities provided to save")
            return results
        
        try:
            if not AsyncSessionLocal:
                raise RuntimeError("Database not configured properly")
                
            async with AsyncSessionLocal() as session:
                # Ensure lookup data exists
                await self._ensure_lookup_data(session)
                
                # Process opportunities in batches
                batch_size = 100  # Configurable batch size
                for i in range(0, len(opportunities), batch_size):
                    batch = opportunities[i:i + batch_size]
                    batch_results = await self._process_opportunity_batch(session, batch)
                    
                    # Aggregate results
                    results["bets_created"] += batch_results["bets_created"]
                    results["bets_updated"] += batch_results["bets_updated"]
                    results["offers_created"] += batch_results["offers_created"]
                    results["errors"].extend(batch_results["errors"])
                
                # Commit all changes
                await session.commit()
                logger.info(
                    f"Successfully saved batch: {results['bets_created']} bets, "
                    f"{results['offers_created']} offers"
                )
                
        except Exception as e:
            logger.error(f"Critical error in batch save: {e}", exc_info=True)
            results["status"] = "error"
            results["errors"].append({"type": "critical", "message": str(e)})
        
        # Calculate processing time
        end_time = datetime.now()
        results["processing_time_ms"] = int((end_time - start_time).total_seconds() * 1000)
        
        return results
    
    async def _process_opportunity_batch(self, session: AsyncSession, 
                                         opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process a single batch of opportunities"""
        results = {
            "bets_created": 0,
            "bets_updated": 0,
            "offers_created": 0,
            "errors": []
        }
        
        for opportunity in opportunities:
            try:
                # Extract or create bet record
                bet_result = await self._ensure_bet_record(session, opportunity)
                if bet_result["created"]:
                    results["bets_created"] += 1
                else:
                    results["bets_updated"] += 1
                
                # Create offer record
                offer_result = await self._create_offer_record(
                    session, bet_result["bet_id"], opportunity
                )
                if offer_result["created"]:
                    results["offers_created"] += 1
                
            except Exception as e:
                error_msg = f"Error processing opportunity: {str(e)}"
                logger.warning(error_msg)
                results["errors"].append({
                    "type": "opportunity_error",
                    "message": error_msg,
                    "opportunity_event": opportunity.get("Event", "unknown")
                })
                # Continue processing other opportunities
                continue
        
        return results
    
    async def _ensure_bet_record(self, session: AsyncSession, 
                                 opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure bet record exists, create if not found"""
        # Generate deterministic bet_id
        bet_id = Bet.create_or_get_bet_id(opportunity)
        
        # Check if bet already exists
        result = await session.execute(
            select(exists().where(Bet.bet_id == bet_id))
        )
        bet_exists = result.scalar()
        
        if not bet_exists:
            # Create new bet record
            bet_data = self._extract_bet_data(opportunity, bet_id)
            bet = Bet(**bet_data)
            session.add(bet)
            
            logger.debug(f"Created new bet record: {bet_id}")
            return {"bet_id": bet_id, "created": True}
        else:
            # Update timestamp on existing bet
            await session.execute(
                text("UPDATE bets SET updated_at = :now WHERE bet_id = :bet_id"),
                {"now": datetime.now(), "bet_id": bet_id}
            )
            
            logger.debug(f"Updated existing bet record: {bet_id}")
            return {"bet_id": bet_id, "created": False}
    
    async def _create_offer_record(self, session: AsyncSession, bet_id: str, 
                                   opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new offer record for this snapshot"""
        try:
            offer_data = self._extract_offer_data(opportunity, bet_id)
            offer = BetOffer(**offer_data)
            session.add(offer)
            
            logger.debug(f"Created offer record for bet: {bet_id}")
            return {"created": True}
            
        except Exception as e:
            logger.warning(f"Failed to create offer for bet {bet_id}: {e}")
            return {"created": False, "error": str(e)}
    
    def _extract_bet_data(self, opportunity: Dict[str, Any], bet_id: str) -> Dict[str, Any]:
        """Extract static bet data from opportunity"""
        # Extract teams from event name
        event_name = opportunity.get('Event', '')
        home_team, away_team = self._parse_teams(event_name)
        
        # Extract player name for props
        player_name = self._extract_player_name(opportunity)
        
        # Determine sport and league 
        sport_id = self._determine_sport(opportunity)
        league_id = self._determine_league(opportunity, sport_id)
        
        # Extract bet type and description
        bet_type = opportunity.get('Market', 'unknown')
        market_description = opportunity.get('Bet Description', '')
        
        # Parse parameters and outcome side
        parameters, outcome_side = self._parse_bet_parameters(opportunity)
        
        return {
            "bet_id": bet_id,
            "sport": sport_id,
            "league": league_id,
            "event_name": event_name,
            "home_team": home_team,
            "away_team": away_team,
            "player_name": player_name,
            "bet_type": bet_type,
            "market_description": market_description,
            "parameters": parameters,
            "outcome_side": outcome_side,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
    
    def _extract_offer_data(self, opportunity: Dict[str, Any], bet_id: str) -> Dict[str, Any]:
        """Extract offer data from opportunity"""
        # Parse odds data
        odds_data = self._parse_odds_data(opportunity)
        
        # Calculate fair odds
        fair_odds_data = self._parse_fair_odds(opportunity)
        
        # Determine book/source
        book_id = self._determine_book(opportunity)
        
        # Extract EV and confidence metrics
        expected_value = opportunity.get('EV_Raw', 0.0)
        confidence_score = self._calculate_confidence_score(opportunity)
        
        return {
            "offer_id": BetOffer.generate_offer_id(),
            "bet_id": bet_id,
            "book": book_id,
            "odds": odds_data,
            "expected_value": expected_value,
            "fair_odds": fair_odds_data,
            "implied_probability": self._calculate_implied_probability(odds_data),
            "confidence_score": confidence_score,
            "volume_indicator": self._determine_volume_indicator(opportunity),
            "available_limits": self._extract_limits(opportunity),
            "offer_metadata": self._extract_offer_metadata(opportunity),
            "timestamp": datetime.now(),
            "refresh_cycle_id": self.refresh_cycle_id
        }
    
    def _parse_teams(self, event_name: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse team names from event string"""
        if ' vs ' in event_name:
            parts = event_name.split(' vs ')
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()
        elif ' @ ' in event_name:
            parts = event_name.split(' @ ')
            if len(parts) == 2:
                return parts[1].strip(), parts[0].strip()  # home @ away
        return None, None
    
    def _extract_player_name(self, opportunity: Dict[str, Any]) -> Optional[str]:
        """Extract player name for prop bets"""
        description = opportunity.get('Bet Description', '')
        # Simple heuristic: if it contains common prop terms, try to extract name
        prop_keywords = ['points', 'rebounds', 'assists', 'hits', 'strikeouts', 'goals']
        if any(keyword in description.lower() for keyword in prop_keywords):
            # Extract the first part before the prop type
            words = description.split()
            if len(words) >= 2:
                # Assume first 1-2 words are player name
                potential_name = ' '.join(words[:2])
                if not any(keyword in potential_name.lower() for keyword in prop_keywords):
                    return potential_name
        return None
    
    def _determine_sport(self, opportunity: Dict[str, Any]) -> str:
        """Determine sport ID from opportunity data"""
        # This could be enhanced with more sophisticated logic
        # For now, use a simple mapping based on common patterns
        description = opportunity.get('Bet Description', '').lower()
        event = opportunity.get('Event', '').lower()
        
        # NFL/Football patterns
        if any(term in description or term in event for term in ['nfl', 'football', 'touchdown', 'yards']):
            return 'americanfootball_nfl'
        
        # NBA/Basketball patterns
        if any(term in description or term in event for term in ['nba', 'basketball', 'points', 'rebounds']):
            return 'basketball_nba'
        
        # MLB/Baseball patterns
        if any(term in description or term in event for term in ['mlb', 'baseball', 'hits', 'strikeouts']):
            return 'baseball_mlb'
        
        # NHL/Hockey patterns
        if any(term in description or term in event for term in ['nhl', 'hockey', 'goals', 'shots']):
            return 'icehockey_nhl'
        
        # Default fallback
        return 'unknown'
    
    def _determine_league(self, opportunity: Dict[str, Any], sport_id: str) -> str:
        """Determine league ID based on sport"""
        # Simple mapping of sport to primary league
        sport_to_league = {
            'americanfootball_nfl': 'nfl',
            'basketball_nba': 'nba', 
            'baseball_mlb': 'mlb',
            'icehockey_nhl': 'nhl'
        }
        return sport_to_league.get(sport_id, 'unknown')
    
    def _parse_bet_parameters(self, opportunity: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
        """Parse bet parameters and outcome side from description"""
        description = opportunity.get('Bet Description', '').lower()
        parameters = {}
        outcome_side = None
        
        # Parse spread values
        import re
        spread_match = re.search(r'[+-]?\d+\.?\d*', description)
        if 'spread' in description and spread_match:
            parameters['spread'] = float(spread_match.group())
        
        # Parse total values
        total_match = re.search(r'\d+\.?\d*', description)
        if any(term in description for term in ['total', 'over', 'under']) and total_match:
            parameters['total'] = float(total_match.group())
        
        # Determine outcome side
        if 'over' in description:
            outcome_side = 'over'
        elif 'under' in description:
            outcome_side = 'under'
        elif 'home' in description:
            outcome_side = 'home'
        elif 'away' in description:
            outcome_side = 'away'
        
        return parameters, outcome_side
    
    def _parse_odds_data(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Parse odds data into structured format"""
        best_odds = opportunity.get('Best Available Odds', '+100')
        
        # Convert American odds to decimal
        decimal_odds = american_to_decimal(best_odds)
        
        return {
            "american": best_odds,
            "decimal": decimal_odds,
            "source": opportunity.get('Best_Odds_Source', 'unknown')
        }
    
    def _parse_fair_odds(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Parse fair odds data"""
        fair_odds = opportunity.get('Fair Odds', '+100')
        decimal_odds = american_to_decimal(fair_odds)
        
        return {
            "american": fair_odds,
            "decimal": decimal_odds
        }
    
    # Use centralized odds utilities instead of duplicate implementation
    
    def _determine_book(self, opportunity: Dict[str, Any]) -> str:
        """Determine bookmaker ID from opportunity"""
        source = opportunity.get('Best_Odds_Source', 'unknown')
        
        # Normalize common bookmaker names
        book_mapping = {
            'draftkings': 'draftkings',
            'fanduel': 'fanduel', 
            'betmgm': 'betmgm',
            'caesars': 'caesars',
            'pointsbet': 'pointsbet'
        }
        
        source_lower = source.lower()
        for key, value in book_mapping.items():
            if key in source_lower:
                return value
        
        return source.lower().replace(' ', '_') if source != 'unknown' else 'unknown'
    
    def _calculate_implied_probability(self, odds_data: Dict[str, Any]) -> float:
        """Calculate implied probability from decimal odds"""
        try:
            decimal_odds = odds_data.get('decimal', 2.0)
            return 1 / decimal_odds if decimal_odds > 0 else 0.5
        except (ZeroDivisionError, TypeError):
            return 0.5
    
    def _calculate_confidence_score(self, opportunity: Dict[str, Any]) -> float:
        """Calculate confidence score for this opportunity"""
        # Simple confidence calculation based on EV and other factors
        ev_raw = opportunity.get('EV_Raw', 0.0)
        
        # Higher EV = higher confidence, capped at 1.0
        base_confidence = min(abs(ev_raw) * 10, 1.0)
        
        # Adjust based on data completeness
        if opportunity.get('All Available Odds', 'N/A') != 'N/A':
            base_confidence *= 1.1  # Boost for complete odds data
        
        return min(base_confidence, 1.0)
    
    def _determine_volume_indicator(self, opportunity: Dict[str, Any]) -> str:
        """Determine volume indicator for the market"""
        # Simple heuristic based on available information
        odds_count = len(opportunity.get('All Available Odds', '').split(';'))
        
        if odds_count >= 5:
            return 'high'
        elif odds_count >= 3:
            return 'medium'
        else:
            return 'low'
    
    def _extract_limits(self, opportunity: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract betting limits if available"""
        # This would be enhanced when limit data is available
        return None
    
    def _extract_offer_metadata(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Extract additional offer metadata"""
        return {
            "links": opportunity.get('Links', ''),
            "all_odds": opportunity.get('All Available Odds', ''),
            "processing_notes": opportunity.get('processing_notes', '')
        }
    
    async def _ensure_lookup_data(self, session: AsyncSession):
        """Ensure basic lookup data exists in the database"""
        try:
            # Create basic sports if they don't exist
            sports_data = [
                {"sport_id": "americanfootball_nfl", "name": "NFL", "category": "americanfootball"},
                {"sport_id": "basketball_nba", "name": "NBA", "category": "basketball"},
                {"sport_id": "baseball_mlb", "name": "MLB", "category": "baseball"},
                {"sport_id": "icehockey_nhl", "name": "NHL", "category": "icehockey"},
                {"sport_id": "unknown", "name": "Unknown Sport", "category": "unknown"}
            ]
            
            for sport_data in sports_data:
                stmt = insert(Sport).values(**sport_data)
                stmt = stmt.on_conflict_do_nothing(index_elements=['sport_id'])
                await session.execute(stmt)
            
            # Create basic leagues
            leagues_data = [
                {"league_id": "nfl", "name": "National Football League", "sport_id": "americanfootball_nfl"},
                {"league_id": "nba", "name": "National Basketball Association", "sport_id": "basketball_nba"},
                {"league_id": "mlb", "name": "Major League Baseball", "sport_id": "baseball_mlb"},
                {"league_id": "nhl", "name": "National Hockey League", "sport_id": "icehockey_nhl"},
                {"league_id": "unknown", "name": "Unknown League", "sport_id": "unknown"}
            ]
            
            for league_data in leagues_data:
                stmt = insert(League).values(**league_data)
                stmt = stmt.on_conflict_do_nothing(index_elements=['league_id'])
                await session.execute(stmt)
            
            # Create basic books
            books_data = [
                {"book_id": "draftkings", "name": "DraftKings", "book_type": "us_book", "region": "us"},
                {"book_id": "fanduel", "name": "FanDuel", "book_type": "us_book", "region": "us"},
                {"book_id": "betmgm", "name": "BetMGM", "book_type": "us_book", "region": "us"},
                {"book_id": "caesars", "name": "Caesars", "book_type": "us_book", "region": "us"},
                {"book_id": "unknown", "name": "Unknown Book", "book_type": "unknown", "region": "unknown"}
            ]
            
            for book_data in books_data:
                stmt = insert(Book).values(**book_data)
                stmt = stmt.on_conflict_do_nothing(index_elements=['book_id'])
                await session.execute(stmt)
            
            logger.debug("Ensured lookup data exists")
            
        except Exception as e:
            logger.warning(f"Failed to ensure lookup data: {e}")
            # Don't fail the whole operation for lookup data issues


# Global instance for easy access
bet_persistence = BetPersistenceService() 