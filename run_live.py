from quant_engine import QuantEngine
from live_fetcher import (
    get_live_nba_games, get_live_soccer_matches,
    get_live_odds
)
from mlb_data_fetcher import (
    get_today_mlb_games, get_pitcher_stats, get_pitcher_last3,
    get_pitcher_vs_team, get_pitcher_home_away_split,
    get_bullpen_data, get_team_momentum
)
from mlb_engine import MLBEngine
from market_intelligence import MarketIntelligence
from sharp_edge_engine import SharpEdgeEngine
from market_exploiter import MarketExploiter
from odds_fetcher import get_fanduel_odds
import pandas as pd
from datetime import datetime

print("=" * 60)
print("🏀⚾⚽ SPORTS QUANT ENGINE V7 - ANÁLISIS HOY")
print("=" * 60)
print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print(f"🎯 NBA: Prob≥0.53 | Vol≤0.65 | Edge≥0.03")
print(f"🎯 MLB: Edge>0.02 | Prob≥0.52 | Vol≤0.68 | Context≥0.45")
print("=" * 60)

quant = QuantEngine()
mlb_engine = MLBEngine()
market_intel = MarketIntelligence()
sharp = SharpEdgeEngine()
exploiter = MarketExploiter()
all_setups = []

# ============================================
# NBA HOY
# ============================================
print("\n🏀 NBA HOY...")
nba_games = get_live_nba_games()
nba_games = nba_games[nba_games['status'].isin(['Scheduled', 'Pre-Game'])] if len(nba_games) > 0 else nba_games

if len(nba_games) > 0:
    nba_odds = get_live_odds('basketball_nba')
    if len(nba_odds) > 0:
        nba_games = nba_games.merge(nba_odds[['match', 'odds_home']], on='match', how='left')
    nba_games['odds_home'] = nba_games.get('odds_home', 2.0).fillna(2.0)
    
    fanduel_nba = get_fanduel_odds('basketball_nba')
    if len(fanduel_nba) > 0:
        nba_games = nba_games.merge(fanduel_nba, on='match', how='left', suffixes=('', '_fd'))
    
    print(f"   {len(nba_games)} partidos\n")
    
    for _, row in nba_games.iterrows():
        home_win = row['home_win_pct']
        away_win = row['away_win_pct']
        is_playoff = row.get('is_playoff', False)
        momentum = 0.65 if is_playoff else 0.58
        
        home_score = quant.nba_team_score({
            'win_pct': home_win, 'net_rating': 0.48 + (home_win - 0.5) * 0.5,
            'injury_impact': 0.70, 'rest_days': 0.55,
            'momentum': momentum, 'rebounding': home_win - 0.03, 'h2h': 0.50
        })
        away_score = quant.nba_team_score({
            'win_pct': away_win, 'net_rating': 0.48 + (away_win - 0.5) * 0.5,
            'injury_impact': 0.65, 'rest_days': 0.48,
            'momentum': momentum - 0.05, 'rebounding': away_win - 0.08, 'h2h': 0.45
        })
        
        match_data = {
            'match': row['match'], 'home_team': row['home_team'], 'away_team': row['away_team'],
            'home_team_score': home_score, 'away_team_score': away_score,
            'sport': 'nba',
            'rivalry_factor': 0.25, 'team_inconsistency': 0.2,
            'injury_uncertainty': 0.2, 'schedule_fatigue': 0.15,
            'odds': row['odds_home']
        }
        
        result = quant.evaluate_match(match_data, 'nba')
        pick = row['home_team'] if home_score >= away_score else row['away_team']
        result['pick'] = pick
        result['sport'] = '🏀 NBA'
        
        fav = row.get('favorite', '')
        dog = row.get('underdog', '')
        
        print(f"   🏀 {row['home_team']} vs {row['away_team']}")
        if fav:
            print(f"      💰 FanDuel: {fav} ({row.get('favorite_odds_american', '')}) FAV | {dog} ({row.get('underdog_odds_american', '')}) DOG")
        print(f"      📊 Prob: {result['probability']} | Edge: {result['edge']} | Vol: {result['volatility']} | {result['confidence_level']}")
        print(f"      🎯 Modelo: {pick}")
        
        if result['approved']:
            all_setups.append(result)
            print(f"      ✅ SETUP APROBADO")
        else:
            print(f"      ❌ No pasa filtros")
        print()
else:
    print("   Sin partidos programados\n")

# ============================================
# MLB HOY - V5 + V6 + V7 + FANDUEL
# ============================================
print("⚾ MLB HOY...")
mlb_games = get_today_mlb_games()

