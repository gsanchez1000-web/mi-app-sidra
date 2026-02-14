import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Ruta Sidrera", layout="wide")
st.title("🍎 Nuestra Ruta de la Sidra")

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl="0")

# --- MAPA INTERACTIVO ---
st.subheader("📍 Toca el mapa para situar un bar o mira los existentes")

# Posición inicial (Barakaldo)
centro = [43.2974, -2.9865]
m = folium.Map(location=centro, zoom_start=15)

# Añadir los bares que ya están en el Excel al mapa
if not df.empty:
    for i, row in df.iterrows():
        if pd.notnull(row['LAT']) and pd.notnull(row['LON']):
            folium.Marker(
                [row['LAT'], row['LON']],
                popup=f"<b>{row['Nombre']}</b><br>Sidra: {row['Marca']}<br>{row['Formato']}",
                tooltip=row['Nombre'],
                icon=folium.Icon(color="red", icon="info-sign")
            ).add_to(m)

# Capturar el clic en el mapa
salida_mapa = st_folium(m, width=1000, height=500)

lat_seleccionada = None
lon_seleccionada = None

if salida_mapa and salida_mapa["last_clicked"]:
    lat_seleccionada = salida_mapa["last_clicked"]["lat"]
    lon_seleccionada = salida_mapa["last_clicked"]["lng"]
    st.success(f"📍 Ubicación seleccionada: {lat_seleccionada:.4f}, {lon_seleccionada:.4f}")

# --- FORMULARIO ---
st.divider()
with st.form("nuevo_bar"):
    st.write("### ➕ Añade un rincón sidrero")
    st.info("Primero toca en el mapa el lugar exacto y luego rellena estos datos:")
    
    nombre = st.text_input("Nombre del Bar")
    
    col1, col2 = st.columns(2)
    with col1:
        marca = st.text_input("Marca de Sidra")
    with col2:
        formato = st.selectbox("¿Cómo la sirven?", ["Pote/Vaso", "Botella entera", "Ambos"])
    
    observaciones = st.text_area("Observaciones")
    
    if st.form_submit_button("Guardar en la Ruta"):
        if nombre and lat_seleccionada:
            nueva_fila = pd.DataFrame([{
                "Nombre": nombre, 
                "LAT": lat_seleccionada, 
                "LON": lon_seleccionada, 
                "Marca": marca, 
                "Formato": formato,
                "Fecha_registro": datetime.now().strftime("%d/%m/%Y"),
                "Observaciones": observaciones
            }])
            
            df_actualizado = pd.concat([df, nueva_fila], ignore_index=True)
            conn.update(data=df_actualizado)
            st.success(f"¡{nombre} guardado correctamente!")
            st.rerun()
        elif not lat_seleccionada:
            st.error("¡Por favor, toca primero el lugar en el mapa!")
        else:
            st.error("Falta el nombre del bar.")

st.write("### 📜 Listado detallado")
st.dataframe(df, use_container_width=True)
