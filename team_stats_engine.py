"""
TEAM STATS ENGINE - Runs/Game, Team WHIP, Team BAA
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

def get_team_stats(team_name):
    team_id = TEAM_IDS.get(team_name)
    if not team_id: return None
    try:
        r = requests.get(f'https://statsapi.mlb.com/api/v1/teams/{team_id}/stats',
                        params={'stats':'season','season':2026,'group':'pitching'}, timeout=10)
        data = r.json()
        splits = data.get('stats',[{}])[0].get('splits',[])
        p_stat = splits[0].get('stat',{}) if splits else {}
        
        r2 = requests.get(f'https://statsapi.mlb.com/api/v1/teams/{team_id}/stats',
                         params={'stats':'season','season':2026,'group':'hitting'}, timeout=10)
        data2 = r2.json()
        splits2 = data2.get('stats',[{}])[0].get('splits',[])
        h_stat = splits2[0].get('stat',{}) if splits2 else {}
        
        return {
            'team_whip': round(float(p_stat.get('whip', 1.40)), 2),
            'team_era': round(float(p_stat.get('era', 4.50)), 2),
            'team_baa': round(float(p_stat.get('avg', '.250')), 3),
            'runs_per_game': round(float(h_stat.get('runs', 200)) / max(1, float(h_stat.get('gamesPlayed', 50))), 1),
            'ops': round(float(h_stat.get('ops', '.720')), 3)
        } if p_stat and h_stat else None
    except: return None

def team_stats_advantage(home_team, away_team):
    h = get_team_stats(home_team)
    a = get_team_stats(away_team)
    if not h or not a: return 0, 0
    
    # WHIP diff: equipo con mejor WHIP tiene ventaja
    whip_adv = (a['team_whip'] - h['team_whip']) * 0.10
    
    # Runs/Game diff
    runs_adv = (h['runs_per_game'] - a['runs_per_game']) * 0.02
    
    # OPS diff
    ops_adv = (float(h['ops']) - float(a['ops'])) * 0.5
    
    total = whip_adv + runs_adv + ops_adv
    return round(total, 3), round(whip_adv + runs_adv, 3)