if len(mlb_games) > 0:
    mlb_odds = get_live_odds('baseball_mlb')
    if len(mlb_odds) > 0:
        mlb_games = mlb_games.merge(mlb_odds[['match', 'odds_home']], on='match', how='left')
    mlb_games['odds_home'] = mlb_games.get('odds_home', 2.0).fillna(2.0)
    
    fanduel_mlb = get_fanduel_odds('baseball_mlb')
    if len(fanduel_mlb) > 0:
        mlb_games = mlb_games.merge(fanduel_mlb, on='match', how='left', suffixes=('', '_fd'))
    
    print(f"   {len(mlb_games)} partidos\n")
    
    for _, row in mlb_games.iterrows():
        home_team = row['home_team']
        away_team = row['away_team']
        home_id = row.get('home_team_id')
        away_id = row.get('away_team_id')
        home_win = row.get('home_win_pct', 0.5)
        away_win = row.get('away_win_pct', 0.5)
        
        fav_fd = row.get('favorite', '')
        dog_fd = row.get('underdog', '')
        fav_odds_dec = row.get('favorite_odds_decimal', 2.0) or 2.0
        
        print(f"   ⚾ {home_team} vs {away_team}")
        print(f"      🏟️ {row.get('stadium', 'Unknown')} | {'Divisional' if row.get('is_divisional', False) else 'No divisional'}")
        
        if fav_fd:
            print(f"      💰 FanDuel: {fav_fd} FAV ({row.get('favorite_odds_american', '')}) | {dog_fd} DOG ({row.get('underdog_odds_american', '')})")
        
        home_p_data = get_pitcher_stats(row.get('home_pitcher_id'))
        away_p_data = get_pitcher_stats(row.get('away_pitcher_id'))
        home_p_name = row.get('home_pitcher_name', 'TBD')
        away_p_name = row.get('away_pitcher_name', 'TBD')
        
        if home_p_name == 'TBD' and not home_p_data:
            print(f"      ⚠️ {home_team} pitcher: TBD - JUEGO NO EVALUADO\n")
            continue
        if away_p_name == 'TBD' and not away_p_data:
            print(f"      ⚠️ {away_team} pitcher: TBD - JUEGO NO EVALUADO\n")
            continue
        
        if not home_p_data:
            home_p_data = mlb_engine.smart_pitcher_defaults(home_p_name)
            print(f"      ⚠️ {home_p_name}: sin datos API")
        else:
            print(f"      ✅ {home_p_name}: {home_p_data['era']} ERA | {home_p_data['whip']} WHIP | {home_p_data['k9']} K9")
        
        if not away_p_data:
            away_p_data = mlb_engine.smart_pitcher_defaults(away_p_name)
            print(f"      ⚠️ {away_p_name}: sin datos API")
        else:
            print(f"      ✅ {away_p_name}: {away_p_data['era']} ERA | {away_p_data['whip']} WHIP | {away_p_data['k9']} K9")
        
        home_last3 = get_pitcher_last3(row.get('home_pitcher_id'))
        away_last3 = get_pitcher_last3(row.get('away_pitcher_id'))
        if home_last3:
            last3_era = sum(g['era'] for g in home_last3) / len(home_last3)
            home_p_data['last3_era'] = round(last3_era, 2)
            print(f"      📊 {home_p_name} Last 3: {last3_era} ERA")
        if away_last3:
            last3_era = sum(g['era'] for g in away_last3) / len(away_last3)
            away_p_data['last3_era'] = round(last3_era, 2)
            print(f"      📊 {away_p_name} Last 3: {last3_era} ERA")
        
        home_vs_away = get_pitcher_vs_team(row.get('home_pitcher_id'), away_id)
        away_vs_home = get_pitcher_vs_team(row.get('away_pitcher_id'), home_id)
        if home_vs_away and home_vs_away.get('plate_appearances', 0) > 0:
            print(f"      📜 {home_p_name} vs {away_team}: {home_vs_away['avg']} AVG | {home_vs_away['ops']} OPS | {home_vs_away['plate_appearances']} PA")
        if away_vs_home and away_vs_home.get('plate_appearances', 0) > 0:
            print(f"      📜 {away_p_name} vs {home_team}: {away_vs_home['avg']} AVG | {away_vs_home['ops']} OPS | {away_vs_home['plate_appearances']} PA")
        
        home_bullpen = get_bullpen_data(home_id)
        away_bullpen = get_bullpen_data(away_id)
        home_momentum = get_team_momentum(home_id)
        away_momentum = get_team_momentum(away_id)
        
        if home_bullpen.get('fatigue') in ['HIGH', 'CRITICAL']:
            print(f"      ⚠️ {home_team} bullpen FATIGADO ({home_bullpen.get('last3_innings')} IP)")
        if away_bullpen.get('fatigue') in ['HIGH', 'CRITICAL']:
            print(f"      ⚠️ {away_team} bullpen FATIGADO ({away_bullpen.get('last3_innings')} IP)")
        
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
        
        print(f"      📊 Prob: {result['probability']} | Edge: {result['edge']} | Vol: {result['volatility']}")
        print(f"      🎯 Pick: {result['pick']} | Confianza: {result['confidence_level']} ({result['confidence_score']})")
        
        intel = market_intel.final_decision(game_data, result)
        
        # V6 SHARP EDGE
        sharp_result = sharp.classify_edge(game_data, result, intel)
        
        if sharp_result['edge_type'] in ['SHARP EDGE', 'SAFE EDGE', 'VALUE EDGE']:
            if sharp_result['false_favorite']['flags']:
                for flag in sharp_result['false_favorite']['flags']:
                    print(f"      🚩 {flag}")
            if sharp_result['underdog_value']['flags']:
                for flag in sharp_result['underdog_value']['flags']:
                    print(f"      💎 {flag}")
            if sharp_result['context_shifts']:
                for shift in sharp_result['context_shifts']:
                    print(f"      🔄 {shift}")
        
        # V7 MARKET EXPLOITER
        v7 = exploiter.full_analysis(game_data, result, intel)
        
        mv = v7['market_vs']
        print(f"      📊 Market: {mv['market_prob']:.1%} | Model: {mv['model_prob']:.1%} | Gap: {mv['discrepancy']:+.1%} [{mv['status']}]")
        
        pb = v7['public_bias']
        if pb['level'] in ['HIGH', 'MEDIUM']:
            print(f"      👥 Public Bias: {pb['level']} ({pb['score']:.0%})")
            for r in pb['reasons'][:2]:
                print(f"         - {r}")
        
        ud = v7['underdog_profile']
        if ud['level'] in ['STRONG', 'MODERATE']:
            print(f"      🐶 Underdog: {ud['underdog']} | Score: {ud['score']}/100 ({ud['level']})")
            for f in ud['flags'][:3]:
                print(f"         - {f}")
        
        for pf in v7['pitcher_flags']['home'] + v7['pitcher_flags']['away']:
            print(f"      🔍 {pf}")
        for n in v7['narratives'][:2]:
            print(f"      📖 {n}")
        
        print(f"      🎯 V6: {sharp_result['edge_type']} | V7: {v7['exploitation_level']}")
        
        if intel['approved']:
            result['sport'] = '⚾ MLB'
            result['match'] = row['match']
            result['home_team'] = home_team
            result['away_team'] = away_team
            result['edge_quality'] = intel['edge_quality']
            result['context_score'] = intel['context_score']
            result['v6_edge_type'] = sharp_result['edge_type']
            result['v7_exploitation'] = v7['exploitation_level']
            all_setups.append(result)
            print(f"      ✅ SETUP APROBADO ({intel['edge_quality']} EDGE)")
            if result.get('underdog_value'):
                info = result['underdog_info']
                print(f"      💰 UNDERDOG VALUE: {info['underdog']} | Market: {info['market_prob']} | Model: {info['model_prob']}")
        else:
            print(f"      ❌ RECHAZADO: {intel['reason']}")
        print()

