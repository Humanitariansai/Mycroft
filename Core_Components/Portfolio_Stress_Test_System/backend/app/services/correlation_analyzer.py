import pandas as pd
import numpy as np
from typing import Dict, Tuple
import logging

logger = logging.getLogger("portfolio_analysis.correlation_analyzer")

class CorrelationAnalyzer:
    """Service for calculating correlation matrices and diversification metrics"""
    
    @staticmethod
    def calculate_regime_correlations(
        returns: pd.DataFrame,
        regimes: pd.Series,
        rolling_window: int = 252
    ) -> Dict[str, pd.DataFrame]:
        """
        Calculate correlation matrices for each regime
        
        Returns:
            Dict mapping regime name -> correlation matrix DataFrame
        """
        logger.info(f"Calculating regime-specific correlation matrices (window={rolling_window})")
        
        regime_correlations = {}
        
        for regime_name in ['low', 'medium', 'high']:
            # Filter returns for this regime
            regime_mask = regimes == regime_name
            regime_returns = returns[regime_mask]
            
            if len(regime_returns) < rolling_window:
                logger.warning(
                    f"Insufficient data for {regime_name} regime: "
                    f"{len(regime_returns)} days (need {rolling_window})"
                )
                # Use whatever data we have
                corr_matrix = regime_returns.corr()
            else:
                # Calculate correlation on regime-filtered data
                corr_matrix = regime_returns.corr()
            
            regime_correlations[regime_name] = corr_matrix
            logger.info(f"  {regime_name.capitalize()} regime: {len(regime_returns)} days, avg corr = {CorrelationAnalyzer._avg_correlation(corr_matrix):.3f}")
        
        return regime_correlations
    
    @staticmethod
    def calculate_diversification_metrics(
        correlation_matrix: pd.DataFrame,
        weights: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate diversification metrics from correlation matrix
        
        Returns:
            Dict with avg_pairwise_correlation, max_correlation, effective_n_assets
        """
        # Align weights with correlation matrix
        tickers = correlation_matrix.columns.tolist()
        weight_array = np.array([weights.get(t, 0) for t in tickers])
        
        # Average pairwise correlation (portfolio-weighted)
        avg_corr = CorrelationAnalyzer._weighted_avg_correlation(
            correlation_matrix.values, 
            weight_array
        )
        
        # Max and min correlations
        upper_tri = np.triu(correlation_matrix.values, k=1)
        max_corr = upper_tri.max()
        min_corr = upper_tri[upper_tri != 0].min() if np.any(upper_tri != 0) else 0
        
        # Effective number of assets
        # N_eff = 1 / sum(w_i * w_j * correlation_ij)
        weighted_corr_sum = 0
        for i in range(len(weight_array)):
            for j in range(len(weight_array)):
                weighted_corr_sum += weight_array[i] * weight_array[j] * correlation_matrix.iloc[i, j]
        
        effective_n = 1 / weighted_corr_sum if weighted_corr_sum > 0 else len(tickers)
        
        return {
            'avg_pairwise_correlation': float(avg_corr),
            'max_correlation': float(max_corr),
            'min_correlation': float(min_corr),
            'effective_n_assets': float(effective_n)
        }
    
    @staticmethod
    def _avg_correlation(corr_matrix: pd.DataFrame) -> float:
        """Calculate simple average of off-diagonal correlations"""
        upper_tri = np.triu(corr_matrix.values, k=1)
        n_pairs = len(corr_matrix) * (len(corr_matrix) - 1) / 2
        return upper_tri.sum() / n_pairs if n_pairs > 0 else 0
    
    @staticmethod
    def _weighted_avg_correlation(corr_matrix: np.ndarray, weights: np.ndarray) -> float:
        """Calculate portfolio-weighted average correlation"""
        n = len(weights)
        weighted_sum = 0
        weight_sum = 0
        
        for i in range(n):
            for j in range(i + 1, n):
                weight_product = weights[i] * weights[j]
                weighted_sum += weight_product * corr_matrix[i, j]
                weight_sum += weight_product
        
        return weighted_sum / weight_sum if weight_sum > 0 else 0



