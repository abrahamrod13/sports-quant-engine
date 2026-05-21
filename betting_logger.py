"""
BETTING LOGGER - Registro CSV + Auto-validación
"""
import pandas as pd
import os
from datetime import datetime

LOG_FILE = 'data/betting_log.csv'

def init_logger():
    """Crea el archivo de log si no existe"""
    os.makedirs('data', exist_ok=True)
    
    if not os.path.exists(LOG_FILE):
        df = pd.DataFrame(columns=[
            'date', 'sport', 'match', 'bet_type', 'pick', 'odds',
            'probability', 'edge', 'volatility', 'confidence',
            'result', 'profit_loss', 'validated_date'
        ])
        df.to_csv(LOG_FILE, index=False)

def save_bet(sport, match, bet_type, pick, odds, probability, edge, volatility, confidence):
    """Guarda una predicción en el log"""
    new_row = pd.DataFrame([{
        'date': datetime.now().strftime('%Y-%m-%d'),
        'sport': sport,
        'match': match,
        'bet_type': bet_type,
        'pick': pick,
        'odds': odds,
        'probability': probability,
        'edge': edge,
        'volatility': volatility,
        'confidence': confidence,
        'result': 'PENDING',
        'profit_loss': 0.0,
        'validated_date': ''
    }])
    
    if os.path.exists(LOG_FILE):
        new_row.to_csv(LOG_FILE, mode='a', header=False, index=False)
    else:
        new_row.to_csv(LOG_FILE, index=False)

def validate_pending_bets():
    """
    Busca predicciones PENDING y las valida contra resultados reales
    """
    if not os.path.exists(LOG_FILE):
        print("No hay historial aún.")
        return
    
    df = pd.read_csv(LOG_FILE)
    pending = df[df['result'] == 'PENDING']
    
    if len(pending) == 0:
        print("✅ Todas las predicciones están validadas.")
        return
    
    print(f"\n🔄 Validando {len(pending)} predicciones pendientes...")
    
    for idx, row in pending.iterrows():
        # Buscar resultado en MLB API
        actual_result = get_mlb_result(row['date'], row['match'])
        
        if actual_result:
            df.at[idx, 'result'] = actual_result['result']
            df.at[idx, 'profit_loss'] = actual_result['profit_loss']
            df.at[idx, 'validated_date'] = datetime.now().strftime('%Y-%m-%d')
    
    df.to_csv(LOG_FILE, index=False)
    print("✅ Validación completada.")

def get_mlb_result(game_date, match_name):
    """Busca resultado real en MLB Stats API"""
    import requests
    
    try:
        url = "https://statsapi.mlb.com/api/v1/schedule"
        params = {'sportId': 1, 'date': game_date}
        
        response = requests.get(url, params=params)
        data = response.json()
        
        for date_data in data.get('dates', []):
            for game in date_data.get('games', []):
                home = game['teams']['home']['team']['name']
                away = game['teams']['away']['team']['name']
                status = game.get('status', {}).get('detailedState', '')
                
                # Verificar si este juego matchea
                if home in match_name and away in match_name and status == 'Final':
                    home_score = game['teams']['home'].get('score', 0)
                    away_score = game['teams']['away'].get('score', 0)
                    winner = home if home_score > away_score else away
                    
                    # Cargar el CSV para ver el pick
                    import pandas as pd
                    import os
                    log_file = 'data/betting_log.csv'
                    
                    if not os.path.exists(log_file):
                        return None
                    
                    df = pd.read_csv(log_file)
                    match_row = df[(df['date'] == game_date) & (df['match'] == match_name) & (df['result'] == 'PENDING')]
                    
                    if len(match_row) == 0:
                        return None
                    
                    for idx, row in match_row.iterrows():
                        pick = str(row['pick'])
                        bet_type = str(row['bet_type'])
                        odds = float(row['odds'])
                        
                        won = False
                        if bet_type == 'Moneyline':
                            # Verificar si el pick contiene el nombre del ganador
                            if pick.lower() in winner.lower() or winner.lower() in pick.lower():
                                won = True
                        
                        if won:
                            if odds < 0:
                                profit = round(100 / abs(odds) * 100, 2)
                            else:
                                profit = round(odds, 2)
                        else:
                            profit = -100.0
                        
                        return {
                            'result': 'WIN' if won else 'LOSS',
                            'profit_loss': profit
                        }
        
        return None
    except Exception as e:
        print(f"      ⚠️ Error validando {match_name}: {e}")
        return None
def get_betting_stats(sport=None):
    """Estadísticas de rendimiento"""
    if not os.path.exists(LOG_FILE):
        return None
    
    df = pd.read_csv(LOG_FILE)
    completed = df[df['result'] != 'PENDING']
    
    if sport:
        completed = completed[completed['sport'] == sport]
    
    if len(completed) == 0:
        return None
    
    # Por tipo de apuesta
    stats_by_type = {}
    for bet_type in completed['bet_type'].unique():
        bt_df = completed[completed['bet_type'] == bet_type]
        wins = len(bt_df[bt_df['result'] == 'WIN'])
        total = len(bt_df)
        profit = bt_df['profit_loss'].sum()
        
        stats_by_type[bet_type] = {
            'bets': total,
            'wins': wins,
            'losses': total - wins,
            'win_rate': round(wins / total * 100, 1) if total > 0 else 0,
            'profit': round(profit, 2),
            'roi': round(profit / (total * 100) * 100, 1) if total > 0 else 0
        }
    
    # Totales
    total_bets = len(completed)
    total_wins = len(completed[completed['result'] == 'WIN'])
    total_profit = completed['profit_loss'].sum()
    
    return {
        'total_bets': total_bets,
        'total_wins': total_wins,
        'win_rate': round(total_wins / total_bets * 100, 1) if total_bets > 0 else 0,
        'total_profit': round(total_profit, 2),
        'roi': round(total_profit / (total_bets * 100) * 100, 1) if total_bets > 0 else 0,
        'by_type': stats_by_type
    }

def deduplicate_log():
    """Elimina registros duplicados del log"""
    import pandas as pd
    import os
    
    if not os.path.exists(LOG_FILE):
        return
    
    df = pd.read_csv(LOG_FILE)
    
    # Eliminar duplicados por fecha + match + pick (mantener el primero)
    before = len(df)
    df = df.drop_duplicates(subset=['date', 'match', 'pick', 'bet_type'], keep='first')
    after = len(df)
    
    if before > after:
        df.to_csv(LOG_FILE, index=False)
        print(f"🧹 Deduplicado: {before} → {after} registros ({before - after} eliminados)")