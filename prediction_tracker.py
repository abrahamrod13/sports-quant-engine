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
    if not os.path.exists(TRACKER_FILE):
        return None
    
    df = pd.read_csv(TRACKER_FILE)
    # Solo validar filas sin resultado
    pending = df[(df['correct'].isna()) | (df['correct'] == '')]
    
    if len(pending) == 0:
        return df
    
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
                    status = game.get('status', {}).get('detailedState', '')
                    
                    # Matcheo flexible
                    match_str = row['match'].lower()
                    if home.lower() in match_str and away.lower() in match_str and status == 'Final':
                        home_score = int(game['teams']['home'].get('score', 0))
                        away_score = int(game['teams']['away'].get('score', 0))
                        actual_winner = home if home_score > away_score else away
                        
                        df.at[idx, 'actual_winner'] = actual_winner
                        if row['predicted_winner'] == 'TOO CLOSE':
                            df.at[idx, 'correct'] = 'SKIP'
                        elif row['predicted_winner'].lower() == actual_winner.lower():
                            df.at[idx, 'correct'] = 'YES'
                        else:
                            df.at[idx, 'correct'] = 'NO'
        except:
            pass
    
    df.to_csv(TRACKER_FILE, index=False)
    return df

def get_winner_stats():
    if not os.path.exists(TRACKER_FILE):
        return None
    
    df = pd.read_csv(TRACKER_FILE)
    # Solo predicciones reales (no SKIP, no TOO CLOSE)
    completed = df[df['correct'].isin(['YES', 'NO'])]
    
    if len(completed) == 0:
        return None
    
    correct = len(completed[completed['correct'] == 'YES'])
    total = len(completed)
    
    return {
        'total': total,
        'correct': correct,
        'accuracy': round(correct / total * 100, 1)
    }