# ============================================
# SOCCER HOY
# ============================================
print("⚽ SOCCER HOY...")
soccer_matches = get_live_soccer_matches()

if len(soccer_matches) > 0:
    soccer_odds = get_live_odds('soccer_epl')
    for league_odds in ['soccer_spain_la_liga', 'soccer_italy_serie_a', 'soccer_uefa_champs_league']:
        extra_odds = get_live_odds(league_odds)
        if len(extra_odds) > 0:
            soccer_odds = pd.concat([soccer_odds, extra_odds])
    
    if len(soccer_odds) > 0:
        soccer_matches = soccer_matches.merge(soccer_odds[['match', 'odds_home']], on='match', how='left')
    soccer_matches['odds_home'] = soccer_matches.get('odds_home', 2.0).fillna(2.0)
    
    fanduel_soccer = get_fanduel_odds('soccer_epl')
    if len(fanduel_soccer) > 0:
        soccer_matches = soccer_matches.merge(fanduel_soccer, on='match', how='left', suffixes=('', '_fd'))
    
    print(f"   {len(soccer_matches)} partidos (ligas top)\n")
    
    for _, row in soccer_matches.iterrows():
        home_form = row.get('home_form', 0.55)
        away_form = row.get('away_form', 0.50)
        home_xg = row.get('home_xg', 1.5)
        away_xg = row.get('away_xg', 1.2)
        
        xg_total = home_xg + away_xg
        home_xg_strength = 0.45 + (home_xg / xg_total) * 0.15 if xg_total > 0 else 0.52
        away_xg_strength = 0.45 + (away_xg / xg_total) * 0.15 if xg_total > 0 else 0.48
        
        home_score = quant.soccer_team_score({
            'form': home_form, 'xg': home_xg_strength,
            'motivation': 0.62, 'injuries_impact': 0.68, 'h2h_advantage': 0.52
        })
        away_score = quant.soccer_team_score({
            'form': away_form, 'xg': away_xg_strength,
            'motivation': 0.52, 'injuries_impact': 0.62, 'h2h_advantage': 0.45
        })
        
        match_data = {
            'match': row['match'], 'home_team': row['home_team'], 'away_team': row['away_team'],
            'home_team_score': home_score, 'away_team_score': away_score,
            'sport': 'soccer', 'home_advantage': 0.58,
            'rivalry_factor': 0.3, 'team_inconsistency': 0.25,
            'injury_uncertainty': 0.2, 'schedule_fatigue': 0.15,
            'odds': row['odds_home']
        }
        
        result = quant.evaluate_match(match_data, 'soccer')
        pick = row['home_team'] if home_score >= away_score else row['away_team']
        result['pick'] = pick
        result['league'] = row.get('league', '')
        result['sport'] = '⚽ SOCCER'
        
        fav = row.get('favorite', '')
        dog = row.get('underdog', '')
        
        print(f"   ⚽ {row['home_team']} vs {row['away_team']} ({row.get('league', '')})")
        if fav:
            print(f"      💰 FanDuel: {fav} FAV ({row.get('favorite_odds_american', '')}) | {dog} DOG ({row.get('underdog_odds_american', '')})")
        print(f"      📊 Prob: {result['probability']} | Edge: {result['edge']} | Vol: {result['volatility']} | {result['confidence_level']}")
        print(f"      🎯 Modelo: {pick}")
        
        if result['approved']:
            all_setups.append(result)
            print(f"      ✅ SETUP APROBADO")
        else:
            print(f"      ❌ No pasa filtros")
        print()

