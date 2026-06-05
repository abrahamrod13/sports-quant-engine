from quant_engine import QuantEngine
from mlb_data_fetcher import (
    get_today_mlb_games, get_pitcher_stats, get_pitcher_last3,
    get_pitcher_vs_team, get_pitcher_home_away_split,
    get_bullpen_data, get_team_momentum
)
from mlb_engine import MLBEngine
from market_intelligence import MarketIntelligence
from odds_fetcher import get_fanduel_odds_full
from betting_logger import save_bet
import pandas as pd
import os
from datetime import datetime

# ============ NUEVOS MÓDULOS ============
from market_sentiment import MarketSentiment
from umpire_engine import UmpireEngine
from historical_similar_spots import HistoricalSimilarSpots
# ========================================

try:
    from mlb_injury_fetcher import get_out_players_mlb
except:
    def get_out_players_mlb(x):
        return []

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

# ============ INICIALIZAR NUEVOS MÓDULOS ============
market_sentiment = MarketSentiment()
umpire_engine = UmpireEngine()
historical_spots = HistoricalSimilarSpots()
# ====================================================

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
        fav_odds_dec = row.get('favorite_odds_decimal', 2.0) or 2.0
        
        # Odds para RLM
        opening_line = row.get('spread_open', 0)
        closing_line = row.get('spread_close', 0)
        
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
        
        # ============ STREAKS para Market Sentiment ============
        home_streak = home_momentum.get('streak', 0)
        away_streak = away_momentum.get('streak', 0)
        
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
            'hr_heavy_teams': home_win > 0.58 or away_win > 0.58, 'wind_outward': False, 'odds': fav_odds_dec,
            # Para Market Sentiment
            'home_streak': home_streak, 'away_streak': away_streak,
            'opening_odds': opening_line, 'closing_odds': closing_line
        }
        
        # ============ PASO 1: MODELO BASE ============
        result = mlb_engine.evaluate_mlb_game(game_data, fav_odds_dec)
        
        # ============ PASO 2: STATCAST ============
        try:
            if statcast_engine:
                hp = statcast_engine.get_team_power(home_team)
                ap = statcast_engine.get_team_power(away_team)
                if hp and ap:
                    result['probability'] = min(0.85, max(0.15, result['probability'] + ((hp['power_score']-ap['power_score'])/10)*0.015))
        except: pass
        
        # ============ PASO 3: SERIES MOMENTUM ============
        try:
            from series_momentum_engine import get_series_momentum
            sm = get_series_momentum(home_team, away_team)
            if sm:
                mb = 0
                hw = int(sm['home_last5'].split('-')[0])
                aw = int(sm['away_last5'].split('-')[0])
                if hw >= 4 and aw <= 1: mb += 0.03
                elif hw >= 3 and aw <= 2: mb += 0.015
                if sm['home_run_diff_last5'] > 15: mb += 0.02
                if sm['h2h_games'] >= 2 and int(sm['h2h_record'].split('-')[0]) == sm['h2h_games']: mb += 0.02
                result['probability'] = min(0.85, max(0.15, result['probability'] + mb))
        except: pass
        
        # ============ PASO 4: INJURIAS MEJORADAS ============
        try:
            stars = {
                'Aaron Judge': 0.05, 'Juan Soto': 0.05, 'Mike Trout': 0.05,
                'Shohei Ohtani': 0.06, 'Mookie Betts': 0.04, 'Freddie Freeman': 0.04,
                'Ronald Acuna': 0.04, 'Fernando Tatis': 0.04, 'Bryce Harper': 0.04,
                'Trea Turner': 0.03, 'Rafael Devers': 0.03, 'Jose Ramirez': 0.03,
                'Corey Seager': 0.03, 'Yordan Alvarez': 0.04, 'Vladimir Guerrero': 0.04,
                'Manny Machado': 0.03, 'Bo Bichette': 0.03, 'Julio Rodriguez': 0.03,
                'Pete Alonso': 0.03, 'Kyle Tucker': 0.03, 'Corbin Carroll': 0.03
            }
            injury_penalty = 0
            for inj in home_injuries:
                player_name = inj.get('player', '')
                for star, penalty in stars.items():
                    if star.lower() in player_name.lower():
                        injury_penalty -= penalty
                        break
            for inj in away_injuries:
                player_name = inj.get('player', '')
                for star, penalty in stars.items():
                    if star.lower() in player_name.lower():
                        injury_penalty += penalty
                        break
            home_outs = len([i for i in home_injuries if i.get('status') == 'OUT'])
            away_outs = len([i for i in away_injuries if i.get('status') == 'OUT'])
            injury_penalty -= home_outs * 0.005
            injury_penalty += away_outs * 0.005
            result['probability'] = min(0.85, max(0.15, result['probability'] + injury_penalty))
        except: pass
        
        # ============ PASO 5: LINEUPS ============
        try:
            from lineup_fetcher import get_lineups_for_match, lineup_impact
            lineups = get_lineups_for_match(home_team, away_team)
            if lineups.get('has_lineups'):
                result['probability'] = min(0.85, max(0.15, result['probability'] + lineup_impact(lineups, home_team, away_team)))
        except: pass
        
        # ============ PASO 6: WEATHER ============
        try:
            from weather_engine import get_weather_for_match, weather_impact
            weather = get_weather_for_match(home_team, away_team)
            if weather:
                wi = weather_impact(weather)
                result['probability'] = min(0.85, max(0.15, result['probability'] + wi['home_boost']))
        except: pass
        
        # ============ PASO 7: TRAVEL ============
        try:
            from travel_engine import get_travel_distance, travel_impact
            stadium = row.get('stadium', '')
            if stadium:
                hb, _ = travel_impact(get_travel_distance(stadium, stadium))
                result['probability'] = min(0.85, max(0.15, result['probability'] + hb))
        except: pass
        
        # ============ PASO 8: STATCAST PITCH ============
        try:
            from statcast_pitch_engine import pitch_advantage
            result['probability'] = min(0.85, max(0.15, result['probability'] + pitch_advantage(home_p_name, away_p_name) * 0.5))
        except: pass
        
        # ============ PASO 9: DEFENSE ============
        try:
            from defense_engine import defense_advantage
            result['probability'] = min(0.85, max(0.15, result['probability'] + defense_advantage(home_team, away_team) * 0.5))
        except: pass
        
        # ============ PASO 10: REST ============
        try:
            from rest_engine import get_team_rest_days, rest_advantage
            result['probability'] = min(0.85, max(0.15, result['probability'] + rest_advantage(get_team_rest_days(home_team), get_team_rest_days(away_team))))
        except: pass
        
        # ============ PASO 11: BULLPEN LEVERAGE ============
        try:
            from bullpen_leverage_engine import bullpen_advantage as ba_lev
            result['probability'] = min(0.85, max(0.15, result['probability'] + ba_lev(home_team, away_team)))
        except: pass
        
        # ============ PASO 12: LINEUP SPLITS ============
        try:
            from lineup_splits_engine import lineup_split_advantage
            away_throws = away_p_data.get('throws', 'R') if away_p_data else 'R'
            result['probability'] = min(0.85, max(0.15, result['probability'] + lineup_split_advantage(home_team, away_team, away_throws)))
        except: pass
        
        # ============ PASO 13: STATCAST BAT ============
        try:
            from statcast_bat_engine import statcast_bat_advantage
            result['probability'] = min(0.85, max(0.15, result['probability'] + statcast_bat_advantage(home_team, away_team)))
        except: pass
        
        # ============ PASO 14: TEAM STATS ============
        try:
            from team_stats_engine import team_stats_advantage
            tsa, _ = team_stats_advantage(home_team, away_team)
            result['probability'] = min(0.85, max(0.15, result['probability'] + tsa))
        except: pass
        
        # ============ NUEVO PASO 15: MARKET SENTIMENT ============
        try:
            sentiment_adj = market_sentiment.market_sentiment_adjustment(game_data, result['probability'])
            result['probability'] = sentiment_adj['adjusted_probability']
            result['market_signal'] = sentiment_adj['market_signal']
            result['overreaction'] = sentiment_adj['overreaction']['level']
            result['rlm_detected'] = sentiment_adj['rlm']['rlm_detected']
        except Exception as e:
            print(f"⚠️ Market Sentiment error: {e}")
            result['market_signal'] = 'ERROR'
        
        # ============ NUEVO PASO 16: UMPIRE ENGINE ============
        total_line = row.get('total_point', 8.5)
        try:
            umpire_analysis = umpire_engine.full_umpire_analysis(game_data, result['probability'], total_line)
            result['probability'] = umpire_analysis['adjusted_prob']
            result['umpire_adjustment'] = umpire_analysis['run_impact_adjustment']
            result['umpire_ou_signal'] = umpire_analysis['over_under_signal']
            result['adjusted_total_line'] = umpire_analysis['total_line_adjusted']
        except Exception as e:
            print(f"⚠️ Umpire Engine error: {e}")
            result['adjusted_total_line'] = total_line
        
        # ============ NUEVO PASO 17: HISTORICAL SIMILAR SPOTS ============
        try:
            historical_blend = historical_spots.blend_with_model(game_data, result['probability'], model_weight=0.60)
            result['probability'] = historical_blend['blended_prob']
            result['historical_similar_games'] = historical_blend['similar_games']
            result['historical_contribution'] = historical_blend['historical_contribution']
            result['historical_prob'] = historical_blend.get('historical_prob', 0.5)
        except Exception as e:
            print(f"⚠️ Historical Spots error: {e}")
            result['historical_similar_games'] = 0
        
        # ============ RECALCULAR EDGE DESPUÉS DE TODOS LOS AJUSTES ============
        result['edge'] = result['probability'] - (1 / fav_odds_dec)
        
        # ============ MARKET INTELLIGENCE FINAL ============
        intel = market_intel.final_decision(game_data, result)
        
        # ============ DETERMINAR PICK ============
        if result['edge'] > 0.02 and result['probability'] >= 0.60 and result['confidence_level'] in ['A+', 'A']:
            pick = home_team if result['probability'] >= 0.5 else away_team
            odds_str = str(h2h_home if pick == home_team else h2h_away)
            if row.get('favorite') and pick == row.get('underdog'):
                pick_label = f"{pick} (UNDERDOG)"
            elif row.get('favorite') and pick == row.get('favorite'):
                pick_label = f"{pick} (VALUE)"
            else:
                pick_label = pick
        else:
            pick = "NO PICK"
            pick_label = "NO PICK"
            odds_str = "-"
        
        # ============ ESTADOS DE MERCADO ============
        ml_status = "[OK]" if intel['approved'] else ("[SUS]" if result['edge'] > 0.03 else "[X]")
        rl_status = "[X]"
        if result['probability'] >= 0.55:
            rl_status = "[OK]" if result['probability'] - 0.08 - 0.45 > 0.02 else "[?]"
        elif result['probability'] <= 0.45:
            rl_status = "[OK]" if (1-result['probability']) - 0.08 - 0.45 > 0.02 else "[?]"
        
        home_eff_era = home_p_data.get('last3_era', home_p_data.get('era', 4.50))
        away_eff_era = away_p_data.get('last3_era', away_p_data.get('era', 4.50))
        total_prob = 0.5
        if home_eff_era > 5.5 and away_eff_era > 5.5:
            total_prob = 0.62
        elif home_eff_era < 3.0 and away_eff_era < 3.0:
            total_prob = 0.38
        elif home_eff_era > 5.0 or away_eff_era > 5.0:
            total_prob = 0.56
        ou_status = "[OK]" if total_prob - 0.45 > 0.02 else ("[OK]U" if (1-total_prob)-0.45 > 0.02 else "[?]")
        home_over_prob = 0.5 + (home_momentum.get('ops_last7', 0.720) - 0.700) * 0.8 + (away_eff_era - 4.0) * 0.05
        team_status = "[OK]" if max(0.25, min(0.85, home_over_prob)) > 0.55 else "[?]"
        f5_status = "[OK]" if result['probability'] - 0.45 > 0.02 else "[?]"
        
        # ============ OUTPUT PRINCIPAL ============
        print(f"MLB|{home_team}|{away_team}|{pick_label}|{odds_str}|{result['probability']:.1%}|{result['edge']:+.1%}|{result['confidence_level']}|{ml_status}|{rl_status}|{ou_status}|{team_status}|{f5_status}")
        
        # ============ OUTPUT DATA COMPLETO CON NUEVAS MÉTRICAS ============
        print(f"DATA|{home_team}|{away_team}|{home_p_name}|{home_p_data.get('era','?')}|{home_p_data.get('whip','?')}|{home_p_data.get('k9','?')}|{away_p_name}|{away_p_data.get('era','?')}|{away_p_data.get('whip','?')}|{away_p_data.get('k9','?')}|{row.get('stadium','Unknown')}|{row.get('is_divisional',False)}|{home_win}|{away_win}|{home_bullpen.get('era','?')}|{away_bullpen.get('era','?')}|{home_bullpen.get('fatigue','NORMAL')}|{away_bullpen.get('fatigue','NORMAL')}|{home_momentum.get('ops_last7','?')}|{away_momentum.get('ops_last7','?')}|{home_momentum.get('run_diff_last10','?')}|{away_momentum.get('run_diff_last10','?')}|{home_inj_str}|{away_inj_str}")
        
        # ============ OUTPUT NUEVAS MÉTRICAS ============
        print(f"ADVANCED|{result.get('market_signal', 'N/A')}|{result.get('overreaction', 'N/A')}|{result.get('rlm_detected', False)}|{result.get('umpire_ou_signal', 'NEUTRAL')}|{result.get('adjusted_total_line', total_line)}|{result.get('historical_similar_games', 0)}|{result.get('historical_contribution', 0):.1%}")
        
        # ============ GUARDAR BET SI APROBADO ============
        if intel['approved']:
            result['sport'] = 'MLB'
            result['match'] = row['match']
            result['home_team'] = home_team
            result['away_team'] = away_team
            result['pick'] = pick
            result['bet_type'] = 'Moneyline'
            result['odds_american'] = h2h_home if pick == home_team else h2h_away
            all_setups.append(result)
            try:
                log_file = 'data/betting_log.csv'
                if os.path.exists(log_file):
                    existing = pd.read_csv(log_file)
                    if len(existing[(existing['date'] == datetime.now().strftime('%Y-%m-%d')) & (existing['match'] == result.get('match', ''))]) == 0:
                        save_bet('MLB', result.get('match', ''), 'Moneyline', pick, 
                                h2h_home if pick == home_team else h2h_away, 
                                result.get('probability', 0), result.get('edge', 0), 
                                result.get('volatility', 0), result.get('confidence_score', 0))
            except:
                pass

print(f"SUMMARY|{len(all_setups)}")