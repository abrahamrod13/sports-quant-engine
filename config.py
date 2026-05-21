# ============================================
# SPORTS QUANT ENGINE V1 - CONFIGURACIÓN
# ============================================

# ⚽ API-Football
SOCCER_API_KEY = "b6c789f0b5dbe986162432cc1bb484a3"
SOCCER_API_BASE = "https://v3.football.api-sports.io"

# 🏀 NBA - ESPN
NBA_ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"

# 🎲 The Odds API
ODDS_API_KEY = "eb5764b3fb452998d328bd8b2546bbd1"
ODDS_API_BASE = "https://api.the-odds-api.com/v4"

# ============================================
# PARÁMETROS DEL MOTOR
# ============================================
MIN_PROBABILITY = 0.53
MAX_VOLATILITY = 0.65
MIN_EDGE = 0.03

# Pesos Soccer
SOCCER_WEIGHTS = {
    'home_form': 0.20,
    'xg_diff': 0.25,
    'motivation': 0.15,
    'injuries': 0.15,
    'home_advantage': 0.15,
    'recent_h2h': 0.10
}

# Pesos NBA
NBA_WEIGHTS = {
    'home_win_pct': 0.20,
    'net_rating_diff': 0.20,
    'injury_factor': 0.15,
    'rest_advantage': 0.12,
    'momentum': 0.13,
    'rebounding_edge': 0.10,
    'h2h_factor': 0.10
}

# Pesos Volatilidad
VOLATILITY_WEIGHTS = {
    'rivalry_factor': 0.25,
    'team_inconsistency': 0.35,
    'injury_uncertainty': 0.20,
    'schedule_fatigue': 0.20
}

# Ligas prioritarias Soccer
PRIORITY_LEAGUE_IDS = {
    39: 'Premier League',
    140: 'La Liga',
    135: 'Serie A',
    2: 'Champions League',
    3: 'Europa League',
}