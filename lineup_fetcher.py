"""
LINEUP FETCHER - Obtiene lineups REALES del día desde MLB feed/live
Solo disponible cuando el juego está en status 'Preview' o 'Live'
"""
import requests

def get_game_lineup(game_pk):
    """
    Obtiene lineups de ambos equipos para un juego específico
    Retorna: dict con home_lineup y away_lineup (lista de dicts)
    """
    try:
        r = requests.get(f'https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live')
        live = r.json()
        
        defense = live.get('liveData', {}).get('linescore', {}).get('defense', {})
        offense = live.get('liveData', {}).get('linescore', {}).get('offense', {})
        
        def_team = defense.get('team', {}).get('name', '')
        off_team = offense.get('team', {}).get('name', '')
        
        # Posiciones titulares
        positions = ['pitcher', 'catcher', 'first', 'second', 'third', 
                     'shortstop', 'left', 'center', 'right']
        
        lineup_def = []
        for pos in positions:
            player = defense.get(pos, {})
            if player and 'fullName' in player:
                lineup_def.append({
                    'position': pos,
                    'name': player['fullName'],
                    'id': player.get('id', '')
                })
        
        lineup_off = []
        for pos in positions:
            player = offense.get(pos, {})
            if player and 'fullName' in player:
                lineup_off.append({
                    'position': pos,
                    'name': player['fullName'],
                    'id': player.get('id', '')
                })
        
        if lineup_def or lineup_off:
            return {
                'defense_team': def_team,
                'offense_team': off_team,
                'defense_lineup': lineup_def,
                'offense_lineup': lineup_off,
                'has_lineups': True
            }
        
        return {'has_lineups': False}
    
    except:
        return {'has_lineups': False}


def get_lineups_for_match(home_team, away_team):
    """
    Busca lineups para un juego específico (home vs away)
    Escanea los juegos de hoy y encuentra el que coincida
    """
    try:
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        
        r = requests.get('https://statsapi.mlb.com/api/v1/schedule', 
                       params={'sportId': 1, 'date': today})
        games = r.json().get('dates', [{}])[0].get('games', [])
        
        for game in games:
            home = game['teams']['home']['team']['name']
            away = game['teams']['away']['team']['name']
            status = game.get('status', {}).get('detailedState', '')
            
            if home == home_team and away == away_team:
                # Solo obtener lineups si el juego está próximo
                if status in ['Preview', 'Pre-Game', 'Live', 'In Progress']:
                    return get_game_lineup(game['gamePk'])
                else:
                    return {'has_lineups': False, 'status': status}
        
        return {'has_lineups': False}
    
    except:
        return {'has_lineups': False}


def lineup_summary(lineup_data):
    """Convierte lineup a string legible"""
    if not lineup_data.get('has_lineups'):
        return "Lineup not yet available"
    
    text = f"**{lineup_data['defense_team']} (defense):**\n"
    for p in lineup_data['defense_lineup']:
        text += f"  {p['position']}: {p['name']}\n"
    
    text += f"\n**{lineup_data['offense_team']} (offense):**\n"
    for p in lineup_data['offense_lineup']:
        text += f"  {p['position']}: {p['name']}\n"
    
    return text


def lineup_impact(lineup_data, home_team, away_team):
    """
    Calcula impacto del lineup en la predicción
    - Si falta una estrella: penalización
    - Si el lineup es fuerte: bonus
    """
    if not lineup_data.get('has_lineups'):
        return 0
    
    # Lista de estrellas (si no están en el lineup = penalización)
    superstars = [
        'Mike Trout', 'Shohei Ohtani', 'Aaron Judge', 'Mookie Betts',
        'Freddie Freeman', 'Juan Soto', 'Ronald Acuña Jr.', 'Manny Machado',
        'Jose Ramirez', 'Corey Seager', 'Bryce Harper', 'Trea Turner',
        'Vladimir Guerrero Jr.', 'Bo Bichette', 'Yordan Alvarez',
        'Julio Rodriguez', 'Fernando Tatis Jr.', 'Rafael Devers'
    ]
    
    impact = 0
    all_players = []
    for p in lineup_data.get('defense_lineup', []):
        all_players.append(p['name'])
    for p in lineup_data.get('offense_lineup', []):
        all_players.append(p['name'])
    
    # Verificar estrellas ausentes
    for star in superstars:
        # Si la estrella es del equipo y NO está en el lineup
        if star in str(all_players):
            continue
        # No podemos saber a qué equipo pertenece sin más datos
        # Simplificación: si falta del lineup de defense (home)
        if lineup_data['defense_team'] == home_team:
            impact -= 0.02
        elif lineup_data['defense_team'] == away_team:
            impact -= 0.02
    
    return max(-0.05, min(0.05, impact))


if __name__ == "__main__":
    # Prueba
    test = get_lineups_for_match('Detroit Tigers', 'Los Angeles Angels')
    if test['has_lineups']:
        print(lineup_summary(test))
    else:
        print(f"No lineups available. Status: {test.get('status', 'Unknown')}")