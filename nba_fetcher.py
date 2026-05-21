import requests
import pandas as pd
from config import NBA_ESPN_BASE

def get_nba_scoreboard():
    """Obtiene partidos NBA del día desde ESPN"""
    url = f"{NBA_ESPN_BASE}/scoreboard"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        games = []
        for event in data.get('events', []):
            comp = event['competitions'][0]
            home = comp['competitors'][0]
            away = comp['competitors'][1]
            
            games.append({
                'date': event['date'][:10],
                'home_team': home['team']['displayName'],
                'away_team': away['team']['displayName'],
                'home_score': home.get('score', '0'),
                'away_score': away.get('score', '0'),
                'status': event['status']['type']['description'],
                'match': f"{home['team']['displayName']} vs {away['team']['displayName']}"
            })
        
        return pd.DataFrame(games)
    
    except Exception as e:
        print(f"❌ Error obteniendo NBA scoreboard: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    df = get_nba_scoreboard()
    print(df)