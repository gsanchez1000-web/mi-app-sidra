import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# Configuración de la página
st.set_page_config(page_title="Ruta Sidrera Barakaldo", layout="wide", page_icon="🍎")

st.title("🍎 Nuestra Ruta de la Sidra")
st.markdown("Mantén pulsado o haz clic en el mapa para marcar la ubicación de un nuevo bar.")

# 1. CONEXIÓN CON GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl="0")

# Limpieza de datos: aseguramos que LAT y LON sean números y quitamos filas vacías para el mapa
df['LAT'] = pd.to_numeric(df['LAT'], errors='coerce')
df['LON'] = pd.to_numeric(df['LON'], errors='coerce')
df_mapa = df.dropna(subset=['LAT', 'LON'])

# 2. CONFIGURACIÓN DEL MAPA (GOOGLE SATELLITE)
# Centro inicial en Barakaldo
centro_barakaldo = [43.2974, -2.9865]

# Creamos el mapa sin capas por defecto (tiles=None)
m = folium.Map(location=centro_barakaldo, zoom_start=17, tiles=None)

# Añadimos la capa de Google Satélite Híbrido con zoom máximo aumentado (20)
folium.TileLayer(
    tiles = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr = 'Google Maps Satellite',
    name = 'Google Satellite',
    max_zoom = 20,
    overlay = False,
    control = False
).add_to(m)

# 3. LÓGICA DE ICONOS PERSONALIZADOS
def obtener_icono(formato_texto):
    formato_texto = str(formato_texto)
    if "Botella" in formato_texto and "Vaso" not in formato_texto:
        # Icono de botella (color verde)
        return folium.Icon(color="green", icon="wine-bottle", prefix="fa")
    else:
        # Icono de vaso (color naranja)
        return folium.Icon(color="orange", icon="glass-half-full", prefix="fa")

# 4. DIBUJAR LOS BARES EXISTENTES
for i, row in df_mapa.iterrows():
    popup_info = f"""
    <b>{row['Nombre']}</b><br>
    <b>Sidra:</b> {row['Marca']}<br>
    <b>Formato:</b> {row['Formato']}<br>
    <i>{row['Observaciones']}</i>
    """
    folium.Marker(
        [row['LAT'], row['LON']],
        popup=folium.Popup(popup_info, max_width=250),
        tooltip=row['Nombre'],
        icon=obtener_icono(row.get('Formato', 'Vaso'))
    ).add_to(m)

# 5. MOSTRAR MAPA Y CAPTURAR CLIC
salida_mapa = st_folium(m, width="100%", height=550)

lat_seleccionada = None
lon_seleccionada = None

if salida_mapa and salida_mapa["last_clicked"]:
    lat_seleccionada = salida_mapa["last_clicked"]["lat"]
    lon_seleccionada = salida_mapa["last_clicked"]["lng"]
    st.success(f"📍 Ubicación capturada: {lat_seleccionada:.5f}, {lon_seleccionada:.5f}")

# 6. FORMULARIO PARA AÑADIR NUEVOS BARES
st.divider()
with st.form("nuevo_bar", clear_on_submit=True):
    st.subheader("➕ Registrar nueva parada")
    
    col_a, col_b = st.columns(2)
