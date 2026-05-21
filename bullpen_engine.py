import requests
from datetime import datetime, timedelta

def get_bullpen_fatigue(team_id):
    if not team_id:
        return {'era': 4.00, 'whip': 1.30, 'last3_innings': 10, 'save_pct': 0.65, 'fatigue': 'NORMAL'}
    
    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/stats"
    params = {
        'stats': 'byDateRange', 'season': 2026,
        'startDate': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
        'endDate': datetime.now().strftime('%Y-%m-%d'),
        'group': 'pitching', 'gameType': 'R'
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        for stat_group in data.get('stats', []):
            for split in stat_group.get('splits', []):
                stat = split.get('stat', {})
                if stat:
                    innings_pitched = float(stat.get('inningsPitched', 27) or 27)
                    bullpen_innings = max(0, innings_pitched * 0.4)
                    
                    fatigue = 'NORMAL'
                    if bullpen_innings > 15:
                        fatigue = 'HIGH'
                    elif bullpen_innings > 20:
                        fatigue = 'CRITICAL'
                    
                    return {
                        'era': float(stat.get('era', 4.00) or 4.00),
                        'whip': float(stat.get('whip', 1.30) or 1.30),
                        'last3_innings': round(bullpen_innings, 1),
                        'save_pct': 0.65,
                        'fatigue': fatigue
                    }
        return {'era': 4.00, 'whip': 1.30, 'last3_innings': 10, 'save_pct': 0.65, 'fatigue': 'NORMAL'}
    except:
        return {'era': 4.00, 'whip': 1.30, 'last3_innings': 10, 'save_pct': 0.65, 'fatigue': 'NORMAL'}