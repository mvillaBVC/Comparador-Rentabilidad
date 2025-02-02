import pandas as pd
import plotly.graph_objects as go
import streamlit as st

def plot_portfolio_value(portfolio, prices_df, start_date, end_date):
    """Genera un gráfico interactivo de área del valor del portafolio en el tiempo usando Plotly."""
    
    # Filtrar precios en el rango de fechas seleccionado
    mask = (prices_df["DATE"].dt.date >= start_date) & (prices_df["DATE"].dt.date <= end_date)
    filtered_prices = prices_df.loc[mask]

    if filtered_prices.empty:
        st.warning("⚠️ No hay datos de precios en el rango de fechas seleccionado.")
        return

    # Calcular el valor del portafolio en cada fecha
    portfolio_values = []
    dates = []

    for date in filtered_prices["DATE"].dt.date.unique():
        value = portfolio.simulate(prices_df, date)
        portfolio_values.append(value)
        dates.append(date)

    # Crear gráfico de área con Plotly
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=dates, 
        y=portfolio_values,
        mode='lines',  # 🔹 Solo líneas, sin puntos
        fill='tozeroy',  # 🔹 Rellena el área bajo la línea
        name='Valor del Portafolio',
        line=dict(color='royalblue', width=2)
    ))

    # Personalizar el diseño del gráfico
    fig.update_layout(
        title="📈 Evolución del Valor del Portafolio",
        xaxis_title="Fecha",
        yaxis_title="Valor en USD",
        template="plotly_white",
        hovermode="x unified",
        showlegend=False
    )

    # Mostrar el gráfico en Streamlit
    st.plotly_chart(fig, use_container_width=True)
