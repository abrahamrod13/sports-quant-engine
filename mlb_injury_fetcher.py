"""
MLB INJURY FETCHER - CBS Sports (gratis, en vivo)
"""
import requests
from bs4 import BeautifulSoup

# Mapeo CBS → nombres completos
CBS_TO_MLB_TEAMS = {
    'Arizona': 'Arizona Diamondbacks', 'Atlanta': 'Atlanta Braves',
    'Baltimore': 'Baltimore Orioles', 'Boston': 'Boston Red Sox',
    'Chi. Cubs': 'Chicago Cubs', 'Chi. White Sox': 'Chicago White Sox',
    'Cincinnati': 'Cincinnati Reds', 'Cleveland': 'Cleveland Guardians',
    'Colorado': 'Colorado Rockies', 'Detroit': 'Detroit Tigers',
    'Houston': 'Houston Astros', 'Kansas City': 'Kansas City Royals',
    'LA Angels': 'Los Angeles Angels', 'LA Dodgers': 'Los Angeles Dodgers',
    'Miami': 'Miami Marlins', 'Milwaukee': 'Milwaukee Brewers',
    'Minnesota': 'Minnesota Twins', 'NY Mets': 'New York Mets',
    'NY Yankees': 'New York Yankees', 'Oakland': 'Athletics',
    'Philadelphia': 'Philadelphia Phillies', 'Pittsburgh': 'Pittsburgh Pirates',
    'San Diego': 'San Diego Padres', 'San Francisco': 'San Francisco Giants',
    'Seattle': 'Seattle Mariners', 'St. Louis': 'St. Louis Cardinals',
    'Tampa Bay': 'Tampa Bay Rays', 'Texas': 'Texas Rangers',
    'Toronto': 'Toronto Blue Jays', 'Washington': 'Washington Nationals'
}

def get_all_mlb_injuries():
    """Obtiene TODAS las lesiones MLB desde CBS Sports"""
    url = 'https://www.cbssports.com/mlb/injuries/'
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        team_headers = soup.find_all('h4')
        tables = soup.find_all('table')
        
        all_injuries = {}
        
        for i, header in enumerate(team_headers):
            team_name_cbs = header.get_text(strip=True)
            team_name_full = CBS_TO_MLB_TEAMS.get(team_name_cbs, team_name_cbs)
            
            if i < len(tables):
                table = tables[i]
                rows = table.find_all('tr')[1:]
                
                injuries = []
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 5:
                        player = cols[0].get_text(strip=True)
                        position = cols[1].get_text(strip=True) if len(cols) > 1 else ''
                        updated = cols[2].get_text(strip=True) if len(cols) > 2 else ''
                        injury = cols[3].get_text(strip=True) if len(cols) > 3 else ''
                        status = cols[4].get_text(strip=True) if len(cols) > 4 else ''
                        
                        injury_status = 'OUT' if 'out' in status.lower() else ('QUESTIONABLE' if 'questionable' in status.lower() else 'INFO')
                        
                        injuries.append({
                            'player': player.split('. ')[-1] if '. ' in player else player,
                            'position': position,
                            'injury': injury,
                            'status': injury_status,
                            'status_detail': status
                        })
                
                all_injuries[team_name_full] = injuries
        
        return all_injuries
    except Exception as e:
        print(f"Error CBS: {e}")
        return {}

def get_team_injuries_mlb(team_name):
    """Lesiones de un equipo específico MLB"""
    all_injuries = get_all_mlb_injuries()
    return all_injuries.get(team_name, [])

def get_out_players_mlb(team_name):
    """Solo jugadores OUT de un equipo"""
    injuries = get_team_injuries_mlb(team_name)
    return [i for i in injuries if i['status'] == 'OUT']