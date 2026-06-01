"""
REST ENGINE - Rest days, back-to-back detection
"""
import requests
from datetime import datetime, timedelta

def get_team_rest_days(team_name, date_str=None):
    if date_str is None: date_str = datetime.now().strftime('%Y-%m-%d')
    rest = 1
    for days_back in range(1, 4):
        d = (datetime.strptime(date_str, '%Y-%m-%d') - timedelta(days=days_back)).strftime('%Y-%m-%d')
        try:
            r = requests.get('https://statsapi.mlb.com/api/v1/schedule', params={'sportId': 1, 'date': d}, timeout=10)
            games = r.json().get('dates', [{}])[0].get('games', [])
            played = any(team_name in [g['teams']['home']['team']['name'], g['teams']['away']['team']['name']] for g in games)
            if played: return days_back - 1
        except: pass
        rest += 1
    return min(rest, 3)

def rest_advantage(home_rest, away_rest):
    diff = home_rest - away_rest
    if diff >= 2: return 0.02
    elif diff >= 1: return 0.01
    elif diff <= -2: return -0.02
    elif diff <= -1: return -0.01
    return 0