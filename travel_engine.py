"""
TRAVEL ENGINE - Distancia entre estadios + Rest Days
"""
from math import radians, sin, cos, sqrt, atan2

STADIUM_COORDS = {
    'Angel Stadium': (33.800, -117.883), 'Comerica Park': (42.339, -83.048),
    'Fenway Park': (42.346, -71.097), 'Guaranteed Rate Field': (41.830, -87.634),
    'Kauffman Stadium': (39.051, -94.480), 'Minute Maid Park': (29.757, -95.355),
    'Oakland Coliseum': (37.751, -122.200), 'Oriole Park at Camden Yards': (39.284, -76.621),
    'Progressive Field': (41.496, -81.685), 'Rogers Centre': (43.641, -79.389),
    'T-Mobile Park': (47.591, -122.332), 'Target Field': (44.982, -93.278),
    'Tropicana Field': (27.768, -82.653), 'Yankee Stadium': (40.829, -73.926),
    'Chase Field': (33.445, -112.067), 'Citi Field': (40.757, -73.846),
    'Citizens Bank Park': (39.906, -75.166), 'Coors Field': (39.756, -104.994),
    'Dodger Stadium': (34.074, -118.240), 'Great American Ball Park': (39.097, -84.506),
    'loanDepot park': (25.778, -80.220), 'American Family Field': (43.028, -87.971),
    'Nationals Park': (38.873, -77.007), 'Oracle Park': (37.778, -122.389),
    'Petco Park': (32.707, -117.157), 'PNC Park': (40.447, -80.006),
    'Busch Stadium': (38.622, -90.193), 'Truist Park': (33.890, -84.468),
    'Wrigley Field': (41.948, -87.655), 'Globe Life Field': (32.747, -97.083)
}

def haversine(lat1, lon1, lat2, lon2):
    R = 3959
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

def get_travel_distance(home_stadium, away_stadium):
    coords_home = STADIUM_COORDS.get(home_stadium)
    coords_away = STADIUM_COORDS.get(away_stadium)
    if not coords_home or not coords_away:
        return 0
    return round(haversine(coords_away[0], coords_away[1], coords_home[0], coords_home[1]))

def travel_impact(distance_miles):
    if distance_miles > 2500: return -0.03, 0.04
    elif distance_miles > 1500: return -0.02, 0.02
    elif distance_miles > 800: return -0.01, 0.01
    return 0, 0

def get_rest_days(team_name, date_str=None):
    from datetime import datetime, timedelta
    if date_str is None: date_str = datetime.now().strftime('%Y-%m-%d')
    try:
        import requests
        yesterday = (datetime.strptime(date_str, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
        r = requests.get('https://statsapi.mlb.com/api/v1/schedule', params={'sportId': 1, 'date': yesterday}, timeout=10)
        games = r.json().get('dates', [{}])[0].get('games', [])
        for g in games:
            home = g['teams']['home']['team']['name']
            away = g['teams']['away']['team']['name']
            if team_name in [home, away]: return 0
        return 1
    except: return 1