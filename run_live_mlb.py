"""
MLB LIVE - VERSIÓN LIMPIA
Solo features que funcionan: Pitcher, Bullpen, Injuries, Park, Weather, Travel, Defense, Rest
Edge > 8% | Prob > 50%
"""
from mlb_data_fetcher import (
    get_today_mlb_games, get_pitcher_stats, get_pitcher_last3,
    get_pitcher_vs_team, get_bullpen_data, get_team_momentum
)
from mlb_engine import MLBEngine
from odds_fetcher import get_fanduel_odds_full
import pandas as pd
import os
import csv
import requests
from datetime import datetime

# NO importar: market_sentiment, umpire_engine, historical_similar_spots, statcast_engine

try:
    from mlb_injury_fetcher import get_out_players_mlb
except:
    def get_out_players_mlb(x):
        return []

# ============ DISCORD WEBHOOK ============
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1513210088201125982/RT6JQxf3MLzqAFg8CwbPO4FYFLSbrwlAHtklsWVCqCHhlJ1eKsQ-JmHOIxS49UZt0Ggr"

def enviar_a_discord(mensaje):
    """Envía un mensaje al canal de Discord usando el webhook."""
    try:
        data = {"content": mensaje}
        requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=5)
    except Exception as e:
        print(f"⚠️ No se pudo enviar a Discord: {e}")

print("MLB|HOME|AWAY|PICK|ODDS|PROB|EDGE|CONF|ML|RL|OU|TEAM|F5")

mlb_engine = MLBEngine()

all_setups = []
mlb_games = get_today_mlb_games()

