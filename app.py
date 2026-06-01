import streamlit as st
import subprocess
import sys
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Sports Quant Engine V10", page_icon="MLB", layout="wide", initial_sidebar_state="collapsed")

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
    .results-table { width: 100%; border-collapse: collapse; margin: 0.5rem 0; font-size: 0.85rem; }
    .results-table th { background: #1a1a2e; color: #e94560; padding: 0.7rem; text-transform: uppercase; letter-spacing: 1px; border-bottom: 2px solid #e94560; }
    .results-table td { background: #161b22; color: #c9d1d9; padding: 0.5rem; border-bottom: 1px solid #21262d; text-align: center; }
    .results-table tr:hover td { background: #1a2332; }
    .pick-highlight { color: #58a6ff; font-weight: bold; }
    .no-pick { color: #f85149; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>MLB NBA SPORTS QUANT ENGINE V10</h1>
    <p>10 Engines | Elite Picks A/A+ | Weather + Travel + Pitch + Defense + Rest + Bullpen + Splits + Statcast</p>
</div>
""", unsafe_allow_html=True)

def run_script_and_parse(script_name):
    output_text = ""
    process = subprocess.Popen([sys.executable, script_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in process.stdout:
        output_text += line
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

def save_pick_safe(match, pick, edge):
    tracker_file = 'data/picks_tracker.csv'
    today_str = datetime.now().strftime('%Y-%m-%d')
    try:
        if os.path.exists(tracker_file):
            existing = pd.read_csv(tracker_file)
            if len(existing[(existing['date'] == today_str) & (existing['match'] == match)]) == 0:
                new_row = pd.DataFrame([{'date': today_str, 'match': match, 'pick': pick, 'edge': edge, 'result': ''}])
                new_row.to_csv(tracker_file, mode='a', header=False, index=False)
    except:
        pass

def validate_picks_tracker():
    tracker_file = 'data/picks_tracker.csv'
    if not os.path.exists(tracker_file):
        return
    try:
        df = pd.read_csv(tracker_file)
        pending = df[(df['result'].isna()) | (df['result'] == '') | (df['result'] == 'PENDING')]
        if len(pending) == 0:
            return
        import requests
        for idx, row in pending.iterrows():
            try:
                r = requests.get('https://statsapi.mlb.com/api/v1/schedule', params={'sportId': 1, 'date': row['date']}, timeout=10)
                games = r.json().get('dates', [{}])[0].get('games', [])
                for g in games:
                    home = g['teams']['home']['team']['name']
                    away = g['teams']['away']['team']['name']
                    if home in row['match'] and away in row['match'] and g.get('status', {}).get('detailedState') == 'Final':
                        hs = int(g['teams']['home'].get('score', 0))
                        aws = int(g['teams']['away'].get('score', 0))
                        aw = home if hs > aws else away
                        df.at[idx, 'result'] = 'WIN' if row['pick'].lower() in aw.lower() else 'LOSS'
            except:
                pass
        df.to_csv(tracker_file, index=False)
    except:
        pass

# MÉTRICAS
try:
    from betting_logger import get_betting_stats
    mlb_stats = get_betting_stats('MLB')
except:
    mlb_stats = None

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    val = f"{mlb_stats['win_rate']}%" if mlb_stats else "N/A"
    st.markdown(f"""<div class="metric-btn"><span class="label">WIN RATE</span><span class="value">{val}</span></div>""", unsafe_allow_html=True)
with col_m2:
    val = f"${mlb_stats['total_profit']}" if mlb_stats else "N/A"
    st.markdown(f"""<div class="metric-btn"><span class="label">PROFIT</span><span class="value">{val}</span></div>""", unsafe_allow_html=True)
with col_m3:
    val = f"{mlb_stats['roi']}%" if mlb_stats else "N/A"
    st.markdown(f"""<div class="metric-btn"><span class="label">ROI</span><span class="value">{val}</span></div>""", unsafe_allow_html=True)
with col_m4:
    val = str(mlb_stats['total_bets']) if mlb_stats else "N/A"
    st.markdown(f"""<div class="metric-btn"><span class="label">TOTAL BETS</span><span class="value">{val}</span></div>""", unsafe_allow_html=True)

# PICK PERFORMANCE
st.markdown('<h2 class="section-title">ELITE PICK PERFORMANCE (A/A+)</h2>', unsafe_allow_html=True)
validate_picks_tracker()
try:
    tracker_file = 'data/picks_tracker.csv'
    if os.path.exists(tracker_file):
        df = pd.read_csv(tracker_file)
        completed = df[df['result'].isin(['WIN', 'LOSS'])]
        if len(completed) > 0:
            wins = len(completed[completed['result'] == 'WIN'])
            total = len(completed)
            col_w1, col_w2, col_w3 = st.columns(3)
            col_w1.metric("Total Picks", total)
            col_w2.metric("Wins", wins)
            col_w3.metric("Accuracy", f"{wins/total*100:.1f}%")
        else:
            st.info("No validated picks yet.")
except:
    st.info("Picks tracker initializing...")

# PICKS CALENDAR
st.markdown('<h2 class="section-title">PICKS CALENDAR</h2>', unsafe_allow_html=True)
try:
    tracker_file = 'data/picks_tracker.csv'
    if os.path.exists(tracker_file):
        df = pd.read_csv(tracker_file)
        if len(df) > 0:
            df = df.drop_duplicates(subset=['date', 'match', 'pick'], keep='first')
            dates = sorted(df['date'].unique(), reverse=True)
            selected_date = st.selectbox("Select date:", dates, key="cal_date")
            day_df = df[df['date'] == selected_date]
            if len(day_df) > 0:
                st.markdown(f"### {selected_date} - {len(day_df)} picks")
                table_html = '<table class="results-table"><thead><tr>'
                for h in ['GAME', 'PICK', 'EDGE', 'RESULT']:
                    table_html += f'<th>{h}</th>'
                table_html += '</tr></thead><tbody>'
                wins = 0
                for _, row in day_df.iterrows():
                    result = str(row.get('result', ''))
                    if result == 'WIN':
                        status = 'WIN'
                        wins += 1
                    elif result == 'LOSS':
                        status = 'LOSS'
                    else:
                        status = 'PENDING'
                    table_html += f'<tr><td>{row["match"]}</td><td class="pick-highlight">{row["pick"]}</td><td>{row["edge"]}</td><td>{status}</td></tr>'
                table_html += '</tbody></table>'
                st.markdown(table_html, unsafe_allow_html=True)
                validated = day_df[day_df['result'].isin(['WIN', 'LOSS'])]
                if len(validated) > 0:
                    st.metric("Day", f"{wins}/{len(validated)}")
except:
    st.info("Calendar loading...")

# BOTONES
st.markdown('<h2 class="section-title">QUICK SCAN</h2>', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)
if 'mlb_data' not in st.session_state:
    st.session_state.mlb_data = None
if 'mlb_metadata' not in st.session_state:
    st.session_state.mlb_metadata = None

with col1:
    if st.button("MLB TODAY", use_container_width=True, key="mlb_today"):
        with st.spinner("Scanning MLB..."):
            output = run_script_and_parse("run_live_mlb.py")
            games, metadata = parse_mlb_output(output)
            st.session_state.mlb_data = games
            st.session_state.mlb_metadata = metadata
            for g in games:
                try:
                    prob_val = float(g['prob'].rstrip('%')) if '%' in str(g['prob']) else float(g['prob'])
                except:
                    prob_val = 0
                if g['pick'] != 'NO PICK' and prob_val >= 60 and g['conf'] in ['A+', 'A']:
                    try:
                        edge_val = float(g['edge'].rstrip('%')) if '%' in str(g['edge']) else float(g['edge'])
                    except:
                        edge_val = 0
                    save_pick_safe(f"{g['home']} vs {g['away']}", g['pick'], edge_val)

with col2:
    if st.button("MLB TOMORROW", use_container_width=True, key="mlb_tomorrow"):
        with st.spinner("Predicting MLB..."):
            output = run_script_and_parse("run_tomorrow_mlb.py")
            games, metadata = parse_mlb_output(output)
            st.session_state.mlb_data = games
            st.session_state.mlb_metadata = metadata
            for g in games:
                try:
                    prob_val = float(g['prob'].rstrip('%')) if '%' in str(g['prob']) else float(g['prob'])
                except:
                    prob_val = 0
                if g['pick'] != 'NO PICK' and prob_val >= 60 and g['conf'] in ['A+', 'A']:
                    try:
                        edge_val = float(g['edge'].rstrip('%')) if '%' in str(g['edge']) else float(g['edge'])
                    except:
                        edge_val = 0
                    save_pick_safe(f"{g['home']} vs {g['away']}", g['pick'], edge_val)

with col3:
    if st.button("NBA TODAY", use_container_width=True, key="nba_today"):
        st.info("NBA loading...")
with col4:
    if st.button("NBA TOMORROW", use_container_width=True, key="nba_tomorrow"):
        st.info("NBA loading...")

# TABLA MLB
if st.session_state.mlb_data:
    st.markdown("---")
    st.markdown(f"### MLB SCAN RESULTS - {len(st.session_state.mlb_data)} games")
    table_html = '<table class="results-table"><thead><tr>'
    for h in ['HOME', 'AWAY', 'PICK', 'ODDS', 'PROB', 'EDGE', 'CONF']:
        table_html += f'<th>{h}</th>'
    table_html += '</tr></thead><tbody>'
    for g in st.session_state.mlb_data:
        pick_display = g['pick'] if g['pick'] != 'NO PICK' else 'NO PICK'
        pick_class = 'pick-highlight' if g['pick'] != 'NO PICK' else 'no-pick'
        table_html += f'<tr><td>{g["home"]}</td><td>{g["away"]}</td><td class="{pick_class}">{pick_display}</td><td>{g["odds"]}</td><td>{g["prob"]}</td><td>{g["edge"]}</td><td>{g["conf"]}</td></tr>'
    table_html += '</tbody></table>'
    st.markdown(table_html, unsafe_allow_html=True)

    game_options = [f"{g['home']} vs {g['away']}" for g in st.session_state.mlb_data]
    selected = st.selectbox("Select game for FULL ANALYSIS:", game_options, key="mlb_select")
    if st.button("SHOW FULL ANALYSIS", use_container_width=True, key="mlb_full"):
        idx = game_options.index(selected)
        g = st.session_state.mlb_data[idx]
        meta = st.session_state.mlb_metadata.get(f"{g['home']}|{g['away']}", {})
        st.markdown(f"## FULL ANALYSIS: {g['home']} vs {g['away']}")
        if g['pick'] != 'NO PICK':
            st.markdown(f"### PICK: {g['pick']} ({g['odds']}) | Edge: {g['edge']} | Conf: {g['conf']}")
        else:
            st.markdown(f"### NO PICK | Edge: {g['edge']}")

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
                st.write(f"Home Bullpen: {meta['home_bullpen_era']} ERA ({meta['home_bullpen_fatigue']})")
                st.write(f"Away Bullpen: {meta['away_bullpen_era']} ERA ({meta['away_bullpen_fatigue']})")
            st.markdown('</div>', unsafe_allow_html=True)

            try:
                from weather_engine import get_weather_for_match, weather_summary, weather_impact
                weather = get_weather_for_match(g['home'], g['away'])
                if weather:
                    wi = weather_impact(weather)
                    st.markdown('<div class="mc-result">', unsafe_allow_html=True)
                    st.markdown("#### WEATHER")
                    st.write(f"**{weather_summary(weather)}**")
                    if wi['total_runs_boost'] != 0:
                        st.write(f"Run Impact: {wi['total_runs_boost']:+.1%}")
                    st.markdown('</div>', unsafe_allow_html=True)
            except:
                pass

            try:
                from rest_engine import get_team_rest_days
                h_rest = get_team_rest_days(g['home'])
                a_rest = get_team_rest_days(g['away'])
                st.markdown('<div class="mc-result">', unsafe_allow_html=True)
                st.markdown("#### REST DAYS")
                st.write(f"{g['home']}: {h_rest} day(s) | {g['away']}: {a_rest} day(s)")
                st.markdown('</div>', unsafe_allow_html=True)
            except:
                pass

            try:
                from bullpen_leverage_engine import get_bullpen_stats
                h_bp = get_bullpen_stats(g['home'])
                a_bp = get_bullpen_stats(g['away'])
                if h_bp and a_bp:
                    st.markdown('<div class="mc-result">', unsafe_allow_html=True)
                    st.markdown("#### BULLPEN")
                    col_bp1, col_bp2 = st.columns(2)
                    with col_bp1:
                        st.write(f"**{g['home']}**")
                        st.write(f"Saves: {h_bp['saves']}/{h_bp['save_opps']} ({h_bp['save_pct']}%)")
                        st.write(f"Blown: {h_bp['blown_saves']}")
                    with col_bp2:
                        st.write(f"**{g['away']}**")
                        st.write(f"Saves: {a_bp['saves']}/{a_bp['save_opps']} ({a_bp['save_pct']}%)")
                        st.write(f"Blown: {a_bp['blown_saves']}")
                    st.markdown('</div>', unsafe_allow_html=True)
            except:
                pass

            st.markdown('<div class="mc-result">', unsafe_allow_html=True)
            st.markdown("#### MOMENTUM")
            col_mo1, col_mo2 = st.columns(2)
            with col_mo1:
                st.write(f"{g['home']} OPS: {meta['home_ops']} | Run Diff: {meta['home_run_diff']}")
            with col_mo2:
                st.write(f"{g['away']} OPS: {meta['away_ops']} | Run Diff: {meta['away_run_diff']}")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="mc-result">', unsafe_allow_html=True)
            st.markdown("#### INJURIES")
            col_i1, col_i2 = st.columns(2)
            with col_i1:
                st.markdown(f"**{g['home']}:**")
                st.write(meta.get('home_injuries', 'None').replace(';', '\n'))
            with col_i2:
                st.markdown(f"**{g['away']}:**")
                st.write(meta.get('away_injuries', 'None').replace(';', '\n'))
            st.markdown('</div>', unsafe_allow_html=True)

            try:
                from series_momentum_engine import get_series_momentum
                sm = get_series_momentum(g['home'], g['away'])
                if sm:
                    st.markdown('<div class="mc-result">', unsafe_allow_html=True)
                    st.markdown("#### SERIES & MOMENTUM")
                    col_sm1, col_sm2, col_sm3 = st.columns(3)
                    with col_sm1:
                        st.metric(f"{g['home']} Last 5", sm['home_last5'])
                        st.metric(f"Last 10", sm['home_last10'])
                        st.write(f"Streak: {sm['home_streak']}W | RD: {sm['home_run_diff_last5']:+d}")
                    with col_sm2:
                        st.metric(f"{g['away']} Last 5", sm['away_last5'])
                        st.metric(f"Last 10", sm['away_last10'])
                        st.write(f"Streak: {sm['away_streak']}W | RD: {sm['away_run_diff_last5']:+d}")
                    with col_sm3:
                        st.metric("H2H", sm['h2h_record'])
                        st.write(f"Games: {sm['h2h_games']}")
                        if sm['h2h_details']:
                            for date, detail in sm['h2h_details'][:3]:
                                st.write(f"{date}: {detail}")
                    st.markdown('</div>', unsafe_allow_html=True)
            except:
                pass

            try:
                from lineup_fetcher import get_lineups_for_match
                lineups = get_lineups_for_match(g['home'], g['away'])
                if lineups.get('has_lineups'):
                    st.markdown('<div class="mc-result">', unsafe_allow_html=True)
                    st.markdown("#### STARTING LINEUPS")
                    col_l1, col_l2 = st.columns(2)
                    with col_l1:
                        st.markdown(f"**{lineups['defense_team']}**")
                        for p in lineups['defense_lineup']:
                            st.write(f"  {p['position']}: {p['name']}")
                    with col_l2:
                        st.markdown(f"**{lineups['offense_team']}**")
                        for p in lineups['offense_lineup']:
                            st.write(f"  {p['position']}: {p['name']}")
                    st.markdown('</div>', unsafe_allow_html=True)
            except:
                pass

        st.markdown('<div class="mc-result">', unsafe_allow_html=True)
        st.markdown("#### BETTING VALUE")
        col_b1, col_b2, col_b3, col_b4, col_b5 = st.columns(5)
        with col_b1:
            if "[OK]" in g['ml']:
                st.success(f"ML: {g['ml']}")
            elif "[SUS]" in g['ml']:
                st.warning(f"ML: {g['ml']}")
            else:
                st.error(f"ML: {g['ml']}")
        with col_b2:
            if "[OK]" in g['rl']:
                st.success(f"RL: {g['rl']}")
            elif "[?]" in g['rl']:
                st.warning(f"RL: {g['rl']}")
            else:
                st.error(f"RL: {g['rl']}")
        with col_b3:
            if "[OK]" in g['ou']:
                st.success(f"O/U: {g['ou']}")
            elif "[?]" in g['ou']:
                st.warning(f"O/U: {g['ou']}")
            else:
                st.error(f"O/U: {g['ou']}")
        with col_b4:
            if "[OK]" in g['team']:
                st.success(f"Team: {g['team']}")
            elif "[?]" in g['team']:
                st.warning(f"Team: {g['team']}")
            else:
                st.error(f"Team: {g['team']}")
        with col_b5:
            if "[OK]" in g['f5']:
                st.success(f"F5: {g['f5']}")
            elif "[?]" in g['f5']:
                st.warning(f"F5: {g['f5']}")
            else:
                st.error(f"F5: {g['f5']}")
        st.markdown('</div>', unsafe_allow_html=True)

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
            with col_mc1:
                selected_mc = st.selectbox("Select game:", list(game_options_mc.keys()), key="mc_select")
            with col_mc2:
                n_sims = st.number_input("Simulations:", 1000, 50000, 10000, 1000, key="mc_n")
            with col_mc3:
                st.write("")
                st.write("")
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
                        if not home_p:
                            home_p = mlb_engine.smart_pitcher_defaults(row_mc.get('home_pitcher_name', ''))
                        if not away_p:
                            away_p = mlb_engine.smart_pitcher_defaults(row_mc.get('away_pitcher_name', ''))
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
                        if abs(diff) > 0.12:
                            diff_color, diff_label = "#f85149", "LARGE"
                        elif abs(diff) > 0.07:
                            diff_color, diff_label = "#d2991d", "MODERATE"
                        elif abs(diff) > 0.03:
                            diff_color, diff_label = "#3fb950", "SLIGHT"
                        else:
                            diff_color, diff_label = "#58a6ff", "ALIGNED"
                        st.markdown(f"""<div class="comparison-box"><b>MODEL vs MONTE CARLO:</b><br>Model: {model_prob:.1%} | Monte Carlo: {mc_prob:.1%} | <span style="color:{diff_color}">Diff: {diff:+.1%} ({diff_label})</span></div>""", unsafe_allow_html=True)
                        col_r1, col_r2 = st.columns(2)
                        with col_r1:
                            st.metric(results['home_team'], f"{results['home_win_pct']:.1%}")
                            st.metric(results['away_team'], f"{results['away_win_pct']:.1%}")
                        with col_r2:
                            st.metric("Over 7.5", f"{results['over_7_5']:.1%}")
                            st.metric("Over 8.5", f"{results['over_8_5']:.1%}")
                            st.metric(f"{results['home_team']} -1.5", f"{results['home_runline_minus1_5']:.1%}")
except:
    st.info("Monte Carlo loading...")

# VALIDATE & RESULTS
st.markdown('<h2 class="section-title">VALIDATE & RESULTS</h2>', unsafe_allow_html=True)
col_v1, col_v2 = st.columns(2)
with col_v1:
    if st.button("VALIDATE PENDING", use_container_width=True):
        try:
            from betting_logger import validate_pending_bets
            validate_pending_bets()
            validate_picks_tracker()
            st.success("Done!")
        except:
            st.error("Validation failed")
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
                col_r1.metric("Total", total)
                col_r2.metric("Wins", wins)
                col_r3.metric("Win Rate", f"{wins/total*100:.1f}%" if total > 0 else "N/A")
                col_r4.metric("Profit", f"${profit:+.2f}")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("No validated results.")
        else:
            st.info("No betting log.")

st.markdown("""<div class="footer">Sports Quant Engine V10 | 10 Engines | Elite Picks A/A+</div>""", unsafe_allow_html=True)