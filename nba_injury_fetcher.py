"""
NBA INJURY FETCHER - CBS Sports (gratis, en vivo)
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Mapeo CBS → ESPN (para compatibilidad con nuestro sistema)
CBS_TO_ESPN_TEAMS = {
    'Atlanta': 'Atlanta Hawks',
    'Boston': 'Boston Celtics',
    'Brooklyn': 'Brooklyn Nets',
    'Charlotte': 'Charlotte Hornets',
    'Chicago': 'Chicago Bulls',
    'Cleveland': 'Cleveland Cavaliers',
    'Dallas': 'Dallas Mavericks',
    'Denver': 'Denver Nuggets',
    'Detroit': 'Detroit Pistons',
    'Golden St.': 'Golden State Warriors',
    'Houston': 'Houston Rockets',
    'Indiana': 'Indiana Pacers',
    'L.A. Clippers': 'LA Clippers',
    'L.A. Lakers': 'Los Angeles Lakers',
    'Memphis': 'Memphis Grizzlies',
    'Miami': 'Miami Heat',
    'Milwaukee': 'Milwaukee Bucks',
    'Minnesota': 'Minnesota Timberwolves',
    'New Orleans': 'New Orleans Pelicans',
    'New York': 'New York Knicks',
    'Oklahoma City': 'Oklahoma City Thunder',
    'Orlando': 'Orlando Magic',
    'Phoenix': 'Phoenix Suns',
    'Portland': 'Portland Trail Blazers',
    'Sacramento': 'Sacramento Kings',
    'San Antonio': 'San Antonio Spurs',
    'Toronto': 'Toronto Raptors',
    'Utah': 'Utah Jazz',
    'Washington': 'Washington Wizards'
}

def get_all_nba_injuries():
    """Obtiene TODAS las lesiones NBA desde CBS Sports"""
    url = 'https://www.cbssports.com/nba/injuries/'
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Encontrar equipos (h4) y tablas
        team_headers = soup.find_all('h4')
        tables = soup.find_all('table')
        
        all_injuries = {}
        
        for i, header in enumerate(team_headers):
            team_name_cbs = header.get_text(strip=True)
            team_name_full = CBS_TO_ESPN_TEAMS.get(team_name_cbs, team_name_cbs)
            
            # La tabla correspondiente está después del h4
            if i < len(tables):
                table = tables[i]
                rows = table.find_all('tr')[1:]  # Saltar encabezado
                
                injuries = []
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        player_info = cols[0].get_text(strip=True)
                        position = cols[1].get_text(strip=True) if len(cols) > 1 else ''
                        updated = cols[2].get_text(strip=True) if len(cols) > 2 else ''
                        injury = cols[3].get_text(strip=True) if len(cols) > 3 else ''
                        status = cols[4].get_text(strip=True) if len(cols) > 4 else ''
                        
                        # Determinar si está OUT
                        if 'out' in status.lower() or 'expected to be out' in status.lower():
                            injury_status = 'OUT'
                        elif 'questionable' in status.lower() or 'doubtful' in status.lower():
                            injury_status = 'QUESTIONABLE'
                        elif 'probable' in status.lower():
                            injury_status = 'PROBABLE'
                        else:
                            injury_status = 'INFO'
                        
                        injuries.append({
                            'player': player_info,
                            'injury': injury,
                            'status': injury_status,
                            'status_detail': status,
                            'updated': updated
                        })
                
                all_injuries[team_name_full] = injuries
        
        return all_injuries
    
    except Exception as e:
        print(f"❌ CBS Sports: {e}")
        return {}


def get_team_injuries(team_name):
    """Lesiones de un equipo específico"""
    all_injuries = get_all_nba_injuries()
    return all_injuries.get(team_name, [])


def get_out_players(team_name):
    """Solo jugadores OUT o QUESTIONABLE"""
    injuries = get_team_injuries(team_name)
    return [i for i in injuries if i['status'] in ['OUT', 'QUESTIONABLE']]


if __name__ == "__main__":
    # Prueba
    injuries = get_all_nba_injuries()
    for team, inj_list in list(injuries.items())[:5]:
        print(f"\n{team}: {len(inj_list)} lesiones")
        for inj in inj_list[:3]:
            print(f"  {inj['player']} - {inj['status']} - {inj['injury']}")