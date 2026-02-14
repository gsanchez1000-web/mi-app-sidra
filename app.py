import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Ruta Sidrera", layout="wide", page_icon="🍎")

st.markdown("""
    <style>
    div.stButton > button { background-color: #2e7d32; color: white; border-radius: 12px; height: 3.5em; width: 100%; font-weight: bold; }
    .stButton button[kind="primary"] { background-color: #d35400 !important; }
    .leaflet-container { cursor: crosshair !important; }
    </style>
""", unsafe_allow_html=True)

# 2. CONEXIÓN SEGURA
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Intentamos leer la primera hoja disponible para evitar fallos de nombre
    df_raw = conn.read(ttl="0") 
    df_mapa = df_raw.copy()
    
    # Nombre de la hoja para cuando vayamos a guardar (asegúrate de que coincida en Excel)
    NOMBRE_HOJA = "Ruta de sidreria colaborativa"
    
except Exception as e:
    st.error("⚠️ Error al conectar con Google Sheets.")
    st.info("Revisa que en 'Secrets' la URL sea correcta y no tenga espacios al final.")
    st.stop()

# Limpieza de datos
if not df_mapa.empty:
    # Convertimos coordenadas y quitamos filas vacías
    df_mapa['LAT'] = pd.to_numeric(df_mapa['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
    df_mapa['LON'] = pd.to_numeric(df_mapa['LON'].astype(str).str.replace(',', '.'), errors='coerce')
    df_mapa = df_mapa.dropna(subset=['LAT', 'LON'])

if 'temp_coords' not in st.session_state:
    st.session_state.temp_coords = None

menu = st.radio("Menú", ["🗺️ Ver Mapa", "📜 Listado", "➕ Añadir Nuevo"], horizontal=True, label_visibility="collapsed")

# --- PANTALLAS ---

if menu == "🗺️ Ver Mapa":
    st.subheader("Mapa de la Ruta")
    m = folium.Map(location=[43.2960, -2.9975], zoom_start=17, tiles=None)
    folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Satélite').add_to(m)
    
    for _, row in df_mapa.iterrows():
        color = "green" if "Botella" in str(row['Formato']) else "blue"
        folium.Marker(
            [row['LAT'], row['LON']], 
            popup=str(row['Nombre']), 
            icon=folium.Icon(color=color, icon="glass-whiskey", prefix="fa")
        ).add_to(m)
    
    st_folium(m, width="100%", height=550, key="mapa_v1")

elif menu == "📜 Listado":
    st.subheader("Bares Registrados")
    st.dataframe(df_mapa[['Nombre', 'Marca', 'Formato', 'Fecha_registro']], use_container_width=True, hide_index=True)

elif menu == "➕ Añadir Nuevo":
    if st.session_state.temp_coords is None:
        st.info("📍 **Paso 1:** Pulsa sobre el mapa donde esté el nuevo bar.")
        m_sel = folium.Map(location=[43.2960, -2.9975], zoom_start=19, tiles=None)
        folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Satélite').add_to(m_sel)
        
        click = st_folium(m_sel, width="100%", height=500, key="mapa_v2")
        
        if click and click.get("last_clicked"):
            st.session_state.temp_coords = (click["last_clicked"]["lat"], click["last_clicked"]["lng"])
            st.rerun()
    else:
        st.subheader("📝 Paso 2: Datos del bar")
        with st.form("registro"):
            nombre = st.text_input("Nombre del Bar")
            marca = st.text_input("Marca de sidra")
            formato = st.radio("Formato", ["Vaso (Pote)", "Botella entera"])
            
            if st.form_submit_button("✅ Guardar"):
                if nombre:
                    nueva = pd.DataFrame([{
                        "Nombre": str(nombre), 
                        "LAT": float(st.session_state.temp_coords[0]), 
                        "LON": float(st.session_state.temp_coords[1]), 
                        "Marca": str(marca), 
                        "Formato": str(formato), 
                        "Fecha_registro": datetime.now().strftime("%d/%m/%Y")
                    }])
                    df_final = pd.concat([df_raw, nueva], ignore_index=True)
                    
                    # Intentamos guardar en la hoja especificada
                    conn.update(worksheet=NOMBRE_HOJA, data=df_final)
                    
                    st.session_state.temp_coords = None
                    st.balloons()
                    st.rerun()
                else:
                    st.error("El nombre es obligatorio")
            
            if st.form_submit_button("❌ Cancelar"):
                st.session_state.temp_coords = None
                st.rerun()
