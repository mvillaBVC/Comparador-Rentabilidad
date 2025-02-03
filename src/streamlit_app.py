import pandas as pd
import streamlit as st
from utils import load_prices, load_dictionary, map_tickers
from portfolio import Portfolio
from visualization import plot_portfolio_value  # ✅ Importamos el nuevo módulo
import os
from optimization import PortfolioOptimization




def main():
    st.title("📊 Simulación de Portafolio de Activos")

    # Obtener el directorio del script actual
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # Construir rutas absolutas a los archivos
    prices_path = os.path.join(BASE_DIR, "data", "precios.xlsx")
    dictionary_path = os.path.join(BASE_DIR, "data", "diccionario.json")

    # Cargar datos usando las rutas absolutas
    prices_df = load_prices(prices_path)
    dictionary = load_dictionary(dictionary_path)

    # Normalizar nombres de columnas y convertir fechas
    prices_df.columns = prices_df.columns.str.strip().str.upper()
    prices_df["DATE"] = pd.to_datetime(prices_df["DATE"], errors="coerce")

    # Filtrar solo fechas válidas
    prices_df = prices_df.dropna(subset=["DATE"]).sort_values(by="DATE")

    # Verificar fechas disponibles en los datos
    if prices_df.empty or "DATE" not in prices_df.columns:
        st.error("⚠️ No se encontraron datos de precios. Verifica el archivo `precios.xlsx`.")
        return

    available_dates = prices_df["DATE"].dt.date.unique()
    min_date, max_date = available_dates[0], available_dates[-1]
    st.sidebar.write(f"📅 Fechas disponibles: {min_date} - {max_date}")

    # Selección de la fecha de inicio del portafolio
    start_date = st.sidebar.date_input("📅 Selecciona la fecha de inicio del portafolio", min_value=min_date, max_value=max_date, value=min_date)

    # Inicializar el portafolio en session_state si no existe
    if "portfolio" not in st.session_state:
        st.session_state.portfolio = Portfolio()

    portfolio = st.session_state.portfolio

    # Sección para definir asignación del capital
    st.sidebar.header("⚖️ Gestión de Portafolio")
    tickers = [col for col in prices_df.columns if col != "DATE"]

    allocation = {}
    total_allocation = 0

    # Slider para asignar % de inversión a cada activo
    for ticker in tickers:
        percentage = st.sidebar.slider(f"% de inversión en {ticker}", 0, 100, 0, step=5)
        allocation[ticker] = percentage
        total_allocation += percentage

    # Validar que la asignación total no exceda el 100%
    if total_allocation > 100:
        st.sidebar.error("⚠️ La suma de los porcentajes no puede superar el 100%. Ajusta las asignaciones.")
    elif st.sidebar.button("✅ Crear Portafolio"):
        if total_allocation == 0:
            st.sidebar.error("Debes asignar al menos un porcentaje de inversión.")
        else:
            # Resetear portafolio y agregar activos con la distribución definida
            st.session_state.portfolio = Portfolio()
            log_messages = []
            missing_tickers = []

            for ticker, percentage in allocation.items():
                if percentage > 0:
                    valid_dates = prices_df.loc[~prices_df[ticker].isna(), "DATE"]

                    if not valid_dates.empty and start_date in valid_dates.dt.date.values:
                        st.session_state.portfolio.add_asset(ticker, percentage, prices_df, start_date)
                        log_messages.append(f"📌 {ticker}: {percentage}% asignado ({start_date})")
                    else:
                        missing_tickers.append(ticker)

            st.sidebar.success("✅ Portafolio creado exitosamente.")
            st.sidebar.text("\n".join(log_messages))

            if missing_tickers:
                st.sidebar.warning(f"⚠️ Tickers sin datos en la fecha seleccionada: {', '.join(missing_tickers)}")

    # Mostrar activos del portafolio
    st.header("📋 Activos en el Portafolio")
    assets = portfolio.list_assets()
    if assets:
        df_assets = pd.DataFrame(assets)
        df_assets["inversión_inicial"] = df_assets["initial_value"]
        df_assets = df_assets[["ticker", "percentage", "cantidad", "initial_price", "inversión_inicial"]]
        df_assets.columns = ["Ticker", "% Asignado", "Cantidad Comprada", "Precio Inicial", "Inversión Inicial"]
        st.table(df_assets)
    else:
        st.write("❌ No se han añadido activos al portafolio.")

    # Simulación del portafolio
    st.header("🔮 Simulación del Portafolio")
    selected_date = st.date_input("📅 Selecciona una fecha para simular el portafolio", min_value=start_date, max_value=max_date)

    if st.button("🔄 Simular Valor del Portafolio"):
        try:
            total_value = portfolio.simulate(prices_df, selected_date)
            st.write(f"💰 **Valor total del portafolio en {selected_date}: ${total_value:.2f}**")
        except ValueError as e:
            st.error(e)

    # Calcular rendimientos y mostrar gráfico
    st.header("📈 Evolución del Portafolio")
    start_date_rend = st.date_input("📅 Fecha de Inicio", min_value=start_date, max_value=max_date, key="start_date_rend")
    end_date = st.date_input("📅 Fecha de Fin", min_value=start_date_rend, max_value=max_date, key="end_date")

    if st.button("📊 Mostrar Evolución del Portafolio"):
        plot_portfolio_value(portfolio, prices_df, start_date_rend, end_date)

    if st.button("📊 Calcular Rendimiento del Portafolio"):
        try:
            returns = portfolio.calculate_returns(prices_df, start_date_rend, end_date)
            st.write(f"📊 **Rendimiento del portafolio de {start_date_rend} a {end_date}: {returns:.2f}%**")
        except ValueError as e:
            st.error(e)

    # Selección de los activos del portafolio
    selected_assets = [asset["ticker"] for asset in portfolio.list_assets()]

    # Verificar si hay activos seleccionados antes de continuar
    if not selected_assets:
        st.warning("⚠️ No hay activos seleccionados en el portafolio.")
    else:
        # Sección de restricciones personalizadas
        st.sidebar.header("⚖️ Restricciones de Asignación")
        custom_bounds = {}

        for asset in selected_assets:
            min_w = st.sidebar.slider(f"🔽 Mínimo % en {asset}", 0.0, 1.0, 0.05, step=0.05)
            max_w = st.sidebar.slider(f"🔼 Máximo % en {asset}", min_w, 1.0, 0.50, step=0.05)
            custom_bounds[asset] = (min_w, max_w)

    st.header("🔬 Optimización de Portafolio")
    objective = st.selectbox("Selecciona el objetivo de optimización:", ["sharpe", "volatility", "return"])

    if st.button("🚀 Optimizar Portafolio"):
        optimizer = PortfolioOptimization(prices_df, selected_assets, objective=objective)
        optimized_weights = optimizer.optimize()

        if optimized_weights:
            st.write("📊 **Pesos óptimos:**")
            st.write(pd.DataFrame(optimized_weights.items(), columns=["Activo", "Peso (%)"]))

    # Frontera Eficiente
    if st.button("📈 Mostrar Frontera Eficiente"):
        optimizer = PortfolioOptimization(prices_df, selected_assets)
        optimizer.plot_efficient_frontier()


if __name__ == "__main__":
    main()
