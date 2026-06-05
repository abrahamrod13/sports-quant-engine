# historical_similar_spots.py
"""
HISTORICAL SIMILAR SPOTS ENGINE
Busca situaciones similares en el historial y extrae probabilidad empírica
"""
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta


class HistoricalSimilarSpots:
    def __init__(self):
        self.history_file = 'data/historical_similar_spots.csv'
        self._load_or_create_db()
    
    def _load_or_create_db(self):
        """Carga o crea la base de datos histórica"""
        os.makedirs('data', exist_ok=True)
        
        if os.path.exists(self.history_file):
            self.db = pd.read_csv(self.history_file)
        else:
            # Esquema inicial
            self.db = pd.DataFrame(columns=[
                'date', 'home_team', 'away_team', 'home_win_pct', 'away_win_pct',
                'home_pitcher_era', 'away_pitcher_era', 'home_pitcher_k9', 'away_pitcher_k9',
                'home_streak', 'away_streak', 'is_divisional', 'stadium',
                'home_score', 'away_score', 'winner', 'total_runs'
            ])
            self.save()
    
    def save(self):
        """Guarda la base de datos"""
        self.db.to_csv(self.history_file, index=False)
    
    def add_game_result(self, game_data, result):
        """
        Agrega un juego completado a la base de datos histórica
        """
        new_row = pd.DataFrame([{
            'date': datetime.now().strftime('%Y-%m-%d'),
            'home_team': game_data.get('home_team', ''),
            'away_team': game_data.get('away_team', ''),
            'home_win_pct': game_data.get('home_win_pct', 0.5),
            'away_win_pct': game_data.get('away_win_pct', 0.5),
            'home_pitcher_era': game_data.get('home_pitcher', {}).get('era', 4.50),
            'away_pitcher_era': game_data.get('away_pitcher', {}).get('era', 4.50),
            'home_pitcher_k9': game_data.get('home_pitcher', {}).get('k9', 8.0),
            'away_pitcher_k9': game_data.get('away_pitcher', {}).get('k9', 8.0),
            'home_streak': game_data.get('home_momentum', {}).get('streak', 0),
            'away_streak': game_data.get('away_momentum', {}).get('streak', 0),
            'is_divisional': game_data.get('divisional_game', False),
            'stadium': game_data.get('stadium', ''),
            'home_score': result.get('home_score', 0),
            'away_score': result.get('away_score', 0),
            'winner': result.get('winner', ''),
            'total_runs': result.get('home_score', 0) + result.get('away_score', 0)
        }])
        
        self.db = pd.concat([self.db, new_row], ignore_index=True)
        self.save()
    
    def find_similar_spots(self, game_data, n=50, tolerance=0.10):
        """
        Encuentra juegos históricamente similares
        
        Parámetros:
        - game_data: datos del juego actual
        - n: mínimo de juegos similares requeridos
        - tolerance: tolerancia para considerar similar (±%)
        """
        if len(self.db) < 10:
            return None
        
        # Características para comparar
        home_win_pct = game_data.get('home_win_pct', 0.5)
        away_win_pct = game_data.get('away_win_pct', 0.5)
        home_era = game_data.get('home_pitcher', {}).get('era', 4.50)
        away_era = game_data.get('away_pitcher', {}).get('era', 4.50)
        home_k9 = game_data.get('home_pitcher', {}).get('k9', 8.0)
        away_k9 = game_data.get('away_pitcher', {}).get('k9', 8.0)
        home_streak = game_data.get('home_momentum', {}).get('streak', 0)
        away_streak = game_data.get('away_momentum', {}).get('streak', 0)
        
        # Calcular scores de similitud
        def similarity_score(row):
            score = 0.0
            # Win% difference
            score += max(0, 1 - abs(row['home_win_pct'] - home_win_pct) / 0.15) * 0.20
            score += max(0, 1 - abs(row['away_win_pct'] - away_win_pct) / 0.15) * 0.20
            
            # Pitcher ERA
            score += max(0, 1 - abs(row['home_pitcher_era'] - home_era) / 1.5) * 0.15
            score += max(0, 1 - abs(row['away_pitcher_era'] - away_era) / 1.5) * 0.15
            
            # Pitcher K9
            score += max(0, 1 - abs(row['home_pitcher_k9'] - home_k9) / 2.0) * 0.10
            score += max(0, 1 - abs(row['away_pitcher_k9'] - away_k9) / 2.0) * 0.10
            
            # Streak (limitado)
            streak_diff_h = min(5, abs(row['home_streak'] - home_streak))
            streak_diff_a = min(5, abs(row['away_streak'] - away_streak))
            score += max(0, 1 - (streak_diff_h + streak_diff_a) / 10) * 0.10
            
            return score
        
        # Aplicar similitud
        if len(self.db) > 0:
            self.db['similarity'] = self.db.apply(similarity_score, axis=1)
            similar = self.db[self.db['similarity'] > tolerance].sort_values('similarity', ascending=False)
        else:
            return None
        
        if len(similar) < n:
            return None
        
        # Análisis de resultados similares
        top_n = similar.head(n)
        
        home_wins = len(top_n[top_n['winner'] == top_n['home_team'].iloc[0]])  # Simplificado
        # Mejor: contar correctamente
        home_wins = 0
        for _, row in top_n.iterrows():
            if row['winner'] == row['home_team']:
                home_wins += 1
        
        empirical_prob = home_wins / len(top_n)
        
        # Distribución de carreras
        avg_total_runs = top_n['total_runs'].mean()
        over_7_5_pct = len(top_n[top_n['total_runs'] > 7.5]) / len(top_n)
        over_8_5_pct = len(top_n[top_n['total_runs'] > 8.5]) / len(top_n)
        
        return {
            'similar_games_found': len(top_n),
            'empirical_home_win_prob': round(empirical_prob, 4),
            'avg_total_runs': round(avg_total_runs, 1),
            'over_7_5_pct': round(over_7_5_pct, 4),
            'over_8_5_pct': round(over_8_5_pct, 4),
            'avg_similarity': round(top_n['similarity'].mean(), 3),
            'confidence': 'HIGH' if len(top_n) >= 100 else ('MEDIUM' if len(top_n) >= 50 else 'LOW')
        }
    
    def blend_with_model(self, game_data, model_prob, model_weight=0.6):
        """
        Combina probabilidad del modelo con evidencia empírica
        """
        similar_analysis = self.find_similar_spots(game_data)
        
        if not similar_analysis or similar_analysis['similar_games_found'] < 20:
            return {
                'blended_prob': model_prob,
                'historical_contribution': 0,
                'similar_games': 0,
                'method': 'model_only'
            }
        
        # Peso histórico basado en cantidad de juegos similares
        historical_weight = min(0.40, similar_analysis['similar_games_found'] / 250)
        
        # Ajustar peso: más confianza si la similitud es alta
        if similar_analysis['avg_similarity'] > 0.70:
            historical_weight = min(0.50, historical_weight * 1.5)
        
        blended = (model_prob * (1 - historical_weight)) + (similar_analysis['empirical_home_win_prob'] * historical_weight)
        
        return {
            'blended_prob': round(blended, 4),
            'model_prob': model_prob,
            'historical_prob': similar_analysis['empirical_home_win_prob'],
            'historical_contribution': round(historical_weight, 3),
            'similar_games': similar_analysis['similar_games_found'],
            'avg_similarity': similar_analysis['avg_similarity'],
            'method': 'blended'
        }


if __name__ == "__main__":
    hss = HistoricalSimilarSpots()
    
    # Simular algunos juegos para prueba
    test_game = {
        'home_team': 'Yankees',
        'away_team': 'Red Sox',
        'home_win_pct': 0.62,
        'away_win_pct': 0.55,
        'home_pitcher': {'era': 3.20, 'k9': 9.5},
        'away_pitcher': {'era': 3.80, 'k9': 8.5},
        'home_momentum': {'streak': 3},
        'away_momentum': {'streak': 1},
        'divisional_game': True,
        'stadium': 'Yankee Stadium'
    }
    
    result = hss.blend_with_model(test_game, 0.58)
    print(f"Model: 58% → Blended: {result['blended_prob']:.1%}")
    print(f"Based on {result['similar_games']} similar games (similarity: {result['avg_similarity']})")