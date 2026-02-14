import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# 1. INICIO RÁPIDO
st.set_page_config(page_title="Ruta Sidrera", layout="wide")
st.title("🍎 Ruta Sidrera Barakaldo")

# Conexión optimizada
conn = st.connection("gsheets", type=GSheetsConnection)
df_raw = conn.read(ttl="0")

# Limpieza básica
df = df_raw.copy()
df['LAT'] = pd.to_numeric(df['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
df['LON'] = pd.to_numeric(df['LON'].astype(str).str.replace(',', '.'), errors='coerce')
df_mapa = df.dropna(subset=['LAT', 'LON'])

# 2. MAPA SIMPLIFICADO
# Usamos un zoom un poco menor al inicio para que cargue más rápido
m = folium.Map(location=[43.2960, -2.9975], zoom_start=17)

# Capa Satélite (sin capas extra para no saturar)
folium.TileLayer(
    tiles = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr = 'Google',
    name = 'Satellite',
    overlay = False,
    control = False
).add_to(m)

# 3. MARCADORES (Iconos estándar para evitar errores de librerías externas)
for i, row in df_mapa.iterrows():
    fecha = row.get('Fecha_registro', '---')
    # Usamos iconos nativos de folium que no fallan
    color_icon = "green" if "Botella" in str(row['Formato']) else "blue"
    
    folium.Marker(
        [row['LAT'], row['LON']],
        popup=f"<b>{row['Nombre']}</b><br>Sidra: {row['Marca']}<br>Fecha: {fecha}",
        icon=folium.Icon(color=color_icon, icon="info-sign")
    ).add_to(m)

# 4. RENDERIZADO DEL MAPA
# 'use_container_width=True' ayuda a que no se rompa el diseño
salida = st_folium(m, height=450, width=800, key="mapa_final")

# 5. FORMULARIO SEPARADO
st.divider()
with st.form("nuevo_registro"):
    st.subheader("➕ Añadir Bar")
    nombre = st.text_input("Nombre del Bar")
    marca = st.text_input("Marca")
    formato = st.radio("Formato", ["Vaso (Pote)", "Botella entera"])
    obs = st.text_area("Notas")
    
    # Captura de coordenadas solo si se ha hecho clic
    lat_clic = salida["last_clicked"]["lat"] if salida and salida["last_clicked"] else None
    lon_clic = salida["last_clicked"]["lng"] if salida and salida["last_clicked"] else None
    
    if st.form_submit_button("Guardar"):
        if nombre and lat_clic:
            nueva_fila = pd.DataFrame([{
                "Nombre": nombre, "LAT": lat_clic, "LON": lon_clic,
                "Marca": marca, "Formato": formato,
                "Fecha_registro": datetime.now().strftime("%d/%m/%Y"),
                "Observaciones": obs
            }])
            df_act = pd.concat([df_raw, nueva_fila], ignore_index=True)
            conn.update(data=df_act)
            st.success("¡Guardado!")
            st.rerun()
        else:
            st.warning("⚠️ Pulsa en el mapa y pon un nombre.")

# 6. TABLA CON FECHAS
st.write("### 📜 Historial")
st.dataframe(df_mapa[['Nombre', 'Marca', 'Formato', 'Fecha_registro']], use_container_width=True)
