import requests
from datetime import datetime, timedelta

def get_team_momentum(team_id):
    if not team_id:
        return {'last10_wins': 5, 'streak': 0, 'run_diff_last10': 0, 'ops_last7': 0.720, 'era_last7': 4.20}
    
    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/stats"
    params = {
        'stats': 'byDateRange', 'season': 2026,
        'startDate': (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'),
        'endDate': datetime.now().strftime('%Y-%m-%d'),
        'group': 'hitting'
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        for stat_group in data.get('stats', []):
            for split in stat_group.get('splits', []):
                stat = split.get('stat', {})
                if stat:
                    return {
                        'last10_wins': min(10, int(stat.get('wins', 5) or 0)),
                        'streak': 0,
                        'run_diff_last10': int(stat.get('runs', 0) or 0),
                        'ops_last7': float(stat.get('ops', '.720') or '.720'),
                        'era_last7': float(stat.get('era', '4.20') or '4.20')
                    }
        return {'last10_wins': 5, 'streak': 0, 'run_diff_last10': 0, 'ops_last7': 0.720, 'era_last7': 4.20}
    except:
        return {'last10_wins': 5, 'streak': 0, 'run_diff_last10': 0, 'ops_last7': 0.720, 'era_last7': 4.20}