from quant_engine import QuantEngine
from mlb_data_fetcher import (
    get_today_mlb_games, get_pitcher_stats, get_pitcher_last3,
    get_pitcher_vs_team, get_pitcher_home_away_split,
    get_bullpen_data, get_team_momentum
)
from mlb_engine import MLBEngine
from market_intelligence import MarketIntelligence
from sharp_edge_engine import SharpEdgeEngine
from market_exploiter import MarketExploiter
from odds_fetcher import get_fanduel_odds_full
from betting_logger import save_bet
from montecarlo_mlb import MonteCarloMLB
import pandas as pd
import os
from datetime import datetime

print("=" * 60)
print("MLB QUANT ENGINE V8 - ANALISIS COMPLETO HOY")
print("=" * 60)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print(f"Filters: Edge>0.02 | Prob>=0.52 | Vol<=0.68 | Context>=0.37")
print("=" * 60)

mlb_engine = MLBEngine()
market_intel = MarketIntelligence()
sharp = SharpEdgeEngine()
exploiter = MarketExploiter()
mc = MonteCarloMLB()
all_setups = []

print("\nMLB HOY...")
mlb_games = get_today_mlb_games()

if len(mlb_games) > 0:
    fanduel_mlb = get_fanduel_odds_full('baseball_mlb')
    if len(fanduel_mlb) > 0:
        mlb_games = mlb_games.merge(fanduel_mlb, on='match', how='left', suffixes=('', '_fd'))
    
    mlb_games = mlb_games.drop_duplicates(subset=['match'], keep='first')
    
    print(f"   {len(mlb_games)} games\n")
    
    for _, row in mlb_games.iterrows():
        home_team = row['home_team']
        away_team = row['away_team']
        home_id = row.get('home_team_id')
        away_id = row.get('away_team_id')
        home_win = row.get('home_win_pct', 0.5)
        away_win = row.get('away_win_pct', 0.5)
        
        h2h_home = row.get('h2h_home', -110)
        h2h_away = row.get('h2h_away', -110)
        spread_home = row.get('spread_home', -110)
        spread_away = row.get('spread_away', -110)
        spread_point = row.get('spread_point', 1.5)
        total_over = row.get('total_over', -110)
        total_under = row.get('total_under', -110)
        total_point = row.get('total_point', 8.5)
        fav_odds_dec = row.get('favorite_odds_decimal', 2.0) or 2.0
        
        print(f"   {home_team} vs {away_team}")
        print(f"      [Stadium] {row.get('stadium', 'Unknown')} | {'Divisional' if row.get('is_divisional', False) else 'No divisional'}")
        print(f"      [Odds] ML: {home_team} ({h2h_home}) | {away_team} ({h2h_away})")
        print(f"      [Odds] Spread: {home_team} {spread_point} ({spread_home}) | {away_team} +{spread_point} ({spread_away})")
        print(f"      [Odds] Total: O/U {total_point} (O:{total_over} / U:{total_under})")
        
        home_p_data = get_pitcher_stats(row.get('home_pitcher_id'))
        away_p_data = get_pitcher_stats(row.get('away_pitcher_id'))
        home_p_name = row.get('home_pitcher_name', 'TBD')
        away_p_name = row.get('away_pitcher_name', 'TBD')
        
        if home_p_name == 'TBD' and not home_p_data:
            print(f"      [!] {home_team} pitcher: TBD - SKIPPED\n")
            continue
        if away_p_name == 'TBD' and not away_p_data:
            print(f"      [!] {away_team} pitcher: TBD - SKIPPED\n")
            continue
        
        if not home_p_data:
            home_p_data = mlb_engine.smart_pitcher_defaults(home_p_name)
        if not away_p_data:
            away_p_data = mlb_engine.smart_pitcher_defaults(away_p_name)
        
        print(f"      [Pitcher] {home_p_name}: {home_p_data.get('era','?')} ERA | {home_p_data.get('whip','?')} WHIP | {home_p_data.get('k9','?')} K9")
        print(f"      [Pitcher] {away_p_name}: {away_p_data.get('era','?')} ERA | {away_p_data.get('whip','?')} WHIP | {away_p_data.get('k9','?')} K9")
        
        home_last3 = get_pitcher_last3(row.get('home_pitcher_id'))
        away_last3 = get_pitcher_last3(row.get('away_pitcher_id'))
        if home_last3:
            home_p_data['last3_era'] = round(sum(g['era'] for g in home_last3) / len(home_last3), 2)
        if away_last3:
            away_p_data['last3_era'] = round(sum(g['era'] for g in away_last3) / len(away_last3), 2)
        
        home_bullpen = get_bullpen_data(home_id)
        away_bullpen = get_bullpen_data(away_id)
        home_momentum = get_team_momentum(home_id)
        away_momentum = get_team_momentum(away_id)
        
        if home_bullpen.get('fatigue') in ['HIGH', 'CRITICAL']:
            print(f"      [!] {home_team} bullpen FATIGADO ({home_bullpen.get('last3_innings')} IP)")
        if away_bullpen.get('fatigue') in ['HIGH', 'CRITICAL']:
            print(f"      [!] {away_team} bullpen FATIGADO ({away_bullpen.get('last3_innings')} IP)")
        
        home_vs_away = get_pitcher_vs_team(row.get('home_pitcher_id'), away_id)
        away_vs_home = get_pitcher_vs_team(row.get('away_pitcher_id'), home_id)
        
        game_data = {
            'home_team': home_team, 'away_team': away_team,
            'home_win_pct': home_win, 'away_win_pct': away_win,
            'home_pitcher': home_p_data, 'away_pitcher': away_p_data,
            'home_pitcher_name': home_p_name, 'away_pitcher_name': away_p_name,
            'home_momentum': home_momentum, 'away_momentum': away_momentum,
            'home_bullpen': home_bullpen, 'away_bullpen': away_bullpen,
            'home_matchup': {
                'avg': home_vs_away.get('avg', 0.250) if home_vs_away else 0.250,
                'ops': home_vs_away.get('ops', 0.720) if home_vs_away else 0.720,
                'hr': home_vs_away.get('hr', 0) if home_vs_away else 0,
                'pa': home_vs_away.get('plate_appearances', 0) if home_vs_away else 0,
                'k_rate': 0.22
            },
            'away_matchup': {
                'avg': away_vs_home.get('avg', 0.250) if away_vs_home else 0.250,
                'ops': away_vs_home.get('ops', 0.720) if away_vs_home else 0.720,
                'hr': away_vs_home.get('hr', 0) if away_vs_home else 0,
                'pa': away_vs_home.get('plate_appearances', 0) if away_vs_home else 0,
                'k_rate': 0.22
            },
            'stadium': row.get('stadium', ''),
            'divisional_game': row.get('is_divisional', False),
            'bullpen_home_weak': home_bullpen.get('fatigue', 'NORMAL') in ['HIGH', 'CRITICAL'],
            'bullpen_away_weak': away_bullpen.get('fatigue', 'NORMAL') in ['HIGH', 'CRITICAL'],
            'hr_heavy_teams': home_win > 0.58 or away_win > 0.58,
            'wind_outward': False,
            'odds': fav_odds_dec
        }
        
        result = mlb_engine.evaluate_mlb_game(game_data, fav_odds_dec)
        intel = market_intel.final_decision(game_data, result)
        
        print(f"\n      -----------------------------------------------------")
        print(f"      MONEYLINE")
        print(f"      -----------------------------------------------------")
        print(f"      Prob: {result['probability']:.1%} | Edge: {result['edge']:+.1%} | Vol: {result['volatility']} | {result['confidence_level']} ({result['confidence_score']:.3f})")
        print(f"      Pick: {result['pick']} | Market: {(1/fav_odds_dec):.1%} | Model: {result['probability']:.1%}")
        
        if intel['approved']:
            print(f"      [OK] SETUP APROBADO ({intel['edge_quality']} EDGE)")
        else:
            print(f"      [X] RECHAZADO: {intel['reason']}")
        print(f"      -----------------------------------------------------")
        
        if intel['approved']:
            result['sport'] = 'MLB'
            result['match'] = row['match']
            result['home_team'] = home_team
            result['away_team'] = away_team
            result['bet_type'] = 'Moneyline'
            result['odds_american'] = h2h_home if result['pick'] == home_team else h2h_away
            all_setups.append(result)
            
            log_file = 'data/betting_log.csv'
            already_saved = False
            if os.path.exists(log_file):
                try:
                    existing = pd.read_csv(log_file)
                    match_name = result.get('match', '')
                    pick_name = result.get('pick', '')
                    today_str = datetime.now().strftime('%Y-%m-%d')
                    already_saved = len(existing[
                        (existing['date'] == today_str) &
                        (existing['match'] == match_name) &
                        (existing['bet_type'] == 'Moneyline')
                    ]) > 0
                except:
                    pass
            if not already_saved:
                save_bet('MLB', result.get('match', ''), 'Moneyline',
                        result.get('pick', ''), h2h_home if result['pick'] == home_team else h2h_away,
                        result.get('probability', 0), result.get('edge', 0),
                        result.get('volatility', 0), result.get('confidence_score', 0))
        
        # BETTING OPTIONS
        model_fav = home_team if result['probability'] >= 0.5 else away_team
        model_dog = away_team if result['probability'] >= 0.5 else home_team
        
        print(f"\n      -----------------------------------------------------")
        print(f"      BETTING OPTIONS (validate with Monte Carlo)")
        print(f"      -----------------------------------------------------")
        
        if result['probability'] >= 0.55:
            rl_prob = result['probability'] - 0.08
            rl_edge = rl_prob - 0.45
            print(f"      Runline {model_fav} -1.5: {rl_prob:.1%} | Edge: {rl_edge:+.1%} {'[OK]' if rl_edge > 0.02 else '[?]'}")
        if result['probability'] <= 0.45:
            rl_prob = (1 - result['probability']) - 0.08
            rl_edge = rl_prob - 0.45
            print(f"      Runline {model_fav} -1.5: {rl_prob:.1%} | Edge: {rl_edge:+.1%} {'[OK]' if rl_edge > 0.02 else '[?]'}")
        
        total_prob = 0.5
        home_eff_era = home_p_data.get('last3_era', home_p_data.get('era', 4.50))
        away_eff_era = away_p_data.get('last3_era', away_p_data.get('era', 4.50))
        
        if home_eff_era > 5.5 and away_eff_era > 5.5:
            total_prob = 0.62
        elif home_eff_era < 3.0 and away_eff_era < 3.0:
            total_prob = 0.38
        elif home_eff_era > 5.0 or away_eff_era > 5.0:
            total_prob = 0.56
        
        over_edge = total_prob - 0.45
        under_prob = 1 - total_prob
        under_edge = under_prob - 0.45
        
        print(f"      Over {total_point}: {total_prob:.1%} | Edge: {over_edge:+.1%} {'[OK]' if over_edge > 0.02 else '[?]'}")
        print(f"      Under {total_point}: {under_prob:.1%} | Edge: {under_edge:+.1%} {'[OK]' if under_edge > 0.02 else '[?]'}")
        
        home_offense = home_momentum.get('ops_last7', 0.720)
        away_offense = away_momentum.get('ops_last7', 0.720)
        
        home_over_prob = 0.5 + (home_offense - 0.700) * 0.8 + (away_eff_era - 4.0) * 0.05
        home_over_prob = max(0.25, min(0.85, home_over_prob))
        
        away_over_prob = 0.5 + (away_offense - 0.700) * 0.8 + (home_eff_era - 4.0) * 0.05
        away_over_prob = max(0.25, min(0.85, away_over_prob))
        
        print(f"      {home_team} Team Over 3.5: {home_over_prob:.1%} {'[OK]' if home_over_prob > 0.55 else '[?]'}")
        print(f"      {away_team} Team Over 3.5: {away_over_prob:.1%} {'[OK]' if away_over_prob > 0.55 else '[?]'}")
        
        f5_prob = result['probability']
        f5_edge = f5_prob - 0.45
        print(f"      First 5 ML {model_fav}: {f5_prob:.1%} | Edge: {f5_edge:+.1%} {'[OK]' if f5_edge > 0.02 else '[?]'}")
        
        print(f"      -----------------------------------------------------")
        print()

print("=" * 60)
print(f"RESULTADO MLB HOY ({datetime.now().strftime('%d/%m/%Y')})")
print("=" * 60)

if len(all_setups) == 0:
    print("\n[STOP] 0 SETUPS A+ hoy (Moneyline)")
    print('Revisa opciones de Totals/Runline arriba')
else:
    all_setups.sort(key=lambda x: x.get('edge', 0), reverse=True)
    print(f"\n[GO] {len(all_setups)} SETUPS MONEYLINE:\n")
    for i, s in enumerate(all_setups[:5], 1):
        print(f"  {i}. {s['home_team']} vs {s['away_team']}")
        print(f"     GANA: {s['pick']} | Prob: {s['probability']} | Edge: {s['edge']}")
        print()

print("=" * 60)
print("Analisis MLB completado - V8 |", datetime.now().strftime('%H:%M'))