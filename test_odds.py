# test_odds.py
from odds_fetcher import get_fanduel_odds_full
import pandas as pd

print("=" * 60)
print("TESTING ODDS FETCHER")
print("=" * 60)

# Probar obtener odds
odds = get_fanduel_odds_full('baseball_mlb')
print(f"\nOdds encontrados: {len(odds)}")

if len(odds) > 0:
    print("\nPrimeros 5 odds:")
    for idx, row in odds.head(5).iterrows():
        print(f"\n  Match: {row['match']}")
        print(f"    h2h_home: {row.get('h2h_home', 'N/A')}")
        print(f"    h2h_away: {row.get('h2h_away', 'N/A')}")
        print(f"    favorite: {row.get('favorite', 'N/A')}")
        print(f"    favorite_odds_decimal: {row.get('favorite_odds_decimal', 'N/A')}")
        print(f"    total_point: {row.get('total_point', 'N/A')}")
else:
    print("\n❌ No se encontraron odds para MLB hoy")
    
    # Probar con otro deporte para ver si la API funciona
    print("\n Probando con NBA...")
    from odds_fetcher import get_fanduel_odds_full as get_nba_odds
    nba_odds = get_nba_odds('basketball_nba')
    print(f"NBA odds encontrados: {len(nba_odds)}")