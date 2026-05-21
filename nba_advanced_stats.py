"""
NBA ADVANCED STATS ENGINE
Extrae Off/Def Rating, eFG%, TS%, Pace, Net Rating desde ESPN
"""
import requests

# Cache para no llamar 30 veces por ejecución
STATS_CACHE = {}

TEAM_IDS = {
    'Atlanta Hawks': 1, 'Boston Celtics': 2, 'Brooklyn Nets': 3,
    'Charlotte Hornets': 4, 'Chicago Bulls': 5, 'Cleveland Cavaliers': 6,
    'Dallas Mavericks': 7, 'Denver Nuggets': 8, 'Detroit Pistons': 9,
    'Golden State Warriors': 10, 'Houston Rockets': 11, 'Indiana Pacers': 12,
    'LA Clippers': 13, 'Los Angeles Lakers': 14, 'Memphis Grizzlies': 15,
    'Miami Heat': 16, 'Milwaukee Bucks': 17, 'Minnesota Timberwolves': 18,
    'New Orleans Pelicans': 19, 'New York Knicks': 20, 'Oklahoma City Thunder': 21,
    'Orlando Magic': 22, 'Philadelphia 76ers': 23, 'Phoenix Suns': 24,
    'Portland Trail Blazers': 25, 'Sacramento Kings': 26, 'San Antonio Spurs': 27,
    'Toronto Raptors': 28, 'Utah Jazz': 29, 'Washington Wizards': 30
}

def get_team_advanced_stats(team_name):
    """Obtiene stats avanzadas del equipo desde ESPN"""
    team_id = TEAM_IDS.get(team_name)
    if not team_id:
        return None
    
    if team_name in STATS_CACHE:
        return STATS_CACHE[team_name]
    
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/statistics"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        cats = data.get('results', {}).get('stats', {}).get('categories', [])
        
        stats = {}
        for cat in cats:
            for s in cat.get('stats', []):
                stats[s['name']] = s.get('value', 0)
        
        # Extraer métricas clave
        off_rating = float(stats.get('avgPoints', 110))
        games_played = float(stats.get('gamesPlayed', 1))
        
        # Calcular eFG%
        fgm = float(stats.get('avgFieldGoalsMade', 38)) * games_played
        fga = float(stats.get('avgFieldGoalsAttempted', 82)) * games_played
        threepm = float(stats.get('avgThreePointFieldGoalsMade', 12)) * games_played
        
        efg = (fgm + 0.5 * threepm) / fga if fga > 0 else 0.50
        
        # TS% estimado (sin FTA exacto, usamos aproximación)
        pts = float(stats.get('points', 110 * games_played))
        fta_est = fga * 0.25  # ~25% de FGA son FTA
        ts = pts / (2 * (fga + 0.44 * fta_est)) if fga > 0 else 0.55
        
        # Pace estimado (NBA promedio ~98)
        pace = 98.0
        
        # Def Rating estimado del récord y Off Rating
        # Asumimos que la diferencia de puntos refleja el Net Rating
        # Net Rating ≈ (Win% - 0.5) * 12
        # Def Rating = Off Rating - Net Rating
        
        result = {
            'off_rating': round(off_rating, 1),
            'efg': round(efg, 3),
            'ts': round(ts, 3),
            'pace': pace,
            'fgm_per_game': round(fgm / games_played, 1),
            'fga_per_game': round(fga / games_played, 1),
            'threepm_per_game': round(threepm / games_played, 1),
            'games_played': int(games_played)
        }
        
        STATS_CACHE[team_name] = result
        return result
    
    except:
        return None


def get_def_rating_from_record(team_name, record_str):
    """
    Estima Def Rating desde el récord
    Win% de 0.700 → Net Rating ~+6
    Win% de 0.300 → Net Rating ~-6
    """
    off_stats = get_team_advanced_stats(team_name)
    if not off_stats:
        return 110.0
    
    off_rating = off_stats['off_rating']
    
    try:
        w, l = map(int, record_str.split('-'))
        win_pct = w / (w + l)
    except:
        win_pct = 0.5
    
    # Net Rating estimado del win%
    net_rating = (win_pct - 0.5) * 14
    
    # Def Rating = Off Rating - Net Rating
    def_rating = off_rating - net_rating
    
    return round(def_rating, 1)


def get_net_rating(team_name, record_str):
    """Net Rating = Off Rating - Def Rating"""
    off_stats = get_team_advanced_stats(team_name)
    if not off_stats:
        return 0
    
    def_rating = get_def_rating_from_record(team_name, record_str)
    return round(off_stats['off_rating'] - def_rating, 1)