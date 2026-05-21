"""
NBA QUANT ENGINE - 15 Módulos Especializados
Team Power, Player Availability, Form, Home/Away, Matchup, 
Schedule Fatigue, Playoff Intensity, Clutch, Market, Volatility,
Player Matchup, Bench, Shooting Variance, Rebound, Confidence
"""
import numpy as np

class NBAEngine:
    def __init__(self):
        # Team power ratings base (se actualizan con datos reales)
        self.team_ratings = {}
    
    # ============================================
    # 1. TEAM POWER RATING ENGINE
    # ============================================
    def team_power_score(self, team_data):
        """
        team_data = {'off_rating': 118, 'def_rating': 110, 'net_rating': 8, 'pace': 102, 'efg': 0.56}
        """
        off_rtg = team_data.get('off_rating', 112)
        def_rtg = team_data.get('def_rating', 112)
        net_rtg = team_data.get('net_rating', off_rtg - def_rtg)
        pace = team_data.get('pace', 100)
        efg = team_data.get('efg', 0.54)
        
        # Normalizar
        net_score = (net_rtg + 10) / 25
        off_score = (off_rtg - 100) / 20
        def_score = (115 - def_rtg) / 20
        efg_score = (efg - 0.48) / 0.10
        
        score = (
            net_score * 0.30 +
            off_score * 0.20 +
            def_score * 0.20 +
            efg_score * 0.15 +
            (pace / 100) * 0.15
        )
        
        return min(1.20, max(0.30, score))
    
    # ============================================
    # 2. PLAYER AVAILABILITY ENGINE
    # ============================================
    def injury_impact(self, team_name, injuries):
        """Calcula impacto de lesiones en el rating del equipo"""
        if not injuries:
            return 1.0
        
        impact = 0
        
        # Estrellas que cambian el equipo
        critical_stars = {
            'Joel Embiid': 8,
            'Nikola Jokic': 9,
            'Giannis Antetokounmpo': 9,
            'Jayson Tatum': 7,
            'Luka Doncic': 8,
            'Shai Gilgeous-Alexander': 7,
            'Jalen Brunson': 6,
            'Anthony Edwards': 6,
            'Victor Wembanyama': 6,
            'LeBron James': 7,
            'Stephen Curry': 7,
            'Kevin Durant': 6,
        }
        
        for injury in injuries:
            for star, star_impact in critical_stars.items():
                if star.lower() in injury.lower():
                    if 'out' in injury.lower():
                        impact += star_impact
                    elif 'questionable' in injury.lower():
                        impact += star_impact * 0.5
                    elif 'probable' in injury.lower():
                        impact += star_impact * 0.2
        
        # Convertir impacto a multiplicador (0.7 = -30% de poder)
        return max(0.55, 1.0 - (impact / 100))
    
    # ============================================
    # 3. RECENT FORM ENGINE
    # ============================================
    def recent_form_score(self, form_data):
        """
        form_data = {'last5_net': 5, 'last10_net': 3, 'streak': 3, 'off_eff_last5': 118}
        """
        last5 = form_data.get('last5_net', 0) / 15
        last10 = form_data.get('last10_net', 0) / 20
        streak = form_data.get('streak', 0) / 7
        off_eff = (form_data.get('off_eff_last5', 112) - 105) / 20
        
        score = (
            last5 * 0.35 +
            last10 * 0.25 +
            streak * 0.20 +
            off_eff * 0.20
        )
        
        return min(1.0, max(-0.5, score))
    
    # ============================================
    # 4. HOME/AWAY SPLIT ENGINE
    # ============================================
    def home_away_factor(self, is_home, is_playoff=False):
        """Factor de localía"""
        base = 1.05 if is_home else 0.95
        
        # Playoffs: localía más importante
        if is_playoff:
            base = 1.08 if is_home else 0.92
        
        # Altitude boost (Denver, Utah)
        return base
    
    # ============================================
    # 5. MATCHUP ENGINE
    # ============================================
    def matchup_score(self, offense_style, defense_style):
        """
        offense_style = {'three_rate': 0.42, 'paint_focus': 0.35, 'pace': 102}
        defense_style = {'three_defense': 'elite', 'paint_defense': 'weak', 'transition_def': 'avg'}
        """
        score_diff = 0
        
        # Triple vs defensa perimetral
        three_rate = offense_style.get('three_rate', 0.38)
        three_def = defense_style.get('three_defense', 'avg')
        
        three_def_mult = {'elite': 0.85, 'good': 0.93, 'avg': 1.0, 'weak': 1.07, 'bad': 1.15}
        score_diff += (three_rate * 0.40) * three_def_mult.get(three_def, 1.0)
        
        # Pintura vs defensa interior
        paint_focus = offense_style.get('paint_focus', 0.40)
        paint_def = defense_style.get('paint_defense', 'avg')
        paint_def_mult = {'elite': 0.80, 'good': 0.90, 'avg': 1.0, 'weak': 1.10, 'bad': 1.20}
        score_diff += (paint_focus * 0.35) * paint_def_mult.get(paint_def, 1.0)
        
        return score_diff
    
    # ============================================
    # 6. SCHEDULE FATIGUE ENGINE
    # ============================================
    def fatigue_penalty(self, fatigue_data):
        """
        fatigue_data = {'back_to_back': False, 'third_in_four': False, 'road_trip_games': 2, 'ot_previous': False}
        """
        penalty = 0
        
        if fatigue_data.get('back_to_back', False):
            penalty += 0.08
        if fatigue_data.get('third_in_four', False):
            penalty += 0.12
        if fatigue_data.get('ot_previous', False):
            penalty += 0.06
        
        road_games = fatigue_data.get('road_trip_games', 0)
        if road_games >= 4:
            penalty += 0.10
        elif road_games >= 2:
            penalty += 0.05
        
        return penalty
    
    # ============================================
    # 7. PLAYOFF INTENSITY ENGINE
    # ============================================
    def playoff_adjustment(self, is_playoff, star_power):
        """Ajuste por intensidad de playoffs"""
        if not is_playoff:
            return 1.0
        
        # Playoffs: estrellas valen más, rotación más corta
        return 0.95 + (star_power * 0.10)
    
    # ============================================
    # 8. CLUTCH ENGINE
    # ============================================
    def clutch_score(self, clutch_data):
        """
        clutch_data = {'net_rating': 5, 'ft_pct': 0.82, 'to_rate': 0.12}
        """
        net = clutch_data.get('net_rating', 0) / 15
        ft = (clutch_data.get('ft_pct', 0.75) - 0.70) / 0.20
        to = (0.15 - clutch_data.get('to_rate', 0.13)) / 0.08
        
        return (net * 0.40 + ft * 0.30 + to * 0.30)
    
    # ============================================
    # 9. SHOOTING VARIANCE ENGINE
    # ============================================
    def shooting_volatility(self, three_rate, three_pct):
        """Equipos que dependen del triple son más volátiles"""
        base_vol = 0
        
        if three_rate > 0.42:
            base_vol += 0.06
        if three_rate > 0.38:
            base_vol += 0.04
        
        # Si el % de triple es bajo pero tiran mucho = alta varianza
        if three_rate > 0.40 and three_pct < 0.34:
            base_vol += 0.05
        
        return base_vol
    
    # ============================================
    # 10. REBOUND ENGINE
    # ============================================
    def rebound_advantage(self, off_reb_rate, def_reb_rate, opp_off_reb, opp_def_reb):
        """Diferencia de rebotes crea posesiones extra"""
        own_total = off_reb_rate + def_reb_rate
        opp_total = opp_off_reb + opp_def_reb
        
        diff = own_total - opp_total
        
        # Cada rebote extra = ~1.1 puntos de ventaja
        return diff * 0.03
    
    # ============================================
    # 11. BENCH DEPTH ENGINE
    # ============================================
    def bench_score(self, bench_net, bench_minutes):
        """
        bench_net: net rating de la banca
        bench_minutes: minutos promedio de banca
        """
        net_score = bench_net / 20
        depth_score = bench_minutes / 48  # Más minutos = más profundo
        
        return (net_score * 0.60 + depth_score * 0.40)
    
    # ============================================
    # NBA VOLATILITY
    # ============================================
    def nba_volatility(self, row):
        base_vol = 0.22
        
        # Factores que aumentan volatilidad
        if row.get('back_to_back', False):
            base_vol += 0.06
        if row.get('young_team', False):
            base_vol += 0.05
        if row.get('high_three_volume', False):
            base_vol += 0.06
        if row.get('injuries_present', False):
            base_vol += 0.08
        if row.get('is_playoff', False):
            base_vol += 0.04
        
        # Shooting variance
        three_rate = row.get('three_rate', 0.38)
        three_pct = row.get('three_pct', 0.36)
        base_vol += self.shooting_volatility(three_rate, three_pct)
        
        return min(0.65, max(0.18, base_vol))
    
    # ============================================
    # NBA PROBABILITY ENGINE
    # ============================================
    def calculate_nba_probability(self, game_data):
        WEIGHTS = {
            'power': 0.25,
            'form': 0.15,
            'home': 0.10,
            'matchup': 0.10,
            'fatigue': 0.08,
            'injuries': 0.12,
            'playoff': 0.05,
            'clutch': 0.05,
            'bench': 0.05,
            'rebound': 0.05
        }
        
        # 1. Power Rating
        home_power = self.team_power_score(game_data.get('home_stats', {}))
        away_power = self.team_power_score(game_data.get('away_stats', {}))
        
        # 2. Injury Impact
        home_injury_mult = self.injury_impact(
            game_data.get('home_team', ''), 
            game_data.get('home_injuries', [])
        )
        away_injury_mult = self.injury_impact(
            game_data.get('away_team', ''),
            game_data.get('away_injuries', [])
        )
        
        # 3. Recent Form
        home_form = self.recent_form_score(game_data.get('home_form', {}))
        away_form = self.recent_form_score(game_data.get('away_form', {}))
        
        # 4. Home/Away
        is_playoff = game_data.get('is_playoff', False)
        home_factor = self.home_away_factor(True, is_playoff)
        away_factor = self.home_away_factor(False, is_playoff)
        
        # 5. Matchup
        matchup = self.matchup_score(
            game_data.get('home_offense_style', {}),
            game_data.get('away_defense_style', {})
        )
        
        # 6. Fatigue
        home_fatigue = self.fatigue_penalty(game_data.get('home_fatigue', {}))
        away_fatigue = self.fatigue_penalty(game_data.get('away_fatigue', {}))
        
        # 7. Playoff
        home_playoff = self.playoff_adjustment(is_playoff, home_power)
        away_playoff = self.playoff_adjustment(is_playoff, away_power)
        
        # 8. Clutch
        home_clutch = self.clutch_score(game_data.get('home_clutch', {}))
        away_clutch = self.clutch_score(game_data.get('away_clutch', {}))
        
        # 9. Bench
        home_bench = self.bench_score(
            game_data.get('home_bench_net', 0),
            game_data.get('home_bench_minutes', 20)
        )
        away_bench = self.bench_score(
            game_data.get('away_bench_net', 0),
            game_data.get('away_bench_minutes', 20)
        )
        
        # 10. Rebound
        rebound = self.rebound_advantage(
            game_data.get('home_off_reb', 0.25), game_data.get('home_def_reb', 0.72),
            game_data.get('away_off_reb', 0.24), game_data.get('away_def_reb', 0.71)
        )
        
        # Score final
        home_score = (
            home_power * home_injury_mult * WEIGHTS['power'] +
            (0.5 + home_form) * WEIGHTS['form'] +
            home_factor * WEIGHTS['home'] +
            matchup * WEIGHTS['matchup'] +
            (1.0 - home_fatigue) * WEIGHTS['fatigue'] +
            home_injury_mult * WEIGHTS['injuries'] +
            home_playoff * WEIGHTS['playoff'] +
            (0.5 + home_clutch) * WEIGHTS['clutch'] +
            (0.5 + home_bench) * WEIGHTS['bench'] +
            (0.5 + rebound) * WEIGHTS['rebound']
        )
        
        away_score = (
            away_power * away_injury_mult * WEIGHTS['power'] +
            (0.5 + away_form) * WEIGHTS['form'] +
            away_factor * WEIGHTS['home'] +
            (1.0 - matchup) * WEIGHTS['matchup'] +
            (1.0 - away_fatigue) * WEIGHTS['fatigue'] +
            away_injury_mult * WEIGHTS['injuries'] +
            away_playoff * WEIGHTS['playoff'] +
            (0.5 + away_clutch) * WEIGHTS['clutch'] +
            (0.5 + away_bench) * WEIGHTS['bench'] +
            (0.5 - rebound) * WEIGHTS['rebound']
        )
        
        total = home_score + away_score
        probability = home_score / total if total > 0 else 0.5
        
        # Expandir rango
        probability = 0.5 + (probability - 0.5) * 1.6
        
        return min(0.85, max(0.15, probability))
    
    # ============================================
    # NBA CONFIDENCE
    # ============================================
    def nba_confidence(self, probability, edge, volatility, power_diff, form_diff):
        confidence = (
            (probability - 0.5) * 0.30 +
            abs(edge) * 2.5 +
            (1 - volatility) * 0.20 +
            abs(power_diff) * 0.15 +
            abs(form_diff) * 0.15
        )
        return round(min(1.0, max(0.0, confidence)), 3)
    
    # ============================================
    # NBA EVALUATION
    # ============================================
    def evaluate_nba_game(self, game_data, odds=2.0):
        probability = self.calculate_nba_probability(game_data)
        volatility = self.nba_volatility(game_data)
        
        market_prob = 1 / odds if odds > 1 else 0.5
        edge = probability - market_prob
        
        home_power = self.team_power_score(game_data.get('home_stats', {}))
        away_power = self.team_power_score(game_data.get('away_stats', {}))
        power_diff = home_power - away_power
        
        home_form = self.recent_form_score(game_data.get('home_form', {}))
        away_form = self.recent_form_score(game_data.get('away_form', {}))
        form_diff = home_form - away_form
        
        confidence = self.nba_confidence(probability, edge, volatility, power_diff, form_diff)
        
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
        
        pick = game_data.get('home_team', '') if probability >= 0.5 else game_data.get('away_team', '')
        if edge <= 0:
            pick = 'NO PICK (edge -)'
        
        return {
            'probability': round(probability, 4),
            'volatility': round(volatility, 2),
            'edge': round(edge, 4),
            'confidence_score': confidence,
            'confidence_level': level,
            'pick': pick,
            'power_home': round(home_power, 3),
            'power_away': round(away_power, 3),
            'market_prob': round(market_prob, 4)
        }