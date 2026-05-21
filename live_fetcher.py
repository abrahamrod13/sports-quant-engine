import requests
import pandas as pd
from datetime import datetime, timedelta
from config import (
    NBA_ESPN_BASE, ODDS_API_KEY, ODDS_API_BASE, 
    SOCCER_API_KEY, SOCCER_API_BASE, PRIORITY_LEAGUE_IDS
)

MLB_ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb"

# ============================================
# HOY
# ============================================

def get_live_nba_games():
    url = f"{NBA_ESPN_BASE}/scoreboard"
    games = _parse_espn_games(url, 'nba')
    return pd.DataFrame(games)

def get_live_mlb_games():
    url = f"{MLB_ESPN_BASE}/scoreboard"
    games = _parse_espn_games(url, 'mlb')
    return pd.DataFrame(games)

def get_live_soccer_matches():
    date = datetime.now().strftime('%Y-%m-%d')
    url = f"{SOCCER_API_BASE}/fixtures"
    headers = {'x-apisports-key': SOCCER_API_KEY}
    params = {'date': date}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        
        matches = []
        for fixture in data.get('response', []):
            league_id = fixture['league']['id']
            if league_id not in PRIORITY_LEAGUE_IDS:
                continue
            
            home = fixture['teams']['home']
            away = fixture['teams']['away']
            status = fixture['fixture']['status']['short']
            
            if status not in ['NS', 'TBD', 'PST']:
                continue
            
            matches.append({
                'sport': 'soccer',
                'match': f"{home['name']} vs {away['name']}",
                'home_team': home['name'],
                'away_team': away['name'],
                'league': PRIORITY_LEAGUE_IDS[league_id],
                'home_win_pct': 0.55,
                'away_win_pct': 0.48,
                'home_form': 0.58,
                'away_form': 0.50,
                'home_xg': 1.8,
                'away_xg': 1.2,
                'status': status
            })
        
        return pd.DataFrame(matches)
    except:
        return pd.DataFrame()


def _parse_espn_games(url, sport):
    try:
        response = requests.get(url)
        data = response.json()
        
        games = []
        for event in data.get('events', []):
            comp = event['competitions'][0]
            home = comp['competitors'][0]
            away = comp['competitors'][1]
            
            home_records = home.get('records', [])
            away_records = away.get('records', [])
            
            home_win_pct = 0.5
            away_win_pct = 0.5
            
            for rec in home_records:
                if rec.get('type') == 'total':
                    parts = rec.get('summary', '0-0').split('-')
                    if len(parts) == 2:
                        w, l = map(int, parts)
                        home_win_pct = w/(w+l) if (w+l) > 0 else 0.5
            
            for rec in away_records:
                if rec.get('type') == 'total':
                    parts = rec.get('summary', '0-0').split('-')
                    if len(parts) == 2:
                        w, l = map(int, parts)
                        away_win_pct = w/(w+l) if (w+l) > 0 else 0.5
            
            notes = comp.get('notes', [])
            is_playoff = any('Playoff' in n.get('headline', '') or 'Semifinal' in n.get('headline', '') or 'Final' in n.get('headline', '') for n in notes)
            
            pitcher_note = ''
            for n in notes:
                if 'Probable' in n.get('headline', '') or 'Pitcher' in n.get('headline', ''):
                    pitcher_note = n.get('headline', '')
            
            games.append({
                'sport': sport,
                'match': f"{home['team']['displayName']} vs {away['team']['displayName']}",
                'home_team': home['team']['displayName'],
                'away_team': away['team']['displayName'],
                'home_win_pct': home_win_pct,
                'away_win_pct': away_win_pct,
                'is_playoff': is_playoff,
                'pitcher_note': pitcher_note,
                'status': event['status']['type']['description']
            })
        
        return games
    except:
        return []