if len(mlb_games) > 0:
    # LIVE ODDS
    fanduel_mlb = get_fanduel_odds_full('baseball_mlb')
    
    if len(fanduel_mlb) > 0:
        odds_dict = {}
        for _, odd_row in fanduel_mlb.iterrows():
            odds_dict[odd_row['match']] = odd_row
        
        for idx, game_row in mlb_games.iterrows():
            match_name = game_row['match']
            if match_name in odds_dict:
                odd_row = odds_dict[match_name]
                mlb_games.at[idx, 'h2h_home'] = odd_row.get('h2h_home')
                mlb_games.at[idx, 'h2h_away'] = odd_row.get('h2h_away')
                mlb_games.at[idx, 'favorite'] = odd_row.get('favorite')
                mlb_games.at[idx, 'underdog'] = odd_row.get('underdog')
                mlb_games.at[idx, 'favorite_odds_decimal'] = odd_row.get('favorite_odds_decimal')
                mlb_games.at[idx, 'underdog_odds_decimal'] = odd_row.get('underdog_odds_decimal')
                mlb_games.at[idx, 'total_point'] = odd_row.get('total_point')
                mlb_games.at[idx, 'spread_home'] = odd_row.get('spread_home')
                mlb_games.at[idx, 'spread_away'] = odd_row.get('spread_away')
                mlb_games.at[idx, 'spread_point'] = odd_row.get('spread_point')
    
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
        
        # OBTENER ODDS
        if pd.notna(row.get('favorite_odds_decimal')) and row.get('favorite_odds_decimal') > 0:
            fav_odds_dec = row.get('favorite_odds_decimal')
        elif pd.notna(row.get('underdog_odds_decimal')) and row.get('underdog_odds_decimal') > 0:
            fav_odds_dec = row.get('underdog_odds_decimal')
        elif h2h_home < 0:
            fav_odds_dec = 1 + 100/abs(h2h_home)
        elif h2h_away < 0:
            fav_odds_dec = 1 + 100/abs(h2h_away)
        elif h2h_home > 0:
            fav_odds_dec = 1 + h2h_home/100
        elif h2h_away > 0:
            fav_odds_dec = 1 + h2h_away/100
        else:
            fav_odds_dec = 2.0
        
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
        home_vs_away = get_pitcher_vs_team(row.get('home_pitcher_id'), away_id)
        away_vs_home = get_pitcher_vs_team(row.get('away_pitcher_id'), home_id)
        
        # INJURIAS (simplificado)
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
            'odds': fav_odds_dec,
            'home_injuries': home_injuries,
            'away_injuries': away_injuries
        }
        
        # MODELO BASE
        result = mlb_engine.evaluate_mlb_game(game_data, fav_odds_dec)
        
        # INJURIAS (sin estrellas, simplificado)
        try:
            home_outs = len([i for i in home_injuries if i.get('status') == 'OUT'])
            away_outs = len([i for i in away_injuries if i.get('status') == 'OUT'])
            injury_penalty = (away_outs - home_outs) * 0.005
            result['probability'] = min(0.85, max(0.15, result['probability'] + injury_penalty))
        except: pass
        
        # WEATHER
        try:
            from weather_engine import get_weather_for_match, weather_impact
            weather = get_weather_for_match(home_team, away_team)
            if weather:
                wi = weather_impact(weather)
                result['probability'] = min(0.85, max(0.15, result['probability'] + wi['home_boost']))
        except: pass
        
        # TRAVEL
        try:
            from travel_engine import get_travel_distance, travel_impact
            stadium = row.get('stadium', '')
            if stadium:
                hb, _ = travel_impact(get_travel_distance(stadium, stadium))
                result['probability'] = min(0.85, max(0.15, result['probability'] + hb))
        except: pass
        
        # DEFENSE
        try:
            from defense_engine import defense_advantage
            result['probability'] = min(0.85, max(0.15, result['probability'] + defense_advantage(home_team, away_team) * 0.5))
        except: pass
        
        # REST
        try:
            from rest_engine import get_team_rest_days, rest_advantage
            result['probability'] = min(0.85, max(0.15, result['probability'] + rest_advantage(get_team_rest_days(home_team), get_team_rest_days(away_team))))
        except: pass
        
        # PARK FACTOR
        try:
            park = mlb_engine.park_adjustment(row.get('stadium', ''))
            park_runs_factor = park.get('runs', 1.0)
            result['probability'] = min(0.85, max(0.15, result['probability'] + (park_runs_factor - 1.0) * 0.05))
        except: pass
        
        # RECALCULAR EDGE
        market_prob = 1 / fav_odds_dec if fav_odds_dec > 1 else 0.5
        result['edge'] = result['probability'] - market_prob
        
        # ============ CONFIGURACIÓN OPTIMIZADA (Edge > 8%) ============
        if result['edge'] > 0.08 and result['probability'] >= 0.50:
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
        
        # ESTADOS (simplificados)
        ml_status = "[OK]" if result['edge'] > 0.08 else "[X]"
        rl_status = "[X]"
        ou_status = "[?]"
        team_status = "[?]"
        f5_status = "[?]"
        
        # OUTPUT
        print(f"MLB|{home_team}|{away_team}|{pick_label}|{odds_str}|{result['probability']:.1%}|{result['edge']:+.1%}|{result['confidence_level']}|{ml_status}|{rl_status}|{ou_status}|{team_status}|{f5_status}")
        print(f"DATA|{home_team}|{away_team}|{home_p_name}|{home_p_data.get('era','?')}|{home_p_data.get('whip','?')}|{home_p_data.get('k9','?')}|{away_p_name}|{away_p_data.get('era','?')}|{away_p_data.get('whip','?')}|{away_p_data.get('k9','?')}|{row.get('stadium','Unknown')}|{row.get('is_divisional',False)}|{home_win}|{away_win}|{home_bullpen.get('era','?')}|{away_bullpen.get('era','?')}|{home_bullpen.get('fatigue','NORMAL')}|{away_bullpen.get('fatigue','NORMAL')}|0.720|0.720|0|0|{home_inj_str}|{away_inj_str}")
        
        # GUARDAR EN CSV LOCAL
        if pick != "NO PICK":
            csv_file = 'data/picks_tracker.csv'
            os.makedirs('data', exist_ok=True)
            today = datetime.now().strftime('%Y-%m-%d')
            match_name = f"{home_team} vs {away_team}"
            
            existing = []
            if os.path.exists(csv_file):
                with open(csv_file, 'r') as f:
                    reader = csv.reader(f)
                    existing = list(reader)
            
            existe = False
            for row_csv in existing:
                if len(row_csv) >= 2 and row_csv[0] == today and row_csv[1] == match_name:
                    existe = True
                    break
            
            if not existe:
                with open(csv_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    if len(existing) == 0:
                        writer.writerow(['date', 'match', 'pick', 'edge', 'result'])
                    writer.writerow([today, match_name, pick, result['edge'], 'PENDING'])
                print(f"💾 GUARDADO: {pick}")
            
            # ============ ENVIAR A DISCORD ============
            mensaje_discord = f"""🔥 **NUEVO PICK MLB** 🔥

**{pick}**
📊 **Probabilidad:** {result['probability']:.1%}
📈 **Edge:** {result['edge']:+.1%}
💰 **Odds:** {odds_str}
⭐ **Confianza:** {result['confidence_level']}

🏟️ **Partido:** {home_team} vs {away_team}
📅 **Fecha:** {today}"""
            enviar_a_discord(mensaje_discord)
        
        all_setups.append(result)

print(f"SUMMARY|{len(all_setups)}")