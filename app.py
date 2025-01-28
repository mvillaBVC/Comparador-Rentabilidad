import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Función para calcular proyección de ahorro
def calcular_futuro(ahorro_mensual, años, rendimiento_anual, inflacion_anual):
    meses = años * 12
    rendimiento_mensual = (1 + rendimiento_anual/100) ** (1/12) - 1
    inflacion_mensual = (1 + inflacion_anual/100) ** (1/12) - 1
    total = 0
    datos = []
    
    for mes in range(1, meses + 1):
        total += ahorro_mensual
        rendimiento = total * rendimiento_mensual
        inflacion = total * inflacion_mensual
        total += rendimiento - inflacion
        if mes % 12 == 0:
            datos.append({
                "Año": mes // 12,
                "Total": round(total, 2),
                "Ahorro Acumulado": ahorro_mensual * mes,
                "Rendimiento": round(rendimiento * 12, 2),
                "Inflación": round(inflacion * 12, 2)
            })
    
    return pd.DataFrame(datos)

# Configuración de la página
st.set_page_config(page_title="Simulador de Retiro", layout="wide")
st.title("🤑 Simulador de Plan de Retiro (MVP)")

# Sidebar: Entradas del usuario
with st.sidebar:
    st.header("Perfil del Usuario")
    edad_actual = st.number_input("Edad actual", min_value=18, max_value=100, value=30)
    edad_retiro = st.number_input("Edad de retiro", min_value=edad_actual+1, max_value=100, value=65)
    ahorro_mensual = st.number_input("Ahorro mensual ($)", min_value=100, value=500)
    riesgo = st.selectbox("Tolerancia al riesgo", ["Conservador", "Moderado", "Agresivo"])
    
    # Parámetros según riesgo
    if riesgo == "Conservador":
        rendimiento, inflacion = 5.0, 3.0
    elif riesgo == "Moderado":
        rendimiento, inflacion = 7.0, 3.5
    else:
        rendimiento, inflacion = 9.0, 4.0

    st.markdown(f"**Rendimiento anual estimado:** {rendimiento}%")
    st.markdown(f"**Inflación anual estimada:** {inflacion}%")

# Calcular proyección
años = edad_retiro - edad_actual
df = calcular_futuro(ahorro_mensual, años, rendimiento, inflacion)

# Mostrar resultados
col1, col2 = st.columns(2)
with col1:
    st.subheader("Proyección de Retiro")
    st.dataframe(df.style.highlight_max(axis=0, color="#90EE90"), height=300)
    
with col2:
    st.subheader("Evolución del Patrimonio")
    fig, ax = plt.subplots()
    ax.plot(df["Año"], df["Total"], label="Total (ajustado por inflación)", marker="o")
    ax.plot(df["Año"], df["Ahorro Acumulado"], label="Ahorro acumulado", linestyle="--")
    ax.set_xlabel("Años")
    ax.set_ylabel("Monto ($)")
    ax.legend()
    st.pyplot(fig)

# Recomendación final
total_final = df["Total"].iloc[-1] if not df.empty else 0
st.success(f"""
**Recomendación:**  
Para un perfil **{riesgo}**, ahorrando **${ahorro_mensual}/mes** durante **{años} años**:  
💰 **Patrimonio proyectado (ajustado por inflación):** ${total_final:,.2f}
""")