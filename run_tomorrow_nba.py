"""
NBA PREDICCIONES MANANA
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

print("=" * 60)
print("NBA QUANT ENGINE V3 - PREDICCIONES MANANA")
print("=" * 60)
print(f"Date: {tomorrow.strftime('%Y-%m-%d')}")
print(f"Filters: Prob>=0.53 | Vol<=0.65 | Edge>=0.03")
print("=" * 60)

core = NBACore()
exploiter = NBAMarketExploiter()
all_setups = []

nba_games = get_tomorrow_nba_games()

if len(nba_games) > 0:
    fanduel = get_fanduel_nba_odds()
    if len(fanduel) > 0:
        nba_games = nba_games.merge(fanduel, on='match', how='left', suffixes=('', '_fd'))
    
    nba_games = nba_games[nba_games['status'].isin(['Scheduled', 'Pre-Game'])]
    
    print(f"   {len(nba_games)} games\n")
    
    for _, row in nba_games.iterrows():
        home_team = row['home_team']
        away_team = row['away_team']
        is_playoff = row.get('is_playoff', False)
        
        home_injuries_raw = get_out_players(home_team)
        away_injuries_raw = get_out_players(away_team)
        
        home_adv = get_team_advanced_stats(home_team)
        away_adv = get_team_advanced_stats(away_team)
        
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
        
        v7 = exploiter.full_analysis(row.to_dict(), result, home_team, away_team)
        
        print(f"   {home_team} vs {away_team}")
        print(f"      Home: {home_team}: {row.get('home_record', 'N/A')} | Away: {away_team}: {row.get('away_record', 'N/A')}")
        
        if row.get('notes'):
            print(f"      [Playoff] {row['notes']}")
        
        if home_adv:
            print(f"      [Stats] {home_team}: ORtg {home_adv['off_rating']} | eFG% {home_adv['efg']:.1%} | Net {home_net:+.1f}")
        if away_adv:
            print(f"      [Stats] {away_team}: ORtg {away_adv['off_rating']} | eFG% {away_adv['efg']:.1%} | Net {away_net:+.1f}")
        
        if series['has_momentum']:
            print(f"      [Series] {series['signal']}: {series['description']}")
            if series['blowout']:
                print(f"      [!!] BLOWOUT detected")
        
        if home_injuries_raw:
            out_home = [i for i in home_injuries_raw if i['status'] == 'OUT']
            if out_home:
                print(f"      [Injury] {home_team} OUT: {', '.join([i['player'] for i in out_home])}")
        
        if away_injuries_raw:
            out_away = [i for i in away_injuries_raw if i['status'] == 'OUT']
            if out_away:
                print(f"      [Injury] {away_team} OUT: {', '.join([i['player'] for i in out_away])}")
        
        fav = row.get('favorite', '')
        dog = row.get('underdog', '')
        if fav:
            print(f"      [Odds] FanDuel: {fav} ({row.get('favorite_odds', '')}) FAV | {dog} ({row.get('underdog_odds', '')}) DOG")
        
        spread_open = row.get('spread_open', 0)
        spread_close = row.get('spread_close', 0)
        if spread_open and spread_close:
            print(f"      [Spread] {spread_open} -> {spread_close}")
        
        mv = v7['market_vs']
        print(f"      [Market] Market: {mv['market_prob']:.1%} | Model: {mv['model_prob']:.1%} | Gap: {mv['discrepancy']:+.1%}")
        
        print(f"      Prob: {result['probability']} | Edge: {result['edge']} | Vol: {result['volatility']}")
        
        if result['edge'] > 0:
            pick = home_team if result['probability'] >= 0.5 else away_team
        else:
            pick = 'NO PICK'
        
        print(f"      Pick: {pick} | V7: {v7['exploitation_level']}")
        
        if result['approved']:
            result['pick'] = pick
            result['sport'] = 'NBA'
            result['match'] = row['match']
            result['home_team'] = home_team
            result['away_team'] = away_team
            all_setups.append(result)
            print(f"      [OK] SETUP APROBADO")
        else:
            print(f"      [X] No pasa filtros")
        print()

print("=" * 60)
print(f"PREDICCIONES NBA MANANA ({tomorrow.strftime('%d/%m/%Y')})")
print("=" * 60)

if len(all_setups) == 0:
    print("\n[STOP] 0 SETUPS A+ manana")
else:
    all_setups.sort(key=lambda x: x.get('edge', 0), reverse=True)
    print(f"\n[GO] {len(all_setups)} SETUPS NBA:\n")
    for i, s in enumerate(all_setups[:5], 1):
        print(f"  {i}. {s['home_team']} vs {s['away_team']}")
        print(f"     GANA: {s['pick']} | Prob: {s['probability']} | Edge: {s['edge']} | {s['confidence_level']}")
        print()

print("=" * 60)
print("NBA Engine completado |", datetime.now().strftime('%H:%M'))