"""
SPORTS QUANT ENGINE V8 - Menú Interactivo Central
Incluye: MLB, NBA, Soccer, Betting Results, Monte Carlo
"""
import os
import sys
from datetime import datetime
from betting_logger import init_logger, validate_pending_bets
from betting_results import show_results

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def run_montecarlo_mlb():
    """Opción 10: Monte Carlo para un juego específico de MLB"""
    from mlb_data_fetcher import (
        get_today_mlb_games, get_pitcher_stats, get_pitcher_last3,
        get_pitcher_vs_team, get_bullpen_data, get_team_momentum
    )
    from odds_fetcher import get_fanduel_odds_full
    from mlb_engine import MLBEngine
    from montecarlo_mlb import MonteCarloMLB
    
    mlb_engine = MLBEngine()
    
    print("\n📥 Cargando juegos de hoy...")
    games = get_today_mlb_games()
    
    if len(games) == 0:
        print("   No hay juegos programados hoy.")
        return
    
    odds = get_fanduel_odds_full('baseball_mlb')
    if len(odds) > 0:
        games = games.merge(odds, on='match', how='left', suffixes=('', '_fd'))
    
    # Mostrar juegos disponibles
    game_list = []
    print(f"\n   🎯 JUEGOS DISPONIBLES PARA MONTE CARLO:\n")
    
    for idx, (_, row) in enumerate(games.iterrows(), 1):
        if row.get('home_pitcher_name', 'TBD') == 'TBD':
            continue
        
        game_list.append(row)
        
        # Obtener datos rápidos para mostrar
        home_p = get_pitcher_stats(row.get('home_pitcher_id'))
        away_p = get_pitcher_stats(row.get('away_pitcher_id'))
        
        if not home_p:
            home_p = mlb_engine.smart_pitcher_defaults(row.get('home_pitcher_name', ''))
        if not away_p:
            away_p = mlb_engine.smart_pitcher_defaults(row.get('away_pitcher_name', ''))
        
        fav = row.get('favorite', '')
        dog = row.get('underdog', '')
        
        print(f"   #{idx:<3} ⚾ {row['home_team']} vs {row['away_team']}")
        print(f"        🏟️ {row.get('stadium', 'Unknown')}")
        print(f"        🔥 {row.get('home_pitcher_name', 'TBD')}: {home_p.get('era', '?')} ERA")
        print(f"        🔥 {row.get('away_pitcher_name', 'TBD')}: {away_p.get('era', '?')} ERA")
        if fav:
            print(f"        💰 {fav} FAV | {dog} DOG")
        print()
    
    if len(game_list) == 0:
        print("   No hay juegos con pitchers anunciados.")
        return
    
    # Elegir juego
    choice = input(f"   🎲 Run Monte Carlo for game # (1-{len(game_list)}): ").strip()
    
    try:
        game_idx = int(choice) - 1
        if game_idx < 0 or game_idx >= len(game_list):
            print("   Invalid game number.")
            return
        
        row = game_list[game_idx]
        
        # Preparar game_data completo
        print(f"\n   📥 Cargando datos completos para {row['home_team']} vs {row['away_team']}...")
        
        home_p_data = get_pitcher_stats(row.get('home_pitcher_id'))
        away_p_data = get_pitcher_stats(row.get('away_pitcher_id'))
        
        if not home_p_data:
            home_p_data = mlb_engine.smart_pitcher_defaults(row.get('home_pitcher_name', ''))
        if not away_p_data:
            away_p_data = mlb_engine.smart_pitcher_defaults(row.get('away_pitcher_name', ''))
        
        # Last 3
        home_last3 = get_pitcher_last3(row.get('home_pitcher_id'))
        away_last3 = get_pitcher_last3(row.get('away_pitcher_id'))
        if home_last3:
            home_p_data['last3_era'] = round(sum(g['era'] for g in home_last3) / len(home_last3), 2)
        if away_last3:
            away_p_data['last3_era'] = round(sum(g['era'] for g in away_last3) / len(away_last3), 2)
        
        # Vs Team
        home_vs_away = get_pitcher_vs_team(row.get('home_pitcher_id'), row.get('away_team_id'))
        away_vs_home = get_pitcher_vs_team(row.get('away_pitcher_id'), row.get('home_team_id'))
        
        game_data = {
            'home_team': row['home_team'],
            'away_team': row['away_team'],
            'home_win_pct': row.get('home_win_pct', 0.5),
            'away_win_pct': row.get('away_win_pct', 0.5),
            'home_pitcher': home_p_data,
            'away_pitcher': away_p_data,
            'home_bullpen': get_bullpen_data(row.get('home_team_id')),
            'away_bullpen': get_bullpen_data(row.get('away_team_id')),
            'home_momentum': get_team_momentum(row.get('home_team_id')),
            'away_momentum': get_team_momentum(row.get('away_team_id')),
            'home_matchup': {
                'avg': home_vs_away.get('avg', 0.250) if home_vs_away else 0.250,
                'ops': home_vs_away.get('ops', 0.720) if home_vs_away else 0.720,
                'hr': home_vs_away.get('hr', 0) if home_vs_away else 0,
                'pa': home_vs_away.get('plate_appearances', 0) if home_vs_away else 0,
                'k_rate': 0.22
            },
            'away_matchup': {
                'avg': away_vs_home.get('avg', 0.250) if away_vs_home else 0.250,
                'ops': away_vs_home.get('ops', 0.720) if away_vs_home else 0.720,
                'hr': away_vs_home.get('hr', 0) if away_vs_home else 0,
                'pa': away_vs_home.get('plate_appearances', 0) if away_vs_home else 0,
                'k_rate': 0.22
            },
            'stadium': row.get('stadium', ''),
            'divisional_game': row.get('is_divisional', False)
        }
        
        # Número de simulaciones
        n = input("   Number of simulations (default 10000, max 50000): ").strip()
        n_sims = int(n) if n else 10000
        n_sims = min(50000, max(1000, n_sims))
        
        print(f"\n   🎲 Running {n_sims:,} Monte Carlo simulations...")
        print(f"   ⏳ This may take a few seconds...\n")
        
        # Ejecutar Monte Carlo
        mc = MonteCarloMLB()
        results = mc.simulate_game(game_data, n_sims)
        
        # Obtener model_prob del motor
        fav_odds = row.get('favorite_odds_decimal', 2.0) or 2.0
        model_result = mlb_engine.evaluate_mlb_game(game_data, fav_odds)
        
        # Imprimir resultados
        mc.print_results(results, model_result.get('probability', 0.5))
        
    except ValueError:
        print("   Please enter a valid number.")

