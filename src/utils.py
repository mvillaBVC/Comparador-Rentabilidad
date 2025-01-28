# src/utils.py
import pandas as pd
import json

def load_prices(filepath):
    df = pd.read_excel(filepath)
    df['DATE'] = pd.to_datetime(df['DATE']).dt.normalize()  # Convertir a datetime
    return df

def load_dictionary(filepath):
    """Carga el diccionario JSON."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


# src/utils.py

def map_tickers(prices_df, dictionary):
    """Mapea los tickers a nombres y categorías con validación."""
    # Normalizar nombres de columnas (eliminar espacios y convertir a mayúsculas)
    prices_df.columns = [col.strip().upper() for col in prices_df.columns]
    
    # Validación de tickers
    valid_tickers = set(prices_df.columns)
    invalid_tickers = [ticker for ticker in valid_tickers if ticker not in dictionary]
    
    if invalid_tickers:
        print(f"Advertencia: Los siguientes tickers no están en el diccionario: {', '.join(invalid_tickers)}")
    
    # Crear un DataFrame con la información del diccionario
    ticker_info = {ticker.upper(): info for ticker, info in dictionary.items()}
    return prices_df, ticker_info
