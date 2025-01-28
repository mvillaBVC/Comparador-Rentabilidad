# src/portfolio.py
import pandas as pd

class Portfolio:
    def __init__(self):
        self.assets = []

    def add_asset(self, ticker, cantidad):
        """Añade un activo al portafolio."""
        self.assets.append({"ticker": ticker.upper(), "cantidad": cantidad})

    def list_assets(self):
        """Lista los activos agregados al portafolio."""
        return self.assets

    def simulate(self, prices_df, date=None):
        """Simula el valor del portafolio en una fecha específica o la última fecha disponible."""
        total_value = 0
        if date:
            if date not in prices_df['DATE'].dt.date.values:
                raise ValueError(f"La fecha {date} no está disponible en los datos.")
            row = prices_df[prices_df['DATE'].dt.date == date].iloc[0]
        else:
            row = prices_df.iloc[-1]  # Última fecha disponible

        for asset in self.assets:
            ticker = asset["ticker"]
            cantidad = asset["cantidad"]
            if ticker in row.index:
                precio = row[ticker]
                total_value += precio * cantidad
            else:
                print(f"Advertencia: Ticker {ticker} no encontrado en los precios.")
        return total_value

    def calculate_returns(self, prices_df, start_date=None, end_date=None):
        """Calcula el rendimiento histórico del portafolio."""
        if start_date:
            if start_date not in prices_df['DATE'].dt.date.values:
                raise ValueError(f"La fecha de inicio {start_date} no está disponible en los datos.")
            start_row = prices_df[prices_df['DATE'].dt.date == start_date].iloc[0]
        else:
            start_row = prices_df.iloc[0]

        if end_date:
            if end_date not in prices_df['DATE'].dt.date.values:
                raise ValueError(f"La fecha de fin {end_date} no está disponible en los datos.")
            end_row = prices_df[prices_df['DATE'].dt.date == end_date].iloc[0]
        else:
            end_row = prices_df.iloc[-1]

        initial_value = 0
        final_value = 0

        for asset in self.assets:
            ticker = asset["ticker"]
            cantidad = asset["cantidad"]
            if ticker in prices_df.columns:
                initial_value += start_row[ticker] * cantidad
                final_value += end_row[ticker] * cantidad
            else:
                print(f"Advertencia: Ticker {ticker} no encontrado en los precios.")

        if initial_value == 0:
            return 0  # Evitar división por cero
        return ((final_value - initial_value) / initial_value) * 100
