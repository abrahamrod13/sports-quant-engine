"""
NBA PREDICCIONES MAÑANA - V3: Advanced Stats + Lesiones Ponderadas + Series Momentum
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
print("🏀 NBA QUANT ENGINE V3 - PREDICCIONES MAÑANA")
print("=" * 60)
print(f"📅 {tomorrow.strftime('%Y-%m-%d')}")
print(f"🎯 Prob≥0.53 | Vol≤0.65 | Edge≥0.03")
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
    
    print(f"   {len(nba_games)} partidos\n")
    
    for _, row in nba_games.iterrows():
        home_team = row['home_team']
        away_team = row['away_team']
        is_playoff = row.get('is_playoff', False)
        
        # LESIONES REALES
        home_injuries_raw = get_out_players(home_team)
        away_injuries_raw = get_out_players(away_team)
        
        # ADVANCED STATS
        home_adv = get_team_advanced_stats(home_team)
        away_adv = get_team_advanced_stats(away_team)
        
        home_net = get_net_rating(home_team, row.get('home_record', '41-41'))
        away_net = get_net_rating(away_team, row.get('away_record', '41-41'))
        
        home_data = {
            'record': row.get('home_record', '41-41'),
            'home_record': row.get('home_home_record', '20-20'),
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
            'road_record': row.get('away_road_record', '20-20'),
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
        
        # SERIES MOMENTUM
        series = series_momentum_analysis(home_team, away_team, is_playoff)
        if series['has_momentum']:
            if series['beneficiary'] == home_team:
                result['probability'] = min(0.85, result['probability'] + series['adjustment'])
            else:
                result['probability'] = max(0.15, result['probability'] - series['adjustment'])
            result['edge'] = result['probability'] - result['market_prob']
        
        v7 = exploiter.full_analysis(row.to_dict(), result, home_team, away_team)
        
        # OUTPUT
        print(f"   🏀 {home_team} vs {away_team}")
        print(f"      🏠 {home_team}: {row.get('home_record', 'N/A')} | ✈️ {away_team}: {row.get('away_record', 'N/A')}")
        
        if row.get('notes'):
            print(f"      🏆 {row['notes']}")
        
        # ADVANCED STATS
        if home_adv:
            print(f"      📊 {home_team}: ORtg {home_adv['off_rating']} | eFG% {home_adv['efg']:.1%} | TS% {home_adv['ts']:.1%} | Net {home_net:+.1f}")
        if away_adv:
            print(f"      📊 {away_team}: ORtg {away_adv['off_rating']} | eFG% {away_adv['efg']:.1%} | TS% {away_adv['ts']:.1%} | Net {away_net:+.1f}")
        
        # SERIES MOMENTUM
        if series['has_momentum']:
            print(f"      📊 Series: {series['signal']}")
            print(f"         {series['description']} (avg margin: {series['avg_margin']:+.0f})")
            if series['blowout']:
                print(f"         💥 BLOWOUT detected - matchup may be broken")
        
        # LESIONES
        if home_injuries_raw:
            out_home = [i for i in home_injuries_raw if i['status'] == 'OUT']
            quest_home = [i for i in home_injuries_raw if i['status'] == 'QUESTIONABLE']
            if out_home:
                print(f"      🏥 {home_team} OUT: {', '.join([i['player'] for i in out_home])}")
            if quest_home:
                print(f"      🟡 {home_team} QUESTIONABLE: {', '.join([i['player'] for i in quest_home])}")
            impact_home = core.injury_impact(home_data['injuries'])
            if impact_home > 0.02:
                print(f"      ⚠️ {home_team} injury impact: -{impact_home:.0%}")
        
        if away_injuries_raw:
            out_away = [i for i in away_injuries_raw if i['status'] == 'OUT']
            quest_away = [i for i in away_injuries_raw if i['status'] == 'QUESTIONABLE']
            if out_away:
                print(f"      🏥 {away_team} OUT: {', '.join([i['player'] for i in out_away])}")
            if quest_away:
                print(f"      🟡 {away_team} QUESTIONABLE: {', '.join([i['player'] for i in quest_away])}")
            impact_away = core.injury_impact(away_data['injuries'])
            if impact_away > 0.02:
                print(f"      ⚠️ {away_team} injury impact: -{impact_away:.0%}")
        
        # FanDuel
        fav = row.get('favorite', '')
        dog = row.get('underdog', '')
        if fav:
            print(f"      💰 FanDuel: {fav} ({row.get('favorite_odds', '')}) FAV | {dog} ({row.get('underdog_odds', '')}) DOG")
        
        # Spread
        spread_open = row.get('spread_open', 0)
        spread_close = row.get('spread_close', 0)
        if spread_open and spread_close:
            movement = spread_close - spread_open
            print(f"      📈 Spread: {spread_open} → {spread_close} ({movement:+.1f})")
        
        # Market vs Model
        mv = v7['market_vs']
        print(f"      📊 Market: {mv['market_prob']:.1%} | Model: {mv['model_prob']:.1%} | Gap: {mv['discrepancy']:+.1%} [{mv['status']}]")
        
        pb = v7['public_bias']
        if pb['level'] in ['HIGH', 'MEDIUM']:
            print(f"      👥 Public Bias: {pb['level']}")
            for r in pb['reasons']:
                print(f"         - {r}")
        
        line = v7['line_movement']
        if line['signal'] != 'NORMAL':
            print(f"      📈 {line['description']}")
        
        print(f"      📊 Prob: {result['probability']} | Edge: {result['edge']} | Vol: {result['volatility']} | {result['confidence_level']}")
        
        pick = home_team if result['edge'] > 0 else away_team
        print(f"      🎯 Modelo: {pick} | V7: {v7['exploitation_level']}")
        
        if result['approved']:
            result['pick'] = pick
            result['sport'] = '🏀 NBA'
            result['match'] = row['match']
            result['home_team'] = home_team
            result['away_team'] = away_team
            result['v7_level'] = v7['exploitation_level']
            result['spread_open'] = spread_open
            result['spread_close'] = spread_close
            all_setups.append(result)
            print(f"      ✅ SETUP APROBADO")
        else:
            print(f"      ❌ No pasa filtros")
        
        print()

# RESUMEN
print("=" * 60)
print(f"📊 PREDICCIONES NBA MAÑANA ({tomorrow.strftime('%d/%m/%Y')})")
print("=" * 60)

if len(all_setups) == 0:
    print("\n🔴 0 SETUPS A+ para mañana")
    print('🧠 "No trade" anticipado.')
else:
    all_setups.sort(key=lambda x: x.get('edge', 0), reverse=True)
    print(f"\n🔥 {len(all_setups)} SETUPS NBA:\n")
    for i, s in enumerate(all_setups[:5], 1):
        v7 = s.get('v7_level', '')
        print(f"  {i}. 🏀 [{v7}] {s['home_team']} vs {s['away_team']}")
        print(f"     👉 GANA: {s['pick']}")
        print(f"     📊 Prob: {s['probability']} | Edge: {s['edge']} | {s['confidence_level']}")
        print()

print("=" * 60)
print("✅ NBA Engine V3 completado")