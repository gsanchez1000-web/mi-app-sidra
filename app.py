import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Ruta Sidrera", layout="wide", page_icon="🍎")

# Estilos personalizados para los botones y el mapa
st.markdown("""
    <style>
    div.stButton > button {
        background-color: #2e7d32; color: white; border-radius: 12px;
        height: 3.5em; width: 100%; font-weight: bold; border: none;
    }
    .stButton button[kind="primary"] {
        background-color: #d35400 !important;
    }
    .leaflet-container {
        cursor: crosshair !important;
    }
    </style>
""", unsafe_allow_html=True)

# 2. CONEXIÓN Y CARGA DE DATOS
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Nombre exacto de tu pestaña en Google Sheets
    NOMBRE_HOJA = "Ruta de sidreria colaborativa"
    
    # Intentamos leer los datos
    df_raw = conn.read(worksheet=NOMBRE_HOJA, ttl="0")
    df_mapa = df_raw.copy()

except Exception as e:
    st.error("⚠️ Error de conexión con el Excel.")
    st.info("Revisa que la URL en 'Secrets' sea correcta y no tenga espacios al final.")
    st.stop()

# Limpieza de coordenadas para el mapa
if not df_mapa.empty:
    df_mapa['LAT'] = pd.to_numeric(df_mapa['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
    df_mapa['LON'] = pd.to_numeric(df_mapa['LON'].astype(str).str.replace(',', '.'), errors='coerce')
    df_mapa = df_mapa.dropna(subset=['LAT', 'LON'])

# 3. CONTROL DE ESTADO (Para recordar el clic del mapa)
if 'temp_coords' not in st.session_state:
    st.session_state.temp_coords = None

# Menú superior
menu = st.radio("Menú", ["🗺️ Ver Mapa", "📜 Listado", "➕ Añadir Nuevo"], 
                horizontal=True, label_visibility="collapsed")

# --- PANTALLAS ---

if menu == "🗺️ Ver Mapa":
    st.subheader("Bares Registrados")
    # Centrado en Barakaldo/Portugalete por defecto
    m = folium.Map(location=[43.2960, -2.9975], zoom_start=16, tiles=None)
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
        attr='Google', name='Satélite'
    ).add_to(m)
    
    for _, row in df_mapa.iterrows():
        # Color según formato: Verde para botella, azul para vaso
        color_pin = "green" if "Botella" in str(row['Formato']) else "blue"
        folium.Marker(
            [row['LAT'], row['LON']], 
            popup=f"<b>{row['Nombre']}</b><br>{row['Marca']}",
            icon=folium.Icon(color=color_pin, icon="glass-whiskey
