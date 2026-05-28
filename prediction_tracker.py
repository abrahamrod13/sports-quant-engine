"""
PREDICTION TRACKER - Guarda predicciones de GANADOR y mide accuracy
VERSIÓN FINAL - Tipos corregidos, matcheo flexible
"""
import pandas as pd
import os
from datetime import datetime

TRACKER_FILE = 'data/winner_predictions.csv'

def init_tracker():
    os.makedirs('data', exist_ok=True)
    if not os.path.exists(TRACKER_FILE):
        df = pd.DataFrame(columns=[
            'date', 'match', 'predicted_winner', 
            'actual_winner', 'correct', 'probability'
        ])
        df.to_csv(TRACKER_FILE, index=False)

def save_winner_prediction(match, predicted_winner, probability):
    """Guarda una predicción en el tracker"""
    init_tracker()
    
    # Leer existente
    if os.path.exists(TRACKER_FILE):
        df = pd.read_csv(TRACKER_FILE)
    else:
        df = pd.DataFrame(columns=[
            'date', 'match', 'predicted_winner',
            'actual_winner', 'correct', 'probability'
        ])
    
    # Crear nueva fila
    new_row = pd.DataFrame([{
        'date': datetime.now().strftime('%Y-%m-%d'),
        'match': match,
        'predicted_winner': predicted_winner,
        'actual_winner': '',
        'correct': '',
        'probability': probability
    }])
    
    # Concatenar y guardar
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(TRACKER_FILE, index=False)

def validate_winner_predictions():
    """
    Busca resultados reales en MLB API y actualiza el CSV
    """
    if not os.path.exists(TRACKER_FILE):
        print("No tracker file found.")
        return None
    
    # Leer CSV
    df = pd.read_csv(TRACKER_FILE)
    
    # Convertir columnas clave a string y limpiar NaN
    for col in ['actual_winner', 'correct', 'predicted_winner', 'match']:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str)
    
    # Encontrar predicciones sin validar
    pending_mask = (df['correct'] == '') | (df['correct'] == 'nan')
    pending = df[pending_mask]
    
    print(f"🔍 {len(pending)} predicciones pendientes de validar")
    
    if len(pending) == 0:
        df.to_csv(TRACKER_FILE, index=False)
        return df
    
    import requests
    validated_count = 0
    
    for idx, row in pending.iterrows():
        try:
            url = "https://statsapi.mlb.com/api/v1/schedule"
            params = {'sportId': 1, 'date': row['date']}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                continue
            
            data = response.json()
            
            for date_data in data.get('dates', []):
                for game in date_data.get('games', []):
                    home = game['teams']['home']['team']['name']
                    away = game['teams']['away']['team']['name']
                    status = game.get('status', {}).get('detailedState', '')
                    
                    # Verificar si este juego matchea con nuestra predicción
                    match_str = str(row['match']).lower()
                    home_in_match = home.lower() in match_str
                    away_in_match = away.lower() in match_str
                    
                    if home_in_match and away_in_match and status == 'Final':
                        home_score = int(game['teams']['home'].get('score', 0))
                        away_score = int(game['teams']['away'].get('score', 0))
                        actual_winner = home if home_score > away_score else away
                        
                        # Guardar resultado
                        df.at[idx, 'actual_winner'] = actual_winner
                        
                        predicted = str(row['predicted_winner'])
                        
                        if predicted == 'TOO CLOSE':
                            df.at[idx, 'correct'] = 'SKIP'
                        elif predicted.lower() == actual_winner.lower():
                            df.at[idx, 'correct'] = 'YES'
                        else:
                            df.at[idx, 'correct'] = 'NO'
                        
                        validated_count += 1
                        break  # Salir del loop de juegos
        except Exception as e:
            print(f"  ⚠️ Error validando {row['date']} - {row['match']}: {e}")
    
    print(f"✅ {validated_count} predicciones validadas")
    df.to_csv(TRACKER_FILE, index=False)
    return df

def get_winner_stats():
    """Obtiene estadísticas de accuracy"""
    if not os.path.exists(TRACKER_FILE):
        return None
    
    df = pd.read_csv(TRACKER_FILE)
    
    # Asegurar tipos
    if 'correct' in df.columns:
        df['correct'] = df['correct'].fillna('').astype(str)
    
    # Solo predicciones reales (YES/NO)
    completed = df[df['correct'].isin(['YES', 'NO'])]
    
    if len(completed) == 0:
        return None
    
    correct = len(completed[completed['correct'] == 'YES'])
    total = len(completed)
    
    return {
        'total': total,
        'correct': correct,
        'accuracy': round(correct / total * 100, 1) if total > 0 else 0
    }