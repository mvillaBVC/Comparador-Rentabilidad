import pandas as pd

class Portfolio:
    def __init__(self, initial_capital=1000):
        self.initial_capital = initial_capital
        self.assets = []  # Lista de activos con su % de inversión y cantidad comprada

    def add_asset(self, ticker, percentage, prices_df, start_date=None):
        """Añade un activo al portafolio asignando un porcentaje del capital inicial."""
        ticker = ticker.upper().strip()

        if not (0 < percentage <= 100):
            raise ValueError("El porcentaje debe estar entre 0 y 100.")

        # Si no se proporciona start_date, tomar la primera fecha válida del ticker
        if start_date is None:
            valid_dates = prices_df.loc[~prices_df[ticker].isna(), "DATE"]
            if valid_dates.empty:
                print(f"⚠️ {ticker} nunca ha tenido datos de precio. No se agregará al portafolio.")
                return  # No agregar el activo
            start_date = valid_dates.min().date()  # Primera fecha donde el ticker tiene datos

        start_row = prices_df[prices_df["DATE"].dt.date == start_date].iloc[0]

        price = start_row[ticker]
        allocated_amount = (self.initial_capital * percentage) / 100  # Monto a invertir
        quantity = allocated_amount / price  # Cantidad de unidades compradas

        self.assets.append({
            "ticker": ticker,
            "percentage": percentage,
            "cantidad": quantity,
            "initial_price": price,
            "initial_value": allocated_amount,
            "start_date": start_date  # Guardamos la fecha inicial válida
        })

        print(f"✅ {ticker}: Asignados ${allocated_amount:.2f}, Precio inicial: ${price:.2f}, Cantidad: {quantity:.4f}, Fecha inicio: {start_date}")

    def list_assets(self):
        """Lista los activos en el portafolio."""
        return self.assets

    def simulate(self, prices_df, date):
        """Calcula el valor actual del portafolio basado en los precios de los activos en una fecha específica."""
        if date not in prices_df["DATE"].dt.date.values:
            raise ValueError(f"⚠️ La fecha {date} no está disponible en los datos.")

        row = prices_df[prices_df["DATE"].dt.date == date].iloc[0]
        total_value = 0
        print(f"\n📅 Simulación del portafolio en {date}:")

        for asset in self.assets:
            ticker = asset["ticker"]
            cantidad = asset["cantidad"]
            initial_value = asset["initial_value"]

            if ticker in row.index and not pd.isna(row[ticker]):
                price = row[ticker]
                current_value = price * cantidad
                total_value += current_value
                
                print(f"📈 {ticker}: Cantidad: {cantidad:.4f}, Precio actual: ${price:.2f}, Valor actual: ${current_value:.2f} (vs ${initial_value:.2f} inicial)")
            else:
                print(f"⚠️ {ticker}: No se encontró precio para esta fecha.")

        print(f"💰 Valor total del portafolio en {date}: ${total_value:.2f}")
        return total_value

    def calculate_returns(self, prices_df, start_date, end_date):
        """Calcula el rendimiento del portafolio entre dos fechas."""
        
        if start_date not in prices_df["DATE"].dt.date.values or end_date not in prices_df["DATE"].dt.date.values:
            raise ValueError("Una de las fechas seleccionadas no está disponible en los datos.")

        print(f"\n📊 Calculando rendimiento del portafolio de {start_date} a {end_date}...")

        start_value = self.simulate(prices_df, start_date)
        end_value = self.simulate(prices_df, end_date)

        print(f"🔍 Valor inicial: ${start_value:.2f}, Valor final: ${end_value:.2f}")

        if start_value == 0:
            print("⚠️ El valor inicial del portafolio es 0, no se puede calcular el rendimiento.")
            return None  # Evitar división por cero
        
        # Corrección: Asegurar que se calcula el rendimiento correctamente
        returns = ((end_value - start_value) / start_value) * 100
        print(f"📉 Rendimiento total del portafolio: {returns:.2f}%")

        return returns

