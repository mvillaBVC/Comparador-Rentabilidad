# src/main.py
from utils import load_prices, load_dictionary, map_tickers
from portfolio import Portfolio
import json

def main():
    # Cargar datos
    prices_df = load_prices('../precios.xlsx')
    dictionary = load_dictionary('../diccionario.json')

    # Mapear tickers
    prices_df, ticker_info = map_tickers(prices_df, dictionary)

    # Crear portafolio
    portfolio = Portfolio()
    portfolio.add_asset("CSPX LN EQUITY", 10)  # Ejemplo: 10 unidades de CSPX
    portfolio.add_asset("QQQ US EQUITY", 5)    # Ejemplo: 5 unidades de QQQ

    # Simular
    total_value = portfolio.simulate(prices_df)
    print(f"Valor total del portafolio: ${total_value:.2f}")

    # Mostrar información de los activos
    for asset in portfolio.assets:
        ticker = asset["ticker"]
        if ticker in ticker_info:
            print(f"\nInformación de {ticker}:")
            print(json.dumps(ticker_info[ticker], indent=4, ensure_ascii=False))

if __name__ == "__main__":
    main()