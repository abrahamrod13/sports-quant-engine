"""
BETTING RESULTS - Vista detallada de resultados
"""
from betting_logger import get_betting_stats
import pandas as pd
import os

LOG_FILE = 'data/betting_log.csv'

def show_results():
    """Muestra resultados detallados por deporte"""
    print("=" * 60)
    print("📊 BETTING RESULTS")
    print("=" * 60)
    
    if not os.path.exists(LOG_FILE):
        print("\n📝 No hay historial todavía.")
        print("   Ejecuta predicciones primero.\n")
        return
    
    df = pd.read_csv(LOG_FILE)
    
    # 1. MLB
    show_sport_results(df, 'MLB')
    
    # 2. NBA
    show_sport_results(df, 'NBA')
    
    # 3. Pendientes
    pending = df[df['result'] == 'PENDING']
    if len(pending) > 0:
        print(f"\n🔄 PENDIENTES: {len(pending)} predicciones por validar")
        print("-" * 40)
        for _, row in pending.iterrows():
            print(f"  {row['date']} | {row['sport']} | {row['bet_type']} | {row['pick']} | {row['match'][:40]}")


def show_sport_results(df, sport):
    """Muestra resultados de un deporte"""
    sport_df = df[df['sport'] == sport]
    
    if len(sport_df) == 0:
        return
    
    completed = sport_df[sport_df['result'] != 'PENDING']
    pending = len(sport_df[sport_df['result'] == 'PENDING'])
    
    print(f"\n{'='*40}")
    print(f"  {sport}")
    print(f"{'='*40}")
    
    if len(completed) == 0:
        print(f"  📝 Sin resultados validados. {pending} pendientes.")
        return
    
    # Stats generales
    wins = len(completed[completed['result'] == 'WIN'])
    total = len(completed)
    profit = completed['profit_loss'].sum()
    win_rate = wins / total * 100 if total > 0 else 0
    roi = profit / (total * 100) * 100 if total > 0 else 0
    
    print(f"  📊 TOTAL: {total} bets | {wins}W-{total-wins}L | Win Rate: {win_rate:.1f}%")
    print(f"  💰 Profit: ${profit:+.2f} | ROI: {roi:+.1f}%")
    
    # Por tipo de apuesta
    print(f"\n  📋 BY BET TYPE:")
    print(f"  {'Type':<20} {'Bets':>5} {'Wins':>5} {'Win%':>7} {'Profit':>10} {'ROI':>7}")
    print(f"  {'-'*54}")
    
    for bet_type in completed['bet_type'].unique():
        bt = completed[completed['bet_type'] == bet_type]
        bt_wins = len(bt[bt['result'] == 'WIN'])
        bt_total = len(bt)
        bt_profit = bt['profit_loss'].sum()
        bt_winrate = bt_wins / bt_total * 100 if bt_total > 0 else 0
        bt_roi = bt_profit / (bt_total * 100) * 100 if bt_total > 0 else 0
        
        print(f"  {bet_type:<20} {bt_total:>5} {bt_wins:>5} {bt_winrate:>6.1f}% ${bt_profit:>+9.2f} {bt_roi:>+6.1f}%")
    
    # Últimas 5
    print(f"\n  📋 ÚLTIMAS 5:")
    last5 = completed.tail(5)[['date', 'bet_type', 'pick', 'result', 'profit_loss']]
    for _, row in last5.iterrows():
        emoji = '✅' if row['result'] == 'WIN' else '❌'
        print(f"  {emoji} {row['date']} | {row['bet_type']} | {row['pick']} | ${row['profit_loss']:+.2f}")