"""
STATCAST PITCH ENGINE - Spin Rate, Velocity, Break por pitcher
"""
from pybaseball import statcast
from datetime import datetime, timedelta

def get_pitcher_arsenal(pitcher_name, days=7):
    try:
        end = datetime.now().strftime('%Y-%m-%d')
        start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        df = statcast(start_dt=start, end_dt=end)
        pitcher_df = df[df['player_name'] == pitcher_name]
        if len(pitcher_df) == 0: return None
        
        arsenal = pitcher_df.groupby('pitch_type').agg(
            count=('pitch_type', 'count'),
            avg_speed=('release_speed', 'mean'),
            avg_spin=('release_spin_rate', 'mean'),
            whiff_pct=('description', lambda x: (x.isin(['swinging_strike', 'swinging_strike_blocked'])).mean())
        ).round(1)
        return arsenal
    except: return None

def pitch_advantage(home_pitcher, away_pitcher):
    try:
        h_arsenal = get_pitcher_arsenal(home_pitcher)
        a_arsenal = get_pitcher_arsenal(away_pitcher)
        if h_arsenal is None or a_arsenal is None: return 0
        
        h_score = h_arsenal['avg_speed'].mean() * 0.3 + h_arsenal['avg_spin'].mean() / 100 * 0.3 + h_arsenal['whiff_pct'].mean() * 100 * 0.4
        a_score = a_arsenal['avg_speed'].mean() * 0.3 + a_arsenal['avg_spin'].mean() / 100 * 0.3 + a_arsenal['whiff_pct'].mean() * 100 * 0.4
        return round((h_score - a_score) / 10, 3)
    except: return 0