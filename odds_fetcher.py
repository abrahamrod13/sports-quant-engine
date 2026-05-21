"""
ODDS FETCHER - FanDuel y otros bookmakers desde The Odds API
Incluye: h2h, spreads, totals
"""
import requests
import pandas as pd
from config import ODDS_API_KEY, ODDS_API_BASE

def get_fanduel_odds(sport='baseball_mlb'):
    """Odds básicos de FanDuel (solo h2h)"""
    url = f"{ODDS_API_BASE}/sports/{sport}/odds"
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
                        
                        if fav_odds > 0:
                            fav_decimal = round(1 + fav_odds/100, 2)
                        else:
                            fav_decimal = round(1 + 100/abs(fav_odds), 2)
                        
                        if dog_odds > 0:
                            dog_decimal = round(1 + dog_odds/100, 2)
                        else:
                            dog_decimal = round(1 + 100/abs(dog_odds), 2)
                        
                        odds_list.append({
                            'match': f"{home} vs {away}",
                            'home_team': home,
                            'away_team': away,
                            'home_odds_american': home_price,
                            'away_odds_american': away_price,
                            'favorite': favorite,
                            'underdog': underdog,
                            'favorite_odds_decimal': fav_decimal,
                            'underdog_odds_decimal': dog_decimal,
                            'favorite_odds_american': fav_odds,
                            'underdog_odds_american': dog_odds
                        })
        
        return pd.DataFrame(odds_list)
    except Exception as e:
        print(f"❌ FanDuel {sport}: {e}")
        return pd.DataFrame()


def get_fanduel_odds_full(sport='baseball_mlb'):
    """
    Odds COMPLETOS de FanDuel: h2h, spreads, totals
    Usado por el betting engine para Runline y Over/Under
    """
    url = f"{ODDS_API_BASE}/sports/{sport}/odds"
    params = {
        'apiKey': ODDS_API_KEY,
        'regions': 'us',
        'markets': 'h2h,spreads,totals',
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
                    row = {
                        'match': f"{game['home_team']} vs {game['away_team']}",
                        'home_team': game['home_team'],
                        'away_team': game['away_team']
                    }
                    
                    for market in bm['markets']:
                        key = market['key']
                        for outcome in market['outcomes']:
                            name = outcome['name']
                            price = outcome['price']
                            point = outcome.get('point', 'N/A')
                            
                            if key == 'h2h':
                                if name == game['home_team']:
                                    row['h2h_home'] = price
                                else:
                                    row['h2h_away'] = price
                            elif key == 'spreads':
                                if name == game['home_team']:
                                    row['spread_home'] = price
                                    row['spread_point'] = point
                                else:
                                    row['spread_away'] = price
                            elif key == 'totals':
                                if name == 'Over':
                                    row['total_over'] = price
                                    row['total_point'] = point
                                else:
                                    row['total_under'] = price
                    
                    # Favorito/Underdog para h2h
                    if row.get('h2h_home') and row.get('h2h_away'):
                        if row['h2h_home'] < row['h2h_away']:
                            row['favorite'] = game['home_team']
                            row['underdog'] = game['away_team']
                            row['favorite_odds_american'] = row['h2h_home']
                            row['underdog_odds_american'] = row['h2h_away']
                        else:
                            row['favorite'] = game['away_team']
                            row['underdog'] = game['home_team']
                            row['favorite_odds_american'] = row['h2h_away']
                            row['underdog_odds_american'] = row['h2h_home']
                        
                        fav = row['favorite_odds_american']
                        dog = row['underdog_odds_american']
                        row['favorite_odds_decimal'] = round(1 + 100/abs(fav) if fav < 0 else 1 + fav/100, 2)
                        row['underdog_odds_decimal'] = round(1 + 100/abs(dog) if dog < 0 else 1 + dog/100, 2)
                    
                    odds_list.append(row)
        
        return pd.DataFrame(odds_list)
    except Exception as e:
        print(f"❌ FanDuel Full {sport}: {e}")
        return pd.DataFrame()


def get_all_bookmakers_odds(sport='baseball_mlb'):
    """
    Odds de TODOS los bookmakers disponibles (para comparación)
    """
    url = f"{ODDS_API_BASE}/sports/{sport}/odds"
    params = {
        'apiKey': ODDS_API_KEY,
        'regions': 'us',
        'markets': 'h2h',
        'oddsFormat': 'american'
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        bookmakers = set()
        for game in data:
            for bm in game.get('bookmakers', []):
                bookmakers.add(bm['title'])
        
        return sorted(bookmakers)
    except:
        return []


def get_best_odds(sport='baseball_mlb'):
    """
    Mejores odds disponibles entre TODOS los bookmakers
    """
    url = f"{ODDS_API_BASE}/sports/{sport}/odds"
    params = {
        'apiKey': ODDS_API_KEY,
        'regions': 'us',
        'markets': 'h2h',
        'oddsFormat': 'american'
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        best_odds = {}
        for game in data:
            match = f"{game['home_team']} vs {game['away_team']}"
            best_odds[match] = {'home_best': -999, 'away_best': -999}
            
            for bm in game.get('bookmakers', []):
                market = bm['markets'][0]
                for outcome in market['outcomes']:
                    if outcome['name'] == game['home_team']:
                        if outcome['price'] > best_odds[match]['home_best']:
                            best_odds[match]['home_best'] = outcome['price']
                            best_odds[match]['home_bookmaker'] = bm['title']
                    elif outcome['name'] == game['away_team']:
                        if outcome['price'] > best_odds[match]['away_best']:
                            best_odds[match]['away_best'] = outcome['price']
                            best_odds[match]['away_bookmaker'] = bm['title']
        
        return best_odds
    except:
        return {}