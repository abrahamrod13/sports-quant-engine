"""
NBA PREDICCIONES MANANA - PIPE FORMAT
"""
from nba_core import NBACore
from nba_data_fetcher import get_tomorrow_nba_games, get_fanduel_nba_odds
from nba_market_exploiter import NBAMarketExploiter
try:
    from nba_injury_fetcher import get_out_players
except:
    def get_out_players(x): return []
from nba_series_momentum import series_momentum_analysis
from nba_advanced_stats import get_team_advanced_stats, get_net_rating
import pandas as pd
from datetime import datetime, timedelta

tomorrow = datetime.now() + timedelta(days=1)

print("NBA|HOME|AWAY|PICK|ODDS|PROB|EDGE|CONF|ML|SPREAD|HOME_RECORD|AWAY_RECORD|PLAYOFF")

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
        if home_ml == 0: home_ml = -110
        
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
            if pick == home_team: odds_str = str(home_ml)
            else: odds_str = str(row.get('away_ml_close', row.get('away_odds', 110)))
        else:
            pick = "NO PICK"
            odds_str = "-"
        
        if result['approved']: ml_status = "[OK]"
        elif result['edge'] > 0.02: ml_status = "[SUS]"
        else: ml_status = "[X]"
        
        spread_close = row.get('spread_close', 0)
        spread_str = f"{spread_close:+.1f}" if spread_close != 0 else "-"
        
        print(f"NBA|{home_team}|{away_team}|{pick}|{odds_str}|{result['probability']:.1%}|{result['edge']:+.1%}|{result['confidence_level']}|{ml_status}|{spread_str}|{row.get('home_record','41-41')}|{row.get('away_record','41-41')}|{is_playoff}")
        
        home_adv = get_team_advanced_stats(home_team)
        away_adv = get_team_advanced_stats(away_team)
        print(f"DATA_NBA|{home_team}|{away_team}|{home_adv.get('off_rating','?') if home_adv else '?'}|{away_adv.get('off_rating','?') if away_adv else '?'}|{home_net}|{away_net}|{row.get('notes','')}|{', '.join([i['player'] for i in home_injuries_raw if i['status']=='OUT']) if home_injuries_raw else 'None'}|{', '.join([i['player'] for i in away_injuries_raw if i['status']=='OUT']) if away_injuries_raw else 'None'}")
        
        if result['approved']:
            result['pick'] = pick
            result['sport'] = 'NBA'
            all_setups.append(result)

print(f"SUMMARY|{len(all_setups)}")