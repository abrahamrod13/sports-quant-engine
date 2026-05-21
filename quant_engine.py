from config import *

class QuantEngine:
    def __init__(self):
        self.min_probability = MIN_PROBABILITY
        self.max_volatility = MAX_VOLATILITY
        self.min_edge = MIN_EDGE
        self.soccer_weights = SOCCER_WEIGHTS
        self.nba_weights = NBA_WEIGHTS
        self.volatility_weights = VOLATILITY_WEIGHTS
    
    def implied_probability(self, decimal_odds):
        if decimal_odds is None or decimal_odds <= 1:
            return 0.5
        return 1 / decimal_odds
    
    def calculate_edge(self, model_prob, odds):
        if odds is None or odds <= 1:
            return 0.0
        market_prob = self.implied_probability(odds)
        return round(model_prob - market_prob, 4)
    
    # ============================================
    # CONFIDENCE SCORE (Prioridad #2)
    # ============================================
    def confidence_score(self, probability, volatility, edge):
        score = (
            probability * 0.50 +
            (1 - volatility) * 0.30 +
            min(edge * 2, 1.0) * 0.20
        )
        return round(score, 3)
    
    def confidence_level(self, score):
        if score >= 0.80:
            return 'A+'
        elif score >= 0.70:
            return 'A'
        elif score >= 0.60:
            return 'B'
        else:
            return 'C'
    
    # ============================================
    # SOCCER
    # ============================================
    def soccer_team_score(self, team_data):
        return (
            team_data.get('form', 0.5) * self.soccer_weights['home_form'] +
            team_data.get('xg', 0.5) * self.soccer_weights['xg_diff'] +
            team_data.get('motivation', 0.5) * self.soccer_weights['motivation'] +
            team_data.get('injuries_impact', 0.5) * self.soccer_weights['injuries'] +
            team_data.get('h2h_advantage', 0.5) * self.soccer_weights['recent_h2h']
        )
    
    def soccer_probability(self, row):
        home_base = row.get('home_team_score', 0.5)
        away_base = row.get('away_team_score', 0.5)
        home_adv = row.get('home_advantage', 0.58)
        home_total = home_base * home_adv
        away_total = away_base * (1 - home_adv + 0.5)
        total = home_total + away_total
        return min(max(home_total / total, 0.05), 0.95) if total > 0 else 0.5
    
    # ============================================
    # NBA
    # ============================================
    def nba_team_score(self, team_data):
        return (
            team_data.get('win_pct', 0.5) * self.nba_weights['home_win_pct'] +
            team_data.get('net_rating', 0.5) * self.nba_weights['net_rating_diff'] +
            team_data.get('injury_impact', 0.5) * self.nba_weights['injury_factor'] +
            team_data.get('rest_days', 0.5) * self.nba_weights['rest_advantage'] +
            team_data.get('momentum', 0.5) * self.nba_weights['momentum'] +
            team_data.get('rebounding', 0.5) * self.nba_weights['rebounding_edge'] +
            team_data.get('h2h', 0.5) * self.nba_weights['h2h_factor']
        )
    
    def nba_probability(self, row):
        home_score = row.get('home_team_score', 0.5)
        away_score = row.get('away_team_score', 0.5)
        total = home_score + away_score
        return min(max(home_score / total, 0.05), 0.95) if total > 0 else 0.5
    
    # ============================================
    # MLB
    # ============================================
    def mlb_team_score(self, team_data):
        return (
            team_data.get('win_pct', 0.5) * 0.55 +
            team_data.get('home_advantage', 0.5) * 0.15 +
            team_data.get('momentum', 0.5) * 0.10 +
            team_data.get('pitcher_factor', 0.5) * 0.20
        )
    
    def mlb_probability(self, row):
        home_score = row.get('home_team_score', 0.5)
        away_score = row.get('away_team_score', 0.5)
        
        if row.get('pitcher_mismatch', False):
            if home_score > away_score:
                home_score += 0.03
            else:
                away_score += 0.03
        
        total = home_score + away_score
        return min(max(home_score / total, 0.05), 0.95) if total > 0 else 0.5
    
    # ============================================
    # VOLATILIDAD
    # ============================================
    def volatility_model(self, row):
        volatility = (
            row.get('rivalry_factor', 0.3) * self.volatility_weights['rivalry_factor'] +
            row.get('team_inconsistency', 0.3) * self.volatility_weights['team_inconsistency'] +
            row.get('injury_uncertainty', 0.3) * self.volatility_weights['injury_uncertainty'] +
            row.get('schedule_fatigue', 0.3) * self.volatility_weights['schedule_fatigue']
        )
        
        if row.get('sport') == 'mlb':
            volatility += 0.10
        
        if row.get('sport') == 'soccer':
            volatility += 0.05
        
        return round(min(volatility, 0.95), 2)
    
    # ============================================
    # MARKET RESPECT
    # ============================================
    def market_respect_penalty(self, model_prob, market_prob):
        diff = abs(model_prob - market_prob)
        if diff > 0.15:
            return diff * 0.2
        return 0
    
    # ============================================
    # EVALUACIÓN
    # ============================================
    def evaluate_match(self, row, sport='nba'):
        if sport == 'nba':
            probability = self.nba_probability(row)
        elif sport == 'mlb':
            probability = self.mlb_probability(row)
        else:
            probability = self.soccer_probability(row)
        
        volatility = self.volatility_model(row)
        odds = row.get('odds', 2.0) or 2.0
        edge = self.calculate_edge(probability, odds)
        
        market_prob = self.implied_probability(odds)
        penalty = self.market_respect_penalty(probability, market_prob)
        edge -= penalty
        
        conf_score = self.confidence_score(probability, volatility, edge)
        conf_level = self.confidence_level(conf_score)
        
        approved = (
            probability >= self.min_probability and
            volatility <= self.max_volatility and
            edge >= self.min_edge
        )
        
        return {
            'match': row.get('match', 'N/A'),
            'home_team': row.get('home_team', ''),
            'away_team': row.get('away_team', ''),
            'probability': round(probability, 4),
            'volatility': volatility,
            'edge': round(edge, 4),
            'market_penalty': round(penalty, 4),
            'confidence_score': conf_score,
            'confidence_level': conf_level,
            'odds': odds,
            'market_prob': round(market_prob, 4),
            'approved': approved
        }