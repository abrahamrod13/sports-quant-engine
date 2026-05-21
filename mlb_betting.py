"""
MLB BETTING ENGINE - Moneyline + Runline + Totals
"""
from odds_fetcher import get_fanduel_odds_full
from mlb_engine import MLBEngine
from market_intelligence import MarketIntelligence
from sharp_edge_engine import SharpEdgeEngine
from market_exploiter import MarketExploiter
from betting_logger import save_bet

mlb_engine = MLBEngine()
market_intel = MarketIntelligence()
sharp = SharpEdgeEngine()
exploiter = MarketExploiter()

def analyze_mlb_game(row, game_data, all_setups, show_output=True):
    """Analiza un juego de MLB y devuelve todos los bet types"""
    home_team = game_data['home_team']
    away_team = game_data['away_team']
    
    # Odds
    ml_home = row.get('h2h_home', 100)
    ml_away = row.get('h2h_away', -100)
    spread_home = row.get('spread_home', 100)
    spread_away = row.get('spread_away', -100)
    spread_point = row.get('spread_point', 1.5)
    total_over = row.get('total_over', -110)
    total_under = row.get('total_under', -110)
    total_point = row.get('total_point', 8.5)
    
    # 1. MONEYLINE
    ml_odds = ml_home if ml_home < 0 else ml_away
    if ml_odds > 0:
        ml_decimal = 1 + ml_odds/100
    else:
        ml_decimal = 1 + 100/abs(ml_odds)
    
    result = mlb_engine.evaluate_mlb_game(game_data, ml_decimal)
    intel = market_intel.final_decision(game_data, result)
    
    if show_output:
        print(f"      📊 Prob: {result['probability']} | Edge: {result['edge']} | Vol: {result['volatility']}")
        print(f"      🎯 Pick: {result['pick']} | Confianza: {result['confidence_level']} ({result['confidence_score']})")
        
        # V6 + V7
        sharp_result = sharp.classify_edge(game_data, result, intel)
        v7 = exploiter.full_analysis(game_data, result, intel)
        
        if sharp_result['edge_type'] in ['SHARP EDGE', 'SAFE EDGE', 'VALUE EDGE']:
            for flag in sharp_result['false_favorite']['flags']:
                print(f"      🚩 {flag}")
            for flag in sharp_result['underdog_value']['flags']:
                print(f"      💎 {flag}")
        
        mv = v7['market_vs']
        print(f"      📊 Market: {mv['market_prob']:.1%} | Model: {mv['model_prob']:.1%} | Gap: {mv['discrepancy']:+.1%} [{mv['status']}]")
        
        ud = v7['underdog_profile']
        if ud['level'] in ['STRONG', 'MODERATE']:
            print(f"      🐶 Underdog: {ud['underdog']} | Score: {ud['score']}/100 ({ud['level']})")
        
        print(f"      🎯 V6: {sharp_result['edge_type']} | V7: {v7['exploitation_level']}")
    
    # Guardar Moneyline
    if intel['approved']:
        result['sport'] = 'MLB'
        result['match'] = row['match']
        result['home_team'] = home_team
        result['away_team'] = away_team
        result['bet_type'] = 'Moneyline'
        result['odds_american'] = ml_home if result['pick'] == home_team else ml_away
        all_setups.append(result)
        
        if show_output:
            print(f"      ✅ MONEYLINE: {result['pick']} ({result['odds_american']})")
        
        # Guardar en historial
        save_bet('MLB', row['match'], 'Moneyline', result['pick'], 
                result['odds_american'], result['probability'], 
                result['edge'], result['volatility'], result['confidence_score'])
    
    # 2. RUNLINE
    runline_prob = analyze_runline(game_data, spread_point, result['probability'])
    runline_edge = runline_prob - 0.5
    
    if runline_edge > 0.03 and runline_prob > 0.55:
        runline_pick = f"{home_team} -1.5" if result['probability'] > 0.55 else f"{away_team} -1.5"
        if show_output:
            print(f"      ✅ RUNLINE -1.5: {runline_pick} ({spread_home if 'home' in runline_pick.lower() else spread_away})")
        
        all_setups.append({
            'sport': 'MLB', 'match': row['match'],
            'home_team': home_team, 'away_team': away_team,
            'bet_type': 'Runline -1.5', 'pick': runline_pick,
            'odds_american': spread_home if 'home' in runline_pick.lower() else spread_away,
            'probability': round(runline_prob, 4),
            'edge': round(runline_edge, 4),
            'volatility': result['volatility'],
            'confidence_score': result['confidence_score'],
            'confidence_level': result['confidence_level']
        })
        
        save_bet('MLB', row['match'], 'Runline -1.5', runline_pick,
                spread_home if 'home' in runline_pick.lower() else spread_away,
                runline_prob, runline_edge, result['volatility'], result['confidence_score'])
    
    # 3. TOTALS
    total_prob = analyze_totals(game_data, total_point, result)
    total_edge = total_prob - 0.5
    
    if total_edge > 0.03 and total_prob > 0.55:
        total_pick = f"Over {total_point}" if total_prob > 0.5 else f"Under {total_point}"
        if show_output:
            print(f"      ✅ TOTALS: {total_pick} ({total_over if 'Over' in total_pick else total_under})")
        
        all_setups.append({
            'sport': 'MLB', 'match': row['match'],
            'home_team': home_team, 'away_team': away_team,
            'bet_type': f'Total {total_pick}',
            'pick': total_pick,
            'odds_american': total_over if 'Over' in total_pick else total_under,
            'probability': round(total_prob, 4),
            'edge': round(total_edge, 4),
            'volatility': result['volatility'],
            'confidence_score': result['confidence_score'],
            'confidence_level': result['confidence_level']
        })
        
        save_bet('MLB', row['match'], f'Total {total_pick}', total_pick,
                total_over if 'Over' in total_pick else total_under,
                total_prob, total_edge, result['volatility'], result['confidence_score'])
    
    return result, intel


def analyze_runline(game_data, spread, ml_prob):
    """Probabilidad de cubrir el runline"""
    # Simplificado: equipos favoritos por mucho tienen más chance de cubrir -1.5
    if ml_prob > 0.60:
        return ml_prob - 0.08
    elif ml_prob > 0.55:
        return ml_prob - 0.12
    else:
        return ml_prob - 0.20


def analyze_totals(game_data, total_line, result):
    """Probabilidad de Over/Under"""
    # Basado en park factor + pitchers
    park_factor = mlb_engine.park_adjustment(game_data.get('stadium', ''))
    runs_factor = park_factor.get('runs', 1.0)
    
    home_p = mlb_engine.pitcher_score(game_data.get('home_pitcher', {}))
    away_p = mlb_engine.pitcher_score(game_data.get('away_pitcher', {}))
    
    # Pitchers malos = más carreras
    if home_p < 0.55 and away_p < 0.55:
        over_prob = 0.58
    elif home_p > 0.70 and away_p > 0.70:
        over_prob = 0.42
    else:
        over_prob = 0.50
    
    # Park factor
    over_prob += (runs_factor - 1.0) * 0.3
    
    return min(0.75, max(0.25, over_prob))