"""
SERIES MOMENTUM ENGINE - Historial de serie, momentum real, run diff
"""
import requests
from datetime import datetime, timedelta

def get_team_recent_games(team_name, days=7):
    """Últimos N días de juegos para un equipo"""
    results = []
    for i in range(days):
        d = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        try:
            r = requests.get('https://statsapi.mlb.com/api/v1/schedule', 
                           params={'sportId': 1, 'date': d})
            games = r.json().get('dates', [{}])[0].get('games', [])
            for g in games:
                home = g['teams']['home']['team']['name']
                away = g['teams']['away']['team']['name']
                if team_name in [home, away]:
                    home_score = int(g['teams']['home'].get('score', 0))
                    away_score = int(g['teams']['away'].get('score', 0))
                    status = g.get('status', {}).get('detailedState', '')
                    if status == 'Final':
                        results.append({
                            'date': d,
                            'home': home,
                            'away': away,
                            'home_score': home_score,
                            'away_score': away_score,
                            'winner': home if home_score > away_score else away,
                            'is_home': team_name == home,
                            'runs_scored': home_score if team_name == home else away_score,
                            'runs_allowed': away_score if team_name == home else home_score,
                            'run_diff': (home_score - away_score) if team_name == home else (away_score - home_score)
                        })
        except:
            pass
    return results

def get_head_to_head(team1, team2, days=14):
    """Historial reciente entre 2 equipos"""
    games = get_team_recent_games(team1, days)
    return [g for g in games if team2 in [g['home'], g['away']]]

def get_series_momentum(home_team, away_team):
    """Análisis completo de momentum de serie"""
    h2h = get_head_to_head(home_team, away_team)
    home_recent = get_team_recent_games(home_team, 10)
    away_recent = get_team_recent_games(away_team, 10)
    
    # Últimos 5
    home_last5 = home_recent[:5]
    away_last5 = away_recent[:5]
    
    home_wins_last5 = sum(1 for g in home_last5 if g['winner'] == home_team)
    away_wins_last5 = sum(1 for g in away_last5 if g['winner'] == away_team)
    
    # Últimos 10
    home_wins_last10 = sum(1 for g in home_recent[:10] if g['winner'] == home_team)
    away_wins_last10 = sum(1 for g in away_recent[:10] if g['winner'] == away_team)
    
    # Run diff
    home_run_diff = sum(g['run_diff'] for g in home_last5)
    away_run_diff = sum(g['run_diff'] for g in away_last5)
    
    # Runs scored/allowed promedios
    home_runs_scored = round(sum(g['runs_scored'] for g in home_last5) / max(1, len(home_last5)), 1)
    away_runs_scored = round(sum(g['runs_scored'] for g in away_last5) / max(1, len(away_last5)), 1)
    home_runs_allowed = round(sum(g['runs_allowed'] for g in home_last5) / max(1, len(home_last5)), 1)
    away_runs_allowed = round(sum(g['runs_allowed'] for g in away_last5) / max(1, len(away_last5)), 1)
    
    # Serie actual (H2H)
    h2h_home_wins = sum(1 for g in h2h if g['winner'] == home_team)
    h2h_away_wins = sum(1 for g in h2h if g['winner'] == away_team)
    
    # Racha actual
    home_streak = 0
    for g in home_recent:
        if g['winner'] == home_team:
            home_streak += 1
        else:
            break
    
    away_streak = 0
    for g in away_recent:
        if g['winner'] == away_team:
            away_streak += 1
        else:
            break
    
    return {
        'home_last5': f"{home_wins_last5}-{5-home_wins_last5}",
        'away_last5': f"{away_wins_last5}-{5-away_wins_last5}",
        'home_last10': f"{home_wins_last10}-{10-home_wins_last10}",
        'away_last10': f"{away_wins_last10}-{10-away_wins_last10}",
        'home_run_diff_last5': home_run_diff,
        'away_run_diff_last5': away_run_diff,
        'home_runs_scored': home_runs_scored,
        'away_runs_scored': away_runs_scored,
        'home_runs_allowed': home_runs_allowed,
        'away_runs_allowed': away_runs_allowed,
        'home_streak': home_streak,
        'away_streak': away_streak,
        'h2h_record': f"{h2h_home_wins}-{h2h_away_wins}",
        'h2h_games': len(h2h),
        'h2h_details': [(g['date'], f"{g['home']} {g['home_score']}-{g['away_score']} {g['away']}") for g in h2h]
    }