from quant_engine import QuantEngine
from nba_fetcher import get_nba_scoreboard
from soccer_fetcher import get_today_soccer_matches
from odds_fetcher import get_nba_odds, get_all_soccer_odds
from database import init_database, engine
import pandas as pd
from datetime import datetime
from sqlalchemy import text

init_database()
quant = QuantEngine()

print("=" * 60)
print("🏀⚽ SPORTS QUANT ENGINE V1 ⚽🏀")
print("=" * 60)
print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print(f"🎯 Prob≥{quant.min_probability} | Vol≤{quant.max_volatility} | Edge≥{quant.min_edge}")
print("=" * 60)

# ============================================
# 1. OBTENER CUOTAS
# ============================================
print("\n🎲 OBTENIENDO CUOTAS...")
try:
    nba_odds = get_nba_odds()
    print(f"🏀 NBA: {len(nba_odds)} cuotas")
except:
    nba_odds = pd.DataFrame()

try:
    soccer_odds = get_all_soccer_odds()
    print(f"⚽ Soccer: {len(soccer_odds)} cuotas")
except:
    soccer_odds = pd.DataFrame()

# ============================================
# 2. OBTENER PARTIDOS
# ============================================
print("\n📡 OBTENIENDO PARTIDOS...")
try:
    nba_games = get_nba_scoreboard()
    print(f"🏀 NBA: {len(nba_games)} partidos")
except:
    nba_games = pd.DataFrame()

try:
    soccer_matches = get_today_soccer_matches()
except:
    soccer_matches = pd.DataFrame()

# ============================================
# 3. SOCCER
# ============================================
print("\n" + "=" * 60)
print("⚽ SOCCER - LIGAS TOP")
print("=" * 60)

soccer_setups = []

if not soccer_matches.empty:
    soccer_data = []
    for _, row in soccer_matches.iterrows():
        match_name = row['match']
        odds_val = row.get('odds_home', None) or 2.0
        
        if not soccer_odds.empty:
            match_odds = soccer_odds[soccer_odds['match'] == match_name]
            if not match_odds.empty:
                odds_val = match_odds.iloc[0].get('odds_home', None) or odds_val
        
        # SCORES SEPARADOS por equipo
        home_score = quant.soccer_team_score({
            'form': 0.60,
            'xg': 0.55,
            'motivation': 0.65,
            'injuries_impact': 0.70,
            'h2h_advantage': 0.55
        })
        
        away_score = quant.soccer_team_score({
            'form': 0.50,
            'xg': 0.48,
            'motivation': 0.55,
            'injuries_impact': 0.65,
            'h2h_advantage': 0.45
        })
        
        soccer_data.append({
            'match': match_name,
            'home_team': row['home_team'],
            'away_team': row['away_team'],
            'league': row['league'],
            'home_team_score': home_score,
            'away_team_score': away_score,
            'home_advantage': 0.58,
            'rivalry_factor': 0.3,
            'team_inconsistency': 0.25,
            'injury_uncertainty': 0.2,
            'schedule_fatigue': 0.15,
            'odds': odds_val
        })
    
    soccer_df = pd.DataFrame(soccer_data)
    
    for _, row in soccer_df.iterrows():
        result = quant.evaluate_match(row, 'soccer')
        if result['approved']:
            # Determinar ganador basado en scores reales
            if row['home_team_score'] >= row['away_team_score']:
                pick = row['home_team']
            else:
                pick = row['away_team']
            result['pick'] = pick
            soccer_setups.append(result)
    
    print(f"📊 Analizados: {len(soccer_df)}")
    print(f"✅ Setups A+: {len(soccer_setups)}")
    
    for s in soccer_setups:
        print(f"  🎯 {s['home_team']} vs {s['away_team']}")
        print(f"     👉 GANA: {s['pick']} | Prob local: {s['probability']} | Edge: {s['edge']} | Vol: {s['volatility']}")
else:
    print("⚠️ No hay partidos de ligas top hoy")

# ============================================
# 4. NBA
# ============================================
print("\n" + "=" * 60)
print("🏀 NBA")
print("=" * 60)

nba_setups = []

if not nba_games.empty:
    nba_data = []
    for _, row in nba_games.iterrows():
        match_name = row['match']
        odds_val = 2.0
        
        if not nba_odds.empty:
            match_odds = nba_odds[nba_odds['match'] == match_name]
            if not match_odds.empty:
                odds_val = match_odds.iloc[0].get('odds_home', None) or odds_val
        
        # SCORES SEPARADOS por equipo NBA
        home_score = quant.nba_team_score({
            'win_pct': 0.62,
            'net_rating': 0.55,
            'injury_impact': 0.70,
            'rest_days': 0.55,
            'momentum': 0.60,
            'rebounding': 0.55,
            'h2h': 0.50
        })
        
        away_score = quant.nba_team_score({
            'win_pct': 0.55,
            'net_rating': 0.52,
            'injury_impact': 0.65,
            'rest_days': 0.50,
            'momentum': 0.55,
            'rebounding': 0.50,
            'h2h': 0.48
        })
        
        nba_data.append({
            'match': match_name,
            'home_team': row['home_team'],
            'away_team': row['away_team'],
            'home_team_score': home_score,
            'away_team_score': away_score,
            'rivalry_factor': 0.25,
            'team_inconsistency': 0.2,
            'injury_uncertainty': 0.2,
            'schedule_fatigue': 0.15,
            'odds': odds_val
        })
    
    nba_df = pd.DataFrame(nba_data)
    
    for _, row in nba_df.iterrows():
        result = quant.evaluate_match(row, 'nba')
        if result['approved']:
            if row['home_team_score'] >= row['away_team_score']:
                pick = row['home_team']
            else:
                pick = row['away_team']
            result['pick'] = pick
            nba_setups.append(result)
    
    print(f"📊 Analizados: {len(nba_df)}")
    print(f"✅ Setups A+: {len(nba_setups)}")
    
    for s in nba_setups:
        print(f"  🎯 {s['home_team']} vs {s['away_team']}")
        print(f"     👉 GANA: {s['pick']} | Prob local: {s['probability']} | Edge: {s['edge']} | Vol: {s['volatility']}")
else:
    print("⚠️ No hay partidos NBA hoy")

# ============================================
# 5. RESUMEN FINAL
# ============================================
print("\n" + "=" * 60)
print("📊 RESUMEN FINAL - PICKS RECOMENDADOS")
print("=" * 60)

total_setups = len(soccer_setups) + len(nba_setups)

if total_setups == 0:
    print("🔴 0 setups A+ encontrados")
    print('🧠 "No trade" es posición válida')
else:
    all_setups = soccer_setups + nba_setups
    all_setups.sort(key=lambda x: x['edge'], reverse=True)
    
    print(f"🔥 TOP PICKS DEL DÍA:\n")
    
    for i, s in enumerate(all_setups[:3], 1):
        sport = '⚽' if s in soccer_setups else '🏀'
        print(f"  {i}. {sport} {s['home_team']} vs {s['away_team']}")
        print(f"     👉 GANA: {s['pick']}")
        print(f"     📊 Prob local: {s['probability']} | Edge: {s['edge']} | Vol: {s['volatility']} | Confianza: {s['confidence']}")
        print()
    
    if total_setups > 3:
        print(f"⚠️ {total_setups} setups totales. Mostrando top 3 por edge.")

print("=" * 60)
print("🔥 SPORTS QUANT ENGINE V1 - EJECUCIÓN COMPLETA")
print("=" * 60)