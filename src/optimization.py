import numpy as np
import pandas as pd
import gurobipy as gp
from gurobipy import GRB
import plotly.graph_objects as go
import streamlit as st

def optimize_portfolio_gurobi(prices_df, selected_assets, objective="return", custom_bounds=None):
    """
    Optimiza el portafolio usando Gurobi con restricciones inteligentes.
    
    Objetivos disponibles:
    - 'return': Maximizar retorno esperado.
    - 'volatility': Minimizar volatilidad.
    - 'sharpe': Maximizar Sharpe Ratio.
    
    custom_bounds (dict): Diccionario con los límites de cada activo, ej:
        {'AAPL': (0.05, 0.50), 'MSFT': (0.10, 0.40)}
    """

    # Filtrar activos y calcular retornos diarios
    returns = prices_df.set_index("DATE")[selected_assets].pct_change().dropna()
    
    # Calcular retornos esperados anualizados
    mean_daily_returns = returns.mean()
    expected_returns = mean_daily_returns * 252
    expected_returns = (expected_returns - expected_returns.min()) / (expected_returns.max() - expected_returns.min())  # Normalización
    n_assets = len(expected_returns)

    # Validar número de activos
    if n_assets == 0:
        st.warning("⚠️ No seleccionaste ningún activo.")
        return None

    # Crear modelo Gurobi
    model = gp.Model("portfolio_optimization")

    # Definir límites dinámicos
    if n_assets == 1:
        min_weight, max_weight = 1.0, 1.0  # Todo el capital en el único activo
    elif n_assets == 2:
        min_weight, max_weight = 0.2, 0.7  # Permitir hasta 70% en un solo activo
    else:
        min_weight, max_weight = 0.05, min(1.0, 0.5 / (n_assets / 2))  # Distribución razonable

    # Variables de decisión con límites dinámicos o personalizados
    weights_vars = {}
    for asset in selected_assets:
        lb, ub = custom_bounds.get(asset, (min_weight, max_weight)) if custom_bounds else (min_weight, max_weight)
        weights_vars[asset] = model.addVar(lb=lb, ub=ub, name=f"weight_{asset}")

    # Restricción: la suma de los pesos debe ser 1
    model.addConstr(gp.quicksum(weights_vars[asset] for asset in selected_assets) == 1, "sum_weights")

    # Definir función objetivo
    if objective == "return":
        model.setObjective(gp.quicksum(weights_vars[asset] * expected_returns[asset] for asset in selected_assets), GRB.MAXIMIZE)

    elif objective == "volatility":
        cov_matrix = returns.cov() * 252
        portfolio_variance = gp.quicksum(
            weights_vars[a] * weights_vars[b] * cov_matrix.loc[a, b] for a in selected_assets for b in selected_assets
        )
        model.setObjective(portfolio_variance, GRB.MINIMIZE)

    elif objective == "sharpe":
        risk_free_rate = 0.02
        cov_matrix = returns.cov() * 252  # Matriz de covarianza anualizada
        
        # Calcular varianza del portafolio
        portfolio_variance = gp.quicksum(
            weights_vars[a] * weights_vars[b] * cov_matrix.loc[a, b] for a in selected_assets for b in selected_assets
        )

        # Variable auxiliar para la desviación estándar (raíz cuadrada de la varianza)
        portfolio_risk = model.addVar(name="portfolio_risk")

        # Restricción para que portfolio_risk sea la raíz cuadrada de portfolio_variance
        model.addConstr(portfolio_risk * portfolio_risk == portfolio_variance, "sqrt_risk")

        # Calcular retorno esperado del portafolio
        expected_portfolio_return = gp.quicksum(weights_vars[asset] * expected_returns[asset] for asset in selected_assets)

        # ✅ Nueva formulación: Maximizar (Retorno - Tasa libre de riesgo - penalización por riesgo)
        model.setObjective((expected_portfolio_return - risk_free_rate) - 0.01 * portfolio_risk, GRB.MAXIMIZE)


    else:
        raise ValueError("Objetivo no reconocido. Usa 'return', 'volatility' o 'sharpe'.")

    # Optimizar modelo
    model.optimize()

    # Obtener resultados
    if model.status == GRB.OPTIMAL:
        optimized_weights = {asset: weights_vars[asset].X for asset in selected_assets}
        return optimized_weights
    else:
        st.warning("⚠️ No se encontró una solución óptima.")
        return None


