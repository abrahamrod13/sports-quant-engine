import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from config import NBA_ESPN_BASE

def get_historical_nba_with_records(days_back=90):
    """
    Récords PRE-partido: final - este resultado, degradado por fecha
    """
    all_matches = []
    
    for day_offset in range(1, days_back):
        date = (datetime.now() - timedelta(days=day_offset)).strftime('%Y%m%d')
        url = f"{NBA_ESPN_BASE}/scoreboard?dates={date}"
        
        try:
            response = requests.get(url)
            data = response.json()
            
            for event in data.get('events', []):
                if event['status']['type']['description'] != 'Final':
                    continue
                
                comp = event['competitions'][0]
                home = comp['competitors'][0]
                away = comp['competitors'][1]
                
                home_winner = home.get('winner', False)
                away_winner = away.get('winner', False)
                match_date = datetime.strptime(event['date'][:10], '%Y-%m-%d')
                
                # Récords
                home_records = home.get('records', [])
                away_records = away.get('records', [])
                home_total = away_total = '0-0'
                
                for rec in home_records:
                    if rec.get('type') == 'total':
                        home_total = rec.get('summary', '0-0')
                for rec in away_records:
                    if rec.get('type') == 'total':
                        away_total = rec.get('summary', '0-0')
                
                # Restar este partido
                if '-' in home_total:
                    w, l = map(int, home_total.split('-'))
                    w = max(0, w - 1) if home_winner else w
                    l = max(0, l - 1) if not home_winner else l
                    home_final = w/(w+l) if (w+l) > 0 else 0.5
                else:
                    home_final = 0.5
                
                if '-' in away_total:
                    w, l = map(int, away_total.split('-'))
                    w = max(0, w - 1) if away_winner else w
                    l = max(0, l - 1) if not away_winner else l
                    away_final = w/(w+l) if (w+l) > 0 else 0.5
                else:
                    away_final = 0.5
                
                # Degradar
                season_start = datetime(2025, 10, 20)
                season_end = datetime(2026, 4, 15)
                progress = max(0.15, min(1.0, (match_date - season_start).days / (season_end - season_start).days))
                
                home_win_pct = 0.5 + (home_final - 0.5) * progress + np.random.normal(0, 0.015)
                away_win_pct = 0.5 + (away_final - 0.5) * progress + np.random.normal(0, 0.015)
                home_win_pct = max(0.25, min(0.82, home_win_pct))
                away_win_pct = max(0.25, min(0.82, away_win_pct))
                
                # Playoff
                notes = comp.get('notes', [])
                is_playoff = any('Playoff' in n.get('headline', '') or 'Semifinal' in n.get('headline', '') or 'Play-In' in n.get('headline', '') for n in notes)
                
                # Resultado
                hs = int(home.get('score', 0))
                aws = int(away.get('score', 0))
                if hs == aws:
                    continue
                
                all_matches.append({
                    'date': event['date'][:10],
                    'sport': 'nba',
                    'league': 'NBA',
                    'home_team': home['team']['displayName'],
                    'away_team': away['team']['displayName'],
                    'home_score': hs,
                    'away_score': aws,
                    'winner': home['team']['displayName'] if hs > aws else away['team']['displayName'],
                    'result': 'home' if hs > aws else 'away',
                    'home_win_pct': round(home_win_pct, 3),
                    'away_win_pct': round(away_win_pct, 3),
                    'season_progress': round(progress, 2),
                    'is_playoff': is_playoff,
                    'odds': 2.0
                })
        except:
            continue
    
    df = pd.DataFrame(all_matches)
    print(f"🏀 NBA: {len(df)} partidos | Home win%: {df['home_win_pct'].mean():.3f} | Away: {df['away_win_pct'].mean():.3f}")
    return df


def get_synthetic_soccer_matches(num_matches=300):
    """Soccer sintético"""
    leagues = ['Premier League', 'La Liga', 'Serie A', 'Champions League', 'Europa League']
    teams = {
        'Premier League': ['Arsenal', 'Chelsea', 'Liverpool', 'Man City', 'Man United', 'Tottenham', 'Newcastle', 'Aston Villa'],
        'La Liga': ['Barcelona', 'Real Madrid', 'Atletico', 'Sevilla', 'Valencia', 'Real Sociedad', 'Villarreal', 'Betis'],
        'Serie A': ['AC Milan', 'Inter', 'Juventus', 'Napoli', 'Roma', 'Lazio', 'Atalanta', 'Fiorentina'],
        'Champions League': ['Bayern', 'PSG', 'Dortmund', 'Porto', 'Benfica', 'Ajax', 'Shakhtar', 'Salzburg'],
        'Europa League': ['Leverkusen', 'Roma', 'Marseille', 'Brighton', 'West Ham', 'Sporting', 'Rangers', 'Fenerbahce']
    }
    
    matches = []
    for _ in range(num_matches):
        league = np.random.choice(leagues)
        t1, t2 = np.random.choice(teams[league], 2, replace=False)
        r = np.random.random()
        
        if r < 0.45:
            hg = np.random.choice([1,2,3,2,1,4], p=[0.30,0.25,0.15,0.12,0.10,0.08])
            ag = np.random.choice([0,0,0,1,1], p=[0.45,0.20,0.15,0.12,0.08])
            res, win = 'home', t1
        elif r < 0.73:
            g = np.random.choice([0,1,1,2,2,3], p=[0.15,0.30,0.20,0.15,0.12,0.08])
            hg = ag = g
            res, win = 'draw', 'draw'
        else:
            ag = np.random.choice([1,2,3,2,1], p=[0.32,0.25,0.15,0.15,0.13])
            hg = np.random.choice([0,0,0,1], p=[0.50,0.20,0.18,0.12])
            res, win = 'away', t2
        
        matches.append({
            'date': f"2026-{np.random.randint(1,6):02d}-{np.random.randint(1,28):02d}",
            'sport': 'soccer', 'league': league,
            'home_team': t1, 'away_team': t2,
            'home_score': int(hg), 'away_score': int(ag),
            'winner': win, 'result': res,
            'home_form': round(np.random.uniform(0.40,0.72), 3),
            'away_form': round(np.random.uniform(0.35,0.68), 3),
            'home_xg': round(np.random.uniform(0.8,2.5), 2),
            'away_xg': round(np.random.uniform(0.6,2.0), 2),
            'odds': 2.0
        })
    
    print(f"⚽ Soccer sintético: {num_matches} partidos")
    return matches


def get_all_historical():
    print("=" * 60)
    print("📥 BACKTEST - RÉCORDS PRE-PARTIDO")
    print("=" * 60)
    nba = get_historical_nba_with_records(90)
    soccer = get_synthetic_soccer_matches(300)
    df = pd.DataFrame(soccer + nba.to_dict('records'))
    if len(df) > 0:
        df = df.sort_values('date', ascending=False)
        print(f"📊 TOTAL: {len(df)} | ⚽ {len(df[df['sport']=='soccer'])} | 🏀 {len(df[df['sport']=='nba'])}")
    return df


if __name__ == "__main__":
    import os
    df = get_all_historical()
    if len(df) > 0:
        os.makedirs('data', exist_ok=True)
        df.to_csv('data/historical_matches.csv', index=False)
        print("✅ Guardado")