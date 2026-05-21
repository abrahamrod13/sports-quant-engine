import requests
import pandas as pd
from datetime import datetime
from config import SOCCER_API_KEY, SOCCER_API_BASE

# SOLO estas ligas. Nada más.
LEAGUE_IDS = {
    39: 'Premier League',
    140: 'La Liga',
    135: 'Serie A',
    2: 'Champions League',
    3: 'Europa League',
}

def get_today_soccer_matches():
    """SOLO partidos de ligas top: Premier, LaLiga, Serie A, Champions, Europa League"""
    date = datetime.now().strftime('%Y-%m-%d')
    
    url = f"{SOCCER_API_BASE}/fixtures"
    headers = {'x-apisports-key': SOCCER_API_KEY}
    params = {'date': date}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
    except Exception as e:
        print(f"❌ Error API-Football: {e}")
        return pd.DataFrame()
    
    matches = []
    for fixture in data.get('response', []):
        league_id = fixture['league']['id']
        
        # FILTRO DURO: solo IDs permitidos
        if league_id not in LEAGUE_IDS:
            continue
        
        matches.append({
            'match': f"{fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}",
            'league': LEAGUE_IDS[league_id],
            'date': fixture['fixture']['date'][:10],
            'home_team': fixture['teams']['home']['name'],
            'away_team': fixture['teams']['away']['name'],
            'xg_home': 0,
            'xg_away': 0,
            'injuries_home': 0,
            'injuries_away': 0,
            'odds_home': None,
            'odds_away': None,
            'odds_draw': None
        })
    
    print(f"⚽ Filtradas {len(matches)} partidos de ligas top")
    return pd.DataFrame(matches)