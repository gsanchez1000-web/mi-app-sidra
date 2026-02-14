import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# 1. CONFIGURACIÓN BÁSICA
st.set_page_config(page_title="Ruta Sidrera Barakaldo", layout="wide", page_icon="🍎")
st.title("🍎 Nuestra Ruta de la Sidra")

# Conexión limpia
conn = st.connection("gsheets", type=GSheetsConnection)
df_raw = conn.read(ttl="0")

# Limpieza de datos
df = df_raw.copy()
df['LAT'] = pd.to_numeric(df['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
df['LON'] = pd.to_numeric(df['LON'].astype(str).str.replace(',', '.'), errors='coerce')
df_mapa = df.dropna(subset=['LAT', 'LON'])

# 2. CREACIÓN DEL MAPA
centro = [43.2960, -2.9975]
m = folium.Map(location=centro, zoom_start=18, tiles=None)

# Capa Satélite Directa
folium.TileLayer(
    tiles = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr = 'Google',
    max_zoom = 20,
    control = False
).add_to(m)

# 3. MARCADORES (Icono Vaso y Fecha)
for i, row in df_mapa.iterrows():
    fecha = row.get('Fecha_registro', '---')
    popup_txt = f"<b>{row['Nombre']}</b><br>Sidra: {row['Marca']}<br><small>Fecha: {fecha}</small>"
    
    # Icono: Botella (verde) o Vaso (azul)
    formato = str(row.get('Formato', ''))
    if "Botella" in formato and "Vasos" not in formato:
        ic = folium.Icon(color="green", icon="wine-bottle", prefix="fa")
    else:
        ic = folium.Icon(color="blue", icon="glass-whiskey", prefix="fa")
        
    folium.Marker(
        [row['LAT'], row['LON']],
        popup=folium.Popup(popup_txt, max_width=200),
        tooltip=row['Nombre'],
        icon=ic
    ).add_to(m)

# 4. MAPA Y CAPTURA
# Añadimos un key único para evitar que Streamlit se confunda al recargar
salida = st_folium(m, width="100%", height=500, key="mapa_barakaldo")

lat_c, lon_c = None, None
if salida and salida["last_clicked"]:
    lat_c = salida["last_clicked"]["lat"]
    lon_c = salida["last_clicked"]["lng"]
    st.info("📍 Ubicación seleccionada. Rellena los datos abajo.")

# 5. FORMULARIO MANUAL
st.divider()
with st.form("registro_pote", clear_on_submit=True):
    st.subheader("➕ Registrar Bar")
    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre del Bar")
        marca = st.text_input("Marca de Sidra")
    with col2:
        formato_opcion = st.radio("¿Qué tienen?", ["Se puede pedir por Vasos (Pote)", "Solo venden la Botella entera"])
    
    obs = st.text_area("Observaciones")
    
    if st.form_submit_button("Guardar"):
        if nombre and lat_c:
            nueva_fila = pd.DataFrame([{
                "Nombre": nombre, "LAT": lat_c, "LON": lon_c,
                "Marca": marca, "Formato": formato_opcion,
                "Fecha_registro": datetime.now().strftime("%d/%m/%Y"),
                "Observaciones": obs
            }])
            df_act = pd.concat([df_raw, nueva_fila], ignore_index=True)
            conn.update(data=df_act)
            st.success("¡Guardado!")
            st.rerun()

# 6. TABLA CON FECHA
st.write("### 📜 Listado")
st.dataframe(df_mapa[['Nombre', 'Marca', 'Formato', 'Fecha_registro', 'Observaciones']], use_container_width=True)
