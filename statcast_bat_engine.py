"""
STATCAST BAT ENGINE - Barrel%, HardHit%, xwOBA avanzado
"""
from pybaseball import statcast
from datetime import datetime, timedelta

def get_team_statcast_bat(team_abbr, days=7):
    try:
        end = datetime.now().strftime('%Y-%m-%d')
        start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        df = statcast(start_dt=start, end_dt=end)
        team_df = df[df['home_team'] == team_abbr]
        if len(team_df) == 0: return None
        
        batting = team_df[team_df['launch_speed'].notna()]
        if len(batting) == 0: return None
        
        return {
            'avg_ev': round(batting['launch_speed'].mean(), 1),
            'hard_hit_pct': round((batting['launch_speed'] >= 95).mean() * 100, 1),
            'barrel_pct': round(batting['estimated_ba_using_speedangle'].notna().mean() * 100, 1),
            'xba': round(batting['estimated_ba_using_speedangle'].mean(), 3),
            'xwoba': round(batting['estimated_woba_using_speedangle'].mean(), 3),
            'bat_speed': round(batting['bat_speed'].dropna().mean(), 1),
            'events': len(batting)
        }
    except: return None

def statcast_bat_advantage(home_team, away_team):
    STATCAST_MAP = {
        'Arizona Diamondbacks': 'ARI', 'Atlanta Braves': 'ATL', 'Baltimore Orioles': 'BAL',
        'Boston Red Sox': 'BOS', 'Chicago Cubs': 'CHC', 'Chicago White Sox': 'CWS',
        'Cincinnati Reds': 'CIN', 'Cleveland Guardians': 'CLE', 'Colorado Rockies': 'COL',
        'Detroit Tigers': 'DET', 'Houston Astros': 'HOU', 'Kansas City Royals': 'KC',
        'Los Angeles Angels': 'LAA', 'Los Angeles Dodgers': 'LAD', 'Miami Marlins': 'MIA',
        'Milwaukee Brewers': 'MIL', 'Minnesota Twins': 'MIN', 'New York Mets': 'NYM',
        'New York Yankees': 'NYY', 'Athletics': 'ATH', 'Philadelphia Phillies': 'PHI',
        'Pittsburgh Pirates': 'PIT', 'San Diego Padres': 'SD', 'San Francisco Giants': 'SF',
        'Seattle Mariners': 'SEA', 'St. Louis Cardinals': 'STL', 'Tampa Bay Rays': 'TB',
        'Texas Rangers': 'TEX', 'Toronto Blue Jays': 'TOR', 'Washington Nationals': 'WSH'
    }
    h_abbr = STATCAST_MAP.get(home_team)
    a_abbr = STATCAST_MAP.get(away_team)
    if not h_abbr or not a_abbr: return 0
    h = get_team_statcast_bat(h_abbr)
    a = get_team_statcast_bat(a_abbr)
    if not h or not a: return 0
    return round((h['xwoba'] - a['xwoba']) * 0.5, 3)