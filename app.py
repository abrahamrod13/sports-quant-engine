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
    .stButton > button { background: linear-gradient(135deg, #0d1117 0%, #161b22 100%); color: #e94560 !important; border: 1px solid #e94560; border-radius: 10px; padding: 0.8rem 1.5rem; font-weight: bold; transition: all 0.3s; height: 60px; text-transform: uppercase; letter-spacing: 1px; width: 100%; }
    .stButton > button:hover { background: linear-gradient(135deg, #e94560 0%, #c23152 100%); color: white !important; border-color: #e94560; transform: scale(1.02); box-shadow: 0 0 15px rgba(233,69,96,0.3); }
    .metric-btn { background: linear-gradient(135deg, #0d1117 0%, #161b22 100%); border: 1px solid #30363d; border-radius: 10px; padding: 1rem; text-align: center; color: #c9d1d9; height: 80px; display: flex; flex-direction: column; justify-content: center; }
    .metric-btn .label { color: #8b949e; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px; }
    .metric-btn .value { color: #e94560; font-size: 1.5rem; font-weight: bold; }
    .section-title { color: #e94560; border-bottom: 2px solid #e94560; padding-bottom: 0.5rem; margin-top: 2rem; text-transform: uppercase; letter-spacing: 2px; font-size: 1.1rem; }
    .footer { text-align: center; color: #484f58; margin-top: 3rem; padding: 1rem; border-top: 1px solid #21262d; }
    .mc-result { background: #0f3460; padding: 1.5rem; border-radius: 10px; margin: 1rem 0; border: 1px solid #30363d; }
    .comparison-box { background: #161b22; padding: 1rem; border-radius: 10px; margin: 1rem 0; border: 1px solid #30363d; }
    .bayesian-box { background: #1a2332; padding: 1rem; border-radius: 10px; margin: 1rem 0; border: 1px solid #58a6ff; }
    .results-table { width: 100%; border-collapse: collapse; margin: 0.5rem 0; font-size: 0.9rem; }
    .results-table th { background: #1a1a2e; color: #e94560; padding: 0.7rem; text-transform: uppercase; letter-spacing: 1px; border-bottom: 2px solid #e94560; }
    .results-table td { background: #161b22; color: #c9d1d9; padding: 0.5rem; border-bottom: 1px solid #21262d; text-align: center; }
    .results-table tr:hover td { background: #1a2332; }
    .pick-highlight { color: #58a6ff; font-weight: bold; }
    .too-close { color: #f0a500; font-style: italic; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>MLB NBA SPORTS QUANT ENGINE V8</h1>
    <p>Market Inefficiency Detection System | Monte Carlo + Bayesian + Statcast + Calendar</p>
</div>
""", unsafe_allow_html=True)

def run_script_and_parse(script_name):
    output_text = ""
    process = subprocess.Popen([sys.executable, script_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in process.stdout: output_text += line
    process.wait()
    return output_text

def parse_mlb_output(output_text):
    games, metadata = [], {}
    for line in output_text.strip().split('\n'):
        if line.startswith('MLB|') and 'HOME' not in line:
            parts = line.split('|')
            if len(parts) >= 13:
                games.append({'home': parts[1], 'away': parts[2], 'pick': parts[3], 'odds': parts[4], 'prob': parts[5], 'edge': parts[6], 'conf': parts[7], 'ml': parts[8], 'rl': parts[9], 'ou': parts[10], 'team': parts[11], 'f5': parts[12]})
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
                    'home_run_diff': parts[21], 'away_run_diff': parts[22] if len(parts) > 22 else '0',
                    'home_injuries': parts[23] if len(parts) > 23 else 'None',
                    'away_injuries': parts[24] if len(parts) > 24 else 'None'
                }
    return games, metadata

def get_winner(home, away, prob_str):
    try:
        prob_val = float(prob_str.rstrip('%'))
        if prob_val >= 60: return home, prob_val
        elif prob_val <= 40: return away, 100 - prob_val
        else: return "TOO CLOSE", prob_val
    except: return "TOO CLOSE", 50

def bayesian_analysis(home_team, away_team, model_prob, confidence):
    log_file = 'data/betting_log.csv'
    hist_win_rate, historical_games = None, 0
    if os.path.exists(log_file):
        try:
            df = pd.read_csv(log_file)
            completed = df[(df['result'] != 'PENDING') & (df['sport'] == 'MLB')]
            matchups = completed[(completed['match'].str.contains(home_team[:10], na=False)) & (completed['match'].str.contains(away_team[:10], na=False))]
            if len(matchups) > 0:
                wins = len(matchups[matchups['result'] == 'WIN'])
                hist_win_rate = wins / len(matchups)
                historical_games = len(matchups)
        except: pass
    if hist_win_rate: posterior = round((float(model_prob.rstrip('%'))/100) * 0.7 + hist_win_rate * 0.3, 4)
    else: posterior = float(model_prob.rstrip('%'))/100
    return {'bayesian_prob': posterior, 'model_prob': float(model_prob.rstrip('%'))/100, 'prior_strength': 'HIGH' if historical_games > 5 else ('MEDIUM' if historical_games > 0 else 'LOW'), 'historical_games': historical_games}

# MÉTRICAS
try:
    from betting_logger import get_betting_stats
    mlb_stats = get_betting_stats('MLB')
except: mlb_stats = None

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.markdown(f"""<div class="metric-btn"><span class="label">WIN RATE</span><span class="value">{mlb_stats['win_rate']}%</span></div>""" if mlb_stats else """<div class="metric-btn"><span class="label">WIN RATE</span><span class="value">N/A</span></div>""", unsafe_allow_html=True)
with col_m2:
    st.markdown(f"""<div class="metric-btn"><span class="label">PROFIT</span><span class="value">${mlb_stats['total_profit']}</span></div>""" if mlb_stats else """<div class="metric-btn"><span class="label">PROFIT</span><span class="value">N/A</span></div>""", unsafe_allow_html=True)
with col_m3:
    st.markdown(f"""<div class="metric-btn"><span class="label">ROI</span><span class="value">{mlb_stats['roi']}%</span></div>""" if mlb_stats else """<div class="metric-btn"><span class="label">ROI</span><span class="value">N/A</span></div>""", unsafe_allow_html=True)
with col_m4:
    st.markdown(f"""<div class="metric-btn"><span class="label">TOTAL BETS</span><span class="value">{mlb_stats['total_bets']}</span></div>""" if mlb_stats else """<div class="metric-btn"><span class="label">TOTAL BETS</span><span class="value">N/A</span></div>""", unsafe_allow_html=True)

# WINNER PREDICTION ACCURACY
st.markdown('<h2 class="section-title">WINNER PREDICTION ACCURACY</h2>', unsafe_allow_html=True)
try:
    from prediction_tracker import get_winner_stats, validate_winner_predictions
    validate_winner_predictions()
    winner_stats = get_winner_stats()
    if winner_stats:
        col_w1, col_w2, col_w3 = st.columns(3)
        with col_w1: st.metric("Total Predictions", winner_stats['total'])
        with col_w2: st.metric("Correct", winner_stats['correct'])
        with col_w3: st.metric("Accuracy", f"{winner_stats['accuracy']}%")
    else:
        st.info("No winner predictions yet.")
except:
    st.info("Prediction tracker initializing...")

# WINNER PREDICTION CALENDAR
st.markdown('<h2 class="section-title">PREDICTION CALENDAR</h2>', unsafe_allow_html=True)
try:
    tracker_file = 'data/winner_predictions.csv'
    if os.path.exists(tracker_file):
        df = pd.read_csv(tracker_file)
        if len(df) > 0:
            dates = sorted(df['date'].unique(), reverse=True)
            selected_date = st.selectbox("Select date:", dates, key="cal_date")
            day_df = df[df['date'] == selected_date]
            if len(day_df) > 0:
                st.markdown(f"### {selected_date} - {len(day_df)} predictions")
                table_html = '<table class="results-table"><thead><tr>'
                for h in ['GAME', 'PREDICTED', 'RESULT', 'STATUS']:
                    table_html += f'<th>{h}</th>'
                table_html += '</tr></thead><tbody>'
                correct, total_predicted = 0, 0
                for _, row in day_df.iterrows():
                    pred = row['predicted_winner']
                    actual = row.get('actual_winner', '')
                    result = row.get('correct', '')
                    parts = row['match'].split(' vs ')
                    home = parts[0] if len(parts) > 0 else ''
                    away = parts[1] if len(parts) > 1 else ''
                    if result == 'YES':
                        status = '✅ WIN'
                        correct += 1
                        total_predicted += 1
                    elif result == 'NO':
                        status = '❌ LOSS'
                        total_predicted += 1
                    elif result == 'SKIP':
                        status = '⏭️ SKIP'
                    else:
                        status = '⏳ PENDING'
                        if row['predicted_winner'] != 'TOO CLOSE':
                            total_predicted += 1
                    table_html += f'<tr><td>{home} vs {away}</td><td class="pick-highlight">{pred}</td><td>{actual}</td><td>{status}</td></tr>'
                table_html += '</tbody></table>'
                st.markdown(table_html, unsafe_allow_html=True)
                if total_predicted > 0:
                    day_acc = correct / total_predicted * 100
                    st.metric(f"Day Accuracy", f"{correct}/{total_predicted} ({day_acc:.1f}%)")
        else:
            st.info("No predictions yet. Run MLB Today/Tomorrow first.")
    else:
        st.info("Prediction tracker initializing...")
except Exception as e:
    st.info(f"Calendar loading...")

# BOTONES
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
            for g in games:
                winner, _ = get_winner(g['home'], g['away'], g['prob'])
                if winner != "TOO CLOSE":
                    try:
                        from prediction_tracker import save_winner_prediction
                        save_winner_prediction(f"{g['home']} vs {g['away']}", winner, float(g['prob'].rstrip('%')))
                    except: pass

with col2:
    if st.button("MLB TOMORROW", use_container_width=True, key="mlb_tomorrow"):
        with st.spinner("Predicting MLB..."):
            output = run_script_and_parse("run_tomorrow_mlb.py")
            games, metadata = parse_mlb_output(output)
            st.session_state.mlb_data = games
            st.session_state.mlb_metadata = metadata
            for g in games:
                winner, _ = get_winner(g['home'], g['away'], g['prob'])
                if winner != "TOO CLOSE":
                    try:
                        from prediction_tracker import save_winner_prediction
                        save_winner_prediction(f"{g['home']} vs {g['away']}", winner, float(g['prob'].rstrip('%')))
                    except: pass

with col3:
    if st.button("NBA TODAY", use_container_width=True, key="nba_today"):
        st.info("NBA engine loading...")

with col4:
    if st.button("NBA TOMORROW", use_container_width=True, key="nba_tomorrow"):
        st.info("NBA engine loading...")

# TABLA MLB
if st.session_state.mlb_data:
    st.markdown("---")
    st.markdown(f"### MLB SCAN RESULTS - {len(st.session_state.mlb_data)} games")
    table_html = '<table class="results-table"><thead><tr>'
    for h in ['HOME', 'AWAY', 'WINNER', 'PROB', 'EDGE', 'CONF']:
        table_html += f'<th>{h}</th>'
    table_html += '</tr></thead><tbody>'
    for g in st.session_state.mlb_data:
        winner, winner_prob = get_winner(g['home'], g['away'], g['prob'])
        winner_class = 'pick-highlight' if winner != "TOO CLOSE" else 'too-close'
        prob_display = f"{winner_prob:.1f}%" if winner != "TOO CLOSE" else g['prob']
        table_html += f'<tr><td>{g["home"]}</td><td>{g["away"]}</td><td class="{winner_class}">{winner}</td><td>{prob_display}</td><td>{g["edge"]}</td><td>{g["conf"]}</td></tr>'
    table_html += '</tbody></table>'
    st.markdown(table_html, unsafe_allow_html=True)
    
    game_options = [f"{g['home']} vs {g['away']}" for g in st.session_state.mlb_data]
    selected = st.selectbox("Select game for FULL ANALYSIS:", game_options, key="mlb_select")
    if st.button("SHOW FULL ANALYSIS", use_container_width=True, key="mlb_full"):
        idx = game_options.index(selected)
        g = st.session_state.mlb_data[idx]
        meta = st.session_state.mlb_metadata.get(f"{g['home']}|{g['away']}", {})
        st.markdown(f"## FULL ANALYSIS: {g['home']} vs {g['away']}")
        winner, winner_prob = get_winner(g['home'], g['away'], g['prob'])
        if winner == "TOO CLOSE": st.markdown(f"### PREDICTION: TOO CLOSE TO CALL ({g['prob']})")
        else: st.markdown(f"### PREDICTED WINNER: {winner} ({winner_prob:.1f}%)")
        if meta:
            st.markdown('<div class="mc-result">', unsafe_allow_html=True)
            st.markdown("#### PITCHERS")
            col_p1, col_p2 = st.columns(2)
            with col_p1: st.markdown(f"**{g['home']}:** {meta['home_pitcher']}"); st.write(f"ERA: {meta['home_era']} | WHIP: {meta['home_whip']} | K9: {meta['home_k9']}")
            with col_p2: st.markdown(f"**{g['away']}:** {meta['away_pitcher']}"); st.write(f"ERA: {meta['away_era']} | WHIP: {meta['away_whip']} | K9: {meta['away_k9']}")
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<div class="mc-result">', unsafe_allow_html=True)
            st.markdown("#### GAME INFO")
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1: st.metric("Stadium", meta['stadium']); st.write(f"Divisional: {'Yes' if meta['divisional'] else 'No'}")
            with col_s2: st.metric(f"{g['home']} Record", meta['home_win']); st.metric(f"{g['away']} Record", meta['away_win'])
            with col_s3: st.write(f"Home Bullpen: {meta['home_bullpen_era']} ERA ({meta['home_bullpen_fatigue']})"); st.write(f"Away Bullpen: {meta['away_bullpen_era']} ERA ({meta['away_bullpen_fatigue']})")
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<div class="mc-result">', unsafe_allow_html=True)
            st.markdown("#### MOMENTUM")
            col_mo1, col_mo2 = st.columns(2)
            with col_mo1: st.write(f"{g['home']} OPS: {meta['home_ops']} | Run Diff: {meta['home_run_diff']}")
            with col_mo2: st.write(f"{g['away']} OPS: {meta['away_ops']} | Run Diff: {meta['away_run_diff']}")
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<div class="mc-result">', unsafe_allow_html=True)
            st.markdown("#### INJURIES")
            col_i1, col_i2 = st.columns(2)
            with col_i1: st.markdown(f"**{g['home']}:**"); st.write(meta.get('home_injuries', 'None').replace(';', '\n'))
            with col_i2: st.markdown(f"**{g['away']}:**"); st.write(meta.get('away_injuries', 'None').replace(';', '\n'))
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="mc-result">', unsafe_allow_html=True)
        st.markdown("#### BETTING VALUE")
        col_b1, col_b2, col_b3, col_b4, col_b5 = st.columns(5)
        with col_b1:
            if "[OK]" in g['ml']: st.success(f"ML: {g['ml']}")
            elif "[SUS]" in g['ml']: st.warning(f"ML: {g['ml']}")
            else: st.error(f"ML: {g['ml']}")
        with col_b2:
            if "[OK]" in g['rl']: st.success(f"RL: {g['rl']}")
            elif "[?]" in g['rl']: st.warning(f"RL: {g['rl']}")
            else: st.error(f"RL: {g['rl']}")
        with col_b3:
            if "[OK]" in g['ou']: st.success(f"O/U: {g['ou']}")
            elif "[?]" in g['ou']: st.warning(f"O/U: {g['ou']}")
            else: st.error(f"O/U: {g['ou']}")
        with col_b4:
            if "[OK]" in g['team']: st.success(f"Team: {g['team']}")
            elif "[?]" in g['team']: st.warning(f"Team: {g['team']}")
            else: st.error(f"Team: {g['team']}")
        with col_b5:
            if "[OK]" in g['f5']: st.success(f"F5: {g['f5']}")
            elif "[?]" in g['f5']: st.warning(f"F5: {g['f5']}")
            else: st.error(f"F5: {g['f5']}")
        st.markdown('</div>', unsafe_allow_html=True)
        try:
            bayes = bayesian_analysis(g['home'], g['away'], g['prob'], g['conf'])
            st.markdown(f"""<div class="bayesian-box"><b>BAYESIAN UPDATE:</b> {bayes['bayesian_prob']:.1%} | Prior: {bayes['prior_strength']} ({bayes['historical_games']} historical games)</div>""", unsafe_allow_html=True)
        except: pass

# MONTE CARLO
st.markdown('<h2 class="section-title">MONTE CARLO SIMULATION</h2>', unsafe_allow_html=True)
try:
    from mlb_data_fetcher import get_today_mlb_games
    games_df = get_today_mlb_games()
    if len(games_df) > 0:
        valid_games = games_df[games_df['home_pitcher_name'].notna() & (games_df['home_pitcher_name'] != 'TBD')]
        if len(valid_games) > 0:
            game_options_mc = {}
            for idx, row in valid_games.iterrows():
                label = f"{row['home_team']} vs {row['away_team']} | {row.get('home_pitcher_name', '')} vs {row.get('away_pitcher_name', '')}"
                game_options_mc[label] = idx
            col_mc1, col_mc2, col_mc3 = st.columns([2, 1, 1])
            with col_mc1: selected_mc = st.selectbox("Select game:", list(game_options_mc.keys()), key="mc_select")
            with col_mc2: n_sims = st.number_input("Simulations:", 1000, 50000, 10000, 1000, key="mc_n")
            with col_mc3:
                st.write(""); st.write("")
                if st.button("RUN MONTE CARLO", use_container_width=True, key="mc_btn"):
                    with st.spinner(f"Running {n_sims:,} simulations..."):
                        from mlb_data_fetcher import get_pitcher_stats, get_bullpen_data, get_team_momentum
                        from mlb_engine import MLBEngine
                        from montecarlo_mlb import MonteCarloMLB
                        idx_mc = game_options_mc[selected_mc]
                        row_mc = valid_games.loc[idx_mc]
                        mlb_engine = MLBEngine()
                        mc = MonteCarloMLB()
                        home_p = get_pitcher_stats(row_mc.get('home_pitcher_id'))
                        away_p = get_pitcher_stats(row_mc.get('away_pitcher_id'))
                        if not home_p: home_p = mlb_engine.smart_pitcher_defaults(row_mc.get('home_pitcher_name', ''))
                        if not away_p: away_p = mlb_engine.smart_pitcher_defaults(row_mc.get('away_pitcher_name', ''))
                        game_data = {
                            'home_team': row_mc['home_team'], 'away_team': row_mc['away_team'],
                            'home_win_pct': row_mc.get('home_win_pct', 0.5), 'away_win_pct': row_mc.get('away_win_pct', 0.5),
                            'home_pitcher': home_p, 'away_pitcher': away_p,
                            'home_bullpen': get_bullpen_data(row_mc.get('home_team_id')),
                            'away_bullpen': get_bullpen_data(row_mc.get('away_team_id')),
                            'home_momentum': get_team_momentum(row_mc.get('home_team_id')),
                            'away_momentum': get_team_momentum(row_mc.get('away_team_id')),
                            'home_matchup': {'avg': 0.250, 'ops': 0.720, 'hr': 0, 'pa': 0, 'k_rate': 0.22},
                            'away_matchup': {'avg': 0.250, 'ops': 0.720, 'hr': 0, 'pa': 0, 'k_rate': 0.22},
                            'stadium': row_mc.get('stadium', ''), 'divisional_game': row_mc.get('is_divisional', False)
                        }
                        results = mc.simulate_game(game_data, n_sims)
                        model_result = mlb_engine.evaluate_mlb_game(game_data, 2.0)
                        model_prob = model_result.get('probability', 0.5)
                        mc_prob = results['home_win_pct']
                        diff = mc_prob - model_prob
                        if abs(diff) > 0.12: diff_color, diff_label = "#f85149", "LARGE"
                        elif abs(diff) > 0.07: diff_color, diff_label = "#d2991d", "MODERATE"
                        elif abs(diff) > 0.03: diff_color, diff_label = "#3fb950", "SLIGHT"
                        else: diff_color, diff_label = "#58a6ff", "ALIGNED"
                        st.markdown(f"""<div class="comparison-box"><b>MODEL vs MONTE CARLO:</b><br>Model: {model_prob:.1%} | Monte Carlo: {mc_prob:.1%} | <span style="color:{diff_color}">Diff: {diff:+.1%} ({diff_label})</span></div>""", unsafe_allow_html=True)
                        col_r1, col_r2 = st.columns(2)
                        with col_r1: st.metric(results['home_team'], f"{results['home_win_pct']:.1%}"); st.metric(results['away_team'], f"{results['away_win_pct']:.1%}")
                        with col_r2: st.metric("Over 7.5", f"{results['over_7_5']:.1%}"); st.metric("Over 8.5", f"{results['over_8_5']:.1%}"); st.metric(f"{results['home_team']} -1.5", f"{results['home_runline_minus1_5']:.1%}")
except: st.info("Monte Carlo data loading...")

# VALIDATE & RESULTS
st.markdown('<h2 class="section-title">VALIDATE & RESULTS</h2>', unsafe_allow_html=True)
col_v1, col_v2 = st.columns(2)
with col_v1:
    if st.button("VALIDATE PENDING", use_container_width=True):
        try:
            from betting_logger import validate_pending_bets
            from prediction_tracker import validate_winner_predictions
            validate_pending_bets()
            validate_winner_predictions()
            st.success("Done!")
        except: st.error("Validation failed")
with col_v2:
    if st.button("RESULTS", use_container_width=True):
        log_file = 'data/betting_log.csv'
        if os.path.exists(log_file):
            df = pd.read_csv(log_file)
            completed = df[df['result'] != 'PENDING']
            if len(completed) > 0:
                wins = len(completed[completed['result'] == 'WIN'])
                total = len(completed)
                profit = completed['profit_loss'].sum()
                st.markdown('<div class="mc-result">', unsafe_allow_html=True)
                st.markdown("#### BETTING RESULTS")
                col_r1, col_r2, col_r3, col_r4 = st.columns(4)
                with col_r1: st.metric("Total Bets", total)
                with col_r2: st.metric("Wins", wins)
                with col_r3: st.metric("Win Rate", f"{wins/total*100:.1f}%" if total > 0 else "N/A")
                with col_r4: st.metric("Profit", f"${profit:+.2f}")
                st.markdown('</div>', unsafe_allow_html=True)
            else: st.info("No validated results yet.")
        else: st.info("No betting log found.")

st.markdown("""<div class="footer">Sports Quant Engine V8 | Market Inefficiency Detection System<br>MLB + NBA + Monte Carlo + Bayesian + Statcast + Calendar</div>""", unsafe_allow_html=True)