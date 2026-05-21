    if sport == "MLB":
        headers = ['GAME', 'PICK', 'ODDS', 'PROB', 'EDGE', 'CONF', 'ML', 'RL', 'O/U', 'TEAM', 'F5']
        table_html += ''.join([f'<th>{h}</th>' for h in headers])
        table_html += '</tr></thead><tbody>'
        
        for row in data_rows:
            if row.startswith('MLB|'):
                parts = row.split('|')
                if len(parts) >= 13:
                    home = parts[1]
                    away = parts[2]
                    pick = parts[3]
                    odds = parts[4]
                    prob = parts[5]
                    edge = parts[6]
                    conf = parts[7]
                    ml_st = parts[8]
                    rl_st = parts[9]
                    ou_st = parts[10]
                    team_st = parts[11]
                    f5_st = parts[12]
                    
                    game = f"{home} vs {away}"[:30]
                    
                    ml_color = 'status-ok' if '[OK]' in ml_st else ('status-sus' if '[SUS]' in ml_st else 'status-no')
                    rl_color = 'status-ok' if '[OK]' in rl_st else 'status-marginal'
                    ou_color = 'status-ok' if '[OK]' in ou_st else 'status-marginal'
                    
                    table_html += f'<tr>'
                    table_html += f'<td>{game}</td>'
                    table_html += f'<td class="pick-highlight">{pick}</td>'
                    table_html += f'<td>{odds}</td>'
                    table_html += f'<td>{prob}</td>'
                    table_html += f'<td>{edge}</td>'
                    table_html += f'<td>{conf}</td>'
                    table_html += f'<td><span class="{ml_color}">{ml_st}</span></td>'
                    table_html += f'<td><span class="{rl_color}">{rl_st}</span></td>'
                    table_html += f'<td><span class="{ou_color}">{ou_st}</span></td>'
                    table_html += f'<td>{team_st}</td>'
                    table_html += f'<td>{f5_st}</td>'
                    table_html += '</tr>'