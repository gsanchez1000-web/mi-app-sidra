import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# 1. CONFIGURACIÓN ULTRA-LIGERA
st.set_page_config(page_title="Ruta Sidrera", layout="wide")
st.title("🍎 Ruta Sidrera Barakaldo")

# Conexión sin caché para evitar datos corruptos
conn = st.connection("gsheets", type=GSheetsConnection)
df_raw = conn.read(ttl=0)

df = df_raw.copy()
df['LAT'] = pd.to_numeric(df['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
df['LON'] = pd.to_numeric(df['LON'].astype(str).str.replace(',', '.'), errors='coerce')
df_mapa = df.dropna(subset=['LAT', 'LON'])

# 2. MAPA SIMPLIFICADO AL MÁXIMO
# Centrado en San Vicente
m = folium.Map(location=[43.2960, -2.9975], zoom_start=17, tiles=None)

# Capa Satélite directa (sin controles extra)
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr='Google',
    name='Google Satellite',
    overlay=False,
    control=False
).add_to(m)

# 3. MARCADORES ESTÁNDAR (Para evitar errores de carga de iconos)
for i, row in df_mapa.iterrows():
    # Azul para vaso, Verde para botella
    color_pinto = "blue"
    if "Botella" in str(row.get('Formato', '')):
        color_pinto = "green"
    
    fecha_reg = row.get('Fecha_registro', '---')
    
    folium.Marker(
        [row['LAT'], row['LON']],
        popup=f"{row['Nombre']} ({fecha_reg})",
        icon=folium.Icon(color=color_pinto, icon="info-sign")
    ).add_to(m)

# 4. RENDERIZADO CON "SHUTDOWN" DE DATOS INNECESARIOS
# Limitamos la respuesta del mapa para que no sature la memoria
salida = st_folium(
    m, 
    height=450, 
    width=700, 
    returned_objects=["last_clicked"], # SOLO pedimos el clic, nada más
    key="mapa_estatico"
)

# 5. FORMULARIO SEPARADO
st.divider()
with st.form("registro_limpio", clear_on_submit=True):
    st.subheader("➕ Añadir nueva parada")
    nombre = st.text_input("Nombre del Bar")
    marca = st.text_input("Marca de Sidra")
    formato = st.radio("Formato", ["Vaso (Pote)", "Botella entera"])
    
    # Solo capturamos si hay un clic real
    lat_clic = salida["last_clicked"]["lat"] if salida and salida.get("last_clicked") else None
    lon_clic = salida["last_clicked"]["lng"] if salida and salida.get("last_clicked") else None
    
    if st.form_submit_button("Guardar"):
        if nombre and lat_clic:
            nueva_fila = pd.DataFrame([{
                "Nombre": nombre, 
                "LAT": lat_clic, 
                "LON": lon_clic,
                "Marca": marca, 
                "Formato": formato,
                "Fecha_registro": datetime.now().strftime("%d/%m/%Y"),
                "Observaciones": ""
            }])
            df_final = pd.concat([df_raw, nueva_fila], ignore_index=True)
            conn.update(data=df_final)
            st.success("✅ ¡Guardado! Recargando...")
            st.rerun()
        else:
            st.warning("⚠️ Toca el mapa y escribe el nombre.")

# 6. TABLA DE REGISTROS
st.write("### 📜 Historial con Fechas")
st.dataframe(df_mapa[['Nombre', 'Marca', 'Fecha_registro']], use_container_width=True)