# ============================================
# RESUMEN
# ============================================
print("=" * 60)
print(f"📊 RESULTADO HOY ({datetime.now().strftime('%d/%m/%Y')})")
print("=" * 60)

if len(all_setups) == 0:
    print("\n🔴 0 SETUPS A+ hoy")
    print('🧠 "No trade" es posición válida')
else:
    all_setups.sort(key=lambda x: x.get('edge', 0), reverse=True)
    
    nba_count = len([s for s in all_setups if 'NBA' in s.get('sport', '')])
    mlb_count = len([s for s in all_setups if 'MLB' in s.get('sport', '')])
    soccer_count = len([s for s in all_setups if 'SOCCER' in s.get('sport', '')])
    
    print(f"\n🔥 {len(all_setups)} SETUPS: 🏀{nba_count} ⚾{mlb_count} ⚽{soccer_count}\n")
    
    for i, s in enumerate(all_setups[:5], 1):
        edge_quality = f" [{s.get('edge_quality', '')}]" if s.get('edge_quality') else ''
        v6_edge = f" [{s.get('v6_edge_type', '')}]" if s.get('v6_edge_type') else ''
        v7_edge = f" [{s.get('v7_exploitation', '')}]" if s.get('v7_exploitation') else ''
        print(f"  {i}. {s['sport']}{edge_quality}{v6_edge}{v7_edge} | {s['home_team']} vs {s['away_team']}")
        print(f"     👉 GANA: {s['pick']}")
        print(f"     📊 Prob: {s['probability']} | Edge: {s['edge']} | Vol: {s['volatility']} | {s.get('confidence_level', '')}")
        if s.get('underdog_value'):
            print(f"     💰 UNDERDOG VALUE DETECTADO")
        print()

print("=" * 60)
print("✅ Análisis completado - V7 Market Exploiter |", datetime.now().strftime('%H:%M'))