import pandas as pd
import os
from datetime import datetime

HISTORY_FILE = 'data/predictions_history.csv'

def init_tracker():
    """Crea el archivo de historial si no existe"""
    os.makedirs('data', exist_ok=True)
    
    if not os.path.exists(HISTORY_FILE):
        df = pd.DataFrame(columns=[
            'date', 'sport', 'league', 'match', 'home_team', 'away_team',
            'pick', 'probability', 'volatility', 'edge', 'confidence_score',
            'confidence_level', 'odds', 'result', 'profit_loss', 'clv'
        ])
        df.to_csv(HISTORY_FILE, index=False)
        print("📝 Historial inicializado")

def save_prediction(sport, league, match, home_team, away_team, pick, 
                    probability, volatility, edge, confidence_score, 
                    confidence_level, odds):
    """Guarda una predicción"""
    df = pd.DataFrame([{
        'date': datetime.now().strftime('%Y-%m-%d'),
        'sport': sport,
        'league': league,
        'match': match,
        'home_team': home_team,
        'away_team': away_team,
        'pick': pick,
        'probability': probability,
        'volatility': volatility,
        'edge': edge,
        'confidence_score': round(confidence_score, 3),
        'confidence_level': confidence_level,
        'odds': odds,
        'result': 'PENDING',
        'profit_loss': 0,
        'clv': 0
    }])
    
    df.to_csv(HISTORY_FILE, mode='a', header=False, index=False)

def update_results(date_to_update=None):
    """Actualiza resultados de predicciones pasadas"""
    if not os.path.exists(HISTORY_FILE):
        return
    
    df = pd.read_csv(HISTORY_FILE)
    
    if date_to_update is None:
        date_to_update = (datetime.now()).strftime('%Y-%m-%d')
    
    # Aquí conectarías con API para verificar resultados reales
    # Por ahora mostramos pendientes
    pending = df[df['result'] == 'PENDING']
    
    if len(pending) > 0:
        print(f"📊 {len(pending)} predicciones pendientes de resultado")
    
    return df

def get_stats():
    """Obtiene estadísticas de rendimiento"""
    if not os.path.exists(HISTORY_FILE):
        return None
    
    df = pd.read_csv(HISTORY_FILE)
    completed = df[df['result'] != 'PENDING']
    
    if len(completed) == 0:
        return None
    
    stats = {
        'total_bets': len(completed),
        'wins': len(completed[completed['result'] == 'WIN']),
        'losses': len(completed[completed['result'] == 'LOSS']),
        'win_rate': len(completed[completed['result'] == 'WIN']) / len(completed) * 100,
        'by_sport': {}
    }
    
    for sport in completed['sport'].unique():
        sport_df = completed[completed['sport'] == sport]
        if len(sport_df) > 0:
            stats['by_sport'][sport] = {
                'bets': len(sport_df),
                'wins': len(sport_df[sport_df['result'] == 'WIN']),
                'win_rate': len(sport_df[sport_df['result'] == 'WIN']) / len(sport_df) * 100
            }
    
    return stats