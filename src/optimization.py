import numpy as np
import pandas as pd
import cvxpy as cp
import plotly.graph_objects as go
import streamlit as st

def optimize_portfolio(prices_df, selected_assets, objective="return", custom_bounds=None):
    """
    Optimiza el portafolio usando `cvxpy` con restricciones inteligentes.

    Objetivos disponibles:
    - 'return': Maximizar retorno esperado.
    - 'volatility': Minimizar volatilidad.
    - 'sharpe': Maximizar Sharpe Ratio.

    custom_bounds (dict): Diccionario con los límites de cada activo, ej:
        {'AAPL': (0.05, 0.50), 'MSFT': (0.10, 0.40)}
    """

    # Verificar si hay activos seleccionados
    if not selected_assets:
        st.warning("⚠️ No seleccionaste ningún activo.")
        return None

    # Filtrar activos y calcular retornos diarios
    returns = prices_df.set_index("DATE")[selected_assets].pct_change().dropna()

    # Calcular retornos esperados anualizados y matriz de covarianza
    expected_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252  # Matriz de covarianza anualizada

    n_assets = len(selected_assets)
    weights = cp.Variable(n_assets)  # Variable de pesos

    # Restricción: la suma de los pesos debe ser 1
    constraints = [cp.sum(weights) == 1, weights >= 0]

    # Aplicar límites personalizados (si existen)
    if custom_bounds:
        for i, asset in enumerate(selected_assets):
            if asset in custom_bounds:
                min_w, max_w = custom_bounds[asset]
                constraints.append(weights[i] >= min_w)
                constraints.append(weights[i] <= max_w)

    # Definir la función objetivo
    if objective == "return":
        obj_function = cp.Maximize(expected_returns.values @ weights)

    elif objective == "volatility":
        obj_function = cp.Minimize(cp.quad_form(weights, cov_matrix))

    elif objective == "sharpe":
        risk_free_rate = 0.02
        portfolio_variance = cp.quad_form(weights, cov_matrix)
        expected_portfolio_return = expected_returns.values @ weights
        sharpe_ratio = (expected_portfolio_return - risk_free_rate) / cp.sqrt(portfolio_variance)
        obj_function = cp.Maximize(sharpe_ratio)

    else:
        raise ValueError("Objetivo no reconocido. Usa 'return', 'volatility' o 'sharpe'.")

    # Resolver la optimización
    problem = cp.Problem(obj_function, constraints)
    
    try:
        problem.solve()
        if problem.status not in ["optimal", "optimal_inaccurate"]:
            st.warning("⚠️ No se encontró una solución óptima.")
            return None
    except Exception as e:
        st.error(f"❌ Error en la optimización: {str(e)}")
        return None

    # Obtener los pesos optimizados
    optimized_weights = dict(zip(selected_assets, weights.value))

    return optimized_weights


def plot_efficient_frontier(prices_df, selected_assets):
    """
    Genera y grafica la Frontera Eficiente usando `cvxpy`.
    """

    # Verificar si hay activos seleccionados
    if not selected_assets:
        st.warning("⚠️ No hay activos seleccionados para graficar la frontera eficiente.")
        return

    returns = prices_df.set_index("DATE")[selected_assets].pct_change().dropna()
    expected_returns = returns.mean() * 252  # Retorno esperado anualizado
    cov_matrix = returns.cov() * 252  # Matriz de covarianza anualizada

    # Definir niveles de riesgo (volatilidad)
    risk_levels = np.linspace(0.05, 0.5, 50)
    optimal_returns = []

    for risk in risk_levels:
        weights = cp.Variable(len(selected_assets))
        constraints = [cp.sum(weights) == 1, weights >= 0]
        portfolio_variance = cp.quad_form(weights, cov_matrix)

        constraints.append(cp.sqrt(portfolio_variance) <= risk)
        portfolio_return = expected_returns.values @ weights

        problem = cp.Problem(cp.Maximize(portfolio_return), constraints)
        
        try:
            problem.solve()
            if problem.status == cp.OPTIMAL:
                optimal_returns.append(portfolio_return.value)
            else:
                optimal_returns.append(None)
        except:
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
