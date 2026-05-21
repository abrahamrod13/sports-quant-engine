"""
MARKET INTELLIGENCE ENGINE
Detecta edge real vs edge falso, narrativas, sobre-reacciones, line movement
"""

class MarketIntelligence:
    def __init__(self):
        # Equipos sobrevalorados por el público (sesgo mediático)
        self.public_teams = [
            'New York Yankees', 'Los Angeles Dodgers', 'Boston Red Sox',
            'Chicago Cubs', 'New York Mets', 'Philadelphia Phillies',
            'Atlanta Braves', 'Houston Astros', 'San Diego Padres'
        ]
        
        # Equipos subvalorados (poco hype, buen rendimiento)
        self.undervalued_teams = [
            'Tampa Bay Rays', 'Milwaukee Brewers', 'Cleveland Guardians',
            'Arizona Diamondbacks', 'Seattle Mariners', 'Miami Marlins',
            'Pittsburgh Pirates', 'Cincinnati Reds', 'Kansas City Royals'
        ]
    
    def edge_plausibility_check(self, edge, sample_size, data_quality):
        """
        ¿Es este edge REAL o es ruido estadístico?
        
        Returns: 'REAL', 'SUSPECT', 'NOISE'
        """
        # Edge demasiado grande = sospechoso
        if abs(edge) > 0.22:
            return 'SUSPECT', -0.08  # Penalización fuerte
        
        if abs(edge) > 0.17:
            return 'SUSPECT', -0.03
        
        # Muestra pequeña = no confiable
        if sample_size < 30:
            return 'NOISE', -0.08
        
        if sample_size < 50:
            return 'SUSPECT', -0.03
        
        # Datos de baja calidad (defaults, no reales)
        if not data_quality:
            return 'SUSPECT', -0.04
        
        return 'REAL', 0.0
    
    def public_bias_factor(self, home_team, away_team):
        """
        ¿El mercado está sesgado por nombres grandes?
        Retorna ajuste de probabilidad
        """
        bias_adjustment = 0
        
        # Si el favorito es un equipo público, el mercado probablemente lo sobrevalora
        if home_team in self.public_teams:
            bias_adjustment -= 0.02  # Reducir probabilidad del favorito público
        
        if away_team in self.public_teams:
            bias_adjustment += 0.02  # El underdog puede tener más valor
        
        # Si el underdog es equipo subvalorado, el mercado lo ignora
        if home_team in self.undervalued_teams:
            bias_adjustment += 0.02  # Equipos subvalorados tienen edge oculto
        
        if away_team in self.undervalued_teams:
            bias_adjustment += 0.01
        
        return bias_adjustment
    
    def narrative_check(self, game_data):
        """
        Detecta narrativas que el mercado puede estar sobrevalorando
        """
        narratives = []
        
        # Racha ganadora grande = mercado sobre-reacciona
        home_streak = game_data.get('home_momentum', {}).get('streak', 0)
        away_streak = game_data.get('away_momentum', {}).get('streak', 0)
        
        if abs(home_streak) >= 5:
            narratives.append({
                'type': 'streak_overreaction',
                'team': game_data.get('home_team'),
                'adjustment': -0.015  # El mercado sobrevalora rachas
            })
        
        if abs(away_streak) >= 5:
            narratives.append({
                'type': 'streak_overreaction',
                'team': game_data.get('away_team'),
                'adjustment': -0.015
            })
        
        # Pitcher estrella vs equipo débil = línea inflada
        home_pitcher = game_data.get('home_pitcher', {})
        away_pitcher = game_data.get('away_pitcher', {})
        
        if home_pitcher.get('era', 4.50) < 2.80 and game_data.get('away_win_pct', 0.5) < 0.42:
            narratives.append({
                'type': 'ace_vs_weak_team',
                'team': game_data.get('home_team'),
                'adjustment': -0.02  # Línea probablemente inflada
            })
        
        if away_pitcher.get('era', 4.50) < 2.80 and game_data.get('home_win_pct', 0.5) < 0.42:
            narratives.append({
                'type': 'ace_vs_weak_team',
                'team': game_data.get('away_team'),
                'adjustment': -0.02
            })
        
        return narratives
    
    def market_context_score(self, game_data, model_prob, market_prob, edge):
        """
        Evalúa el CONTEXTO completo del mercado
        Retorna score 0-1 de calidad del edge
        """
        score = 0.5  # Base neutral
        
        # 1. Plausibilidad del edge
        sample_size = game_data.get('home_matchup', {}).get('pa', 50)
        data_quality = game_data.get('home_pitcher', {}).get('innings', 0) > 10
        
        plausibility, penalty = self.edge_plausibility_check(edge, sample_size, data_quality)
        score += penalty
        
        # 2. Sesgo público
        bias = self.public_bias_factor(
            game_data.get('home_team', ''),
            game_data.get('away_team', '')
        )
        score += bias
        
        # 3. Narrativas
        narratives = self.narrative_check(game_data)
        for n in narratives:
            score += n.get('adjustment', 0)
        
        # 4. Si el edge es enorme, desconfiar
        if abs(edge) > 0.25:
            score -= 0.15
        elif abs(edge) > 0.18:
            score -= 0.08
        
        # 5. Si el mercado ya ajustó (línea muy diferente a apertura)
        opening_line = game_data.get('opening_odds', game_data.get('odds', 2.0))
        current_line = game_data.get('odds', 2.0)
        line_movement = abs(current_line - opening_line) if opening_line else 0
        
        if line_movement > 0.15:
            score -= 0.05  # El mercado ya se movió, edge puede ser menor
        
        return max(0.0, min(1.0, score))
    
    def edge_quality_label(self, edge, market_context_score, probability, volatility):
        """
        Clasifica la CALIDAD del edge
        """
        if market_context_score >= 0.70 and edge > 0.03 and volatility < 0.50:
            return 'STRUCTURAL'  # Edge real y sostenible
        
        if market_context_score >= 0.55 and edge > 0.02:
            return 'FUNDAMENTAL'  # Edge basado en fundamentos
        
        if edge > 0.10 and market_context_score < 0.50:
            return 'SUSPECT'  # Edge probablemente inflado
        
        if edge > 0 and market_context_score >= 0.60:
            return 'VALUE'  # Hay valor pero no enorme
        
        if edge <= 0:
            return 'NO_EDGE'
        
        return 'MARGINAL'  # Muy pequeño para confiar
    
    def final_decision(self, game_data, model_result):
        """
        Decisión FINAL considerando market intelligence
        """
        probability = model_result['probability']
        edge = model_result['edge']
        volatility = model_result['volatility']
        market_prob = model_result['market_prob']
        
        # Market context
        context_score = self.market_context_score(
            game_data, probability, market_prob, edge
        )
        
        # Edge quality
        edge_quality = self.edge_quality_label(edge, context_score, probability, volatility)
        
        # Decisión
        approved = (
            edge > 0.02 and
            probability >= 0.52 and
            volatility <= 0.68 and
            context_score >= 0.38 and
            edge_quality in ['STRUCTURAL', 'FUNDAMENTAL', 'VALUE', 'SUSPECT']
        )
        
        return {
            'context_score': round(context_score, 3),
            'edge_quality': edge_quality,
            'approved': approved,
            'reason': f"Edge: {edge_quality} | Context: {context_score:.2f}"
        }