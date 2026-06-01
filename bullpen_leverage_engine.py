"""
BULLPEN LEVERAGE ENGINE - Saves, blown saves, leverage
"""
import requests

TEAM_IDS = {
    'Arizona Diamondbacks': 109, 'Atlanta Braves': 144, 'Baltimore Orioles': 110,
    'Boston Red Sox': 111, 'Chicago Cubs': 112, 'Chicago White Sox': 145,
    'Cincinnati Reds': 113, 'Cleveland Guardians': 114, 'Colorado Rockies': 115,
    'Detroit Tigers': 116, 'Houston Astros': 117, 'Kansas City Royals': 118,
    'Los Angeles Angels': 108, 'Los Angeles Dodgers': 119, 'Miami Marlins': 146,
    'Milwaukee Brewers': 158, 'Minnesota Twins': 142, 'New York Mets': 121,
    'New York Yankees': 147, 'Athletics': 133, 'Philadelphia Phillies': 143,
    'Pittsburgh Pirates': 134, 'San Diego Padres': 135, 'San Francisco Giants': 137,
    'Seattle Mariners': 136, 'St. Louis Cardinals': 138, 'Tampa Bay Rays': 139,
    'Texas Rangers': 140, 'Toronto Blue Jays': 141, 'Washington Nationals': 120
}

def get_bullpen_stats(team_name):
    team_id = TEAM_IDS.get(team_name)
    if not team_id: return None
    try:
        r = requests.get(f'https://statsapi.mlb.com/api/v1/teams/{team_id}/stats',
                        params={'stats':'season','season':2026,'group':'pitching','gameType':'R'}, timeout=10)
        data = r.json()
        splits = data.get('stats',[{}])[0].get('splits',[])
        stat = splits[0].get('stat',{}) if splits else {}
        return {
            'saves': stat.get('saves', 0),
            'save_opps': stat.get('saveOpportunities', 0),
            'blown_saves': stat.get('blownSaves', 0),
            'holds': stat.get('holds', 0),
            'save_pct': round(stat.get('saves', 0) / max(1, stat.get('saveOpportunities', 1)) * 100, 1)
        } if stat else None
    except: return None

def bullpen_advantage(home_team, away_team):
    h = get_bullpen_stats(home_team)
    a = get_bullpen_stats(away_team)
    if not h or not a: return 0
    h_score = h['save_pct'] / 100 - (h['blown_saves'] / max(1, h['save_opps']))
    a_score = a['save_pct'] / 100 - (a['blown_saves'] / max(1, a['save_opps']))
    return round((h_score - a_score) * 0.5, 3)