def plot_efficient_frontier_gurobi(prices_df, selected_assets):
    """
    Genera y grafica la Frontera Eficiente usando Gurobi con una mejor distribución de riesgo.
    """

    returns = prices_df.set_index("DATE")[selected_assets].pct_change().dropna()
    expected_returns = returns.mean() * 252  # Retorno esperado anualizado
    cov_matrix = returns.cov() * 252  # Matriz de covarianza anualizada

    # Determinar los límites mínimo y máximo de volatilidad
    min_volatility = np.sqrt(np.min(np.diag(cov_matrix)))  # Activo menos riesgoso
    max_volatility = np.sqrt(np.max(np.diag(cov_matrix)))  # Activo más riesgoso
    risk_levels = np.linspace(min_volatility * 0.5, max_volatility * 1.5, 50)  # 50 niveles bien distribuidos

    optimal_returns = []

    for risk in risk_levels:
        model = gp.Model("efficient_frontier")
        weights = model.addVars(len(selected_assets), lb=0, ub=1, name="weights")

        # Restricción: La suma de los pesos debe ser 1
        model.addConstr(gp.quicksum(weights[i] for i in range(len(selected_assets))) == 1, "sum_weights")

        # Calcular varianza del portafolio
        portfolio_variance = gp.quicksum(
            weights[i] * weights[j] * cov_matrix.iloc[i, j] 
            for i in range(len(selected_assets)) for j in range(len(selected_assets))
        )

        # Restricción de volatilidad
        model.addConstr(portfolio_variance <= risk**2, "risk_constraint")

        # Maximizar retorno esperado
        portfolio_return = gp.quicksum(weights[i] * expected_returns.iloc[i] for i in range(len(selected_assets)))
        model.setObjective(portfolio_return, GRB.MAXIMIZE)
        model.optimize()

        if model.status == GRB.OPTIMAL:
            optimal_returns.append(portfolio_return.getValue())
        else:
            optimal_returns.append(None)

    # **Corrección importante:** Filtramos valores None para evitar problemas en el gráfico
    risk_levels_filtered = [r for r, ret in zip(risk_levels, optimal_returns) if ret is not None]
    optimal_returns_filtered = [ret for ret in optimal_returns if ret is not None]

    # Crear gráfico con Plotly
    fig = go.Figure()

    # Agregar la Frontera Eficiente
    fig.add_trace(go.Scatter(
        x=risk_levels_filtered, 
        y=optimal_returns_filtered,
        mode='lines',
        fill='tozeroy',
        name='Frontera Eficiente',
        line=dict(color='green', width=2)
    ))

    # Agregar punto del portafolio de mínima volatilidad
    min_risk_index = np.argmin(risk_levels_filtered)
    fig.add_trace(go.Scatter(
        x=[risk_levels_filtered[min_risk_index]],
        y=[optimal_returns_filtered[min_risk_index]],
        mode='markers',
        marker=dict(color='red', size=10),
        name='Portafolio Mínima Volatilidad'
    ))

    # Personalizar gráfico
    fig.update_layout(
        title="📈 Frontera Eficiente de Portafolio",
        xaxis_title="Riesgo (Volatilidad Anualizada)",
        yaxis_title="Retorno Esperado",
        template="plotly_white",
        hovermode="x unified"
    )

    # Mostrar en Streamlit
    st.plotly_chart(fig, use_container_width=True)


