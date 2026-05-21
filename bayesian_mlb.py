"""
BAYESIAN MLB LAYER - Aprende de resultados pasados
Independiente del modelo V7
"""
import pandas as pd
import os

class BayesianMLB:
    def __init__(self):
        self.log_file = 'data/betting_log.csv'
    
    def get_pitcher_history(self, pitcher_name):
        """Busca resultados históricos de un pitcher"""
        if not os.path.exists(self.log_file):
            return None
        
        df = pd.read_csv(self.log_file)
        # Simplificado: buscar juegos donde aparece el pitcher
        return None  # Se construye con más datos
    
    def calculate_bayesian_prob(self, model_prob, confidence, historical_win_rate=None):
        """
        Actualiza probabilidad usando Bayes
        prior = model_prob
        likelihood = confidence
        posterior = prior actualizado
        """
        if historical_win_rate is None:
            # Sin historial, devuelve la probabilidad del modelo
            return model_prob
        
        # Bayes ingenuo: promedio ponderado
        posterior = (model_prob * 0.7) + (historical_win_rate * 0.3)
        return round(posterior, 4)
    
    def analyze_game(self, home_team, away_team, model_prob, confidence):
        """Análisis bayesiano para un juego"""
        # Buscar historial de enfrentamientos
        hist_win_rate = None
        
        if os.path.exists(self.log_file):
            df = pd.read_csv(self.log_file)
            completed = df[(df['result'] != 'PENDING')]
            
            # Buscar juegos previos entre estos equipos
            matchups = completed[
                (completed['match'].str.contains(home_team, na=False)) &
                (completed['match'].str.contains(away_team, na=False))
            ]
            
            if len(matchups) > 0:
                wins = len(matchups[matchups['result'] == 'WIN'])
                hist_win_rate = wins / len(matchups)
        
        bayesian_prob = self.calculate_bayesian_prob(model_prob, confidence, hist_win_rate)
        
        return {
            'bayesian_prob': bayesian_prob,
            'model_prob': model_prob,
            'prior_strength': 'HIGH' if hist_win_rate and len(matchups) > 5 else ('MEDIUM' if hist_win_rate else 'LOW'),
            'historical_games': len(matchups) if hist_win_rate else 0
        }