"""
WEATHER ENGINE - Datos de clima desde MLB feed/live
Viento, temperatura, condición - Impacto en carreras y HR
"""
import requests

def get_game_weather(game_pk):
    """Obtiene clima de un juego específico"""
    try:
        r = requests.get(f'https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live', timeout=10)
        live = r.json()
        weather = live.get('gameData', {}).get('weather', {})
        return weather
    except:
        return {}

def get_weather_for_match(home_team, away_team, date_str=None):
    """Busca clima para un juego home vs away"""
    from datetime import datetime
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    try:
        r = requests.get('https://statsapi.mlb.com/api/v1/schedule', 
                       params={'sportId': 1, 'date': date_str})
        games = r.json().get('dates', [{}])[0].get('games', [])
        
        for g in games:
            home = g['teams']['home']['team']['name']
            away = g['teams']['away']['team']['name']
            if home == home_team and away == away_team:
                return get_game_weather(g['gamePk'])
        return {}
    except:
        return {}

def parse_wind(wind_str):
    """
    Parsea string de viento: '6 mph, Out To RF'
    Retorna: (speed_mph, direction)
    """
    if not wind_str:
        return 0, 'Unknown'
    
    try:
        parts = wind_str.split(',')
        speed_str = parts[0].replace('mph', '').strip()
        speed = int(speed_str) if speed_str.isdigit() else 0
        direction = parts[1].strip() if len(parts) > 1 else 'Unknown'
        return speed, direction
    except:
        return 0, 'Unknown'

def weather_impact(weather):
    """
    Calcula impacto del clima en:
    - Probabilidad del home team
    - Total de carreras
    - Volatilidad
    
    Retorna: dict con ajustes
    """
    if not weather:
        return {'home_boost': 0, 'total_runs_boost': 0, 'volatility_boost': 0}
    
    wind = weather.get('wind', '')
    temp = weather.get('temp', '70')
    condition = weather.get('condition', 'Clear')
    
    wind_speed, wind_dir = parse_wind(wind)
    
    home_boost = 0
    total_boost = 0
    vol_boost = 0
    
    # VIENTO
    if wind_speed > 0:
        if 'Out' in wind_dir:  # Viento hacia el outfield = más HR
            if wind_speed >= 15:
                total_boost += 0.08  # +8% carreras
                vol_boost += 0.04
            elif wind_speed >= 10:
                total_boost += 0.05
                vol_boost += 0.02
            elif wind_speed >= 5:
                total_boost += 0.02
        
        elif 'In' in wind_dir:  # Viento hacia el infield = menos HR
            if wind_speed >= 15:
                total_boost -= 0.06
                vol_boost += 0.03
            elif wind_speed >= 10:
                total_boost -= 0.03
        
        # Viento cruzado = más volatilidad
        if 'L' in wind_dir or 'R' in wind_dir:
            vol_boost += 0.02
    
    # TEMPERATURA
    try:
        temp_f = int(temp)
        if temp_f >= 90:  # Mucho calor = la bola vuela
            total_boost += 0.04
            vol_boost += 0.02
        elif temp_f >= 80:
            total_boost += 0.02
        elif temp_f <= 50:  # Frío = la bola no viaja
            total_boost -= 0.03
    except:
        pass
    
    # CONDICIÓN
    if 'Rain' in condition or 'Drizzle' in condition:
        total_boost -= 0.04
        vol_boost += 0.06  # Lluvia = mucha incertidumbre
    elif 'Cloudy' in condition or 'Overcast' in condition:
        vol_boost += 0.01
    elif 'Dome' in condition or 'Roof' in condition:
        vol_boost -= 0.02  # Techo cerrado = condiciones controladas
    
    return {
        'home_boost': round(home_boost, 3),
        'total_runs_boost': round(total_boost, 3),
        'volatility_boost': round(vol_boost, 3)
    }

def weather_summary(weather):
    """Resumen legible del clima"""
    if not weather:
        return "No weather data"
    return f"{weather.get('condition', '?')}, {weather.get('temp', '?')}F, Wind: {weather.get('wind', '?')}"