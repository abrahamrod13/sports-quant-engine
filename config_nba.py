# NBA ENGINE CONFIG
MIN_PROBABILITY_NBA = 0.53
MAX_VOLATILITY_NBA = 0.65
MIN_EDGE_NBA = 0.03

NBA_WEIGHTS = {
    'team_strength': 0.25,
    'fatigue': 0.15,
    'injuries': 0.15,
    'matchup': 0.12,
    'playoff': 0.10,
    'home_court': 0.10,
    'rest': 0.08,
    'momentum': 0.05
}

PUBLIC_TEAMS_NBA = [
    'Los Angeles Lakers', 'Boston Celtics', 'Golden State Warriors',
    'New York Knicks', 'Philadelphia 76ers', 'Miami Heat',
    'Dallas Mavericks', 'Phoenix Suns'
]

UNDERVALUED_TEAMS_NBA = [
    'Indiana Pacers', 'Orlando Magic', 'Sacramento Kings',
    'Oklahoma City Thunder', 'New Orleans Pelicans',
    'Detroit Pistons', 'Houston Rockets'
]