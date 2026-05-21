import streamlit as st
import subprocess
import sys
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Sports Quant Engine V8", page_icon="MLB", layout="wide", initial_sidebar_state="collapsed")

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
    .mc-result { background: #0f3460; padding: 1.5rem; border-radius: 10px; margin: 1rem 0; border: 1px solid #30363d; }
    .comparison-box { background: #161b22; padding: 1rem; border-radius: 10px; margin: 1rem 0; border: 1px solid #30363d; }
    .results-table { width: 100%; border-collapse: collapse; margin: 0.5rem 0; font-size: 0.9rem; }
    .results-table th { background: #1a1a2e; color: #e94560; padding: 0.7rem; text-transform: uppercase; letter-spacing: 1px; border-bottom: 2px solid #e94560; }
    .results-table td { background: #161b22; color: #c9d1d9; padding: 0.5rem; border-bottom: 1px solid #21262d; text-align: center; }
    .results-table tr:hover td { background: #1a2332; }
    .pick-highlight { color: #58a6ff; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>MLB NBA SPORTS QUANT ENGINE V8</h1>
    <p>Market Inefficiency Detection System | Monte Carlo Validation</p>
</div>
""", unsafe_allow_html=True)

def run_script_and_parse(script_name):
    output_text = ""
    process = subprocess.Popen([sys.executable, script_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in process.stdout: output_text += line
    process.wait()
    return output_text

def parse_mlb_output(output_text):
    games = []
    metadata = {}
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
        elif line.startswith('DATA|'):
            parts = line.split('|')
            if len(parts) >= 22:
                key = f"{parts[1]}|{parts[2]}"
                metadata[key] = {
                    'home_pitcher': parts[3], 'home_era': parts[4], 'home_whip': parts[5], 'home_k9': parts[6],
                    'away_pitcher': parts[7], 'away_era': parts[8], 'away_whip': parts[9], 'away_k9': parts[10],
                    'stadium': parts[11], 'divisional': parts[12] == 'True',
                    'home_win': parts[13], 'away_win': parts[14],
                    'home_bullpen_era': parts[15], 'away_bullpen_era': parts[16],
                    'home_bullpen_fatigue': parts[17], 'away_bullpen_fatigue': parts[18],
                    'home_ops': parts[19], 'away_ops': parts[20],
                    'home_run_diff': parts[21], 'away_run_diff': parts[22] if len(parts) > 22 else '0'
                }
    return games, metadata

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

st.markdown('<h2 class="section-title">QUICK SCAN</h2>', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)

if 'mlb_data' not in st.session_state: st.session_state.mlb_data = None
if 'mlb_metadata' not in st.session_state: st.session_state.mlb_metadata = None

with col1:
    if st.button("MLB TODAY", use_container_width=True, key="mlb_today"):
        with st.spinner("Scanning MLB..."):
            output = run_script_and_parse("run_live_mlb.py")
            games, metadata = parse_mlb_output(output)
            st.session_state.mlb_data = games
            st.session_state.mlb_metadata = metadata

with col2:
    if st.button("MLB TOMORROW", use_container_width=True, key="mlb_tomorrow"):
        with st.spinner("Predicting MLB..."):
            output = run_script_and_parse("run_tomorrow_mlb.py")
            games, metadata = parse_mlb_output(output)
            st.session_state.mlb_data = games
            st.session_state.mlb_metadata = metadata

with col3:
    if st.button("NBA TODAY", use_container_width=True, key="nba_today"):
        st.info("NBA in development")

with col4:
    if st.button("NBA TOMORROW", use_container_width=True, key="nba_tomorrow"):
        st.info("NBA in development")

# ============================================
# TABLA COMPACTA
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
    # SELECTOR FULL ANALYSIS
    # ============================================
    st.markdown("---")
    game_options = [f"{g['home']} vs {g['away']}" for g in st.session_state.mlb_data]
    selected = st.selectbox("Select game for FULL ANALYSIS:", game_options)
    
    if st.button("SHOW FULL ANALYSIS", use_container_width=True):
        idx = game_options.index(selected)
        g = st.session_state.mlb_data[idx]
        meta = st.session_state.mlb_metadata.get(f"{g['home']}|{g['away']}", {})
        
        st.markdown("---")
        st.markdown(f"## FULL ANALYSIS: {g['home']} vs {g['away']}")
        
        # PITCHERS (si hay metadata)
        if meta:
            st.markdown('<div class="mc-result">', unsafe_allow_html=True)
            st.markdown("#### PITCHERS")
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.markdown(f"**{g['home']}:** {meta['home_pitcher']}")
                st.write(f"ERA: {meta['home_era']} | WHIP: {meta['home_whip']} | K9: {meta['home_k9']}")
            with col_p2:
                st.markdown(f"**{g['away']}:** {meta['away_pitcher']}")
                st.write(f"ERA: {meta['away_era']} | WHIP: {meta['away_whip']} | K9: {meta['away_k9']}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # GAME INFO
            st.markdown('<div class="mc-result">', unsafe_allow_html=True)
            st.markdown("#### GAME INFO")
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                st.metric("Stadium", meta['stadium'])
                st.write(f"Divisional: {'Yes' if meta['divisional'] else 'No'}")
            with col_s2:
                st.metric(f"{g['home']} Record", meta['home_win'])
                st.metric(f"{g['away']} Record", meta['away_win'])
            with col_s3:
                st.write(f"Home Bullpen ERA: {meta['home_bullpen_era']} ({meta['home_bullpen_fatigue']})")
                st.write(f"Away Bullpen ERA: {meta['away_bullpen_era']} ({meta['away_bullpen_fatigue']})")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # MOMENTUM
            st.markdown('<div class="mc-result">', unsafe_allow_html=True)
            st.markdown("#### MOMENTUM")
            col_mo1, col_mo2 = st.columns(2)
            with col_mo1:
                st.write(f"{g['home']} OPS: {meta['home_ops']} | Run Diff: {meta['home_run_diff']}")
            with col_mo2:
                st.write(f"{g['away']} OPS: {meta['away_ops']} | Run Diff: {meta['away_run_diff']}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # MONEYLINE
        st.markdown('<div class="mc-result">', unsafe_allow_html=True)
        st.markdown("#### MONEYLINE")
        col_ml1, col_ml2, col_ml3, col_ml4, col_ml5 = st.columns(5)
        with col_ml1: st.metric("Pick", g['pick'])
        with col_ml2: st.metric("Odds", g['odds'])
        with col_ml3: st.metric("Probability", g['prob'])
        with col_ml4: st.metric("Edge", g['edge'])
        with col_ml5: st.metric("Confidence", g['conf'])
        st.markdown('</div>', unsafe_allow_html=True)
        
        # BETTING OPTIONS
        st.markdown('<div class="mc-result">', unsafe_allow_html=True)
        st.markdown("#### BETTING OPTIONS")
        col_b1, col_b2, col_b3, col_b4, col_b5 = st.columns(5)
        with col_b1:
            if "[OK]" in g['ml']: st.success(f"Moneyline: {g['ml']}")
            elif "[SUS]" in g['ml']: st.warning(f"Moneyline: {g['ml']}")
            else: st.error(f"Moneyline: {g['ml']}")
        with col_b2:
            if "[OK]" in g['rl']: st.success(f"Runline: {g['rl']}")
            elif "[?]" in g['rl']: st.warning(f"Runline: {g['rl']}")
            else: st.error(f"Runline: {g['rl']}")
        with col_b3:
            if "[OK]" in g['ou']: st.success(f"Over/Under: {g['ou']}")
            elif "[?]" in g['ou']: st.warning(f"Over/Under: {g['ou']}")
            else: st.error(f"Over/Under: {g['ou']}")
        with col_b4:
            if "[OK]" in g['team']: st.success(f"Team Total: {g['team']}")
            elif "[?]" in g['team']: st.warning(f"Team Total: {g['team']}")
            else: st.error(f"Team Total: {g['team']}")
        with col_b5:
            if "[OK]" in g['f5']: st.success(f"First 5: {g['f5']}")
            elif "[?]" in g['f5']: st.warning(f"First 5: {g['f5']}")
            else: st.error(f"First 5: {g['f5']}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.caption("[OK] = Approved | [SUS] = Suspect (validate MC) | [X] = No edge | [?] = Marginal")
        
        # MONTE CARLO DIRECT BTN
        if st.button("RUN MONTE CARLO FOR THIS GAME", use_container_width=True):
            with st.spinner("Running 10,000 Monte Carlo simulations..."):
                from mlb_data_fetcher import get_today_mlb_games, get_pitcher_stats, get_bullpen_data, get_team_momentum
                from mlb_engine import MLBEngine
                from montecarlo_mlb import MonteCarloMLB
                
                games_df = get_today_mlb_games()
                mc = MonteCarloMLB()
                mlb_engine = MLBEngine()
                
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
                        'home_win_pct': game_row.get('home_win_pct', 0.5), 'away_win_pct': game_row.get('away_win_pct', 0.5),
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
                        st.metric("Over 7.5", f"{results['over_7_5']:.1%}")
                        st.metric("Over 8.5", f"{results['over_8_5']:.1%}")
                        st.metric(f"{results['home_team']} -1.5", f"{results['home_runline_minus1_5']:.1%}")

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