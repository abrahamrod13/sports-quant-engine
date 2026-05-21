import streamlit as st
import subprocess
import sys
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Sports Quant Engine V8", page_icon="MLB", layout="wide", initial_sidebar_state="collapsed")

# ============================================
# CSS
# ============================================
st.markdown("""
<style>
    .main-header { background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0f3460 100%); padding: 2rem; border-radius: 15px; text-align: center; margin-bottom: 2rem; border: 1px solid #e94560; }
    .main-header h1 { color: #e94560; font-size: 2.5rem; margin: 0; }
    .main-header p { color: #8b949e; font-size: 1.1rem; }
    .stButton > button { background: linear-gradient(135deg, #0d1117 0%, #161b22 100%); color: #e94560 !important; border: 1px solid #e94560; border-radius: 10px; padding: 0.8rem 1.5rem; font-weight: bold; transition: all 0.3s; height: 60px; text-transform: uppercase; letter-spacing: 1px; }
    .stButton > button:hover { background: linear-gradient(135deg, #e94560 0%, #c23152 100%); color: white !important; border-color: #e94560; transform: scale(1.02); box-shadow: 0 0 15px rgba(233,69,96,0.3); }
    .metric-card { background: #161b22; padding: 1.5rem; border-radius: 10px; border: 1px solid #30363d; text-align: center; }
    .section-title { color: #e94560; border-bottom: 2px solid #e94560; padding-bottom: 0.5rem; margin-top: 2rem; text-transform: uppercase; letter-spacing: 2px; font-size: 1.1rem; }
    .footer { text-align: center; color: #484f58; margin-top: 3rem; padding: 1rem; border-top: 1px solid #21262d; }
    .results-table { width: 100%; border-collapse: collapse; margin: 0.5rem 0; font-size: 0.9rem; }
    .results-table th { background: #1a1a2e; color: #e94560; padding: 0.7rem; text-transform: uppercase; letter-spacing: 1px; border-bottom: 2px solid #e94560; }
    .results-table td { background: #161b22; color: #c9d1d9; padding: 0.5rem; border-bottom: 1px solid #21262d; text-align: center; }
    .results-table tr:hover td { background: #1a2332; }
    .full-analysis { background: #0f3460; padding: 2rem; border-radius: 15px; margin: 2rem 0; border: 1px solid #30363d; }
    .betting-box { background: #161b22; padding: 1.5rem; border-radius: 10px; margin: 1rem 0; border: 1px solid #30363d; }
    .pick-highlight { color: #58a6ff; font-weight: bold; }
    .status-ok { color: #3fb950; font-weight: bold; }
    .status-sus { color: #d2991d; font-weight: bold; }
    .status-no { color: #f85149; }
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
# FUNCIONES
# ============================================
def run_script_and_parse(script_name):
    output_text = ""
    process = subprocess.Popen([sys.executable, script_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in process.stdout: output_text += line
    process.wait()
    return output_text

def parse_mlb_data(output_text):
    """Parsea output pipe | a lista de diccionarios"""
    games = []
    for line in output_text.strip().split('\n'):
        if line.startswith('MLB|'):
            parts = line.split('|')
            if len(parts) >= 13:
                games.append({
                    'home': parts[1], 'away': parts[2], 'pick': parts[3],
                    'odds': parts[4], 'prob': parts[5], 'edge': parts[6],
                    'conf': parts[7], 'ml': parts[8], 'rl': parts[9],
                    'ou': parts[10], 'team': parts[11], 'f5': parts[12]
                })
    return games

# ============================================
# MÉTRICAS
# ============================================
try:
    from betting_logger import get_betting_stats
    mlb_stats = get_betting_stats('MLB')
except: mlb_stats = None

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Win Rate", f"{mlb_stats['win_rate']}%" if mlb_stats else "N/A")
    st.markdown('</div>', unsafe_allow_html=True)
with col_m2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Profit", f"${mlb_stats['total_profit']}" if mlb_stats else "N/A")
    st.markdown('</div>', unsafe_allow_html=True)
with col_m3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("ROI", f"{mlb_stats['roi']}%" if mlb_stats else "N/A")
    st.markdown('</div>', unsafe_allow_html=True)
with col_m4:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Bets", mlb_stats['total_bets'] if mlb_stats else "N/A")
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# BOTONES PRINCIPALES
# ============================================
st.markdown('<h2 class="section-title">QUICK SCAN</h2>', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)

if 'mlb_data' not in st.session_state: st.session_state.mlb_data = None
if 'nba_data' not in st.session_state: st.session_state.nba_data = None

with col1:
    if st.button("MLB TODAY", use_container_width=True, key="mlb_today"):
        with st.spinner("Scanning MLB..."):
            output = run_script_and_parse("run_live_mlb.py")
            st.session_state.mlb_data = parse_mlb_data(output)

with col2:
    if st.button("MLB TOMORROW", use_container_width=True, key="mlb_tomorrow"):
        with st.spinner("Predicting MLB..."):
            output = run_script_and_parse("run_tomorrow_mlb.py")
            st.session_state.mlb_data = parse_mlb_data(output)

with col3:
    if st.button("NBA TODAY", use_container_width=True, key="nba_today"):
        with st.spinner("Scanning NBA..."): st.info("NBA available in full version")

with col4:
    if st.button("NBA TOMORROW", use_container_width=True, key="nba_tomorrow"):
        with st.spinner("Predicting NBA..."): st.info("NBA available in full version")

# ============================================
# TABLA COMPACTA (solo hasta CONF)
# ============================================
if st.session_state.mlb_data:
    st.markdown("---")
    st.markdown(f"### MLB SCAN RESULTS - {len(st.session_state.mlb_data)} games")
    
    table_html = '<table class="results-table"><thead><tr>'
    for h in ['HOME', 'AWAY', 'PICK', 'ODDS', 'PROB', 'EDGE', 'CONF']:
        table_html += f'<th>{h}</th>'
    table_html += '</tr></thead><tbody>'
    
    for g in st.session_state.mlb_data:
        table_html += f'<tr><td>{g["home"]}</td><td>{g["away"]}</td><td class="pick-highlight">{g["pick"]}</td><td>{g["odds"]}</td><td>{g["prob"]}</td><td>{g["edge"]}</td><td>{g["conf"]}</td></tr>'
    
    table_html += '</tbody></table>'
    st.markdown(table_html, unsafe_allow_html=True)
    
    # ============================================
    # SELECTOR PARA FULL ANALYSIS
    # ============================================
    st.markdown("---")
    game_options = [f"{g['home']} vs {g['away']}" for g in st.session_state.mlb_data]
    selected = st.selectbox("Select game for FULL ANALYSIS:", game_options)
    
    if st.button("SHOW FULL ANALYSIS", use_container_width=True):
        idx = game_options.index(selected)
        g = st.session_state.mlb_data[idx]
        
        st.markdown(f"""
        <div class="full-analysis">
            <h2>FULL ANALYSIS: {g['home']} vs {g['away']}</h2>
            
            <h3>MONEYLINE</h3>
            <p><b>Pick:</b> {g['pick']} | <b>Odds:</b> {g['odds']}</p>
            <p><b>Probability:</b> {g['prob']} | <b>Edge:</b> {g['edge']} | <b>Confidence:</b> {g['conf']}</p>
            
            <div class="betting-box">
                <h3>BETTING OPTIONS</h3>
                <p>Moneyline: {g['ml']} | Runline: {g['rl']} | Over/Under: {g['ou']} | Team Total: {g['team']} | First 5: {g['f5']}</p>
            </div>
            
            <h3>LEGEND</h3>
            <p><span class="status-ok">[OK]</span> = Approved | <span class="status-sus">[SUS]</span> = Suspect (validate MC) | <span style="color:#f85149">[X]</span> = No edge</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Monte Carlo directo
        if st.button("RUN MONTE CARLO FOR THIS GAME", use_container_width=True):
            with st.spinner("Running 10,000 simulations..."):
                from mlb_data_fetcher import get_today_mlb_games, get_pitcher_stats, get_bullpen_data, get_team_momentum
                from mlb_engine import MLBEngine
                from montecarlo_mlb import MonteCarloMLB
                
                games_df = get_today_mlb_games()
                mc = MonteCarloMLB()
                mlb_engine = MLBEngine()
                
                # Buscar el juego
                game_row = None
                for _, row in games_df.iterrows():
                    if row['home_team'] == g['home'] and row['away_team'] == g['away']:
                        game_row = row
                        break
                
                if game_row is not None:
                    home_p = get_pitcher_stats(game_row.get('home_pitcher_id'))
                    away_p = get_pitcher_stats(game_row.get('away_pitcher_id'))
                    if not home_p: home_p = mlb_engine.smart_pitcher_defaults(game_row.get('home_pitcher_name', ''))
                    if not away_p: away_p = mlb_engine.smart_pitcher_defaults(game_row.get('away_pitcher_name', ''))
                    
                    game_data = {
                        'home_team': g['home'], 'away_team': g['away'],
                        'home_win_pct': game_row.get('home_win_pct', 0.5),
                        'away_win_pct': game_row.get('away_win_pct', 0.5),
                        'home_pitcher': home_p, 'away_pitcher': away_p,
                        'home_bullpen': get_bullpen_data(game_row.get('home_team_id')),
                        'away_bullpen': get_bullpen_data(game_row.get('away_team_id')),
                        'home_momentum': get_team_momentum(game_row.get('home_team_id')),
                        'away_momentum': get_team_momentum(game_row.get('away_team_id')),
                        'home_matchup': {'avg': 0.250, 'ops': 0.720, 'hr': 0, 'pa': 0, 'k_rate': 0.22},
                        'away_matchup': {'avg': 0.250, 'ops': 0.720, 'hr': 0, 'pa': 0, 'k_rate': 0.22},
                        'stadium': game_row.get('stadium', ''), 'divisional_game': game_row.get('is_divisional', False)
                    }
                    
                    results = mc.simulate_game(game_data, 10000)
                    model_result = mlb_engine.evaluate_mlb_game(game_data, 2.0)
                    model_prob = model_result.get('probability', 0.5)
                    mc_prob = results['home_win_pct']
                    diff = mc_prob - model_prob
                    
                    if abs(diff) > 0.12: diff_color, diff_label = "#f85149", "LARGE"
                    elif abs(diff) > 0.07: diff_color, diff_label = "#d2991d", "MODERATE"
                    elif abs(diff) > 0.03: diff_color, diff_label = "#3fb950", "SLIGHT"
                    else: diff_color, diff_label = "#58a6ff", "ALIGNED"
                    
                    st.markdown(f"""
                    <div class="comparison-box">
                        <b>MODEL vs MONTE CARLO:</b><br>
                        Model: {model_prob:.1%} | Monte Carlo: {mc_prob:.1%} | 
                        <span style="color:{diff_color}">Diff: {diff:+.1%} ({diff_label})</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col_mc1, col_mc2 = st.columns(2)
                    with col_mc1:
                        st.metric(f"{results['home_team']} Win", f"{results['home_win_pct']:.1%}")
                        st.metric(f"{results['away_team']} Win", f"{results['away_win_pct']:.1%}")
                    with col_mc2:
                        st.write(f"Over 7.5: {results['over_7_5']:.1%}")
                        st.write(f"Over 8.5: {results['over_8_5']:.1%}")
                        st.write(f"{results['home_team']} -1.5: {results['home_runline_minus1_5']:.1%}")

# ============================================
# VALIDATE
# ============================================
st.markdown('<h2 class="section-title">VALIDATE & RESULTS</h2>', unsafe_allow_html=True)
col_v1, col_v2 = st.columns(2)
with col_v1:
    if st.button("VALIDATE PENDING", use_container_width=True):
        from betting_logger import validate_pending_bets
        validate_pending_bets()
        st.success("Done!")
with col_v2:
    if st.button("MLB RESULTS", use_container_width=True):
        from betting_results import show_results
        show_results()

st.markdown("""
<div class="footer">
    Sports Quant Engine V8 | Market Inefficiency Detection System<br>
    MLB + NBA + Monte Carlo Validation
</div>
""", unsafe_allow_html=True)