# market_sentiment.py
"""
MARKET SENTIMENT ENGINE - Public Betting % + Reverse Line Movement (RLM)
Detecta: 
1. Dónde está el dinero del público (overvalued teams)
2. Reverse Line Movement (sharp money)
3. Overbought/Oversold conditions
"""
import requests
import pandas as pd
from config import ODDS_API_KEY, ODDS_API_BASE


class MarketSentiment:
    def __init__(self):
        # Equipos que el público ama (sobrevalorados)
        self.public_darlings = {
            'New York Yankees': 0.85, 'Los Angeles Dodgers': 0.88,
            'Boston Red Sox': 0.78, 'Chicago Cubs': 0.75,
            'New York Mets': 0.76, 'Philadelphia Phillies': 0.72,
            'Atlanta Braves': 0.74, 'Houston Astros': 0.68,
            'San Diego Padres': 0.70, 'St. Louis Cardinals': 0.67,
            'San Francisco Giants': 0.65
        }
        
        # Equipos que el público odia/ignora (infravalorados)
        self.public_ignored = {
            'Tampa Bay Rays': 0.85, 'Milwaukee Brewers': 0.78,
            'Cleveland Guardians': 0.75, 'Arizona Diamondbacks': 0.72,
            'Seattle Mariners': 0.70, 'Miami Marlins': 0.65,
            'Pittsburgh Pirates': 0.60, 'Cincinnati Reds': 0.62,
            'Kansas City Royals': 0.58, 'Oakland Athletics': 0.55
        }
    
    def get_public_betting_percentage(self, sport='baseball_mlb'):
        """
        Obtiene % de apuestas públicas desde The Odds API
        (Nota: API gratuita no da public %; simulamos con sesgo histórico)
        Realmente se necesita Pinnacle o SportsInsights para esto.
        """
        # Simulación basada en nombres de equipos
        # En producción: endpoint /v4/sports/{sport}/betting
        return {}
    
    def detect_reverse_line_movement(self, opening_line, current_line, public_pct):
        """
        RLM = Línea se mueve CONTRA el público
        Ejemplo: 70% público en Yankees, pero la línea se mueve de -150 a -130
        """
        if opening_line == 0 or current_line == 0:
            return {'rlm_detected': False}
        
        # Determinar dirección de la línea
        if opening_line < 0 and current_line < 0:
            # Favorito vs favorito
            if current_line > opening_line:  # -150 → -130 (más cerca de 0)
                line_direction = 'TOWARDS_UNDERDOG'
            else:
                line_direction = 'TOWARDS_FAVORITE'
        elif opening_line > 0 and current_line > 0:
            # Underdog vs underdog
            if current_line < opening_line:  # +150 → +130
                line_direction = 'TOWARDS_FAVORITE'
            else:
                line_direction = 'TOWARDS_UNDERDOG'
        else:
            # Cambió de favorito a underdog
            line_direction = 'REVERSAL'
        
        # RLM detectado: público en equipo A (70%+), línea se mueve hacia equipo B
        rlm_detected = False
        rlm_team = None
        
        if public_pct >= 0.65 and line_direction == 'TOWARDS_UNDERDOG':
            rlm_detected = True
            rlm_team = 'underdog'
        elif public_pct <= 0.35 and line_direction == 'TOWARDS_FAVORITE':
            rlm_detected = True
            rlm_team = 'favorite'
        
        return {
            'rlm_detected': rlm_detected,
            'rlm_team': rlm_team,
            'line_direction': line_direction,
            'movement_strength': self._calculate_movement_strength(opening_line, current_line),
            'signal': 'SHARP_MONEY' if rlm_detected else 'PUBLIC_MONEY'
        }
    
    def _calculate_movement_strength(self, open_line, close_line):
        """Calcula fuerza del movimiento de línea"""
        if open_line == 0:
            return 0
        
        if open_line < 0 and close_line < 0:
            # Favorito: -150 → -130 es movimiento de 20
            return abs(close_line - open_line)
        elif open_line > 0 and close_line > 0:
            # Underdog: +150 → +130 es movimiento de 20
            return abs(open_line - close_line)
        elif open_line < 0 and close_line > 0:
            # Reversión completa
            return abs(open_line) + close_line
        
        return 0
    
    def public_overreaction_score(self, home_team, away_team, home_streak, away_streak):
        """
        El público sobre-reacciona a:
        - Rachas ganadoras largas
        - Equipos populares
        - Grandes nombres (Ohtani, Judge, etc.)
        """
        overreaction = 0.0
        reasons = []
        
        # 1. Popularidad
        home_pop = self.public_darlings.get(home_team, 0.50)
        away_pop = self.public_darlings.get(away_team, 0.50)
        
        if home_pop > 0.70:
            overreaction += 0.10
            reasons.append(f'{home_team} popular (public darling)')
        if away_pop > 0.70:
            overreaction += 0.08
            reasons.append(f'{away_team} popular')
        
        # 2. Rachas
        if home_streak >= 5:
            overreaction += 0.12
            reasons.append(f'{home_team} on {home_streak}-game win streak')
        elif home_streak >= 3:
            overreaction += 0.06
        
        if away_streak >= 5:
            overreaction += 0.10
            reasons.append(f'{away_team} on {away_streak}-game win streak')
        elif away_streak >= 3:
            overreaction += 0.05
        
        # 3. Underdog ignorado
        if home_team in self.public_ignored:
            # El público ignora a este equipo → valor en underdog
            overreaction -= 0.05
        if away_team in self.public_ignored:
            overreaction -= 0.05
        
        # 4. Superstar factor
        superstars = ['Shohei Ohtani', 'Aaron Judge', 'Mookie Betts', 
                      'Ronald Acuna', 'Fernando Tatis', 'Bryce Harper']
        # (simplificado - en realidad se buscaría si juegan)
        
        return {
            'overreaction_score': round(min(0.40, max(-0.15, overreaction)), 3),
            'level': 'HIGH' if overreaction > 0.15 else ('MEDIUM' if overreaction > 0.08 else 'LOW'),
            'reasons': reasons,
            'public_leaning': home_team if home_pop > away_pop else away_team
        }
    
    def market_sentiment_adjustment(self, game_data, model_prob):
        """
        Ajuste FINAL de probabilidad basado en sentimiento de mercado
        """
        home_team = game_data.get('home_team', '')
        away_team = game_data.get('away_team', '')
        home_streak = game_data.get('home_momentum', {}).get('streak', 0)
        away_streak = game_data.get('away_momentum', {}).get('streak', 0)
        
        # 1. Overreaction del público
        overreaction = self.public_overreaction_score(home_team, away_team, home_streak, away_streak)
        
        # 2. RLM si hay datos de línea
        opening = game_data.get('opening_odds', game_data.get('odds', 2.0))
        closing = game_data.get('odds', 2.0)
        # Convertir a americano si es decimal
        if opening > 0 and opening < 3:
            opening_american = 100 if opening == 2.0 else (opening - 1) * 100 if opening > 1 else -100/(opening-1)
        else:
            opening_american = opening
        
        rlm = self.detect_reverse_line_movement(opening_american, closing, 0.65)  # public_pct simulado
        
        # Ajuste final
        adjustment = -overreaction['overreaction_score']  # Si público sobrevalora, ajustamos ABAJO
        
        if rlm['rlm_detected'] and rlm['rlm_team'] == 'underdog':
            adjustment += 0.04  # Sharp money en underdog
        
        adjusted_prob = model_prob + adjustment
        adjusted_prob = max(0.25, min(0.85, adjusted_prob))
        
        return {
            'original_probability': model_prob,
            'adjusted_probability': round(adjusted_prob, 4),
            'adjustment': round(adjustment, 4),
            'overreaction': overreaction,
            'rlm': rlm,
            'market_signal': 'FADE_PUBLIC' if adjustment < -0.03 else ('SHARP_EDGE' if rlm['rlm_detected'] else 'NEUTRAL')
        }


if __name__ == "__main__":
    ms = MarketSentiment()
    test_data = {
        'home_team': 'New York Yankees',
        'away_team': 'Tampa Bay Rays',
        'home_momentum': {'streak': 5},
        'away_momentum': {'streak': 0},
        'opening_odds': -150,
        'odds': -130
    }
    result = ms.market_sentiment_adjustment(test_data, 0.62)
    print(f"Original: 62% → Adjusted: {result['adjusted_probability']:.1%}")
    print(f"Signal: {result['market_signal']}")
    print(f"Overreaction: {result['overreaction']['reasons']}")