"""
NBA PREDICCIONES MANANA - COMPACT MODE
"""
from nba_core import NBACore
from nba_data_fetcher import get_tomorrow_nba_games, get_fanduel_nba_odds
from nba_market_exploiter import NBAMarketExploiter
from nba_injury_fetcher import get_out_players
from nba_series_momentum import series_momentum_analysis
from nba_advanced_stats import get_team_advanced_stats, get_net_rating
import pandas as pd
from datetime import datetime, timedelta

tomorrow = datetime.now() + timedelta(days=1)

print("=" * 100)
print("NBA QUANT ENGINE V3 - COMPACT MODE (TOMORROW)")
print("=" * 100)
print(f"{'GAME':<35} {'PICK':<25} {'ODDS':>8} {'PROB':>7} {'EDGE':>8} {'CONF':>5} {'ML':>5} {'SPREAD':>8} {'O/U':>5}")
print("-" * 100)

core = NBACore()
exploiter = NBAMarketExploiter()
all_setups = []

nba_games = get_tomorrow_nba_games()

if len(nba_games) > 0:
    fanduel = get_fanduel_nba_odds()
    if len(fanduel) > 0:
        nba_games = nba_games.merge(fanduel, on='match', how='left', suffixes=('', '_fd'))
    
    nba_games = nba_games[nba_games['status'].isin(['Scheduled', 'Pre-Game'])]
    
    for _, row in nba_games.iterrows():
        home_team = row['home_team']
        away_team = row['away_team']
        is_playoff = row.get('is_playoff', False)
        
        home_injuries_raw = get_out_players(home_team)
        away_injuries_raw = get_out_players(away_team)
        
        home_net = get_net_rating(home_team, row.get('home_record', '41-41'))
        away_net = get_net_rating(away_team, row.get('away_record', '41-41'))
        
        home_data = {
            'record': row.get('home_record', '41-41'),
            'injuries': [f"OUT: {i['player']}" for i in home_injuries_raw if i['status'] == 'OUT'],
            'fatigue': [],
            'is_playoff': is_playoff,
            'is_elimination': row.get('is_elimination', False),
            'is_home': True,
            'net_rating': home_net,
            'last10': '5-5'
        }
        
        away_data = {
            'record': row.get('away_record', '41-41'),
            'injuries': [f"OUT: {i['player']}" for i in away_injuries_raw if i['status'] == 'OUT'],
            'fatigue': [],
            'is_playoff': is_playoff,
            'is_elimination': row.get('is_elimination', False),
            'is_home': False,
            'net_rating': away_net,
            'last10': '5-5'
        }
        
        home_ml = row.get('home_ml_close', row.get('home_odds', -110))
        if home_ml == 0:
            home_ml = -110
        
        result = core.evaluate_nba_game(home_data, away_data, home_ml)
        
        series = series_momentum_analysis(home_team, away_team, is_playoff)
        if series['has_momentum']:
            if series['beneficiary'] == home_team:
                result['probability'] = min(0.85, result['probability'] + series['adjustment'])
            else:
                result['probability'] = max(0.15, result['probability'] - series['adjustment'])
            result['edge'] = result['probability'] - result['market_prob']
        
        if result['edge'] > 0:
            pick = home_team if result['probability'] >= 0.5 else away_team
            if pick == home_team:
                odds_str = str(home_ml)
            else:
                odds_str = str(row.get('away_ml_close', row.get('away_odds', 110)))
        else:
            pick = "NO PICK"
            odds_str = "-"
        
        if result['approved']:
            ml_status = "[OK]"
        elif result['edge'] > 0.02:
            ml_status = "[SUS]"
        else:
            ml_status = "[X]"
        
        spread_open = row.get('spread_open', 0)
        spread_close = row.get('spread_close', 0)
        if spread_close != 0:
            spread_status = f"{spread_close:+.1f}"
        else:
            spread_status = "-"
        
        ou_status = "[?]"
        
        game_name = f"{home_team} vs {away_team}"[:33]
        pick_name = pick[:23] if pick != "NO PICK" else pick
        
        print(f"{game_name:<35} {pick_name:<25} {odds_str:>8} {result['probability']:>6.1%} {result['edge']:>+7.1%} {result['confidence_level']:>5} {ml_status:>5} {spread_status:>8} {ou_status:>5}")
        
        if result['approved']:
            result['pick'] = pick
            result['sport'] = 'NBA'
            result['match'] = row['match']
            result['home_team'] = home_team
            result['away_team'] = away_team
            all_setups.append(result)

print("-" * 100)
print(f"\n[GO] {len(all_setups)} SETUPS | [SUS] = Suspect | [X] = No edge")
print(f"Date: {tomorrow.strftime('%Y-%m-%d')}")
print("=" * 100)