"""
LINEUP SPLITS ENGINE - vs LHP/RHP performance
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

def get_team_splits(team_name, split='vsLeft'):
    team_id = TEAM_IDS.get(team_name)
    if not team_id: return None
    try:
        r = requests.get(f'https://statsapi.mlb.com/api/v1/teams/{team_id}/stats',
                        params={'stats':'season','season':2026,'group':'hitting','gameType':'R','split':split}, timeout=10)
        data = r.json()
        splits = data.get('stats',[{}])[0].get('splits',[])
        stat = splits[0].get('stat',{}) if splits else {}
        if stat:
            return {
                'avg': str(stat.get('avg','.250')),
                'ops': str(stat.get('ops','.720')),
                'hr': int(stat.get('homeRuns',0) or 0),
                'so': int(stat.get('strikeOuts',0) or 0),
                'games': int(stat.get('gamesPlayed',0) or 0)
            }
        return None
    except: return None

def lineup_split_advantage(home_team, away_team, away_pitcher_throws='R'):
    """V11 - Calcula ventaja por platoon splits"""
    split_type = 'vsLeft' if away_pitcher_throws == 'L' else 'vsRight'
    home_splits = get_team_splits(home_team, split_type)
    
    if not home_splits: return 0
    
    try:
        home_ops = float(home_splits.get('ops', '.720'))
    except:
        return 0
    
    # Bonus/penalty según OPS vs este tipo de pitcher
    if home_ops > 0.760: return 0.03
    elif home_ops > 0.740: return 0.02
    elif home_ops > 0.730: return 0.01
    elif home_ops < 0.680: return -0.02
    elif home_ops < 0.700: return -0.01
    return 0