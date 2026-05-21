"""
MONTE CARLO MLB - Simulación RIGUROSA independiente del modelo
Usa datos CRUDOS (ERA, WHIP, K9), NO los scores del motor
"""
import numpy as np
from mlb_engine import MLBEngine

class MonteCarloMLB:
    def __init__(self):
        self.mlb = MLBEngine()
    
    def simulate_game(self, game_data, n_sims=10000, show_progress=True):
        """
        Simula un juego de MLB n veces usando datos CRUDOS
        
        INDEPENDIENTE del motor: usa ERA, WHIP, K9 directamente
        """
        home_team = game_data.get('home_team', 'Home')
        away_team = game_data.get('away_team', 'Away')
        
        # ============================================
        # DATOS CRUDOS (NO SCORES DEL MOTOR)
        # ============================================
        home_p = game_data.get('home_pitcher', {})
        away_p = game_data.get('away_pitcher', {})
        home_bp = game_data.get('home_bullpen', {})
        away_bp = game_data.get('away_bullpen', {})
        home_mom = game_data.get('home_momentum', {})
        away_mom = game_data.get('away_momentum', {})
        home_match = game_data.get('home_matchup', {})
        away_match = game_data.get('away_matchup', {})
        stadium = game_data.get('stadium', '')
        is_divisional = game_data.get('divisional_game', False)
        home_win_pct = game_data.get('home_win_pct', 0.5)
        away_win_pct = game_data.get('away_win_pct', 0.5)
        
        # ============================================
        # MÉTRICAS CRUDAS DEL PITCHER
        # ============================================
        # Starter home
        h_era = home_p.get('era', 4.50)
        h_whip = home_p.get('whip', 1.35)
        h_k9 = home_p.get('k9', 7.5)
        h_bb9 = home_p.get('bb9', 3.0)
        h_hr9 = home_p.get('hr9', 1.2)
        h_last3 = home_p.get('last3_era', h_era)
        h_innings = home_p.get('innings', 40)
        
        # Starter away
        a_era = away_p.get('era', 4.50)
        a_whip = away_p.get('whip', 1.35)
        a_k9 = away_p.get('k9', 7.5)
        a_bb9 = away_p.get('bb9', 3.0)
        a_hr9 = away_p.get('hr9', 1.2)
        a_last3 = away_p.get('last3_era', a_era)
        a_innings = away_p.get('innings', 40)
        
        # ============================================
        # MÉTRICAS CRUDAS DEL BULLPEN
        # ============================================
        h_bp_era = home_bp.get('era', 4.00)
        h_bp_whip = home_bp.get('whip', 1.30)
        h_bp_ip = home_bp.get('last3_innings', 10)
        h_bp_fatigue = home_bp.get('fatigue', 'NORMAL')
        
        a_bp_era = away_bp.get('era', 4.00)
        a_bp_whip = away_bp.get('whip', 1.30)
        a_bp_ip = away_bp.get('last3_innings', 10)
        a_bp_fatigue = away_bp.get('fatigue', 'NORMAL')
        
        # ============================================
        # MÉTRICAS CRUDAS DEL MOMENTUM
        # ============================================
        h_ops = home_mom.get('ops_last7', 0.720)
        h_runs = home_mom.get('runs_last5', 20)
        h_run_diff = home_mom.get('run_diff_last10', 0)
        
        a_ops = away_mom.get('ops_last7', 0.720)
        a_runs = away_mom.get('runs_last5', 20)
        a_run_diff = away_mom.get('run_diff_last10', 0)
        
        # ============================================
        # MATCHUP HISTORY (CRUDO)
        # ============================================
        h_vs_avg = home_match.get('avg', 0.250)
        h_vs_ops = home_match.get('ops', 0.720)
        a_vs_avg = away_match.get('avg', 0.250)
        a_vs_ops = away_match.get('ops', 0.720)
        
        # ============================================
        # PARK FACTOR
        # ============================================
        park = self.mlb.park_adjustment(stadium)
        park_runs = park.get('runs', 1.0)
        park_hr = park.get('hr', 1.0)
        
        # ============================================
        # CÁLCULO DE CARRERAS ESPERADAS DEL STARTER
        # ============================================
        # Un starter típico lanza ~5.5 innings
        # Las carreras esperadas = ERA * (IP/9)
        starter_ip = 5.5
        
        # Si el pitcher tiene pocos innings (lesionado/rookie), lanza menos
        if h_innings < 20:
            starter_ip = 4.5
        elif h_innings < 40:
            starter_ip = 5.0
        
        # ERA ajustada: 70% season ERA + 30% last 3 ERA
        h_effective_era = h_era * 0.70 + min(h_last3, 12.0) * 0.30
        a_effective_era = a_era * 0.70 + min(a_last3, 12.0) * 0.30
        
        # Carreras esperadas del starter
        h_starter_runs = h_effective_era * (starter_ip / 9)
        a_starter_runs = a_effective_era * (starter_ip / 9)
        
        # Ajuste por park factor
        h_starter_runs *= park_runs
        a_starter_runs *= park_runs
        
        # ============================================
        # BULLPEN: CARRERAS ESPERADAS (innings 6-9)
        # ============================================
        bp_ip = 3.5  # Innings del bullpen
        
        # Bullpen fatigue multiplier
        def fatigue_mult(ip, fatigue_label):
            if fatigue_label == 'CRITICAL':
                return 1.40
            elif fatigue_label == 'HIGH':
                return 1.25
            elif ip > 15:
                return 1.20
            elif ip > 12:
                return 1.10
            return 1.0
        
        h_bp_mult = fatigue_mult(h_bp_ip, h_bp_fatigue)
        a_bp_mult = fatigue_mult(a_bp_ip, a_bp_fatigue)
        
        h_bullpen_runs_expected = (h_bp_era * h_bp_mult) * (bp_ip / 9)
        a_bullpen_runs_expected = (a_bp_era * a_bp_mult) * (bp_ip / 9)
        
        # ============================================
        # AJUSTES OFENSIVOS
        # ============================================
        # OPS del equipo vs promedio (.720)
        h_offense_mult = 1.0 + (h_ops - 0.720) * 2.0
        a_offense_mult = 1.0 + (a_ops - 0.720) * 2.0
        
        # Run diff reciente
        h_momentum_mult = 1.0 + (h_run_diff / 50)
        a_momentum_mult = 1.0 + (a_run_diff / 50)
        
        # Matchup history
        h_matchup_mult = 1.0 + (h_vs_ops - 0.720) * 1.5
        a_matchup_mult = 1.0 + (a_vs_ops - 0.720) * 1.5
        
        # ============================================
        # FACTORES DE VOLATILIDAD
        # ============================================
        # WHIP alto = más varianza en carreras permitidas
        h_variance = 1.0 + max(0, (h_whip - 1.20) * 2.0)
        a_variance = 1.0 + max(0, (a_whip - 1.20) * 2.0)
        
        # Divisional = más varianza
        if is_divisional:
            h_variance *= 1.20
            a_variance *= 1.20
        
        # Park factor de HR
        h_variance *= park_hr
        a_variance *= park_hr
        
        # K9 bajo = más bolas en juego = más varianza
        if h_k9 < 7.0:
            h_variance *= 1.15
        if a_k9 < 7.0:
            a_variance *= 1.15
        
        # ============================================
        # MONTE CARLO SIMULATION
        # ============================================
        home_wins = 0
        away_wins = 0
        home_runs_list = []
        away_runs_list = []
        
        for i in range(n_sims):
            # Simular carreras permitidas por el pitcher AWAY (home anota)
            home_runs_vs_starter = np.random.normal(
                a_starter_runs * h_offense_mult * h_momentum_mult * h_matchup_mult,
                1.5 * a_variance
            )
            home_runs_vs_starter = max(0, home_runs_vs_starter)
            
            # Simular carreras vs bullpen AWAY
            home_runs_vs_bullpen = np.random.normal(
                a_bullpen_runs_expected * h_offense_mult,
                1.0 * a_variance
            )
            home_runs_vs_bullpen = max(0, home_runs_vs_bullpen)
            
            # Simular carreras permitidas por el pitcher HOME (away anota)
            away_runs_vs_starter = np.random.normal(
                h_starter_runs * a_offense_mult * a_momentum_mult * a_matchup_mult,
                1.5 * h_variance
            )
            away_runs_vs_starter = max(0, away_runs_vs_starter)
            
            # Simular carreras vs bullpen HOME
            away_runs_vs_bullpen = np.random.normal(
                h_bullpen_runs_expected * a_offense_mult,
                1.0 * h_variance
            )
            away_runs_vs_bullpen = max(0, away_runs_vs_bullpen)
            
            # Total carreras
            home_runs = home_runs_vs_starter + home_runs_vs_bullpen
            away_runs = away_runs_vs_starter + away_runs_vs_bullpen
            
            # Ruido aleatorio puro (errores, jugadas increíbles)
            home_runs += np.random.normal(0, 0.8)
            away_runs += np.random.normal(0, 0.8)
            
            home_runs = max(0, round(home_runs))
            away_runs = max(0, round(away_runs))
            
            home_runs_list.append(home_runs)
            away_runs_list.append(away_runs)
            
            if home_runs > away_runs:
                home_wins += 1
            elif away_runs > home_runs:
                away_wins += 1
            else:
                # Extra innings: home gana 52%
                if np.random.random() < 0.52:
                    home_wins += 1
                else:
                    away_wins += 1
        
        # ============================================
        # RESULTADOS
        # ============================================
        home_win_pct = home_wins / n_sims
        away_win_pct = away_wins / n_sims
        avg_home_runs = np.mean(home_runs_list)
        avg_away_runs = np.mean(away_runs_list)
        avg_total_runs = avg_home_runs + avg_away_runs
        
        # Distribución de carreras
        home_run_dist = {}
        away_run_dist = {}
        total_run_dist = {}
        
        for h, a in zip(home_runs_list, away_runs_list):
            total = h + a
            home_run_dist[h] = home_run_dist.get(h, 0) + 1
            away_run_dist[a] = away_run_dist.get(a, 0) + 1
            total_run_dist[total] = total_run_dist.get(total, 0) + 1
        
        # Percentiles
        home_runs_sorted = sorted(home_runs_list)
        away_runs_sorted = sorted(away_runs_list)
        total_runs_sorted = sorted([h + a for h, a in zip(home_runs_list, away_runs_list)])
        
        def percentile(data, p):
            idx = int(len(data) * p)
            return data[min(idx, len(data)-1)]
        
        # Over/Under probabilidades
        over_6_5 = sum(1 for t in total_runs_sorted if t > 6.5) / n_sims
        over_7_5 = sum(1 for t in total_runs_sorted if t > 7.5) / n_sims
        over_8_5 = sum(1 for t in total_runs_sorted if t > 8.5) / n_sims
        over_9_5 = sum(1 for t in total_runs_sorted if t > 9.5) / n_sims
        over_10_5 = sum(1 for t in total_runs_sorted if t > 10.5) / n_sims
        
        # Runline probabilidades
        home_rl_1_5 = sum(1 for h, a in zip(home_runs_list, away_runs_list) if h - a >= 2) / n_sims
        away_rl_1_5 = sum(1 for h, a in zip(home_runs_list, away_runs_list) if a - h >= 2) / n_sims
        home_rl_2_5 = sum(1 for h, a in zip(home_runs_list, away_runs_list) if h - a >= 3) / n_sims
        away_rl_2_5 = sum(1 for h, a in zip(home_runs_list, away_runs_list) if a - h >= 3) / n_sims
        
        # Team totals
        home_over_3_5 = sum(1 for h in home_runs_list if h > 3.5) / n_sims
        home_over_4_5 = sum(1 for h in home_runs_list if h > 4.5) / n_sims
        away_over_3_5 = sum(1 for a in away_runs_list if a > 3.5) / n_sims
        away_over_4_5 = sum(1 for a in away_runs_list if a > 4.5) / n_sims
        
        return {
            'home_team': home_team,
            'away_team': away_team,
            'home_win_pct': round(home_win_pct, 4),
            'away_win_pct': round(away_win_pct, 4),
            'avg_home_runs': round(avg_home_runs, 1),
            'avg_away_runs': round(avg_away_runs, 1),
            'avg_total_runs': round(avg_total_runs, 1),
            'median_total_runs': percentile(total_runs_sorted, 0.5),
            'total_std': round(np.std(total_runs_sorted), 1),
            'over_6_5': round(over_6_5, 4),
            'over_7_5': round(over_7_5, 4),
            'over_8_5': round(over_8_5, 4),
            'over_9_5': round(over_9_5, 4),
            'over_10_5': round(over_10_5, 4),
            'home_runline_minus1_5': round(home_rl_1_5, 4),
            'away_runline_minus1_5': round(away_rl_1_5, 4),
            'home_runline_minus2_5': round(home_rl_2_5, 4),
            'away_runline_minus2_5': round(away_rl_2_5, 4),
            'home_over_3_5': round(home_over_3_5, 4),
            'home_over_4_5': round(home_over_4_5, 4),
            'away_over_3_5': round(away_over_3_5, 4),
            'away_over_4_5': round(away_over_4_5, 4),
            'n_sims': n_sims,
            'home_effective_era': round(h_effective_era, 2),
            'away_effective_era': round(a_effective_era, 2),
            'home_park_factor': park_runs,
            'home_bullpen_mult': round(h_bp_mult, 2),
            'away_bullpen_mult': round(a_bp_mult, 2)
        }
    
    def print_results(self, results, model_prob=None):
        """Imprime resultados del Monte Carlo de forma profesional"""
        print("\n" + "=" * 65)
        print(f"  🎲 MONTE CARLO SIMULATION - {results['n_sims']:,} simulations")
        print("=" * 65)
        
        print(f"\n  ⚾ {results['home_team']} vs {results['away_team']}")
        
        # Win probability
        print(f"\n  ┌─────────────────────────────────────────────────┐")
        print(f"  │  WIN PROBABILITY                                │")
        print(f"  ├─────────────────────────────────────────────────┤")
        print(f"  │  {results['home_team']:<30} {results['home_win_pct']:>8.1%}  │")
        print(f"  │  {results['away_team']:<30} {results['away_win_pct']:>8.1%}  │")
        print(f"  └─────────────────────────────────────────────────┘")
        
        # Comparison with model
        if model_prob:
            diff = results['home_win_pct'] - model_prob
            print(f"\n  📊 MODEL COMPARISON:")
            print(f"     Model Probability: {model_prob:.1%}")
            print(f"     Monte Carlo:       {results['home_win_pct']:.1%}")
            print(f"     Difference:        {diff:+.1%}")
            
            if abs(diff) > 0.12:
                print(f"     🔴 LARGE DISCREPANCY - Model may be overfitting")
            elif abs(diff) > 0.07:
                print(f"     🟡 MODERATE DISCREPANCY - Adjust confidence")
            elif abs(diff) > 0.03:
                print(f"     🟢 SLIGHT DISCREPANCY - Within acceptable range")
            else:
                print(f"     ✅ MODEL VALIDATED - Independent confirmation")
        
        # Runs
        print(f"\n  📊 RUNS (average):")
        print(f"     {results['home_team']}: {results['avg_home_runs']}")
        print(f"     {results['away_team']}: {results['avg_away_runs']}")
        print(f"     Total: {results['avg_total_runs']} (median: {results['median_total_runs']}, σ: {results['total_std']})")
        
        # Totals
        print(f"\n  📊 TOTALS PROBABILITIES:")
        print(f"     Over 6.5:  {results['over_6_5']:.1%}")
        print(f"     Over 7.5:  {results['over_7_5']:.1%}")
        print(f"     Over 8.5:  {results['over_8_5']:.1%}")
        print(f"     Over 9.5:  {results['over_9_5']:.1%}")
        print(f"     Over 10.5: {results['over_10_5']:.1%}")
        
        # Runlines
        print(f"\n  📊 RUNLINE PROBABILITIES:")
        print(f"     {results['home_team']} -1.5: {results['home_runline_minus1_5']:.1%}")
        print(f"     {results['away_team']} -1.5: {results['away_runline_minus1_5']:.1%}")
        print(f"     {results['home_team']} -2.5: {results['home_runline_minus2_5']:.1%}")
        print(f"     {results['away_team']} -2.5: {results['away_runline_minus2_5']:.1%}")
        
        # Team totals
        print(f"\n  📊 TEAM TOTALS:")
        print(f"     {results['home_team']} Over 3.5: {results['home_over_3_5']:.1%}")
        print(f"     {results['home_team']} Over 4.5: {results['home_over_4_5']:.1%}")
        print(f"     {results['away_team']} Over 3.5: {results['away_over_3_5']:.1%}")
        print(f"     {results['away_team']} Over 4.5: {results['away_over_4_5']:.1%}")
        
        # Key metrics
        print(f"\n  📊 KEY METRICS:")
        print(f"     Home effective ERA: {results['home_effective_era']}")
        print(f"     Away effective ERA: {results['away_effective_era']}")
        print(f"     Park factor (runs): {results['home_park_factor']}")
        print(f"     Home bullpen mult:  {results['home_bullpen_mult']}")
        print(f"     Away bullpen mult:  {results['away_bullpen_mult']}")
        
        print("\n" + "=" * 65)