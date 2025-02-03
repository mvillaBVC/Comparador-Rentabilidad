import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import scipy.optimize as sc


class PortfolioOptimization:
    """
    Clase para realizar optimización de portafolios, incluyendo:
    - Maximización del ratio de Sharpe.
    - Minimización de la volatilidad.
    - Maximización del retorno esperado.
    """

    def __init__(self, prices_df, selected_assets, objective="sharpe", risk_free_rate=0.02, constraint_set=(0, 1)):
        """
        Inicializa la optimización del portafolio.

        Parámetros:
        - prices_df (DataFrame): Datos históricos de precios de los activos.
        - selected_assets (list): Lista de activos seleccionados.
        - objective (str): 'return', 'volatility' o 'sharpe'.
        - risk_free_rate (float): Tasa libre de riesgo (por defecto 0.02).
        - constraint_set (tuple): Límites de pesos de los activos (por defecto (0,1)).
        """
        if not selected_assets:
            st.warning("⚠️ No seleccionaste ningún activo.")
            return None

        self.returns = prices_df.set_index("DATE")[selected_assets].pct_change().dropna()
        self.mean_returns = self.returns.mean() * 252  # Retornos esperados anualizados
        self.cov_matrix = self.returns.cov() * 252  # Matriz de covarianza anualizada
        self.selected_assets = selected_assets
        self.objective = objective
        self.risk_free_rate = risk_free_rate
        self.constraint_set = constraint_set

    def _negative_sharpe(self, weights):
        """ Calcula el Sharpe Ratio negativo para maximización. """
        portfolio_return = np.dot(weights, self.mean_returns)
        portfolio_std = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
        return -(portfolio_return - self.risk_free_rate) / portfolio_std  # Se multiplica por -1 para maximizar

    def _portfolio_std(self, weights):
        """ Calcula la desviación estándar (volatilidad) del portafolio. """
        return np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))

    def _negative_return(self, weights):
        """ Calcula el retorno negativo del portafolio para maximización. """
        return -np.dot(weights, self.mean_returns)

    def optimize(self):
        """ Ejecuta la optimización según el objetivo seleccionado. """
        num_assets = len(self.selected_assets)
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})  # Restricción: suma de pesos = 1
        bounds = tuple(self.constraint_set for _ in range(num_assets))

        # Selección del objetivo
        if self.objective == "sharpe":
            result = sc.minimize(self._negative_sharpe, num_assets * [1. / num_assets], method='SLSQP', bounds=bounds, constraints=constraints)
        elif self.objective == "volatility":
            result = sc.minimize(self._portfolio_std, num_assets * [1. / num_assets], method='SLSQP', bounds=bounds, constraints=constraints)
        elif self.objective == "return":
            result = sc.minimize(self._negative_return, num_assets * [1. / num_assets], method='SLSQP', bounds=bounds, constraints=constraints)
        else:
            raise ValueError("Objetivo no reconocido. Usa 'return', 'volatility' o 'sharpe'.")

        if result.success:
            optimized_weights = dict(zip(self.selected_assets, result.x))
            return optimized_weights
        else:
            st.warning("⚠️ No se encontró una solución óptima.")
            return None

    def plot_efficient_frontier(self):
        """ Genera y grafica la Frontera Eficiente. """
        risk_levels = np.linspace(0.05, 0.5, 50)
        optimal_returns = []

        for risk in risk_levels:
            num_assets = len(self.selected_assets)
            weights = np.ones(num_assets) / num_assets
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # Suma de pesos = 1
                {'type': 'ineq', 'fun': lambda x: risk - np.sqrt(np.dot(x.T, np.dot(self.cov_matrix, x)))}
            ]
            bounds = tuple(self.constraint_set for _ in range(num_assets))

            result = sc.minimize(self._negative_return, weights, method='SLSQP', bounds=bounds, constraints=constraints)

            if result.success:
                optimal_returns.append(-result.fun)  # Multiplicado por -1 para reflejar el retorno real
            else:
                optimal_returns.append(None)

        # Filtrar valores inválidos
        risk_levels_filtered = [r for r, ret in zip(risk_levels, optimal_returns) if ret is not None]
        optimal_returns_filtered = [ret for ret in optimal_returns if ret is not None]

        if not risk_levels_filtered:
            st.warning("⚠️ No se pudo calcular la frontera eficiente.")
            return

        # Crear gráfico con Plotly
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=risk_levels_filtered,
            y=optimal_returns_filtered,
            mode='lines',
            name='Frontera Eficiente',
            line=dict(color='green', width=2)
        ))

        # Personalizar gráfico
        fig.update_layout(
            title="📈 Frontera Eficiente de Portafolio",
            xaxis_title="Riesgo (Volatilidad Anualizada)",
            yaxis_title="Retorno Esperado",
            template="plotly_white"
        )

        # Mostrar en Streamlit
        st.plotly_chart(fig, use_container_width=True)