def menu():
    init_logger()
    
    while True:
        clear_screen()
        print("=" * 50)
        print("   🏀⚾⚽ SPORTS QUANT ENGINE V8 ⚽⚾🏀")
        print("=" * 50)
        print(f"   📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 50)
        print("\n   1.  ⚾ MLB Today")
        print("   2.  ⚾ MLB Tomorrow")
        print("   3.  🏀 NBA Today")
        print("   4.  🏀 NBA Tomorrow")
        print("   5.  ⚽ Soccer Today")
        print("   6.  ⚽ Soccer Tomorrow")
        print("   7.  📊 MLB Betting Results")
        print("   8.  📊 NBA Betting Results")
        print("   9.  🔄 Validate All Pending")
        print("   10. 🎲 Monte Carlo MLB")
        print("   0.  Exit")
        print("\n" + "=" * 50)
        
        choice = input("\n   Option: ").strip()
        
        if choice == '1':
            clear_screen()
            os.system('python run_live_mlb.py')
            input("\n   Press Enter to continue...")
        
        elif choice == '2':
            clear_screen()
            os.system('python run_tomorrow_mlb.py')
            input("\n   Press Enter to continue...")
        
        elif choice == '3':
            clear_screen()
            os.system('python run_live_nba.py')
            input("\n   Press Enter to continue...")
        
        elif choice == '4':
            clear_screen()
            os.system('python run_tomorrow_nba.py')
            input("\n   Press Enter to continue...")
        
        elif choice == '5':
            clear_screen()
            os.system('python run_live.py')
            input("\n   Press Enter to continue...")
        
        elif choice == '6':
            clear_screen()
            os.system('python run_tomorrow.py')
            input("\n   Press Enter to continue...")
        
        elif choice == '7':
            clear_screen()
            from betting_results import show_sport_results
            import pandas as pd
            if os.path.exists('data/betting_log.csv'):
                df = pd.read_csv('data/betting_log.csv')
                show_sport_results(df, 'MLB')
            else:
                print("\n📝 No hay historial MLB todavía.")
            input("\n   Press Enter to continue...")
        
        elif choice == '8':
            clear_screen()
            from betting_results import show_sport_results
            import pandas as pd
            if os.path.exists('data/betting_log.csv'):
                df = pd.read_csv('data/betting_log.csv')
                show_sport_results(df, 'NBA')
            else:
                print("\n📝 No hay historial NBA todavía.")
            input("\n   Press Enter to continue...")
        
        elif choice == '9':
            clear_screen()
            print("🔄 VALIDANDO PREDICCIONES PENDIENTES...\n")
            validate_pending_bets()
            print()
            input("   Press Enter to continue...")
        
        elif choice == '10':
            clear_screen()
            print("🎲 MONTE CARLO MLB")
            print("=" * 50)
            run_montecarlo_mlb()
            input("\n   Press Enter to continue...")
        
        elif choice == '0':
            clear_screen()
            print("\n   👋 Goodbye! 🔥\n")
            break
        
        else:
            print("\n   ❌ Invalid option.")
            input("   Press Enter to continue...")

if __name__ == "__main__":
    menu()