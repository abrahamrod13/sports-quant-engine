"""
NBA DATA FETCHER - ESPN + The Odds API
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
from config import NBA_ESPN_BASE, ODDS_API_KEY, ODDS_API_BASE

def get_nba_scoreboard(date_str=None):
    """Partidos NBA desde ESPN"""
    if date_str is None:
        url = f"{NBA_ESPN_BASE}/scoreboard"
    else:
        url = f"{NBA_ESPN_BASE}/scoreboard?dates={date_str}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        games = []
        for event in data.get('events', []):
            comp = event['competitions'][0]
            home = comp['competitors'][0]
            away = comp['competitors'][1]
            odds_data = comp.get('odds', [{}])[0] if comp.get('odds') else {}
            
            # Récords
            home_records = home.get('records', [])
            away_records = away.get('records', [])
            
            home_total = '0-0'
            home_home = '0-0'
            away_total = '0-0'
            away_road = '0-0'
            
            for rec in home_records:
                if rec.get('type') == 'total':
                    home_total = rec.get('summary', '0-0')
                elif rec.get('type') == 'home':
                    home_home = rec.get('summary', '0-0')
            
            for rec in away_records:
                if rec.get('type') == 'total':
                    away_total = rec.get('summary', '0-0')
                elif rec.get('type') == 'road':
                    away_road = rec.get('summary', '0-0')
            
            # Notas (playoffs, etc)
            notes = comp.get('notes', [])
            headline = notes[0].get('headline', '') if notes else ''
            is_playoff = any(w in headline for w in ['Playoff', 'Semifinal', 'Final', 'Play-In'])
            is_elimination = 'Elimination' in headline or 'Game 7' in headline
            
            # Odds
            moneyline = odds_data.get('moneyline', {})
            spread = odds_data.get('pointSpread', {})
            
            home_ml_open = int(moneyline.get('home', {}).get('open', {}).get('odds', 0))
            home_ml_close = int(moneyline.get('home', {}).get('close', {}).get('odds', 0))
            away_ml_open = int(moneyline.get('away', {}).get('open', {}).get('odds', 0))
            away_ml_close = int(moneyline.get('away', {}).get('close', {}).get('odds', 0))
            
            spread_open = float(spread.get('home', {}).get('open', {}).get('line', 0))
            spread_close = float(spread.get('home', {}).get('close', {}).get('line', 0))
            
            games.append({
                'match': f"{home['team']['displayName']} vs {away['team']['displayName']}",
                'home_team': home['team']['displayName'],
                'away_team': away['team']['displayName'],
                'home_record': home_total,
                'away_record': away_total,
                'home_home_record': home_home,
                'away_road_record': away_road,
                'is_playoff': is_playoff,
                'is_elimination': is_elimination,
                'notes': headline,
                'status': event['status']['type']['description'],
                'home_ml_open': home_ml_open,
                'home_ml_close': home_ml_close,
                'away_ml_open': away_ml_open,
                'away_ml_close': away_ml_close,
                'spread_open': spread_open,
                'spread_close': spread_close,
                'home_score': int(home.get('score', 0)),
                'away_score': int(away.get('score', 0))
            })
        
        return pd.DataFrame(games)
    except Exception as e:
        print(f"❌ NBA: {e}")
        return pd.DataFrame()


def get_today_nba_games():
    today = datetime.now().strftime('%Y%m%d')
    return get_nba_scoreboard(today)


def get_tomorrow_nba_games():
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y%m%d')
    return get_nba_scoreboard(tomorrow)


def get_fanduel_nba_odds():
    """FanDuel odds para NBA"""
    url = f"{ODDS_API_BASE}/sports/basketball_nba/odds"
    params = {
        'apiKey': ODDS_API_KEY,
        'regions': 'us',
        'markets': 'h2h',
        'oddsFormat': 'american',
        'bookmakers': 'fanduel'
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        odds_list = []
        for game in data:
            for bm in game.get('bookmakers', []):
                if bm['key'] == 'fanduel':
                    market = bm['markets'][0]
                    outcomes = market['outcomes']
                    
                    home = game['home_team']
                    away = game['away_team']
                    
                    home_price = away_price = None
                    for o in outcomes:
                        if o['name'] == home:
                            home_price = o['price']
                        elif o['name'] == away:
                            away_price = o['price']
                    
                    if home_price and away_price:
                        if home_price < away_price:
                            favorite = home
                            fav_odds = home_price
                            underdog = away
                            dog_odds = away_price
                        else:
                            favorite = away
                            fav_odds = away_price
                            underdog = home
                            dog_odds = home_price
                        
                        odds_list.append({
                            'match': f"{home} vs {away}",
                            'home_team': home,
                            'away_team': away,
                            'home_odds': home_price,
                            'away_odds': away_price,
                            'favorite': favorite,
                            'underdog': underdog,
                            'favorite_odds': fav_odds,
                            'underdog_odds': dog_odds
                        })
        
        return pd.DataFrame(odds_list)
    except:
        return pd.DataFrame()