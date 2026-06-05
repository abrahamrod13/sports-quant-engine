# umpire_engine.py
"""
UMPIRE TENDENCIES ENGINE - Strike zone, Over/Under bias, Run impact
Fuente: Umpire Scorecards, Umpire Auditor
"""
import requests
import pandas as pd
from datetime import datetime


class UmpireEngine:
    def __init__(self):
        # Datos históricos de umpires (2025-2026)
        # En producción se carga de CSV o API
        self.umpire_data = {
            # NOMBRE: {'strike_zone_accuracy': 0-1, 'over_tendency': -1 a 1, 'run_impact': -0.5 a 0.5}
            'Larry Vanover': {'strike_zone': 0.86, 'over_under_tendency': 0.08, 'run_impact': 0.35, 'k_rate': 8.2},
            'Joe West': {'strike_zone': 0.79, 'over_under_tendency': 0.12, 'run_impact': 0.52, 'k_rate': 7.5},
            'Angel Hernandez': {'strike_zone': 0.68, 'over_under_tendency': -0.05, 'run_impact': -0.18, 'k_rate': 7.8},
            'Rob Drake': {'strike_zone': 0.83, 'over_under_tendency': -0.08, 'run_impact': -0.22, 'k_rate': 8.5},
            'Cory Blaser': {'strike_zone': 0.81, 'over_under_tendency': 0.03, 'run_impact': 0.12, 'k_rate': 8.0},
            'Dan Iassogna': {'strike_zone': 0.84, 'over_under_tendency': 0.06, 'run_impact': 0.28, 'k_rate': 8.3},
            'Bill Miller': {'strike_zone': 0.82, 'over_under_tendency': -0.10, 'run_impact': -0.35, 'k_rate': 8.8},
            'Tom Hallion': {'strike_zone': 0.78, 'over_under_tendency': 0.15, 'run_impact': 0.48, 'k_rate': 7.9},
            'Jeff Nelson': {'strike_zone': 0.87, 'over_under_tendency': -0.02, 'run_impact': -0.08, 'k_rate': 8.6},
            'Sam Holbrook': {'strike_zone': 0.80, 'over_under_tendency': 0.10, 'run_impact': 0.32, 'k_rate': 8.1},
            'Ron Kulpa': {'strike_zone': 0.76, 'over_under_tendency': -0.12, 'run_impact': -0.41, 'k_rate': 9.0},
            'Mike Estabrook': {'strike_zone': 0.85, 'over_under_tendency': 0.00, 'run_impact': 0.00, 'k_rate': 8.4},
            'Chris Guccione': {'strike_zone': 0.82, 'over_under_tendency': 0.04, 'run_impact': 0.15, 'k_rate': 8.2},
            'Mark Carlson': {'strike_zone': 0.79, 'over_under_tendency': -0.07, 'run_impact': -0.25, 'k_rate': 7.7},
            'Lance Barksdale': {'strike_zone': 0.84, 'over_under_tendency': 0.02, 'run_impact': 0.08, 'k_rate': 8.3},
        }
        
        # Umpires con tendencia a "tight zone" (pocas bases por bolas)
        self.tight_zone_umpires = ['Jeff Nelson', 'Larry Vanover', 'Rob Drake', 'Dan Iassogna']
        
        # Umpires con tendencia a "wide zone" (más K, menos walks)
        self.wide_zone_umpires = ['Ron Kulpa', 'Tom Hallion', 'Angel Hernandez']
    
    def get_todays_umpire(self, game_id=None, home_team=None, away_team=None):
        """
        Obtiene el umpire asignado al juego
        MLB API: /api/v1/schedule?hydrate=umpires
        """
        try:
            url = "https://statsapi.mlb.com/api/v1/schedule"
            params = {'sportId': 1, 'date': datetime.now().strftime('%Y-%m-%d'), 'hydrate': 'umpires'}
            response = requests.get(url, params=params)
            data = response.json()
            
            for date_data in data.get('dates', []):
                for game in date_data.get('games', []):
                    home = game['teams']['home']['team']['name']
                    away = game['teams']['away']['team']['name']
                    
                    if (home_team and home == home_team and away_team and away == away_team) or not home_team:
                        umpires = game.get('umpires', [])
                        for ump in umpires:
                            if ump.get('officialType') == 'Home Plate':
                                ump_name = ump['official']['fullName']
                                return self.umpire_data.get(ump_name, {'strike_zone': 0.80, 'over_under_tendency': 0, 'run_impact': 0, 'k_rate': 8.0})
            
            return self.umpire_data.get('Average', {'strike_zone': 0.80, 'over_under_tendency': 0, 'run_impact': 0, 'k_rate': 8.0})
        except:
            return {'strike_zone': 0.80, 'over_under_tendency': 0, 'run_impact': 0, 'k_rate': 8.0}
    
    def strike_zone_adjustment(self, umpire_data, home_pitcher_k9, away_pitcher_k9):
        """
        Umpires con zona de strike amplia benefician a pitchers con alto K9
        Umpires con zona apretada benefician a bateadores (más walks)
        """
        ump_name = umpire_data.get('name', 'Average')
        
        # Zona amplia = +5-10% a K9 de los pitchers
        if ump_name in self.wide_zone_umpires:
            home_boost = (home_pitcher_k9 - 8.0) * 0.03
            away_boost = (away_pitcher_k9 - 8.0) * 0.03
            return home_boost + away_boost
        
        # Zona apretada = penaliza a pitchers que caminan muchos
        elif ump_name in self.tight_zone_umpires:
            return -0.02
        
        return 0
    
    def over_under_tendency(self, umpire_data):
        """
        Algunos umpires tienen tendencia histórica a Over o Under
        """
        tendency = umpire_data.get('over_under_tendency', 0)
        
        if tendency > 0.08:
            return {'over_adjustment': 0.04, 'under_adjustment': -0.04, 'signal': 'OVER_LEAN'}
        elif tendency < -0.08:
            return {'over_adjustment': -0.04, 'under_adjustment': 0.04, 'signal': 'UNDER_LEAN'}
        elif tendency > 0.03:
            return {'over_adjustment': 0.02, 'under_adjustment': -0.02, 'signal': 'SLIGHT_OVER'}
        elif tendency < -0.03:
            return {'over_adjustment': -0.02, 'under_adjustment': 0.02, 'signal': 'SLIGHT_UNDER'}
        
        return {'over_adjustment': 0, 'under_adjustment': 0, 'signal': 'NEUTRAL'}
    
    def run_impact_adjustment(self, umpire_data):
        """
        Impacto directo en carreras esperadas
        """
        run_impact = umpire_data.get('run_impact', 0)
        
        # Convertir a ajuste de probabilidad de ganar local
        # Un umpire que añade +0.5 runs al juego beneficia ligeramente al favorito
        if run_impact > 0.3:
            return 0.015
        elif run_impact > 0.1:
            return 0.008
        elif run_impact < -0.3:
            return -0.015
        elif run_impact < -0.1:
            return -0.008
        
        return 0
    
    def full_umpire_analysis(self, game_data, model_prob, total_line):
        """
        Análisis COMPLETO del umpire
        """
        home_team = game_data.get('home_team', '')
        away_team = game_data.get('away_team', '')
        home_pitcher = game_data.get('home_pitcher', {})
        away_pitcher = game_data.get('away_pitcher', {})
        
        # Obtener umpire
        umpire = self.get_todays_umpire(home_team=home_team, away_team=away_team)
        umpire['name'] = 'Average'  # Placeholder
        
        # Ajustes
        strike_adj = self.strike_zone_adjustment(umpire, home_pitcher.get('k9', 8.0), away_pitcher.get('k9', 8.0))
        ou_adj = self.over_under_tendency(umpire)
        run_adj = self.run_impact_adjustment(umpire)
        
        # Ajustar probabilidad
        adjusted_prob = model_prob + strike_adj + run_adj
        adjusted_prob = max(0.25, min(0.85, adjusted_prob))
        
        # Ajustar Total
        total_adjustment = ou_adj['over_adjustment']
        adjusted_total_line = total_line + total_adjustment
        
        return {
            'umpire': umpire.get('name', 'Unknown'),
            'original_prob': model_prob,
            'adjusted_prob': round(adjusted_prob, 4),
            'strike_zone_adjustment': round(strike_adj, 4),
            'run_impact_adjustment': round(run_adj, 4),
            'total_line_original': total_line,
            'total_line_adjusted': round(adjusted_total_line, 1),
            'over_under_signal': ou_adj['signal'],
            'total_adjustment': round(total_adjustment, 3),
            'umpire_profile': 'WIDE_ZONE' if umpire.get('name') in self.wide_zone_umpires else 
                              ('TIGHT_ZONE' if umpire.get('name') in self.tight_zone_umpires else 'AVERAGE')
        }


if __name__ == "__main__":
    ue = UmpireEngine()
    result = ue.full_umpire_analysis({'home_team': 'Yankees', 'away_team': 'Red Sox'}, 0.58, 8.5)
    print(f"Umpire: {result['umpire']}")
    print(f"Prob: {result['original_prob']:.1%} → {result['adjusted_prob']:.1%}")
    print(f"Total: 8.5 → {result['total_line_adjusted']}")
    print(f"OU Signal: {result['over_under_signal']}")