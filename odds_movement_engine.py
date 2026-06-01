"""
ODDS MOVEMENT ENGINE - Line movement, sharp money detection
"""
import requests
from config import ODDS_API_KEY, ODDS_API_BASE

def get_odds_movement(sport='baseball_mlb'):
    try:
        url = f"{ODDS_API_BASE}/sports/{sport}/odds"
        params = {'apiKey': ODDS_API_KEY, 'regions': 'us', 'markets': 'h2h', 'oddsFormat': 'american'}
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        movements = {}
        for game in data:
            match = f"{game['home_team']} vs {game['away_team']}"
            for bm in game.get('bookmakers', []):
                if bm['key'] == 'fanduel':
                    market = bm['markets'][0]
                    outcomes = market['outcomes']
                    home_odds = next((o['price'] for o in outcomes if o['name'] == game['home_team']), 0)
                    away_odds = next((o['price'] for o in outcomes if o['name'] == game['away_team']), 0)
                    movements[match] = {
                        'home_odds': home_odds, 'away_odds': away_odds,
                        'last_update': bm.get('last_update', '')
                    }
        return movements
    except: return {}

def detect_steam_move(match, current_odds, previous_odds=None):
    if previous_odds is None: return 0
    diff = abs(current_odds - previous_odds)
    if diff >= 20: return 0.02 if current_odds < previous_odds else -0.02
    elif diff >= 10: return 0.01 if current_odds < previous_odds else -0.01
    return 0