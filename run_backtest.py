from backtest_collector import get_all_historical
from backtest_engine import BacktestEngine
import pandas as pd
import os

print("=" * 60)
print("🧪 SPORTS QUANT - BACKTEST COMPLETO")
print("🏀 NBA + ⚽ SOCCER")
print("=" * 60)

# 1. Cargar o descargar datos históricos
if os.path.exists('data/historical_matches.csv'):
    print("\n📂 Cargando datos guardados...")
    historical = pd.read_csv('data/historical_matches.csv')
    print(f"✅ {len(historical)} partidos cargados")
else:
    print("\n📥 Descargando datos históricos (90 días)...")
    historical = get_all_historical()
    if len(historical) > 0:
        os.makedirs('data', exist_ok=True)
        historical.to_csv('data/historical_matches.csv', index=False)
        print("✅ Datos guardados")
    else:
        print("❌ No se pudieron obtener datos")
        exit()

# 2. Añadir odds simuladas (luego reemplazamos con reales)
if 'odds' not in historical.columns:
    historical['odds'] = 2.0

# 3. Ejecutar backtest
engine = BacktestEngine()
report = engine.run_backtest(historical, bankroll=1000, stake_pct=0.03)

# 4. Imprimir reporte
engine.print_report(report)

# 5. Guardar resultados
if engine.results:
    results_df = pd.DataFrame(engine.results)
    results_df.to_csv('data/backtest_results.csv', index=False)
    print("\n💾 Resultados guardados en data/backtest_results.csv")
    
    balance_df = pd.DataFrame({'balance': engine.balance_history})
    balance_df.to_csv('data/balance_history.csv', index=False)
    print("💾 Balance guardado en data/balance_history.csv")
    
    # Mostrar últimos 5 picks
    print("\n📋 ÚLTIMOS 5 PICKS:")
    print(results_df[['date', 'sport', 'match', 'pick', 'won', 'profit']].tail(5))