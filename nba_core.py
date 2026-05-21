"""
NBA CORE ENGINE - Motor principal con Injury Impact Weighting
"""
from config_nba import *

class NBACore:
    def __init__(self):
        self.weights = NBA_WEIGHTS
        self.min_prob = MIN_PROBABILITY_NBA
        self.max_vol = MAX_VOLATILITY_NBA
        self.min_edge = MIN_EDGE_NBA
    
    def implied_probability(self, odds):
        if odds > 0:
            return round(100 / (odds + 100), 4)
        else:
            return round(abs(odds) / (abs(odds) + 100), 4)
    
    def team_strength_score(self, record):
        try:
            w, l = map(int, record.split('-'))
            total = w + l
            return w / total if total > 0 else 0.5
        except:
            return 0.5
    
    def home_court_boost(self, is_home, is_playoff=False):
        base = 0.06 if is_home else 0.0
        if is_playoff:
            base *= 1.3
        return base
    
    def fatigue_penalty(self, fatigue_flags):
        if not fatigue_flags:
            return 0.0
        penalty = 0.0
        for flag in fatigue_flags:
            if flag == 'B2B':
                penalty += 0.06
            elif flag == '3in4':
                penalty += 0.10
            elif flag == 'OT':
                penalty += 0.04
            elif flag == 'RoadTrip4+':
                penalty += 0.05
            elif flag == 'RoadTrip6+':
                penalty += 0.08
        return min(0.15, penalty)
    
    def injury_impact(self, injuries):
        """
        Impacto PONDERADO por calidad del jugador
        """
        if not injuries:
            return 0.0
        
        impact = 0.0
        
        # TIER 1: Superestrellas
        tier1 = [
            'Nikola Jokic', 'Giannis Antetokounmpo', 'Luka Doncic',
            'Shai Gilgeous-Alexander', 'Jayson Tatum', 'Stephen Curry',
            'LeBron James', 'Kevin Durant', 'Joel Embiid',
            'Anthony Davis', 'Kawhi Leonard', 'James Harden',
            'Anthony Edwards', 'Victor Wembanyama'
        ]
        
        # TIER 2: Estrellas
        tier2 = [
            'Jalen Brunson', 'Donovan Mitchell', 'Tyrese Haliburton',
            'Damian Lillard', 'Devin Booker', 'Ja Morant',
            'Trae Young', 'Bam Adebayo', 'Jaylen Brown',
            'Domantas Sabonis', 'Julius Randle', 'Paolo Banchero',
            'DeAaron Fox', 'Rudy Gobert', 'Karl-Anthony Towns',
            'Kyrie Irving', 'Jimmy Butler', 'Paul George',
            'Lauri Markkanen', 'Zion Williamson', 'Chet Holmgren',
            'Jaren Jackson Jr.', 'Evan Mobley', 'Tyrese Maxey',
            'Scottie Barnes', 'Cade Cunningham', 'Alperen Sengun',
            'Franz Wagner', 'Brandon Ingram'
        ]
        
        # TIER 3: Titulares sólidos
        tier3 = [
            'Mikal Bridges', 'OG Anunoby', 'Jrue Holiday',
            'Kristaps Porzingis', 'Jamal Murray', 'Aaron Gordon',
            'Michael Porter Jr.', 'Desmond Bane', 'Jalen Williams',
            'CJ McCollum', 'DeMar DeRozan', 'Zach LaVine',
            'Bradley Beal', 'Draymond Green', 'Darius Garland',
            'Jarrett Allen', 'Nic Claxton', 'Myles Turner',
            'Brook Lopez', 'Khris Middleton', 'Marcus Smart',
            'Austin Reaves', 'Tyler Herro', 'Jordan Poole',
            'Kyle Kuzma', 'Jonas Valanciunas', 'Donte DiVincenzo'
        ]
        
        for injury in injuries:
            player = injury.replace('OUT: ', '').replace('QUESTIONABLE: ', '').replace('DOUBTFUL: ', '')
            
            if any(p.lower() in player.lower() for p in tier1):
                weight = 0.10
            elif any(p.lower() in player.lower() for p in tier2):
                weight = 0.06
            elif any(p.lower() in player.lower() for p in tier3):
                weight = 0.03
            else:
                weight = 0.01
            
            if 'OUT' in injury:
                impact += weight
            elif 'QUESTIONABLE' in injury:
                impact += weight * 0.5
            elif 'DOUBTFUL' in injury:
                impact += weight * 0.7
        
        return min(0.30, impact)
    
    def playoff_intensity(self, is_playoff, is_elimination=False):
        if is_elimination:
            return 0.08
        elif is_playoff:
            return 0.04
        return 0.0
    
    def line_movement_signal(self, open_line, current_line):
        if open_line == 0 or current_line == 0:
            return 'NORMAL'
        movement = current_line - open_line
        if abs(movement) >= 1.5:
            if movement > 0:
                return 'SHARP_HOME'
            else:
                return 'SHARP_AWAY'
        return 'NORMAL'
    
    def calculate_nba_probability(self, home_data, away_data):
        home_win_pct = self.team_strength_score(home_data.get('record', '41-41'))
        away_win_pct = self.team_strength_score(away_data.get('record', '41-41'))
        
        home_boost = self.home_court_boost(home_data.get('is_home', True),
                                           home_data.get('is_playoff', False))
        
        home_net = home_data.get('net_rating', 0)
        away_net = away_data.get('net_rating', 0)
        net_diff = (home_net - away_net) / 20
        
        home_fatigue = self.fatigue_penalty(home_data.get('fatigue', []))
        away_fatigue = self.fatigue_penalty(away_data.get('fatigue', []))
        
        home_injuries = self.injury_impact(home_data.get('injuries', []))
        away_injuries = self.injury_impact(away_data.get('injuries', []))
        
        home_playoff = self.playoff_intensity(
            home_data.get('is_playoff', False),
            home_data.get('is_elimination', False)
        )
        away_playoff = self.playoff_intensity(
            away_data.get('is_playoff', False),
            away_data.get('is_elimination', False)
        )
        
        home_last10 = home_data.get('last10', '5-5')
        away_last10 = away_data.get('last10', '5-5')
        try:
            home_l10_wins = int(home_last10.split('-')[0]) / 10
        except:
            home_l10_wins = 0.5
        try:
            away_l10_wins = int(away_last10.split('-')[0]) / 10
        except:
            away_l10_wins = 0.5
        
        home_score = (
            home_win_pct * self.weights['team_strength'] +
            home_boost * self.weights['home_court'] +
            (0.5 + net_diff * 0.5) * self.weights['team_strength'] +
            (1.0 - home_fatigue) * self.weights['fatigue'] +
            (1.0 - home_injuries) * self.weights['injuries'] +
            home_playoff * self.weights['playoff'] +
            home_l10_wins * self.weights['momentum'] +
            0.5 * self.weights['rest']
        )
        
        away_score = (
            away_win_pct * self.weights['team_strength'] +
            (1.0 - away_fatigue) * self.weights['fatigue'] +
            (1.0 - away_injuries) * self.weights['injuries'] +
            away_playoff * self.weights['playoff'] +
            away_l10_wins * self.weights['momentum'] +
            0.5 * self.weights['rest']
        )
        
        total = home_score + away_score
        probability = home_score / total if total > 0 else 0.5
        
        return min(0.85, max(0.15, probability))
    
    def nba_volatility(self, home_data, away_data):
        vol = 0.25
        
        if home_data.get('injuries') or away_data.get('injuries'):
            vol += 0.06
        if home_data.get('fatigue') or away_data.get('fatigue'):
            vol += 0.05
        if home_data.get('is_playoff'):
            vol += 0.04
        
        return min(0.65, vol)
    
    def evaluate_nba_game(self, home_data, away_data, market_odds):
        probability = self.calculate_nba_probability(home_data, away_data)
        volatility = self.nba_volatility(home_data, away_data)
        
        market_prob = self.implied_probability(market_odds)
        edge = probability - market_prob
        
        confidence = (probability - 0.5) * 0.4 + abs(edge) * 3 + (1 - volatility) * 0.2
        confidence = min(1.0, max(0.0, confidence))
        
        if confidence >= 0.65 and edge > 0.03:
            level = 'A+'
        elif confidence >= 0.50 and edge > 0.02:
            level = 'A'
        elif confidence >= 0.35 and edge > 0:
            level = 'B'
        else:
            level = 'C'
        
        approved = (probability >= self.min_prob and 
                   volatility <= self.max_vol and 
                   edge >= self.min_edge)
        
        return {
            'probability': round(probability, 4),
            'volatility': round(volatility, 2),
            'edge': round(edge, 4),
            'market_prob': round(market_prob, 4),
            'confidence_score': round(confidence, 3),
            'confidence_level': level,
            'approved': approved
        }