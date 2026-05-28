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

try:
    from mlb_injury_fetcher import get_out_players_mlb
except:
    def get_out_players_mlb(x): return []

try:
    from statcast_engine import StatcastEngine
    statcast_engine = StatcastEngine()
    statcast_engine.fetch_data()
    statcast_engine.calculate_team_rankings()
except:
    statcast_engine = None

print("MLB|HOME|AWAY|PICK|ODDS|PROB|EDGE|CONF|ML|RL|OU|TEAM|F5")

mlb_engine = MLBEngine()
market_intel = MarketIntelligence()
all_setups = []

mlb_games = get_today_mlb_games()

if len(mlb_games) > 0:
    fanduel_mlb = get_fanduel_odds_full('baseball_mlb')
    if len(fanduel_mlb) > 0:
        mlb_games = mlb_games.merge(fanduel_mlb, on='match', how='left', suffixes=('', '_fd'))
    mlb_games = mlb_games.drop_duplicates(subset=['match'], keep='first')
    
    for _, row in mlb_games.iterrows():
        home_team = row['home_team']
        away_team = row['away_team']
        home_id = row.get('home_team_id')
        away_id = row.get('away_team_id')
        home_win = row.get('home_win_pct', 0.5)
        away_win = row.get('away_win_pct', 0.5)
        
        h2h_home = row.get('h2h_home', -110)
        h2h_away = row.get('h2h_away', -110)
        total_point = row.get('total_point', 8.5)
        fav_odds_dec = row.get('favorite_odds_decimal', 2.0) or 2.0
        
        home_p_data = get_pitcher_stats(row.get('home_pitcher_id'))
        away_p_data = get_pitcher_stats(row.get('away_pitcher_id'))
        home_p_name = row.get('home_pitcher_name', 'TBD')
        away_p_name = row.get('away_pitcher_name', 'TBD')
        
        if home_p_name == 'TBD' or away_p_name == 'TBD':
            continue
        
        if not home_p_data: home_p_data = mlb_engine.smart_pitcher_defaults(home_p_name)
        if not away_p_data: away_p_data = mlb_engine.smart_pitcher_defaults(away_p_name)
        
        home_last3 = get_pitcher_last3(row.get('home_pitcher_id'))
        away_last3 = get_pitcher_last3(row.get('away_pitcher_id'))
        if home_last3: home_p_data['last3_era'] = round(sum(g['era'] for g in home_last3) / len(home_last3), 2)
        if away_last3: away_p_data['last3_era'] = round(sum(g['era'] for g in away_last3) / len(away_last3), 2)
        
        home_bullpen = get_bullpen_data(home_id)
        away_bullpen = get_bullpen_data(away_id)
        home_momentum = get_team_momentum(home_id)
        away_momentum = get_team_momentum(away_id)
        home_vs_away = get_pitcher_vs_team(row.get('home_pitcher_id'), away_id)
        away_vs_home = get_pitcher_vs_team(row.get('away_pitcher_id'), home_id)
        
        try:
            home_injuries = get_out_players_mlb(home_team)
            away_injuries = get_out_players_mlb(away_team)
        except:
            home_injuries = []
            away_injuries = []
        home_inj_str = ';'.join([f"{i['player']}({i['injury']})" for i in home_injuries]) if home_injuries else 'None'
        away_inj_str = ';'.join([f"{i['player']}({i['injury']})" for i in away_injuries]) if away_injuries else 'None'
        
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
                'pa': home_vs_away.get('plate_appearances', 0) if home_vs_away else 0, 'k_rate': 0.22
            },
            'away_matchup': {
                'avg': away_vs_home.get('avg', 0.250) if away_vs_home else 0.250,
                'ops': away_vs_home.get('ops', 0.720) if away_vs_home else 0.720,
                'hr': away_vs_home.get('hr', 0) if away_vs_home else 0,
                'pa': away_vs_home.get('plate_appearances', 0) if away_vs_home else 0, 'k_rate': 0.22
            },
            'stadium': row.get('stadium', ''), 'divisional_game': row.get('is_divisional', False),
            'bullpen_home_weak': home_bullpen.get('fatigue', 'NORMAL') in ['HIGH', 'CRITICAL'],
            'bullpen_away_weak': away_bullpen.get('fatigue', 'NORMAL') in ['HIGH', 'CRITICAL'],
            'hr_heavy_teams': home_win > 0.58 or away_win > 0.58, 'wind_outward': False, 'odds': fav_odds_dec
        }
        
        result = mlb_engine.evaluate_mlb_game(game_data, fav_odds_dec)
        
        # STATCAST POWER BONUS
        try:
            if statcast_engine:
                home_power = statcast_engine.get_team_power(home_team)
                away_power = statcast_engine.get_team_power(away_team)
                if home_power and away_power:
                    power_diff = home_power['power_score'] - away_power['power_score']
                    result['probability'] = min(0.85, max(0.15, result['probability'] + (power_diff / 10) * 0.015))
        except: pass
        
        # SERIES MOMENTUM BONUS
        try:
            from series_momentum_engine import get_series_momentum
            sm = get_series_momentum(home_team, away_team)
            if sm:
                momentum_bonus = 0
                home_wins = int(sm['home_last5'].split('-')[0])
                away_wins = int(sm['away_last5'].split('-')[0])
                if home_wins >= 4 and away_wins <= 1: momentum_bonus += 0.03
                elif home_wins >= 3 and away_wins <= 2: momentum_bonus += 0.015
                if sm['home_run_diff_last5'] > 15: momentum_bonus += 0.02
                if sm['h2h_games'] >= 2:
                    h2h_home = int(sm['h2h_record'].split('-')[0])
                    if h2h_home == sm['h2h_games']: momentum_bonus += 0.02
                result['probability'] = min(0.85, max(0.15, result['probability'] + momentum_bonus))
        except: pass
        
        # LESIONES IMPACT
        try:
            stars = ['Trout', 'Ohtani', 'Judge', 'Betts', 'Soto', 'Freeman', 'Tatis', 'Harper', 'Turner', 'Devers', 'Ramirez']
            injury_penalty = 0
            for inj in home_injuries:
                if any(star.lower() in inj.get('player', '').lower() for star in stars):
                    injury_penalty -= 0.04
            for inj in away_injuries:
                if any(star.lower() in inj.get('player', '').lower() for star in stars):
                    injury_penalty += 0.04
            result['probability'] = min(0.85, max(0.15, result['probability'] + injury_penalty))
        except: pass
        
        # LINEUP IMPACT
        try:
            from lineup_fetcher import get_lineups_for_match, lineup_impact
            lineups = get_lineups_for_match(home_team, away_team)
            if lineups.get('has_lineups'):
                lineup_adj = lineup_impact(lineups, home_team, away_team)
                result['probability'] = min(0.85, max(0.15, result['probability'] + lineup_adj))
        except: pass
        
        result['edge'] = result['probability'] - (1 / fav_odds_dec)
        
        intel = market_intel.final_decision(game_data, result)
        
        if result['edge'] > 0:
            pick = home_team if result['probability'] >= 0.5 else away_team
            odds_str = str(h2h_home if pick == home_team else h2h_away)
        else:
            pick = "NO PICK"
            odds_str = "-"
        
        ml_status = "[OK]" if intel['approved'] else ("[SUS]" if result['edge'] > 0.03 else "[X]")
        rl_status = "[X]"
        if result['probability'] >= 0.55: rl_status = "[OK]" if result['probability'] - 0.08 - 0.45 > 0.02 else "[?]"
        elif result['probability'] <= 0.45: rl_status = "[OK]" if (1-result['probability']) - 0.08 - 0.45 > 0.02 else "[?]"
        
        home_eff_era = home_p_data.get('last3_era', home_p_data.get('era', 4.50))
        away_eff_era = away_p_data.get('last3_era', away_p_data.get('era', 4.50))
        total_prob = 0.5
        if home_eff_era > 5.5 and away_eff_era > 5.5: total_prob = 0.62
        elif home_eff_era < 3.0 and away_eff_era < 3.0: total_prob = 0.38
        elif home_eff_era > 5.0 or away_eff_era > 5.0: total_prob = 0.56
        over_edge = total_prob - 0.45
        ou_status = "[OK]" if over_edge > 0.02 else ("[OK]U" if (1-total_prob)-0.45 > 0.02 else "[?]")
        
        home_over_prob = 0.5 + (home_momentum.get('ops_last7', 0.720) - 0.700) * 0.8 + (away_eff_era - 4.0) * 0.05
        home_over_prob = max(0.25, min(0.85, home_over_prob))
        team_status = "[OK]" if home_over_prob > 0.55 else "[?]"
        f5_status = "[OK]" if result['probability'] - 0.45 > 0.02 else "[?]"
        
        print(f"MLB|{home_team}|{away_team}|{pick}|{odds_str}|{result['probability']:.1%}|{result['edge']:+.1%}|{result['confidence_level']}|{ml_status}|{rl_status}|{ou_status}|{team_status}|{f5_status}")
        print(f"DATA|{home_team}|{away_team}|{home_p_name}|{home_p_data.get('era','?')}|{home_p_data.get('whip','?')}|{home_p_data.get('k9','?')}|{away_p_name}|{away_p_data.get('era','?')}|{away_p_data.get('whip','?')}|{away_p_data.get('k9','?')}|{row.get('stadium','Unknown')}|{row.get('is_divisional',False)}|{home_win}|{away_win}|{home_bullpen.get('era','?')}|{away_bullpen.get('era','?')}|{home_bullpen.get('fatigue','NORMAL')}|{away_bullpen.get('fatigue','NORMAL')}|{home_momentum.get('ops_last7','?')}|{away_momentum.get('ops_last7','?')}|{home_momentum.get('run_diff_last10','?')}|{away_momentum.get('run_diff_last10','?')}|{home_inj_str}|{away_inj_str}")
        
        if intel['approved']:
            result['sport'] = 'MLB'; result['match'] = row['match']
            result['home_team'] = home_team; result['away_team'] = away_team
            result['pick'] = pick; result['bet_type'] = 'Moneyline'
            result['odds_american'] = h2h_home if pick == home_team else h2h_away
            all_setups.append(result)
            log_file = 'data/betting_log.csv'
            if os.path.exists(log_file):
                try:
                    existing = pd.read_csv(log_file)
                    if len(existing[(existing['date'] == datetime.now().strftime('%Y-%m-%d')) & (existing['match'] == result.get('match', '')) & (existing['bet_type'] == 'Moneyline')]) == 0:
                        save_bet('MLB', result.get('match', ''), 'Moneyline', pick, h2h_home if pick == home_team else h2h_away, result.get('probability', 0), result.get('edge', 0), result.get('volatility', 0), result.get('confidence_score', 0))
                except: pass

print(f"SUMMARY|{len(all_setups)}")