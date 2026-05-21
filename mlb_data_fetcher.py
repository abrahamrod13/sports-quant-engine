"""
MLB DATA FETCHER - Datos reales de MLB Stats API
Incluye: Pitchers, Last3, Vs Team, Bullpen, Momentum
"""
import requests
import pandas as pd
from datetime import datetime, timedelta

MLB_API = "https://statsapi.mlb.com/api/v1"

def get_today_mlb_games():
    """Partidos MLB de HOY con datos completos"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    url = f"{MLB_API}/schedule"
    params = {
        'sportId': 1,
        'date': today,
        'hydrate': 'team,probablePitcher,stats,venue'
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        games = []
        for date_data in data.get('dates', []):
            for game in date_data.get('games', []):
                home = game['teams']['home']
                away = game['teams']['away']
                venue = game.get('venue', {})
                
                home_record = home.get('leagueRecord', {})
                away_record = away.get('leagueRecord', {})
                home_wins = home_record.get('wins', 0)
                home_losses = home_record.get('losses', 0)
                away_wins = away_record.get('wins', 0)
                away_losses = away_record.get('losses', 0)
                
                home_win_pct = home_wins / (home_wins + home_losses) if (home_wins + home_losses) > 0 else 0.5
                away_win_pct = away_wins / (away_wins + away_losses) if (away_wins + away_losses) > 0 else 0.5
                
                home_pitcher = home.get('probablePitcher', {})
                away_pitcher = away.get('probablePitcher', {})
                
                home_div = home['team'].get('division', {}).get('id', 0)
                away_div = away['team'].get('division', {}).get('id', 0)
                is_divisional = (home_div == away_div)
                
                games.append({
                    'match': f"{home['team']['name']} vs {away['team']['name']}",
                    'home_team': home['team']['name'],
                    'away_team': away['team']['name'],
                    'home_team_id': home['team'].get('id'),
                    'away_team_id': away['team'].get('id'),
                    'home_win_pct': round(home_win_pct, 3),
                    'away_win_pct': round(away_win_pct, 3),
                    'home_pitcher_name': home_pitcher.get('fullName', 'TBD'),
                    'away_pitcher_name': away_pitcher.get('fullName', 'TBD'),
                    'home_pitcher_id': home_pitcher.get('id'),
                    'away_pitcher_id': away_pitcher.get('id'),
                    'stadium': venue.get('name', 'Unknown'),
                    'is_divisional': is_divisional,
                    'status': game.get('status', {}).get('detailedState', 'Scheduled')
                })
        
        return pd.DataFrame(games)
    except Exception as e:
        print(f"❌ MLB Schedule: {e}")
        return pd.DataFrame()


def get_tomorrow_mlb_games():
    """Partidos MLB de MAÑANA con datos completos"""
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    url = f"{MLB_API}/schedule"
    params = {
        'sportId': 1,
        'date': tomorrow,
        'hydrate': 'team,probablePitcher,stats,venue'
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        games = []
        for date_data in data.get('dates', []):
            for game in date_data.get('games', []):
                home = game['teams']['home']
                away = game['teams']['away']
                venue = game.get('venue', {})
                
                home_record = home.get('leagueRecord', {})
                away_record = away.get('leagueRecord', {})
                home_wins = home_record.get('wins', 0)
                home_losses = home_record.get('losses', 0)
                away_wins = away_record.get('wins', 0)
                away_losses = away_record.get('losses', 0)
                
                home_win_pct = home_wins / (home_wins + home_losses) if (home_wins + home_losses) > 0 else 0.5
                away_win_pct = away_wins / (away_wins + away_losses) if (away_wins + away_losses) > 0 else 0.5
                
                home_pitcher = home.get('probablePitcher', {})
                away_pitcher = away.get('probablePitcher', {})
                
                home_div = home['team'].get('division', {}).get('id', 0)
                away_div = away['team'].get('division', {}).get('id', 0)
                is_divisional = (home_div == away_div)
                
                games.append({
                    'match': f"{home['team']['name']} vs {away['team']['name']}",
                    'home_team': home['team']['name'],
                    'away_team': away['team']['name'],
                    'home_team_id': home['team'].get('id'),
                    'away_team_id': away['team'].get('id'),
                    'home_win_pct': round(home_win_pct, 3),
                    'away_win_pct': round(away_win_pct, 3),
                    'home_pitcher_name': home_pitcher.get('fullName', 'TBD'),
                    'away_pitcher_name': away_pitcher.get('fullName', 'TBD'),
                    'home_pitcher_id': home_pitcher.get('id'),
                    'away_pitcher_id': away_pitcher.get('id'),
                    'stadium': venue.get('name', 'Unknown'),
                    'is_divisional': is_divisional,
                    'status': game.get('status', {}).get('detailedState', 'Scheduled')
                })
        
        return pd.DataFrame(games)
    except Exception as e:
        print(f"❌ MLB Schedule: {e}")
        return pd.DataFrame()


def get_pitcher_stats(pitcher_id):
    """Stats de temporada del pitcher"""
    if not pitcher_id or pitcher_id != pitcher_id:
        return {}
    
    try:
        pitcher_id = int(pitcher_id)
    except:
        return {}
    
    url = f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats"
    
    for season in [2026, 2025]:
        params = {'stats': 'season', 'season': season, 'group': 'pitching'}
        
        try:
            response = requests.get(url, params=params)
            if response.status_code != 200:
                continue
            
            data = response.json()
            stats_list = data.get('stats', [])
            if not stats_list:
                continue
            
            splits = stats_list[0].get('splits', [])
            if not splits:
                continue
            
            stat = splits[0].get('stat', {})
            if stat.get('era'):
                innings = float(stat.get('inningsPitched', 0) or 0)
                return {
                    'era': float(stat.get('era', 4.50)),
                    'whip': float(stat.get('whip', 1.35)),
                    'k9': float(stat.get('strikeoutsPer9Inn', 7.5)),
                    'bb9': float(stat.get('walksPer9Inn', 3.0)),
                    'hr9': float(stat.get('homeRunsPer9', 1.2)),
                    'innings': round(innings, 1),
                    'wins': int(stat.get('wins', 0) or 0),
                    'losses': int(stat.get('losses', 0) or 0),
                    'babip': float(stat.get('babip', 0.290) or 0.290)
                }
        except:
            continue
    
    return {}


def get_pitcher_last3(pitcher_id):
    """Últimos 3 juegos del pitcher"""
    if not pitcher_id or pitcher_id != pitcher_id:
        return []
    try:
        pitcher_id = int(pitcher_id)
    except:
        return []
    
    url = f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats"
    params = {'stats': 'gameLog', 'season': 2026, 'limit': 3}
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        games = []
        for split in data.get('stats', [{}])[0].get('splits', []):
            stat = split.get('stat', {})
            innings = float(stat.get('inningsPitched', 5) or 5)
            
            if innings < 1.0:
                continue
            
            earned_runs = float(stat.get('earnedRuns', 3) or 3)
            hits = int(stat.get('hits', 5) or 5)
            walks = int(stat.get('baseOnBalls', 2) or 2)
            strikeouts = int(stat.get('strikeOuts', 5) or 5)
            homers = int(stat.get('homeRuns', 1) or 1)
            
            era_game = (earned_runs * 9) / innings
            whip_game = (hits + walks) / innings
            k9_game = (strikeouts * 9) / innings
            bb9_game = (walks * 9) / innings
            hr9_game = (homers * 9) / innings
            
            era_game = min(era_game, 15.0)
            whip_game = min(whip_game, 4.0)
            
            games.append({
                'date': split.get('date', ''),
                'era': round(era_game, 2),
                'whip': round(whip_game, 2),
                'k9': round(k9_game, 1),
                'bb9': round(bb9_game, 1),
                'hr9': round(hr9_game, 1),
                'innings': round(innings, 1),
                'opponent': split.get('opponent', {}).get('name', ''),
                'is_home': split.get('isHome', False)
            })
        
        return games
    except:
        return []


def get_pitcher_vs_team(pitcher_id, opponent_team_id):
    """Stats del pitcher CONTRA este equipo"""
    if not pitcher_id or pitcher_id != pitcher_id:
        return None
    if not opponent_team_id or opponent_team_id != opponent_team_id:
        return None
    
    try:
        pitcher_id = int(pitcher_id)
        opponent_team_id = int(opponent_team_id)
    except:
        return None
    
    url = f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats"
    params = {
        'stats': 'vsTeamTotal',
        'season': 2026,
        'opposingTeamId': opponent_team_id,
        'group': 'pitching'
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 404:
            params['season'] = 2025
            response = requests.get(url, params=params)
        if response.status_code != 200:
            return None
        
        data = response.json()
        splits = data.get('stats', [{}])[0].get('splits', [])
        if not splits:
            return None
        
        stat = splits[0].get('stat', {})
        return {
            'avg': float(stat.get('avg', '.250') or '.250'),
            'ops': float(stat.get('ops', '.720') or '.720'),
            'hr': int(stat.get('homeRuns', 0) or 0),
            'strikeouts': int(stat.get('strikeOuts', 0) or 0),
            'hits': int(stat.get('hits', 0) or 0),
            'at_bats': int(stat.get('atBats', 0) or 0),
            'walks': int(stat.get('baseOnBalls', 0) or 0),
            'innings': round(float(stat.get('inningsPitched', 5) or 5), 1),
            'plate_appearances': int(stat.get('plateAppearances', 0) or 0)
        }
    except:
        return None


def get_pitcher_home_away_split(pitcher_id):
    """Home/Away split del pitcher"""
    if not pitcher_id or pitcher_id != pitcher_id:
        return {'home_era': 4.50, 'away_era': 4.50}
    
    try:
        pitcher_id = int(pitcher_id)
    except:
        return {'home_era': 4.50, 'away_era': 4.50}
    
    splits_data = {'home_era': 4.50, 'away_era': 4.50}
    
    for split_type in ['home', 'away']:
        url = f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats"
        params = {
            'stats': 'statSplits',
            'season': 2026,
            'group': 'pitching',
            'splitType': split_type
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                splits = data.get('stats', [{}])[0].get('splits', [])
                if splits:
                    era = float(splits[0].get('stat', {}).get('era', 4.50) or 4.50)
                    splits_data[f'{split_type}_era'] = era
        except:
            pass
    
    return splits_data


def get_bullpen_data(team_id):
    """Datos del bullpen (últimos 3 días)"""
    if not team_id:
        return {'era': 4.00, 'whip': 1.30, 'last3_innings': 10, 'save_pct': 0.65, 'fatigue': 'NORMAL'}
    
    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/stats"
    params = {
        'stats': 'byDateRange',
        'season': 2026,
        'startDate': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
        'endDate': datetime.now().strftime('%Y-%m-%d'),
        'group': 'pitching'
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        for stat_group in data.get('stats', []):
            for split in stat_group.get('splits', []):
                stat = split.get('stat', {})
                if stat:
                    innings = float(stat.get('inningsPitched', 27) or 27)
                    bullpen_ip = max(0, innings * 0.45)
                    
                    fatigue = 'NORMAL'
                    if bullpen_ip > 18:
                        fatigue = 'CRITICAL'
                    elif bullpen_ip > 14:
                        fatigue = 'HIGH'
                    
                    return {
                        'era': float(stat.get('era', 4.00) or 4.00),
                        'whip': float(stat.get('whip', 1.30) or 1.30),
                        'last3_innings': round(bullpen_ip, 1),
                        'save_pct': 0.65,
                        'fatigue': fatigue
                    }
        
        return {'era': 4.00, 'whip': 1.30, 'last3_innings': 10, 'save_pct': 0.65, 'fatigue': 'NORMAL'}
    except:
        return {'era': 4.00, 'whip': 1.30, 'last3_innings': 10, 'save_pct': 0.65, 'fatigue': 'NORMAL'}


def get_team_momentum(team_id):
    """Momentum del equipo (últimos 10 días)"""
    if not team_id:
        return {'last10_wins': 5, 'streak': 0, 'run_diff_last10': 0, 'ops_last7': 0.720, 'era_last7': 4.20, 'runs_last5': 20, 'hard_hit_rate': 0.35}
    
    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/stats"
    params = {
        'stats': 'byDateRange',
        'season': 2026,
        'startDate': (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'),
        'endDate': datetime.now().strftime('%Y-%m-%d'),
        'group': 'hitting'
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        for stat_group in data.get('stats', []):
            for split in stat_group.get('splits', []):
                stat = split.get('stat', {})
                if stat:
                    return {
                        'last10_wins': min(10, int(stat.get('wins', 5) or 0)),
                        'streak': 0,
                        'run_diff_last10': int(stat.get('runs', 20) or 20),
                        'ops_last7': float(stat.get('ops', '.720') or '.720'),
                        'era_last7': 4.20,
                        'runs_last5': int(stat.get('runs', 20) or 20) // 2,
                        'hard_hit_rate': 0.35
                    }
        
        return {'last10_wins': 5, 'streak': 0, 'run_diff_last10': 0, 'ops_last7': 0.720, 'era_last7': 4.20, 'runs_last5': 20, 'hard_hit_rate': 0.35}
    except:
        return {'last10_wins': 5, 'streak': 0, 'run_diff_last10': 0, 'ops_last7': 0.720, 'era_last7': 4.20, 'runs_last5': 20, 'hard_hit_rate': 0.35}