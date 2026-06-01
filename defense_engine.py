"""
DEFENSE ENGINE - Fielding %, Errors, Double Plays por equipo
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

def get_team_defense(team_name):
    team_id = TEAM_IDS.get(team_name)
    if not team_id: return None
    try:
        r = requests.get(f'https://statsapi.mlb.com/api/v1/teams/{team_id}/stats', 
                        params={'stats':'season','season':2026,'group':'fielding'}, timeout=10)
        data = r.json()
        splits = data.get('stats',[{}])[0].get('splits',[])
        stat = splits[0].get('stat',{}) if splits else {}
        return {
            'errors': stat.get('errors', 0),
            'fielding_pct': stat.get('fielding', '.985'),
            'double_plays': stat.get('doublePlays', 0)
        } if stat else None
    except: return None

def defense_advantage(home_team, away_team):
    h_def = get_team_defense(home_team)
    a_def = get_team_defense(away_team)
    if not h_def or not a_def: return 0
    h_score = float(h_def['fielding_pct'].replace('%','')) / 100 if '%' in h_def['fielding_pct'] else float(h_def['fielding_pct'])
    a_score = float(a_def['fielding_pct'].replace('%','')) / 100 if '%' in a_def['fielding_pct'] else float(a_def['fielding_pct'])
    return round((h_score - a_score) * 5, 3)