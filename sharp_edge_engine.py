"""
SHARP EDGE ENGINE V6 - Capa adicional sobre V5
Detecta ineficiencias del mercado, no solo predice juegos
Se suma al sistema existente, no lo reemplaza
"""
import numpy as np

class SharpEdgeEngine:
    def __init__(self):
        self.overvalued_franchises = [
            'New York Yankees', 'Los Angeles Dodgers', 'Boston Red Sox',
            'Chicago Cubs', 'New York Mets', 'Philadelphia Phillies',
            'Atlanta Braves', 'Houston Astros', 'San Diego Padres',
            'St. Louis Cardinals'
        ]
        
        self.undervalued_franchises = [
            'Tampa Bay Rays', 'Milwaukee Brewers', 'Cleveland Guardians',
            'Arizona Diamondbacks', 'Seattle Mariners', 'Miami Marlins',
            'Pittsburgh Pirates', 'Cincinnati Reds', 'Kansas City Royals',
            'Oakland Athletics'
        ]
    
    # ============================================
    # 1. CHAOS ADJUSTMENT LAYER
    # ============================================
    
    def pitcher_shock_risk(self, pitcher_data):
        """
        PSR: Riesgo de colapso inesperado (0-1)
        """
        risk = 0.0
        
        # Last 3 ERA vs Season ERA (degradación reciente)
        season_era = pitcher_data.get('era', 4.50)
        last3_era = pitcher_data.get('last3_era', season_era)
        
        if last3_era and last3_era < 15:
            era_jump = last3_era - season_era
            if era_jump > 1.5:
                risk += 0.25
            elif era_jump > 1.0:
                risk += 0.15
            elif era_jump > 0.5:
                risk += 0.08
        
        # WHIP alto = más corredores = más riesgo
        whip = pitcher_data.get('whip', 1.35)
        if whip > 1.80:
            risk += 0.20
        elif whip > 1.60:
            risk += 0.12
        elif whip > 1.40:
            risk += 0.06
        
        # Pocos innings = muestra pequeña = incertidumbre
        innings = pitcher_data.get('innings', 50)
        if innings < 15:
            risk += 0.20
        elif innings < 30:
            risk += 0.10
        
        return min(1.0, risk)
    
    def bullpen_forced_usage(self, bullpen_data):
        """
        BFU: Índice de uso forzado del bullpen (0-1)
        """
        fatigue_score = 0.0
        
        innings_last3 = bullpen_data.get('last3_innings', 10)
        fatigue = bullpen_data.get('fatigue', 'NORMAL')
        
        if fatigue == 'CRITICAL':
            fatigue_score = 0.85
        elif fatigue == 'HIGH':
            fatigue_score = 0.55
        elif innings_last3 > 14:
            fatigue_score = 0.35
        elif innings_last3 > 11:
            fatigue_score = 0.20
        
        return fatigue_score
    
    def game_state_fragility(self, team_data):
        """
        GSF: Fragilidad del equipo (0-1)
        """
        fragility = 0.0
        
        # Run differential reciente (equipos con -10 runs en últimos juegos son frágiles)
        run_diff = team_data.get('run_diff_last10', 0)
        if run_diff < -10:
            fragility += 0.25
        elif run_diff < -5:
            fragility += 0.15
        
        # OPS bajo = lineup frío
        ops = team_data.get('ops_last7', 0.720)
        if ops < 0.650:
            fragility += 0.20
        elif ops < 0.700:
            fragility += 0.10
        
        # Win% del equipo
        win_pct = team_data.get('win_pct', 0.5)
        if win_pct < 0.42:
            fragility += 0.25
        elif win_pct < 0.46:
            fragility += 0.12
        
        return min(1.0, fragility)
    
    # ============================================
    # 2. PITCHER VS LINEUP 2.0
    # ============================================
    
    def ceiling_game_probability(self, pitcher_data, opponent_ops, opponent_k_rate):
        """
        ¿Probabilidad de que el pitcher DOMINE completamente?
        Returns: 0-1 (1 = alta probabilidad de joya)
        """
        ceiling = 0.5  # Base
        
        # K9 alto vs equipo que se poncha mucho
        k9 = pitcher_data.get('k9', 7.5)
        if k9 > 9.5 and opponent_k_rate > 0.24:
            ceiling += 0.15
        elif k9 > 8.0 and opponent_k_rate > 0.22:
            ceiling += 0.08
        
        # WHIP bajo vs OPS bajo
        whip = pitcher_data.get('whip', 1.35)
        if whip < 1.10 and opponent_ops < 0.700:
            ceiling += 0.15
        elif whip < 1.20 and opponent_ops < 0.730:
            ceiling += 0.08
        
        # ERA elite
        era = pitcher_data.get('era', 4.50)
        if era < 2.50:
            ceiling += 0.15
        elif era < 3.20:
            ceiling += 0.08
        
        return min(1.0, ceiling)
    
    # ============================================
    # 3. MARKET INEFFICIENCY DETECTOR
    # ============================================
    
    def false_favorite_detection(self, game_data):
        """
        Detecta cuando el favorito del mercado NO debería serlo
        """
        flags = []
        false_fav_score = 0.0
        
        home_team = game_data.get('home_team', '')
        away_team = game_data.get('away_team', '')
        
        # 1. Bullpen fatigado en el favorito
        home_bullpen_fatigue = self.bullpen_forced_usage(game_data.get('home_bullpen', {}))
        away_bullpen_fatigue = self.bullpen_forced_usage(game_data.get('away_bullpen', {}))
        
        if home_bullpen_fatigue > 0.50:
            flags.append(f'Home bullpen FATIGADO ({home_bullpen_fatigue:.0%})')
            false_fav_score += 0.20
        
        # 2. Pitcher shock risk alto en el favorito
        home_psr = self.pitcher_shock_risk(game_data.get('home_pitcher', {}))
        if home_psr > 0.40:
            flags.append(f'Home pitcher SHOCK RISK ({home_psr:.0%})')
            false_fav_score += 0.18
        
        # 3. Equipo sobrevalorado por nombre
        if home_team in self.overvalued_franchises:
            flags.append(f'{home_team} overvalued franchise')
            false_fav_score += 0.12
        
        # 4. Underdog es equipo subvalorado
        if away_team in self.undervalued_franchises:
            flags.append(f'{away_team} undervalued franchise')
            false_fav_score += 0.10
        
        return {
            'false_favorite': false_fav_score > 0.35,
            'score': round(false_fav_score, 2),
            'flags': flags
        }
    
    def underdog_structural_value(self, game_data):
        """
        Detecta cuando el underdog tiene valor ESTRUCTURAL
        """
        value_score = 0.0
        flags = []
        
        away_team = game_data.get('away_team', '')
        home_team = game_data.get('home_team', '')
        
        # 1. Bullpen más fresco que el rival
        home_bullpen = self.bullpen_forced_usage(game_data.get('home_bullpen', {}))
        away_bullpen = self.bullpen_forced_usage(game_data.get('away_bullpen', {}))
        
        if away_bullpen < 0.20 and home_bullpen > 0.50:
            flags.append('Away bullpen FRESHER')
            value_score += 0.20
        
        # 2. Pitcher del underdog tiene ceiling game alto
        away_ceiling = self.ceiling_game_probability(
            game_data.get('away_pitcher', {}),
            game_data.get('home_momentum', {}).get('ops_last7', 0.720),
            0.22
        )
        if away_ceiling > 0.65:
            flags.append(f'Away pitcher CEILING ({away_ceiling:.0%})')
            value_score += 0.18
        
        # 3. Home team frágil
        home_fragility = self.game_state_fragility({
            'run_diff_last10': game_data.get('home_momentum', {}).get('run_diff_last10', 0),
            'ops_last7': game_data.get('home_momentum', {}).get('ops_last7', 0.720),
            'win_pct': game_data.get('home_win_pct', 0.5)
        })
        if home_fragility > 0.40:
            flags.append(f'Home team FRAGILE ({home_fragility:.0%})')
            value_score += 0.15
        
        # 4. Underdog es equipo subvalorado
        if away_team in self.undervalued_franchises:
            flags.append(f'{away_team} undervalued')
            value_score += 0.10
        
        return {
            'structural_value': value_score > 0.40,
            'score': round(value_score, 2),
            'flags': flags
        }
    
    # ============================================
    # 4. CONTEXT SHIFT ENGINE
    # ============================================
    
    def context_shift(self, game_data):
        """
        Detecta cambios invisibles que el mercado no ha priced-in
        """
        shifts = []
        shift_score = 0.0
        
        # Pitcher con last 3 ERA muy diferente a season ERA
        home_p = game_data.get('home_pitcher', {})
        away_p = game_data.get('away_pitcher', {})
        
        for p, team in [(home_p, game_data.get('home_team', '')), 
                        (away_p, game_data.get('away_team', ''))]:
            season_era = p.get('era', 4.50)
            last3_era = p.get('last3_era', season_era)
            
            if last3_era and last3_era < 15:
                diff = abs(last3_era - season_era)
                if diff > 2.0:
                    shifts.append(f'{team} pitcher recent SHIFT ({diff:.1f} ERA diff)')
                    shift_score += 0.15
        
        # Divisional game = más volatilidad
        if game_data.get('divisional_game', False):
            shifts.append('Divisional game')
            shift_score += 0.05
        
        return {
            'shifts_detected': len(shifts) > 0,
            'score': round(shift_score, 2),
            'shifts': shifts
        }
    
    # ============================================
    # 5. FINAL OUTPUT LAYER
    # ============================================
    
    def classify_edge(self, game_data, model_result, market_intel_result):
        """
        Clasifica el setup en SAFE / VALUE / SHARP EDGE
        Se suma al sistema V5 existente
        """
        edge = model_result.get('edge', 0)
        probability = model_result.get('probability', 0.5)
        volatility = model_result.get('volatility', 0.5)
        edge_quality = market_intel_result.get('edge_quality', 'MARGINAL')
        
        # 1. Chaos Adjustment
        psr_home = self.pitcher_shock_risk(game_data.get('home_pitcher', {}))
        psr_away = self.pitcher_shock_risk(game_data.get('away_pitcher', {}))
        
        # 2. False Favorite
        false_fav = self.false_favorite_detection(game_data)
        
        # 3. Underdog Structural Value
        underdog_val = self.underdog_structural_value(game_data)
        
        # 4. Context Shift
        context = self.context_shift(game_data)
        
        # CLASIFICACIÓN FINAL
        if edge_quality in ['STRUCTURAL', 'FUNDAMENTAL'] and edge > 0.04:
            if underdog_val['structural_value'] or false_fav['false_favorite']:
                edge_type = 'SHARP EDGE'
                description = 'Market mispricing detected - Structural advantage'
            elif volatility < 0.45 and psr_home < 0.30 and psr_away < 0.30:
                edge_type = 'SAFE EDGE'
                description = 'Stable, low variance setup'
            else:
                edge_type = 'VALUE EDGE'
                description = 'Small inefficiency detected'
        elif edge_quality == 'VALUE' and edge > 0.02:
            edge_type = 'VALUE EDGE'
            description = 'Marginal value, size accordingly'
        else:
            edge_type = 'NO EDGE'
            description = 'No significant advantage'
        
        return {
            'edge_type': edge_type,
            'description': description,
            'false_favorite': false_fav,
            'underdog_value': underdog_val,
            'context_shifts': context['shifts'],
            'pitcher_risk': {'home': round(psr_home, 2), 'away': round(psr_away, 2)}
        }