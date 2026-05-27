"""
STATCAST ENGINE - Power Rankings Avanzados con Baseball Savant
xwOBA, Barrel%, Exit Velocity, Luck Detector, Underrated Detector
"""
import pandas as pd
import numpy as np
from baseball_savant import client, data

STATCAST_TEAM_MAP = {
    'KC': 'Kansas City Royals', 'TEX': 'Texas Rangers', 'PIT': 'Pittsburgh Pirates',
    'MIL': 'Milwaukee Brewers', 'DET': 'Detroit Tigers', 'TOR': 'Toronto Blue Jays',
    'CLE': 'Cleveland Guardians', 'LAD': 'Los Angeles Dodgers', 'BAL': 'Baltimore Orioles',
    'BOS': 'Boston Red Sox', 'SF': 'San Francisco Giants', 'SD': 'San Diego Padres',
    'ATH': 'Athletics', 'CWS': 'Chicago White Sox', 'NYM': 'New York Mets',
    'NYY': 'New York Yankees', 'HOU': 'Houston Astros', 'ATL': 'Atlanta Braves',
    'SEA': 'Seattle Mariners', 'PHI': 'Philadelphia Phillies', 'STL': 'St. Louis Cardinals',
    'CHC': 'Chicago Cubs', 'MIN': 'Minnesota Twins', 'TB': 'Tampa Bay Rays',
    'ARI': 'Arizona Diamondbacks', 'CIN': 'Cincinnati Reds', 'COL': 'Colorado Rockies',
    'MIA': 'Miami Marlins', 'WSH': 'Washington Nationals', 'LAA': 'Los Angeles Angels'
}

class StatcastEngine:
    def __init__(self):
        self.bs_client = client.BaseballSavant()
        self.df = None
        self.team_stats = {}
    
    def fetch_data(self):
        print("📥 Descargando datos Statcast...")
        try:
            self.bs_data = data.BaseballSavantData(self.bs_client, 'data/statcast')
            self.bs_data.fetch_data()
            self.df = self.bs_data.get_data_df()
            print(f"✅ {len(self.df)} eventos descargados")
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def calculate_team_rankings(self):
        if self.df is None or len(self.df) == 0:
            return {}
        
        batting = self.df[self.df['launch_speed'].notna()].copy()
        team_stats = {}
        
        for team in pd.concat([batting['home_team'], batting['away_team']]).unique():
            if pd.isna(team):
                continue
            
            team_batting = batting[batting['home_team'] == team]
            if len(team_batting) < 10:
                continue
            
            avg_ev = team_batting['launch_speed'].mean()
            avg_la = team_batting['launch_angle'].mean()
            hard_hit_pct = (team_batting['launch_speed'] >= 95).mean()
            barrel_pct = team_batting['estimated_ba_using_speedangle'].notna().mean()
            avg_xba = team_batting['estimated_ba_using_speedangle'].mean()
            avg_xwoba = team_batting['estimated_woba_using_speedangle'].mean()
            hit_dist = team_batting['hit_distance_sc'].dropna()
            avg_distance = hit_dist.mean() if len(hit_dist) > 0 else 0
            avg_bat_speed = team_batting['bat_speed'].dropna().mean()
            
            full_name = STATCAST_TEAM_MAP.get(team, team)
            
            team_stats[full_name] = {
                'avg_exit_velo': round(avg_ev, 1),
                'avg_launch_angle': round(avg_la, 1),
                'hard_hit_pct': round(hard_hit_pct * 100, 1),
                'barrel_pct': round(barrel_pct * 100, 1),
                'avg_xba': round(avg_xba, 3),
                'avg_xwoba': round(avg_xwoba, 3),
                'avg_distance': round(avg_distance, 0),
                'avg_bat_speed': round(avg_bat_speed, 1) if not pd.isna(avg_bat_speed) else 0,
                'events': len(team_batting)
            }
        
        self.team_stats = team_stats
        return team_stats
    
    def luck_detector(self, team_name):
        if team_name not in self.team_stats:
            return 'NO DATA'
        s = self.team_stats[team_name]
        ev = s['avg_exit_velo']
        xba = s['avg_xba']
        if ev > 89 and xba < 0.240:
            return 'UNLUCKY'
        elif ev < 87 and xba > 0.270:
            return 'LUCKY'
        else:
            return 'NORMAL'
    
    def get_power_score(self, team_name):
        if team_name not in self.team_stats:
            return 50
        s = self.team_stats[team_name]
        score = min(25, s['avg_exit_velo'] / 4) + min(25, s['hard_hit_pct'] * 0.6) + min(20, s['barrel_pct'] * 2) + min(15, s['avg_xwoba'] * 50) + min(15, s['avg_distance'] / 20)
        return min(100, round(score))
    
    def get_team_power(self, team_name):
        if team_name not in self.team_stats:
            return None
        s = self.team_stats[team_name]
        return {
            'power_score': self.get_power_score(team_name),
            'exit_velo': s['avg_exit_velo'], 'hard_hit': s['hard_hit_pct'],
            'barrel': s['barrel_pct'], 'xba': s['avg_xba'], 'xwoba': s['avg_xwoba'],
            'luck': self.luck_detector(team_name)
        }
    
    def print_rankings(self, top=30):
        if not self.team_stats:
            print("No data.")
            return
        sorted_teams = sorted(self.team_stats.items(), key=lambda x: x[1]['avg_exit_velo'], reverse=True)
        print(f"\n{'TEAM':<25} {'EV':>6} {'LA':>6} {'Hard%':>6} {'BRL%':>6} {'xBA':>6} {'xwOBA':>6} {'DIST':>6} {'LUCK':>10} {'PWR':>5}")
        print("-" * 100)
        for team, s in sorted_teams[:top]:
            luck = self.luck_detector(team)
            power = self.get_power_score(team)
            print(f"{team:<25} {s['avg_exit_velo']:>5.1f} {s['avg_launch_angle']:>5.1f} {s['hard_hit_pct']:>5.1f}% {s['barrel_pct']:>5.1f}% {s['avg_xba']:>5.3f} {s['avg_xwoba']:>5.3f} {s['avg_distance']:>5.0f} {luck:>10} {power:>4}")

if __name__ == "__main__":
    engine = StatcastEngine()
    if engine.fetch_data():
        engine.calculate_team_rankings()
        engine.print_rankings()