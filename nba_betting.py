"""
NBA BETTING ENGINE - Moneyline + Spread + Totals
"""
from nba_core import NBACore
from nba_market_exploiter import NBAMarketExploiter
from betting_logger import save_bet

nba_core = NBACore()
nba_exploiter = NBAMarketExploiter()

def analyze_nba_game(row, home_data, away_data, all_setups, show_output=True):
    """Analiza un juego de NBA y devuelve todos los bet types"""
    home_team = home_data['home_team']
    away_team = away_data['away_team']
    
    # Odds
    ml_home = row.get('home_ml_close', row.get('h2h_home', -110))
    ml_away = row.get('away_ml_close', row.get('h2h_away', -110))
    spread_line = row.get('spread_close', row.get('spread_point', 0))
    
    # 1. MONEYLINE
    result = nba_core.evaluate_nba_game(home_data, away_data, ml_home)
    v7 = nba_exploiter.full_analysis(row.to_dict(), result, home_team, away_team)
    
    if show_output:
        print(f"      📊 Prob: {result['probability']} | Edge: {result['edge']} | Vol: {result['volatility']} | {result['confidence_level']}")
        
        mv = v7['market_vs']
        print(f"      📊 Market: {mv['market_prob']:.1%} | Model: {mv['model_prob']:.1%} | Gap: {mv['discrepancy']:+.1%}")
    
    # Guardar Moneyline
    if result['approved']:
        pick = home_team if result['edge'] > 0 else away_team
        result['pick'] = pick
        result['sport'] = 'NBA'
        result['match'] = row['match']
        result['home_team'] = home_team
        result['away_team'] = away_team
        result['bet_type'] = 'Moneyline'
        result['odds_american'] = ml_home if pick == home_team else ml_away
        all_setups.append(result)
        
        if show_output:
            print(f"      ✅ MONEYLINE: {pick} ({result['odds_american']})")
        
        save_bet('NBA', row['match'], 'Moneyline', pick,
                result['odds_american'], result['probability'],
                result['edge'], result['volatility'], result['confidence_score'])
    
    # 2. SPREAD
    spread_prob = analyze_nba_spread(home_data, away_data, spread_line)
    spread_edge = spread_prob - 0.5
    
    if spread_edge > 0.03 and spread_prob > 0.55:
        spread_pick = f"{home_team} {spread_line}" if spread_prob > 0.5 else f"{away_team} +{abs(spread_line)}"
        if show_output:
            print(f"      ✅ SPREAD: {spread_pick}")
        
        save_bet('NBA', row['match'], 'Spread', spread_pick, -110,
                spread_prob, spread_edge, result['volatility'], result['confidence_score'])
    
    return result, v7


def analyze_nba_spread(home_data, away_data, spread):
    """Probabilidad de cubrir el spread"""
    ml_prob = nba_core.calculate_nba_probability(home_data, away_data)
    
    # Ajustar por spread
    if abs(spread) > 8:
        return ml_prob - 0.05
    elif abs(spread) > 5:
        return ml_prob - 0.03
    else:
        return ml_prob