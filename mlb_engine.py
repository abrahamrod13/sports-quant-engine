"""
MLB QUANT ENGINE V5 - Weighted Features + Sample Control + Data Corruption Fix
Season 60% | Last3 25% | Bullpen 10% | H2H 5%
"""
import numpy as np

class MLBEngine:
    def __init__(self):
        self.park_factors = {
            'Coors Field': {'runs': 1.35, 'hr': 1.25, 'volatility': 0.12},
            'Yankee Stadium': {'runs': 1.08, 'hr': 1.18, 'volatility': 0.05},
            'Fenway Park': {'runs': 1.10, 'hr': 0.95, 'volatility': 0.06},
            'Tropicana Field': {'runs': 0.92, 'hr': 0.88, 'volatility': -0.03},
            'Dodger Stadium': {'runs': 0.95, 'hr': 0.98, 'volatility': -0.02},
            'Wrigley Field': {'runs': 1.05, 'hr': 1.10, 'volatility': 0.04},
            'Petco Park': {'runs': 0.93, 'hr': 0.95, 'volatility': -0.01},
            'Oracle Park': {'runs': 0.94, 'hr': 0.85, 'volatility': -0.02},
            'Minute Maid Park': {'runs': 1.02, 'hr': 1.05, 'volatility': 0.02},
            'Nationals Park': {'runs': 1.00, 'hr': 1.02, 'volatility': 0.01},
            'Progressive Field': {'runs': 1.02, 'hr': 1.00, 'volatility': 0.01},
            'Angel Stadium': {'runs': 0.97, 'hr': 0.98, 'volatility': -0.01},
            'Target Field': {'runs': 0.98, 'hr': 0.95, 'volatility': -0.01},
            'T-Mobile Park': {'runs': 0.93, 'hr': 0.92, 'volatility': -0.02},
            'Comerica Park': {'runs': 0.96, 'hr': 0.90, 'volatility': -0.01},
            'Kauffman Stadium': {'runs': 1.02, 'hr': 0.95, 'volatility': 0.01},
            'Guaranteed Rate Field': {'runs': 1.04, 'hr': 1.08, 'volatility': 0.03},
            'Rogers Centre': {'runs': 1.00, 'hr': 1.05, 'volatility': 0.02},
            'Chase Field': {'runs': 1.05, 'hr': 1.02, 'volatility': 0.03},
            'Great American Ball Park': {'runs': 1.08, 'hr': 1.15, 'volatility': 0.06},
            'PNC Park': {'runs': 0.97, 'hr': 0.88, 'volatility': -0.02},
            'Busch Stadium': {'runs': 0.95, 'hr': 0.90, 'volatility': -0.02},
            'American Family Field': {'runs': 1.02, 'hr': 1.08, 'volatility': 0.03},
            'Citizens Bank Park': {'runs': 1.05, 'hr': 1.18, 'volatility': 0.06},
            'loanDepot park': {'runs': 0.96, 'hr': 0.85, 'volatility': -0.02},
            'Truist Park': {'runs': 1.02, 'hr': 1.05, 'volatility': 0.02},
            'Camden Yards': {'runs': 1.04, 'hr': 1.10, 'volatility': 0.04},
        }
        self.default_park = {'runs': 1.00, 'hr': 1.00, 'volatility': 0.0}
    
    def smart_pitcher_defaults(self, pitcher_name):
        aces = ['Shane McClanahan', 'Tarik Skubal', 'Corbin Burnes', 'Zack Wheeler',
                'Logan Webb', 'Luis Castillo', 'Framber Valdez', 'Tyler Glasnow',
                'Pablo López', 'Max Fried', 'Sandy Alcantara', 'Jacob deGrom',
                'Gerrit Cole', 'Shohei Ohtani', 'Spencer Strider', 'Chris Sale',
                'Blake Snell', 'Zac Gallen', 'Sonny Gray', 'Paul Skenes',
                'Yoshinobu Yamamoto', 'Freddy Peralta']
        good = ['Tanner Bibee', 'Gavin Williams', 'George Kirby', 'Logan Gilbert',
                'Kevin Gausman', 'José Berríos', 'Chris Bassitt', 'Merrill Kelly',
                'Aaron Nola', 'Justin Steele', 'Joe Ryan', 'Bailey Ober',
                'Hunter Brown', 'Brayan Bello', 'Tanner Houck', 'Reid Detmers',
                'Kyle Bradish', 'Grayson Rodriguez', 'Bryan Woo', 'Bryce Miller',
                'Brandon Pfaadt', 'Cole Ragans', 'Brady Singer', 'Miles Mikolas',
                'Erick Fedde', 'Zack Littell', 'Jeffrey Springs', 'MacKenzie Gore']
        weak = ['Patrick Corbin', 'Jordan Lyles', 'Kyle Freeland', 'Austin Gomber',
                'Martín Pérez', 'Jake Irvin', 'Joey Wentz', 'Kris Bubic',
                'Slade Cecconi', 'Walbert Ureña', 'Will Warren', 'Grant Holmes',
                'Colin Rea', 'Brandon Sproat']
        
        name = pitcher_name or ''
        
        if any(ace in name for ace in aces):
            return {'era': 2.85, 'whip': 1.05, 'k9': 10.5, 'bb9': 2.0,
                    'hr9': 0.8, 'innings': 60, 'babip': 0.280}
        elif any(g in name for g in good):
            return {'era': 3.50, 'whip': 1.18, 'k9': 8.8, 'bb9': 2.6,
                    'hr9': 1.0, 'innings': 50, 'babip': 0.290}
        elif any(w in name for w in weak):
            return {'era': 5.20, 'whip': 1.50, 'k9': 6.5, 'bb9': 3.5,
                    'hr9': 1.5, 'innings': 35, 'babip': 0.310}
        else:
            return {'era': 4.20, 'whip': 1.32, 'k9': 7.8, 'bb9': 2.9,
                    'hr9': 1.2, 'innings': 40, 'babip': 0.290}
    
    def calculate_fip(self, pitcher_data):
        hr9 = pitcher_data.get('hr9', 1.2)
        bb9 = pitcher_data.get('bb9', 3.0)
        k9 = pitcher_data.get('k9', 7.5)
        innings = pitcher_data.get('innings', 30)
        if innings == 0:
            return pitcher_data.get('era', 4.50)
        hr_total = (hr9 * innings) / 9
        bb_total = (bb9 * innings) / 9
        k_total = (k9 * innings) / 9
        fip = ((13 * hr_total) + (3 * bb_total) - (2 * k_total)) / innings + 3.10
        return round(fip, 2)
    
    def advanced_pitcher_score(self, pitcher_data):
        era = pitcher_data.get('era', 4.50)
        fip = self.calculate_fip(pitcher_data)
        k9 = pitcher_data.get('k9', 7.5)
        bb9 = pitcher_data.get('bb9', 3.0)
        hr9 = pitcher_data.get('hr9', 1.2)
        whip = pitcher_data.get('whip', 1.35)
        babip = pitcher_data.get('babip', 0.290)
        luck_factor = (babip - 0.290) / 0.030
        
        whip_penalty = 0
        if whip > 2.20:
            whip_penalty = 0.10
        elif whip > 1.90:
            whip_penalty = 0.06
        elif whip > 1.60:
            whip_penalty = 0.03
        
        score = (
            (4.50 / max(fip, 0.5)) * 0.25 +
            (4.50 / max(era, 0.5)) * 0.15 +
            (1.30 / max(whip, 0.5)) * 0.15 +
            (k9 / 9.0) * 0.15 +
            (2.5 / max(bb9, 0.5)) * 0.10 +
            (1.0 / max(hr9, 0.2)) * 0.10 +
            (1.0 - luck_factor * 0.3) * 0.10 -
            whip_penalty
        )
        return min(1.20, max(0.20, score))
    
    def pitcher_score(self, pitcher_data):
        return self.advanced_pitcher_score(pitcher_data)
    
    def momentum_score(self, team_data):
        last10 = team_data.get('last10_wins', 5) / 10
        streak = team_data.get('streak', 0)
        run_diff = team_data.get('run_diff_last10', 0)
        ops = team_data.get('ops_last7', 0.720)
        era = team_data.get('era_last7', 4.50)
        run_diff_norm = min(1.0, max(-1.0, run_diff / 20))
        streak_norm = min(1.0, max(-1.0, streak / 5))
        ops_norm = (ops - 0.650) / 0.200
        era_norm = (5.00 - era) / 2.00
        score = (
            last10 * 0.20 + (streak_norm + 1) / 2 * 0.15 +
            (run_diff_norm + 1) / 2 * 0.20 + ops_norm * 0.25 + era_norm * 0.20
        )
        return min(1.0, max(0.0, score))
    
    def offensive_context_score(self, team_data, opponent_pitcher):
        ops = team_data.get('ops_last7', 0.720)
        runs = team_data.get('runs_last5', 20)
        hard_hit = team_data.get('hard_hit_rate', 0.35)
        ops_score = (ops - 0.650) / 0.200
        runs_score = (runs - 20) / 10
        hard_hit_score = (hard_hit - 0.30) / 0.10
        pitcher_era = opponent_pitcher.get('era', 4.50)
        pitcher_vulnerability = (pitcher_era - 3.50) / 2.00
        score = ops_score * 0.35 + runs_score * 0.25 + hard_hit_score * 0.20 + pitcher_vulnerability * 0.20
        return min(1.5, max(-0.5, score))
    
    def bullpen_score(self, bullpen_data):
        era = bullpen_data.get('era', 4.50)
        whip = bullpen_data.get('whip', 1.40)
        last3_ip = bullpen_data.get('last3_innings', 10)
        save_pct = bullpen_data.get('save_pct', 0.60)
        fatigue = bullpen_data.get('fatigue', 'NORMAL')
        fatigue_penalty = 0
        if fatigue == 'HIGH':
            fatigue_penalty = 0.10
        elif fatigue == 'CRITICAL':
            fatigue_penalty = 0.20
        score = (
            (4.50 / max(era, 0.5)) * 0.35 + (1.30 / max(whip, 0.5)) * 0.25 +
            save_pct * 0.20 - fatigue_penalty * 0.20
        )
        return min(1.10, max(0.20, score))
    
    def matchup_factor(self, matchup_data):
        avg = matchup_data.get('avg', 0.250)
        ops = matchup_data.get('ops', 0.720)
        hr = matchup_data.get('hr', 1)
        k_rate = matchup_data.get('k_rate', 0.23)
        sample = matchup_data.get('pa', 0)
        avg_factor = (avg - 0.250) / 0.050
        ops_factor = (ops - 0.720) / 0.100
        hr_factor = min(hr / 5, 1.0)
        k_factor = (0.25 - k_rate) / 0.10
        raw_score = avg_factor * 0.20 + ops_factor * 0.30 + hr_factor * 0.20 + k_factor * 0.15
        if sample < 30:
            raw_score *= (sample / 30)
        return raw_score
    
    def park_adjustment(self, stadium_name):
        return self.park_factors.get(stadium_name, self.default_park)
    
    def mlb_volatility(self, row):
        base_vol = 0.28
        boosts = 0
        if row.get('divisional_game', False):
            boosts += 0.08
        if row.get('bullpen_home_weak', False):
            boosts += 0.06
        if row.get('bullpen_away_weak', False):
            boosts += 0.06
        if row.get('hr_heavy_teams', False):
            boosts += 0.07
        if row.get('wind_outward', False):
            boosts += 0.05
        park = self.park_adjustment(row.get('stadium', ''))
        boosts += park.get('volatility', 0)
        home_p = self.pitcher_score(row.get('home_pitcher', {}))
        away_p = self.pitcher_score(row.get('away_pitcher', {}))
        if home_p < 0.55 and away_p < 0.55:
            boosts += 0.10
        if home_p > 0.75 and away_p > 0.75:
            boosts -= 0.08
        final_vol = base_vol + boosts
        return min(0.82, max(0.20, final_vol))
    
    def calculate_mlb_probability(self, game_data):
        WEIGHTS = {
            'pitcher_season': 0.28,
            'momentum': 0.12,
            'bullpen': 0.10,
            'matchup': 0.05,
            'offensive': 0.10,
            'park': 0.05,
            'base': 0.20
        }
        
        # Pitcher season
        home_pitcher_season = self.pitcher_score(game_data.get('home_pitcher', {}))
        away_pitcher_season = self.pitcher_score(game_data.get('away_pitcher', {}))
        
        # Pitcher Last3 (si hay datos y son válidos)
        home_last3 = game_data.get('home_pitcher', {}).get('last3_era')
        away_last3 = game_data.get('away_pitcher', {}).get('last3_era')
        
        if home_last3 and home_last3 < 15:
            home_pitcher_last3 = 4.50 / max(home_last3, 0.5)
        else:
            home_pitcher_last3 = home_pitcher_season
        
        if away_last3 and away_last3 < 15:
            away_pitcher_last3 = 4.50 / max(away_last3, 0.5)
        else:
            away_pitcher_last3 = away_pitcher_season
        
        # Combinado: 70% season, 30% last3
        home_pitcher_combined = home_pitcher_season * 0.70 + home_pitcher_last3 * 0.30
        away_pitcher_combined = away_pitcher_season * 0.70 + away_pitcher_last3 * 0.30
        
        # Momentum
        home_momentum = self.momentum_score(game_data.get('home_momentum', {}))
        away_momentum = self.momentum_score(game_data.get('away_momentum', {}))
        
        # Bullpen
        home_bullpen = self.bullpen_score(game_data.get('home_bullpen', {}))
        away_bullpen = self.bullpen_score(game_data.get('away_bullpen', {}))
        
        # Matchup con SAMPLE CONTROL estricto
        home_matchup_raw = self.matchup_factor(game_data.get('home_matchup', {}))
        away_matchup_raw = self.matchup_factor(game_data.get('away_matchup', {}))
        
        # Si PA < 30, reducir peso
        home_matchup_pa = game_data.get('home_matchup', {}).get('pa', 0)
        away_matchup_pa = game_data.get('away_matchup', {}).get('pa', 0)
        if home_matchup_pa < 30:
            home_matchup_raw *= (home_matchup_pa / 30)
        if away_matchup_pa < 30:
            away_matchup_raw *= (away_matchup_pa / 30)
        
        home_win_pct = game_data.get('home_win_pct', 0.5)
        away_win_pct = game_data.get('away_win_pct', 0.5)
        
        # Ofensiva contextual
        home_offensive = self.offensive_context_score(
            game_data.get('home_momentum', {}), game_data.get('away_pitcher', {}))
        away_offensive = self.offensive_context_score(
            game_data.get('away_momentum', {}), game_data.get('home_pitcher', {}))
        
        park = self.park_adjustment(game_data.get('stadium', ''))
        park_runs_factor = park.get('runs', 1.0)
        
        pitcher_diff = home_pitcher_combined - away_pitcher_combined
        pitcher_amplified = 1.0 + pitcher_diff * 0.4
        
        home_score = (
            home_pitcher_combined * WEIGHTS['pitcher_season'] * pitcher_amplified +
            home_momentum * WEIGHTS['momentum'] +
            home_bullpen * WEIGHTS['bullpen'] +
            (0.5 + home_matchup_raw) * WEIGHTS['matchup'] +
            (0.5 + home_offensive * 0.25) * WEIGHTS['offensive'] +
            home_win_pct * WEIGHTS['base']
        )
        
        away_score = (
            away_pitcher_combined * WEIGHTS['pitcher_season'] * (2 - pitcher_amplified) +
            away_momentum * WEIGHTS['momentum'] +
            away_bullpen * WEIGHTS['bullpen'] +
            (0.5 + away_matchup_raw) * WEIGHTS['matchup'] +
            (0.5 + away_offensive * 0.25) * WEIGHTS['offensive'] +
            away_win_pct * WEIGHTS['base']
        )
        
        home_score *= (1.04 + (park_runs_factor - 1.0) * 0.3)
        
        total = home_score + away_score
        probability = home_score / total if total > 0 else 0.5
        probability = 0.5 + (probability - 0.5) * 1.6
        
        return min(0.80, max(0.20, probability))
    
    def mlb_confidence(self, probability, edge, volatility, pitcher_diff, momentum_diff):
        confidence = (
            (probability - 0.5) * 0.30 + abs(edge) * 2.5 +
            (1 - volatility) * 0.15 + abs(momentum_diff) * 0.20 + abs(pitcher_diff) * 0.20
        )
        return round(min(1.0, max(0.0, confidence)), 3)
    
    def detect_underdog_value(self, probability, odds, home_team, away_team):
        market_prob = 1 / odds if odds > 1 else 0.5
        if market_prob < 0.5:
            underdog = home_team
            underdog_market_prob = market_prob
        else:
            underdog = away_team
            underdog_market_prob = 1 - market_prob
        model_underdog_prob = probability if underdog == home_team else (1 - probability)
        if model_underdog_prob > underdog_market_prob + 0.04:
            return {
                'underdog': underdog,
                'market_prob': round(underdog_market_prob, 3),
                'model_prob': round(model_underdog_prob, 3),
                'value_detected': True,
                'edge': round(model_underdog_prob - underdog_market_prob, 4)
            }
        return {'value_detected': False}
    
    def evaluate_mlb_game(self, game_data, odds=2.0):
        if not game_data.get('home_pitcher') or len(game_data.get('home_pitcher', {})) == 0:
            game_data['home_pitcher'] = self.smart_pitcher_defaults(game_data.get('home_pitcher_name', ''))
        if not game_data.get('away_pitcher') or len(game_data.get('away_pitcher', {})) == 0:
            game_data['away_pitcher'] = self.smart_pitcher_defaults(game_data.get('away_pitcher_name', ''))
        
        probability = self.calculate_mlb_probability(game_data)
        volatility = self.mlb_volatility(game_data)
        market_prob = 1 / odds if odds > 1 else 0.5
        edge = probability - market_prob
        
        home_p = self.pitcher_score(game_data.get('home_pitcher', {}))
        away_p = self.pitcher_score(game_data.get('away_pitcher', {}))
        pitcher_diff = home_p - away_p
        
        home_m = self.momentum_score(game_data.get('home_momentum', {}))
        away_m = self.momentum_score(game_data.get('away_momentum', {}))
        momentum_diff = home_m - away_m
        
        confidence = self.mlb_confidence(probability, edge, volatility, pitcher_diff, momentum_diff)
        
        if edge <= 0:
            confidence = min(confidence, 0.45)
        
        if confidence >= 0.65 and edge > 0.03:
            level = 'A+'
        elif confidence >= 0.50 and edge > 0.02:
            level = 'A'
        elif confidence >= 0.35 and edge > 0:
            level = 'B'
        else:
            level = 'C'
        
        underdog_check = self.detect_underdog_value(probability, odds, 
            game_data.get('home_team', ''), game_data.get('away_team', ''))
        
        pick = game_data.get('home_team', '') if (edge > 0 and probability >= 0.5) else (
            game_data.get('away_team', '') if (edge > 0 and probability < 0.5) else 'NO PICK')
        
        return {
            'probability': round(probability, 4),
            'volatility': round(volatility, 2),
            'edge': round(edge, 4),
            'confidence_score': confidence,
            'confidence_level': level,
            'pick': pick,
            'pitcher_home': round(home_p, 3),
            'pitcher_away': round(away_p, 3),
            'momentum_home': round(home_m, 3),
            'momentum_away': round(away_m, 3),
            'market_prob': round(market_prob, 4),
            'underdog_value': underdog_check['value_detected'],
            'underdog_info': underdog_check if underdog_check['value_detected'] else None
        }