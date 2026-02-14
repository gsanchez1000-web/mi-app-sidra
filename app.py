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

# --- MAPA INTERACTIVO (GOOGLE SATELLITE) ---
st.subheader("📍 Toca el mapa para situar un bar o mira los existentes")

# Coordenadas de Barakaldo
centro = [43.2974, -2.9865]
m = folium.Map(location=centro, zoom_start=17)

# Añadimos la capa de Google Satélite Híbrido (más actualizado)
google_satellite = folium.TileLayer(
    tiles = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr = 'Google',
    name = 'Google Satellite',
    overlay = False,
    control = True
).add_to(m)

# Lógica de Iconos Personalizados
def obtener_icono(formato):
    # Usamos iconos de FontAwesome que se parecen a lo que buscas
    if "Botella" in formato and "Vaso" not in formato:
        return folium.Icon(color="green", icon="wine-bottle", prefix="fa")
    else:
        # Por defecto el vaso (vidrio/glass)
        return folium.Icon(color="orange", icon="glass-half-full", prefix="fa")

# Dibujar puntos existentes
if not df.empty:
    for i, row in df.iterrows():
        if pd.notnull(row['LAT']) and pd.notnull(row['LON']):
            folium.Marker(
                [row['LAT'], row['LON']],
                popup=f"<b>{row['Nombre']}</b><br>Sidra: {row['Marca']}",
                tooltip=row['Nombre'],
                icon=obtener_icono(row['Formato'])
            ).add_to(m)

salida_mapa = st_folium(m, width="100%", height=500)

lat_sel, lon_sel = None, None
if salida_mapa and salida_mapa["last_clicked"]:
    lat_sel = salida_mapa["last_clicked"]["lat"]
    lon_sel = salida_mapa["last_clicked"]["lng"]
    st.success(f"📍 Punto marcado. Ahora rellena los datos de abajo.")

# --- FORMULARIO SIMPLIFICADO ---
st.divider()
with st.form("nuevo_bar"):
    nombre = st.text_input("Nombre del Bar")
    marca = st.text_input("Marca de Sidra")
    
    # Nueva lógica de formato según tu idea
    formato = st.radio("¿Cómo se sirve aquí?", 
                       ["Se puede pedir por Vasos (Pote)", "Solo venden la Botella entera"])
    
    observaciones = st.text_area("Observaciones")
    
    if st.form_submit_button("Guardar en la Ruta"):
        if nombre and lat_sel:
            nueva_fila = pd.DataFrame([{
                "Nombre": nombre, "LAT": lat_sel, "LON": lon_sel, 
                "Marca": marca, "Formato": formato,
                "Fecha_registro": datetime.now().strftime("%d/%m/%Y"),
                "Observaciones": observaciones
            }])
            df_act = pd.concat([df, nueva_fila], ignore_index=True)
            conn.update(data=df_act)
            st.success(f"✅ {nombre} añadido a la ruta.")
            st.rerun()
        else:
            st.error("Asegúrate de haber marcado el punto en el mapa y puesto el nombre.")

st.dataframe(df, use_container_width=True)
