import pandas as pd
import streamlit as st
from utils import load_prices, load_dictionary, map_tickers
from portfolio import Portfolio
import json

def main():
    st.title("Simulación de Portafolio de Activos")

    # Cargar datos
    prices_df = load_prices('src/data/precios.xlsx')
    dictionary = load_dictionary('src/data/diccionario.json')

    # Mapear tickers
    prices_df, ticker_info = map_tickers(prices_df, dictionary)

    # Inicializar el portafolio en session_state
    if "portfolio" not in st.session_state:
        st.session_state.portfolio = Portfolio()

    portfolio = st.session_state.portfolio

    # Sección para añadir activos
    st.sidebar.header("Gestión de Portafolio")
    tickers = [col for col in prices_df.columns if col != 'DATE']  # Excluir DATE
    ticker = st.sidebar.selectbox("Selecciona el Ticker", options=tickers)
    cantidad = st.sidebar.number_input(f"Cantidad de {ticker}", min_value=1, step=1)

    if st.sidebar.button("Añadir al Portafolio"):
        portfolio.add_asset(ticker, cantidad)
        st.sidebar.success(f"Activo {ticker} añadido al portafolio con cantidad {cantidad}.")

    # Mostrar activos del portafolio
    st.header("Activos en el Portafolio")
    assets = portfolio.list_assets()
    if assets:
        st.table(pd.DataFrame(assets))
    else:
        st.write("No se han añadido activos al portafolio.")

    # Simulación del portafolio
    st.header("Simulación del Portafolio")
    selected_date = st.date_input("Selecciona una fecha para simular el portafolio (opcional)", value=None)

    if st.button("Simular Valor del Portafolio"):
        try:
            if selected_date:
                total_value = portfolio.simulate(prices_df, selected_date)
            else:
                total_value = portfolio.simulate(prices_df)
            st.write(f"Valor total del portafolio: ${total_value:.2f}")
        except ValueError as e:
            st.error(e)

    # Calcular rendimientos
    st.header("Cálculo de Rendimientos")
    start_date = st.date_input("Fecha de Inicio", value=None, key="start_date")
    end_date = st.date_input("Fecha de Fin", value=None, key="end_date")

    if st.button("Calcular Rendimiento del Portafolio"):
        try:
            returns = portfolio.calculate_returns(prices_df, start_date, end_date)
            st.write(f"Rendimiento del portafolio: {returns:.2f}%")
        except ValueError as e:
            st.error(e)

if __name__ == "__main__":
    main()
