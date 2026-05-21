import pandas as pd
import numpy as np
from quant_engine import QuantEngine

class BacktestEngine:
    def __init__(self):
        self.quant = QuantEngine()
        self.results = []
    
    def run_backtest(self, historical_df, bankroll=1000, stake_pct=0.03):
        print("\n" + "=" * 60)
        print(f"🧪 BACKTEST CON FEATURES REALES - {len(historical_df)} partidos")
        print("=" * 60)
        
        balance = bankroll
        bets = []
        wins = 0
        losses = 0
        pushes = 0
        balance_history = [bankroll]
        
        soccer_bets = 0
        nba_bets = 0
        
        for idx, row in historical_df.iterrows():
            sport = row['sport']
            
            if sport == 'soccer':
                # Features del soccer sintético
                home_form = row.get('home_form', 0.52)
                away_form = row.get('away_form', 0.48)
                home_xg = row.get('home_xg', 1.5)
                away_xg = row.get('away_xg', 1.2)
                
                # Normalizar xG a fuerza 0-1
                xg_total = home_xg + away_xg
                home_xg_strength = 0.45 + (home_xg / xg_total) * 0.15 if xg_total > 0 else 0.52
                away_xg_strength = 0.45 + (away_xg / xg_total) * 0.15 if xg_total > 0 else 0.48
                
                home_score_val = self.quant.soccer_team_score({
                    'form': home_form,
                    'xg': home_xg_strength,
                    'motivation': 0.62,
                    'injuries_impact': 0.68,
                    'h2h_advantage': 0.52
                })
                away_score_val = self.quant.soccer_team_score({
                    'form': away_form,
                    'xg': away_xg_strength,
                    'motivation': 0.52,
                    'injuries_impact': 0.62,
                    'h2h_advantage': 0.45
                })
            else:
                # FEATURES REALES NBA
                home_win_pct = row.get('home_win_pct', 0.5)
                away_win_pct = row.get('away_win_pct', 0.5)
                home_home_pct = row.get('home_home_pct', home_win_pct)
                away_road_pct = row.get('away_road_pct', away_win_pct)
                is_playoff = row.get('is_playoff', False)
                
                # Net rating estimado del win%
                home_net = 0.45 + (home_win_pct - 0.3) * 0.5
                away_net = 0.45 + (away_win_pct - 0.3) * 0.5
                
                # Home court advantage
                home_rest = 0.55
                away_rest = 0.48
                
                # Momentum (playoff boost)
                home_momentum = 0.65 if is_playoff else 0.58
                away_momentum = 0.58 if is_playoff else 0.52
                
                home_score_val = self.quant.nba_team_score({
                    'win_pct': home_win_pct,
                    'net_rating': home_net,
                    'injury_impact': 0.70,
                    'rest_days': home_rest,
                    'momentum': home_momentum,
                    'rebounding': home_win_pct - 0.05,
                    'h2h': 0.50
                })
                away_score_val = self.quant.nba_team_score({
                    'win_pct': away_win_pct,
                    'net_rating': away_net,
                    'injury_impact': 0.60,
                    'rest_days': away_rest,
                    'momentum': away_momentum,
                    'rebounding': away_win_pct - 0.10,
                    'h2h': 0.45
                })
            
            match_data = self._prepare_match_data(row, sport, home_score_val, away_score_val)
            evaluation = self.quant.evaluate_match(match_data, sport)
            
            if evaluation['approved']:
                if match_data['home_team_score'] >= match_data['away_team_score']:
                    pick = 'home'
                    pick_team = row['home_team']
                else:
                    pick = 'away'
                    pick_team = row['away_team']
                
                stake = balance * stake_pct
                actual_result = row['result']
                odds = row.get('odds', 2.0)
                
                if sport == 'soccer':
                    if (pick == 'home' and actual_result == 'home') or \
                       (pick == 'away' and actual_result == 'away'):
                        won = True
                        wins += 1
                        profit = stake * (odds - 1)
                    elif actual_result == 'draw':
                        won = False
                        pushes += 1
                        profit = 0
                    else:
                        won = False
                        losses += 1
                        profit = -stake
                    soccer_bets += 1
                else:
                    if (pick == 'home' and actual_result == 'home') or \
                       (pick == 'away' and actual_result == 'away'):
                        won = True
                        wins += 1
                        profit = stake * (odds - 1)
                    else:
                        won = False
                        losses += 1
                        profit = -stake
                    nba_bets += 1
                
                balance += profit
                balance_history.append(balance)
                
                bets.append({
                    'date': row['date'],
                    'sport': sport,
                    'league': row.get('league', 'NBA'),
                    'match': f"{row['home_team']} vs {row['away_team']}",
                    'pick': pick_team,
                    'pick_side': pick,
                    'actual_result': actual_result,
                    'actual_winner': row['winner'],
                    'won': won,
                    'probability': evaluation['probability'],
                    'edge': evaluation['edge'],
                    'volatility': evaluation['volatility'],
                    'confidence': evaluation['confidence'],
                    'odds': odds,
                    'stake': round(stake, 2),
                    'profit': round(profit, 2),
                    'balance': round(balance, 2)
                })
        
        self.results = bets
        self.final_balance = balance
        self.balance_history = balance_history
        
        return self._generate_report(bankroll, wins, losses, pushes, soccer_bets, nba_bets)
    
    def _prepare_match_data(self, row, sport, home_score, away_score):
        odds = row.get('odds', 2.0)
        if odds is None or odds != odds or odds <= 1:
            odds = 2.0
            
        if sport == 'soccer':
            return {
                'match': f"{row['home_team']} vs {row['away_team']}",
                'home_team': row['home_team'],
                'away_team': row['away_team'],
                'home_team_score': home_score,
                'away_team_score': away_score,
                'home_advantage': 0.58,
                'rivalry_factor': 0.3,
                'team_inconsistency': 0.25,
                'injury_uncertainty': 0.2,
                'schedule_fatigue': 0.15,
                'odds': odds
            }
        else:
            return {
                'match': f"{row['home_team']} vs {row['away_team']}",
                'home_team': row['home_team'],
                'away_team': row['away_team'],
                'home_team_score': home_score,
                'away_team_score': away_score,
                'rivalry_factor': 0.25,
                'team_inconsistency': 0.2,
                'injury_uncertainty': 0.2,
                'schedule_fatigue': 0.15,
                'odds': odds
            }
    
    def _generate_report(self, initial_bankroll, wins, losses, pushes, soccer_bets, nba_bets):
        total_bets = wins + losses + pushes
        
        if total_bets == 0:
            return {
                'total_bets': 0, 'wins': 0, 'losses': 0, 'pushes': 0,
                'win_rate': 0, 'roi': 0, 'profit_factor': 0,
                'sharpe_ratio': 0, 'max_win_streak': 0, 'max_loss_streak': 0,
                'initial_bankroll': initial_bankroll,
                'final_balance': initial_bankroll,
                'total_profit': 0, 'soccer_bets': 0, 'nba_bets': 0,
                'soccer_roi': 0, 'nba_roi': 0
            }
        
        win_rate = wins / total_bets * 100
        roi = ((self.final_balance - initial_bankroll) / initial_bankroll) * 100
        
        gross_profit = sum(b['profit'] for b in self.results if b['profit'] > 0)
        gross_loss = abs(sum(b['profit'] for b in self.results if b['profit'] < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        max_streak = 0
        current_streak = 0
        loss_streak = 0
        max_loss_streak = 0
        for b in self.results:
            if b['won']:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
                loss_streak = 0
            else:
                current_streak = 0
                loss_streak += 1
                max_loss_streak = max(max_loss_streak, loss_streak)
        
        returns = [b['profit'] for b in self.results]
        sharpe = np.mean(returns) / np.std(returns) * np.sqrt(len(returns)) if len(returns) > 1 and np.std(returns) > 0 else 0
        
        soccer_returns = [b['profit'] for b in self.results if b['sport'] == 'soccer']
        nba_returns = [b['profit'] for b in self.results if b['sport'] == 'nba']
        
        avg_stake = initial_bankroll * 0.03
        soccer_roi = (sum(soccer_returns) / (soccer_bets * avg_stake)) * 100 if soccer_bets > 0 else 0
        nba_roi = (sum(nba_returns) / (nba_bets * avg_stake)) * 100 if nba_bets > 0 else 0
        
        return {
            'total_bets': total_bets,
            'wins': wins, 'losses': losses, 'pushes': pushes,
            'win_rate': round(win_rate, 2),
            'roi': round(roi, 2),
            'profit_factor': round(profit_factor, 2),
            'sharpe_ratio': round(sharpe, 2),
            'max_win_streak': max_streak,
            'max_loss_streak': max_loss_streak,
            'initial_bankroll': initial_bankroll,
            'final_balance': round(self.final_balance, 2),
            'total_profit': round(self.final_balance - initial_bankroll, 2),
            'soccer_bets': soccer_bets,
            'nba_bets': nba_bets,
            'soccer_roi': round(soccer_roi, 2),
            'nba_roi': round(nba_roi, 2)
        }
    
    def print_report(self, report):
        print("\n" + "=" * 60)
        print("📊 REPORTE DE BACKTEST (FEATURES REALES)")
        print("=" * 60)
        
        if report['total_bets'] == 0:
            print("🔴 No se encontraron setups en el período")
            return
        
        if self.results:
            print(f"📅 Período: {self.results[-1]['date']} → {self.results[0]['date']}")
        
        print(f"\n💰 Bankroll inicial: ${report['initial_bankroll']:,.2f}")
        print(f"💰 Bankroll final: ${report['final_balance']:,.2f}")
        print(f"📈 Ganancia neta: ${report['total_profit']:,.2f}")
        
        print(f"\n🎯 TOTAL APUESTAS: {report['total_bets']}")
        print(f"   ⚽ Soccer: {report['soccer_bets']}")
        print(f"   🏀 NBA: {report['nba_bets']}")
        print(f"   ✅ Ganadas: {report['wins']}")
        print(f"   ❌ Perdidas: {report['losses']}")
        print(f"   🔄 Empates: {report['pushes']}")
        
        print(f"\n📊 MÉTRICAS CLAVE:")
        print(f"   Win Rate: {report['win_rate']}%")
        print(f"   ROI: {report['roi']}%")
        print(f"   Profit Factor: {report['profit_factor']}")
        print(f"   Sharpe Ratio: {report['sharpe_ratio']}")
        print(f"   🔥 Racha ganadora: {report['max_win_streak']}")
        print(f"   💀 Racha perdedora: {report['max_loss_streak']}")
        
        if report['soccer_bets'] > 0:
            print(f"\n   ⚽ Soccer ROI: {report['soccer_roi']}%")
        if report['nba_bets'] > 0:
            print(f"   🏀 NBA ROI: {report['nba_roi']}%")
        
        print("\n" + "=" * 60)
        print("VEREDICTO:")
        
        if report['roi'] > 5 and report['profit_factor'] > 1.3:
            print("🟢 SISTEMA RENTABLE - Edge confirmado")
        elif report['roi'] > 0 and report['profit_factor'] > 1.1:
            print("🟡 SISTEMA MARGINAL - Necesita ajustes")
        elif report['roi'] > -5:
            print("🟠 SISTEMA PLANO - Cerca de break-even")
        else:
            print("🔴 SISTEMA NO RENTABLE - Revisar lógica")
        
        print("=" * 60)