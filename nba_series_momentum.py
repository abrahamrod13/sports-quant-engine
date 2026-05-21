"""
NBA SERIES MOMENTUM ENGINE
Detecta colapsos estructurales en series de playoffs
"""
import requests
from datetime import datetime, timedelta

def get_series_results(team1, team2, days_back=14):
    """
    Busca resultados entre estos 2 equipos en los últimos 14 días
    Usando ESPN scoreboard histórico
    """
    results = []
    
    for day_offset in range(days_back):
        date = (datetime.now() - timedelta(days=day_offset)).strftime('%Y%m%d')
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date}"
        
        try:
            response = requests.get(url)
            data = response.json()
            
            for event in data.get('events', []):
                comp = event['competitions'][0]
                home = comp['competitors'][0]['team']['displayName']
                away = comp['competitors'][1]['team']['displayName']
                
                if (team1 in [home, away] and team2 in [home, away]):
                    home_score = int(comp['competitors'][0].get('score', 0))
                    away_score = int(comp['competitors'][1].get('score', 0))
                    
                    if home_score > 0:  # Partido jugado
                        results.append({
                            'date': event['date'][:10],
                            'home': home,
                            'away': away,
                            'home_score': home_score,
                            'away_score': away_score,
                            'margin': home_score - away_score if home == team1 else away_score - home_score,
                            'winner': home if home_score > away_score else away
                        })
        except:
            continue
    
    return results


def series_momentum_analysis(home_team, away_team, is_playoff=False):
    """
    Analiza momentum de la serie
    """
    if not is_playoff:
        return {'has_momentum': False, 'signal': 'regular_season'}
    
    results = get_series_results(home_team, away_team)
    
    if len(results) < 2:
        return {'has_momentum': False, 'signal': 'insufficient_data'}
    
    # Ordenar por fecha
    results.sort(key=lambda x: x['date'])
    
    # Últimos 2 juegos
    last2 = results[-2:]
    
    # Margen promedio últimos 2
    avg_margin = sum(r['margin'] for r in last2) / 2
    
    # ¿Hubo blowout (+20)?
    has_blowout = any(abs(r['margin']) >= 20 for r in last2)
    
    # ¿Mismo ganador en últimos 2?
    same_winner = last2[0]['winner'] == last2[1]['winner']
    
    # Trend de margen
    margins = [r['margin'] for r in results[-4:]]
    trend_increasing = margins[-1] > margins[0] if len(margins) >= 2 else False
    
    # Determinar señal
    if same_winner and has_blowout:
        if abs(avg_margin) >= 15:
            signal = 'STRUCTURAL_COLLAPSE'
            description = f'Blowout trend detected (avg margin: {avg_margin:+.0f})'
            adjustment = 0.08 if avg_margin > 0 else -0.08
        else:
            signal = 'MOMENTUM_SHIFT'
            description = f'Same winner last 2 games (margin: {avg_margin:+.0f})'
            adjustment = 0.04 if avg_margin > 0 else -0.04
    elif same_winner:
        signal = 'SLIGHT_EDGE'
        description = 'Won last 2 games'
        adjustment = 0.02 if avg_margin > 0 else -0.02
    else:
        signal = 'BALANCED'
        description = 'Series evenly matched'
        adjustment = 0.0
    
    # ¿A quién beneficia?
    if avg_margin > 0:
        beneficiary = home_team
    else:
        beneficiary = away_team
        adjustment = -adjustment
    
    return {
        'has_momentum': signal != 'BALANCED',
        'signal': signal,
        'description': description,
        'adjustment': round(adjustment, 3),
        'beneficiary': beneficiary,
        'avg_margin': round(avg_margin, 1),
        'blowout': has_blowout,
        'games_in_series': len(results),
        'last_scores': [(r['home_score'], r['away_score']) for r in results]
    }