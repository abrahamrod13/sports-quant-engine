"""
PREDICTION TRACKER - Guarda predicciones de GANADOR y mide accuracy
"""
import pandas as pd
import os
from datetime import datetime

TRACKER_FILE = 'data/winner_predictions.csv'

def init_tracker():
    os.makedirs('data', exist_ok=True)
    if not os.path.exists(TRACKER_FILE):
        df = pd.DataFrame(columns=['date', 'match', 'predicted_winner', 'actual_winner', 'correct', 'probability'])
        df.to_csv(TRACKER_FILE, index=False)

def save_winner_prediction(match, predicted_winner, probability):
    init_tracker()
    new_row = pd.DataFrame([{
        'date': datetime.now().strftime('%Y-%m-%d'),
        'match': match,
        'predicted_winner': predicted_winner,
        'actual_winner': '',
        'correct': '',
        'probability': probability
    }])
    new_row.to_csv(TRACKER_FILE, mode='a', header=False, index=False)

def validate_winner_predictions():
    """Busca resultados reales y actualiza aciertos"""
    if not os.path.exists(TRACKER_FILE):
        return None
    
    df = pd.read_csv(TRACKER_FILE)
    pending = df[df['correct'] == '']
    
    if len(pending) == 0:
        return None
    
    import requests
    
    for idx, row in pending.iterrows():
        try:
            url = "https://statsapi.mlb.com/api/v1/schedule"
            params = {'sportId': 1, 'date': row['date']}
            response = requests.get(url, params=params)
            data = response.json()
            
            for date_data in data.get('dates', []):
                for game in date_data.get('games', []):
                    home = game['teams']['home']['team']['name']
                    away = game['teams']['away']['team']['name']
                    
                    if home in row['match'] and away in row['match']:
                        status = game.get('status', {}).get('detailedState', '')
                        if status == 'Final':
                            home_score = game['teams']['home'].get('score', 0)
                            away_score = game['teams']['away'].get('score', 0)
                            actual_winner = home if home_score > away_score else away
                            
                            df.at[idx, 'actual_winner'] = actual_winner
                            df.at[idx, 'correct'] = 'YES' if row['predicted_winner'] == actual_winner else 'NO'
        except:
            pass
    
    df.to_csv(TRACKER_FILE, index=False)
    return df

def get_winner_stats():
    """Estadísticas de aciertos de predicción pura"""
    if not os.path.exists(TRACKER_FILE):
        return None
    
    df = pd.read_csv(TRACKER_FILE)
    completed = df[df['correct'] != '']
    
    if len(completed) == 0:
        return None
    
    correct = len(completed[completed['correct'] == 'YES'])
    total = len(completed)
    
    return {
        'total': total,
        'correct': correct,
        'accuracy': round(correct / total * 100, 1),
        'last5': completed.tail(5)[['date', 'match', 'predicted_winner', 'correct']].to_dict('records')
    }