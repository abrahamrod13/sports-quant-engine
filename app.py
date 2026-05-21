import streamlit as st
import subprocess
import sys
import pandas as pd
import os
from datetime import datetime

# ============================================
# CONFIGURACIÓN DE PÁGINA
# ============================================
st.set_page_config(
    page_title="Sports Quant Engine V8",
    page_icon="MLB",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================
# CSS PERSONALIZADO
# ============================================
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        color: #e94560;
        font-size: 2.5rem;
        margin: 0;
    }
    .main-header p {
        color: #a0a0a0;
        font-size: 1.1rem;
    }
    .stButton > button {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: white !important;
        border: 1px solid #e94560;
        border-radius: 10px;
        padding: 0.8rem 1.5rem;
        font-weight: bold;
        transition: all 0.3s;
        height: 60px;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #e94560 0%, #c23152 100%);
        border-color: #e94560;
        transform: scale(1.02);
    }
    .metric-card {
        background: #1a1a2e;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #333;
        text-align: center;
    }
    .section-title {
        color: #e94560;
        border-bottom: 2px solid #e94560;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
    }
    .footer {
        text-align: center;
        color: #666;
        margin-top: 3rem;
        padding: 1rem;
        border-top: 1px solid #333;
    }
    .mc-result {
        background: #0f3460;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .comparison-box {
        background: #1a1a2e;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #333;
    }
    .results-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
        font-size: 0.9rem;
    }
    .results-table th {
        background: #0f3460;
        color: #e94560;
        padding: 0.7rem;
        text-align: center;
        border-bottom: 2px solid #e94560;
    }
    .results-table td {
        background: #1a1a2e;
        color: #ccc;
        padding: 0.5rem;
        text-align: center;
        border-bottom: 1px solid #333;
    }
    .results-table tr:hover td {
        background: #16213e;
    }
    .status-ok { color: #00ff88; font-weight: bold; }
    .status-sus { color: #f0a500; font-weight: bold; }
    .status-no { color: #e94560; }
    .status-marginal { color: #888; }
</style>
""", unsafe_allow_html=True)

# ============================================
# HEADER
# ============================================
st.markdown("""
<div class="main-header">
    <h1>MLB NBA SPORTS QUANT ENGINE V8</h1>
    <p>Market Inefficiency Detection System | Monte Carlo Validation</p>
</div>
""", unsafe_allow_html=True)

# ============================================
# FUNCIÓN PARA EJECUTAR SCRIPTS Y PARSEAR OUTPUT
# ============================================
def run_script_and_parse(script_name):
    """Ejecuta script y devuelve líneas parseadas para tabla"""
    output_text = ""
    
    process = subprocess.Popen(
        [sys.executable, script_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    for line in process.stdout:
        output_text += line
    
    process.wait()
    return output_text

def parse_compact_output(output_text):
    """Parsea el output compacto a lista de diccionarios"""
    lines = output_text.strip().split('\n')
    results = []
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('===') or line.startswith('---') or line.startswith('[GO]') or line.startswith('ML =') or line.startswith('Date:'):
            continue
        if 'GAME' in line and 'PICK' in line:
            continue
        
        parts = line.split()
        if len(parts) >= 10:
            try:
                game = ' '.join(parts[0:3]) if len(parts) > 3 else parts[0]
                # Intentar extraer campos
                results.append(line)
            except:
                pass
    
    return results

def display_results_table(output_text, sport="MLB"):
    """Muestra output como tabla visual"""
    if not output_text.strip():
        st.warning(f"No {sport} games found or data unavailable.")
        return
    
    lines = output_text.strip().split('\n')
    data_rows = []
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('===') or line.startswith('---'):
            continue
        if 'GAME' in line and 'PICK' in line:
            continue
        if line.startswith('[GO]') or line.startswith('ML =') or line.startswith('Date:'):
            continue
        
        parts = line.split()
        if len(parts) >= 8:
            data_rows.append(line)
    
    if not data_rows:
        st.code(output_text[-3000:], language=None)
        return
    
    # Crear tabla visual
    table_html = '<table class="results-table"><thead><tr>'
    
    if sport == "MLB":
        headers = ['GAME', 'PICK', 'ODDS', 'PROB', 'EDGE', 'CONF', 'ML', 'RL', 'O/U', 'TEAM', 'F5']
        table_html += ''.join([f'<th>{h}</th>' for h in headers])
        table_html += '</tr></thead><tbody>'
        
        for row in data_rows:
            parts = row.split()
            if len(parts) >= 11:
                game = ' '.join(parts[0:3])
                pick = ' '.join(parts[3:6]) if len(parts) > 6 else parts[3]
                odds = parts[-8] if len(parts) >= 8 else '-'
                prob = parts[-7] if len(parts) >= 7 else '-'
                edge = parts[-6] if len(parts) >= 6 else '-'
                conf = parts[-5] if len(parts) >= 5 else '-'
                ml = parts[-4] if len(parts) >= 4 else '-'
                rl = parts[-3] if len(parts) >= 3 else '-'
                ou = parts[-2] if len(parts) >= 2 else '-'
                team = parts[-1] if len(parts) >= 1 else '-'
                f5 = parts[0] if len(parts) > 0 else '-'
                
                # Reorganizar para MLB
                try:
                    game = ' '.join(parts[0:3])[:30]
                    pick = parts[3][:20] if len(parts) > 3 else ''
                    odds = parts[4] if len(parts) > 4 else ''
                    prob = parts[5] if len(parts) > 5 else ''
                    edge = parts[6] if len(parts) > 6 else ''
                    conf = parts[7] if len(parts) > 7 else ''
                    ml_st = parts[8] if len(parts) > 8 else ''
                    rl_st = parts[9] if len(parts) > 9 else ''
                    ou_st = parts[10] if len(parts) > 10 else ''
                    team_st = parts[11] if len(parts) > 11 else ''
                    f5_st = parts[12] if len(parts) > 12 else ''
                    
                    # Colores
                    ml_color = 'status-ok' if '[OK]' in ml_st else ('status-sus' if '[SUS]' in ml_st else 'status-no')
                    rl_color = 'status-ok' if '[OK]' in rl_st else 'status-marginal'
                    ou_color = 'status-ok' if '[OK]' in ou_st else 'status-marginal'
                    
                    table_html += f'<tr>'
                    table_html += f'<td>{game}</td>'
                    table_html += f'<td><b>{pick}</b></td>'
                    table_html += f'<td>{odds}</td>'
                    table_html += f'<td>{prob}</td>'
                    table_html += f'<td>{edge}</td>'
                    table_html += f'<td>{conf}</td>'
                    table_html += f'<td class="{ml_color}">{ml_st}</td>'
                    table_html += f'<td class="{rl_color}">{rl_st}</td>'
                    table_html += f'<td class="{ou_color}">{ou_st}</td>'
                    table_html += f'<td>{team_st}</td>'
                    table_html += f'<td>{f5_st}</td>'
                    table_html += '</tr>'
                except:
                    pass
    
    elif sport == "NBA":
        headers = ['GAME', 'PICK', 'ODDS', 'PROB', 'EDGE', 'CONF', 'ML', 'SPREAD']
        table_html += ''.join([f'<th>{h}</th>' for h in headers])
        table_html += '</tr></thead><tbody>'
        
        for row in data_rows:
            parts = row.split()
            if len(parts) >= 8:
                try:
                    game = ' '.join(parts[0:3])[:30]
                    pick = parts[3][:20] if len(parts) > 3 else ''
                    odds = parts[4] if len(parts) > 4 else ''
                    prob = parts[5] if len(parts) > 5 else ''
                    edge = parts[6] if len(parts) > 6 else ''
                    conf = parts[7] if len(parts) > 7 else ''
                    ml_st = parts[8] if len(parts) > 8 else ''
                    spread = parts[9] if len(parts) > 9 else ''
                    
                    ml_color = 'status-ok' if '[OK]' in ml_st else ('status-sus' if '[SUS]' in ml_st else 'status-no')
                    
                    table_html += f'<tr>'
                    table_html += f'<td>{game}</td>'
                    table_html += f'<td><b>{pick}</b></td>'
                    table_html += f'<td>{odds}</td>'
                    table_html += f'<td>{prob}</td>'
                    table_html += f'<td>{edge}</td>'
                    table_html += f'<td>{conf}</td>'
                    table_html += f'<td class="{ml_color}">{ml_st}</td>'
                    table_html += f'<td>{spread}</td>'
                    table_html += '</tr>'
                except:
                    pass
    
    table_html += '</tbody></table>'
    st.markdown(table_html, unsafe_allow_html=True)
    
    # Mostrar resumen
    for line in lines:
        if line.startswith('[GO]'):
            st.info(line)
        if line.startswith('ML ='):
            st.caption(line)

# ============================================
# MÉTRICAS RÁPIDAS
# ============================================
try:
    from betting_logger import get_betting_stats
    mlb_stats = get_betting_stats('MLB')
    nba_stats = get_betting_stats('NBA')
except:
    mlb_stats = None
    nba_stats = None

col_m1, col_m2, col_m3, col_m4 = st.columns(4)

with col_m1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("MLB Win Rate", f"{mlb_stats['win_rate']}%" if mlb_stats else "N/A")
    st.markdown('</div>', unsafe_allow_html=True)

with col_m2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("MLB Profit", f"${mlb_stats['total_profit']}" if mlb_stats else "N/A")
    st.markdown('</div>', unsafe_allow_html=True)

with col_m3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("MLB ROI", f"{mlb_stats['roi']}%" if mlb_stats else "N/A")
    st.markdown('</div>', unsafe_allow_html=True)

with col_m4:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Total Bets", mlb_stats['total_bets'] if mlb_stats else "N/A")
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# BOTONES PRINCIPALES
# ============================================
st.markdown('<h2 class="section-title">QUICK SCAN</h2>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("MLB TODAY", use_container_width=True, key="mlb_today"):
        with st.spinner("Scanning MLB games..."):
            output = run_script_and_parse("run_live_mlb.py")
            display_results_table(output, "MLB")

with col2:
    if st.button("MLB TOMORROW", use_container_width=True, key="mlb_tomorrow"):
        with st.spinner("Predicting MLB games..."):
            output = run_script_and_parse("run_tomorrow_mlb.py")
            display_results_table(output, "MLB")

with col3:
    if st.button("NBA TODAY", use_container_width=True, key="nba_today"):
        with st.spinner("Scanning NBA games..."):
            output = run_script_and_parse("run_live_nba.py")
            display_results_table(output, "NBA")

with col4:
    if st.button("NBA TOMORROW", use_container_width=True, key="nba_tomorrow"):
        with st.spinner("Predicting NBA games..."):
            output = run_script_and_parse("run_tomorrow_nba.py")
            display_results_table(output, "NBA")

# ============================================
# MONTE CARLO
# ============================================
st.markdown('<h2 class="section-title">MONTE CARLO SIMULATION</h2>', unsafe_allow_html=True)

from mlb_data_fetcher import get_today_mlb_games
games_df = get_today_mlb_games()

if len(games_df) > 0:
    valid_games = games_df[games_df['home_pitcher_name'].notna() & (games_df['home_pitcher_name'] != 'TBD')]
    
    if len(valid_games) > 0:
        game_options = {}
        for idx, row in valid_games.iterrows():
            label = f"{row['home_team']} vs {row['away_team']} | {row.get('home_pitcher_name', '')} vs {row.get('away_pitcher_name', '')}"
            game_options[label] = idx
        
        col_mc1, col_mc2, col_mc3 = st.columns([2, 1, 1])
        
        with col_mc1:
            selected_label = st.selectbox("Select game:", list(game_options.keys()), key="mc_game")
            selected_idx = game_options[selected_label]
        with col_mc2:
            n_sims = st.number_input("Simulations:", min_value=1000, max_value=50000, value=10000, step=1000, key="mc_sims")
        with col_mc3:
            st.write("")
            st.write("")
            run_mc = st.button("RUN MONTE CARLO", use_container_width=True, key="mc_run")
        
        if run_mc:
            with st.spinner(f"Running {n_sims:,} Monte Carlo simulations..."):
                row = valid_games.loc[selected_idx]
                
                from mlb_data_fetcher import get_pitcher_stats, get_bullpen_data, get_team_momentum
                from mlb_engine import MLBEngine
                from montecarlo_mlb import MonteCarloMLB
                
                mlb_engine = MLBEngine()
                mc = MonteCarloMLB()
                
                home_p_data = get_pitcher_stats(row.get('home_pitcher_id'))
                away_p_data = get_pitcher_stats(row.get('away_pitcher_id'))
                
                if not home_p_data:
                    home_p_data = mlb_engine.smart_pitcher_defaults(row.get('home_pitcher_name', ''))
                if not away_p_data:
                    away_p_data = mlb_engine.smart_pitcher_defaults(row.get('away_pitcher_name', ''))
                
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
                    'home_matchup': {'avg': 0.250, 'ops': 0.720, 'hr': 0, 'pa': 0, 'k_rate': 0.22},
                    'away_matchup': {'avg': 0.250, 'ops': 0.720, 'hr': 0, 'pa': 0, 'k_rate': 0.22},
                    'stadium': row.get('stadium', ''),
                    'divisional_game': row.get('is_divisional', False)
                }
                
                results = mc.simulate_game(game_data, n_sims)
                model_result = mlb_engine.evaluate_mlb_game(game_data, 2.0)
                model_prob = model_result.get('probability', 0.5)
                mc_prob = results['home_win_pct']
                diff = mc_prob - model_prob
                
                if abs(diff) > 0.12:
                    diff_color = "#e94560"
                    diff_label = "LARGE DISCREPANCY"
                elif abs(diff) > 0.07:
                    diff_color = "#f0a500"
                    diff_label = "MODERATE"
                elif abs(diff) > 0.03:
                    diff_color = "#4caf50"
                    diff_label = "SLIGHT"
                else:
                    diff_color = "#00ff88"
                    diff_label = "ALIGNED"
                
                st.success(f"Monte Carlo Complete - {n_sims:,} simulations")
                st.markdown(f"### {results['home_team']} vs {results['away_team']}")
                
                st.markdown(f"""
                <div class="comparison-box">
                    <b>MODEL vs MONTE CARLO:</b><br>
                    Model: {model_prob:.1%} | Monte Carlo: {mc_prob:.1%} | 
                    <span style="color:{diff_color}">Diff: {diff:+.1%} ({diff_label})</span>
                </div>
                """, unsafe_allow_html=True)
                
                col_r1, col_r2 = st.columns(2)
                
                with col_r1:
                    st.markdown('<div class="mc-result">', unsafe_allow_html=True)
                    st.markdown("#### WIN PROBABILITY")
                    st.metric(results['home_team'], f"{results['home_win_pct']:.1%}")
                    st.metric(results['away_team'], f"{results['away_win_pct']:.1%}")
                    st.markdown("#### RUNS (average)")
                    st.write(f"{results['home_team']}: {results['avg_home_runs']}")
                    st.write(f"{results['away_team']}: {results['avg_away_runs']}")
                    st.write(f"Total: {results['avg_total_runs']} (median: {results['median_total_runs']})")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col_r2:
                    st.markdown('<div class="mc-result">', unsafe_allow_html=True)
                    st.markdown("#### TOTALS")
                    st.write(f"Over 6.5: {results['over_6_5']:.1%}")
                    st.write(f"Over 7.5: {results['over_7_5']:.1%}")
                    st.write(f"Over 8.5: {results['over_8_5']:.1%}")
                    st.write(f"Over 9.5: {results['over_9_5']:.1%}")
                    st.markdown("#### RUNLINE")
                    st.write(f"{results['home_team']} -1.5: {results['home_runline_minus1_5']:.1%}")
                    st.write(f"{results['away_team']} -1.5: {results['away_runline_minus1_5']:.1%}")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    st.markdown("#### TEAM TOTALS")
                    st.write(f"{results['home_team']} Over 3.5: {results['home_over_3_5']:.1%}")
                    st.write(f"{results['home_team']} Over 4.5: {results['home_over_4_5']:.1%}")
                with col_t2:
                    st.markdown("#### &nbsp;")
                    st.write(f"{results['away_team']} Over 3.5: {results['away_over_3_5']:.1%}")
                    st.write(f"{results['away_team']} Over 4.5: {results['away_over_4_5']:.1%}")

# ============================================
# VALIDATE & RESULTS
# ============================================
st.markdown('<h2 class="section-title">VALIDATE & RESULTS</h2>', unsafe_allow_html=True)

col_v1, col_v2, col_v3 = st.columns(3)

with col_v1:
    if st.button("VALIDATE PENDING", use_container_width=True):
        from betting_logger import validate_pending_bets
        with st.spinner("Validating..."):
            validate_pending_bets()
            st.success("Done!")

with col_v2:
    if st.button("MLB RESULTS", use_container_width=True):
        from betting_results import show_results
        show_results()

with col_v3:
    if st.button("DEDUPLICATE LOG", use_container_width=True):
        from betting_logger import deduplicate_log
        deduplicate_log()
        st.success("Done!")

# ============================================
# FOOTER
# ============================================
st.markdown("""
<div class="footer">
    Sports Quant Engine V8 | Market Inefficiency Detection System<br>
    MLB + NBA + Monte Carlo Validation
</div>
""", unsafe_allow_html=True)