def get_live_odds(sport='basketball_nba'):
    url = f"{ODDS_API_BASE}/sports/{sport}/odds"
    params = {
        'apiKey': ODDS_API_KEY,
        'regions': 'eu',
        'markets': 'h2h',
        'oddsFormat': 'decimal'
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        odds_list = []
        for game in data:
            if game['bookmakers']:
                bm = game['bookmakers'][0]
                market = bm['markets'][0]
                
                odds_home = odds_away = odds_draw = None
                for outcome in market['outcomes']:
                    if outcome['name'] == game['home_team']:
                        odds_home = outcome['price']
                    elif outcome['name'] == game['away_team']:
                        odds_away = outcome['price']
                    elif outcome['name'] == 'Draw':
                        odds_draw = outcome['price']
                
                odds_list.append({
                    'match': f"{game['home_team']} vs {game['away_team']}",
                    'home_team': game['home_team'],
                    'away_team': game['away_team'],
                    'odds_home': odds_home,
                    'odds_away': odds_away,
                    'odds_draw': odds_draw
                })
        
        # DEDUPLICAR: mejor cuota por partido
        if len(odds_list) > 0:
            df = pd.DataFrame(odds_list)
            df = df.groupby('match', as_index=False).agg({
                'home_team': 'first',
                'away_team': 'first',
                'odds_home': 'max',
                'odds_away': 'max',
                'odds_draw': 'max'
            })
            return df
        
        return pd.DataFrame()
    except:
        return pd.DataFrame()


# ============================================
# MAÑANA
# ============================================

def get_tomorrow_nba_games():
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y%m%d')
    url = f"{NBA_ESPN_BASE}/scoreboard?dates={tomorrow}"
    games = _parse_espn_games(url, 'nba')
    return pd.DataFrame(games)


def get_tomorrow_mlb_games():
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y%m%d')
    url = f"{MLB_ESPN_BASE}/scoreboard?dates={tomorrow}"
    games = _parse_espn_games(url, 'mlb')
    return pd.DataFrame(games)


def get_tomorrow_soccer_matches():
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    url = f"{SOCCER_API_BASE}/fixtures"
    headers = {'x-apisports-key': SOCCER_API_KEY}
    params = {'date': tomorrow}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        
        matches = []
        for fixture in data.get('response', []):
            league_id = fixture['league']['id']
            if league_id not in PRIORITY_LEAGUE_IDS:
                continue
            
            home = fixture['teams']['home']
            away = fixture['teams']['away']
            
            matches.append({
                'sport': 'soccer',
                'match': f"{home['name']} vs {away['name']}",
                'home_team': home['name'],
                'away_team': away['name'],
                'league': PRIORITY_LEAGUE_IDS[league_id],
                'home_win_pct': 0.55,
                'away_win_pct': 0.48,
                'home_form': 0.58,
                'away_form': 0.50,
                'home_xg': 1.8,
                'away_xg': 1.2,
                'status': 'NS'
            })
        
        return pd.DataFrame(matches)
    except:
        return pd.DataFrame()


def get_tomorrow_odds(sport='basketball_nba'):
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    url = f"{ODDS_API_BASE}/sports/{sport}/odds"
    params = {
        'apiKey': ODDS_API_KEY,
        'regions': 'eu',
        'markets': 'h2h',
        'oddsFormat': 'decimal',
        'date': f"{tomorrow}T12:00:00Z"
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        odds_list = []
        for game in data:
            if game['bookmakers']:
                bm = game['bookmakers'][0]
                market = bm['markets'][0]
                
                odds_home = odds_away = odds_draw = None
                for outcome in market['outcomes']:
                    if outcome['name'] == game['home_team']:
                        odds_home = outcome['price']
                    elif outcome['name'] == game['away_team']:
                        odds_away = outcome['price']
                    elif outcome['name'] == 'Draw':
                        odds_draw = outcome['price']
                
                odds_list.append({
                    'match': f"{game['home_team']} vs {game['away_team']}",
                    'home_team': game['home_team'],
                    'away_team': game['away_team'],
                    'odds_home': odds_home,
                    'odds_away': odds_away,
                    'odds_draw': odds_draw
                })
        
        # DEDUPLICAR
        if len(odds_list) > 0:
            df = pd.DataFrame(odds_list)
            df = df.groupby('match', as_index=False).agg({
                'home_team': 'first',
                'away_team': 'first',
                'odds_home': 'max',
                'odds_away': 'max',
                'odds_draw': 'max'
            })
            return df
        
        return pd.DataFrame()
    except:
        return pd.DataFrame()