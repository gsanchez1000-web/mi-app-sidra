import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# 1. CONFIGURACIÓN E INTERFAZ
st.set_page_config(page_title="Ruta Sidrera", layout="wide", page_icon="🍎")

# Estilos visuales
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
conn = st.connection("gsheets", type=GSheetsConnection)

# Leemos la hoja específica
df_raw = conn.read(worksheet="Ruta de sidreria colaborativa", ttl="0")
df_mapa = df_raw.copy()

# Limpieza de coordenadas para el mapa
if not df_mapa.empty:
    df_mapa['LAT'] = pd.to_numeric(df_mapa['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
    df_mapa['LON'] = pd.to_numeric(df_mapa['LON'].astype(str).str.replace(',', '.'), errors='coerce')
    df_mapa = df_mapa.dropna(subset=['LAT', 'LON'])

# 3. CONTROL DE ESTADO
if 'temp_coords' not in st.session_state:
    st.session_state.temp_coords = None

# Menú superior
menu = st.radio("Menú", ["🗺️ Ver Mapa", "📜 Listado", "➕ Añadir Nuevo"], 
                horizontal=True, label_visibility="collapsed")

# --- PANTALLAS ---

if menu == "🗺️ Ver Mapa":
    st.subheader("Bares Registrados")
    m = folium.Map(location=[43.2960, -2.9975], zoom_start=17, tiles=None)
    folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                     attr='Google', name='Satélite').add_to(m)
    
    for _, row in df_mapa.iterrows():
        color = "green" if "Botella" in str(row['Formato']) else "blue"
        folium.Marker(
            [row['LAT'], row['LON']], 
            popup=f"<b>{row['Nombre']}</b><br>{row['Marca']}",
            icon=folium.Icon(color=color, icon="glass-whiskey", prefix="fa")
        ).add_to(m)
    
    st_folium(m, width="100%", height=550, key="mapa_lectura")

elif menu == "📜 Listado":
    st.subheader("Listado de la Ruta")
    st.dataframe(df_mapa[['Nombre', 'Marca', 'Formato', 'Fecha_registro', 'Observaciones']], 
                 use_container_width=True, hide_index=True)

elif menu == "➕ Añadir Nuevo":
    if st.session_state.temp_coords is None:
        st.info("📍 **Paso 1:** Busca el bar en el mapa y **pulsa directamente sobre él**.")
        
        m_sel = folium.Map(location=[43.2960, -2.9975], zoom_start=19, tiles=None)
        folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                         attr='Google', name='Satélite').add_to(m_sel)
        
        # Captura el clic
        salida_sel = st_folium(m_sel, width="100%", height=500, key="mapa_interactivo")
        
        if salida_sel and salida_sel.get("last_clicked"):
            st.session_state.temp_coords = (
                salida_sel["last_clicked"]["lat"], 
                salida_sel["last_clicked"]["lng"]
            )
            st.rerun()
            
    else:
        # PANTALLA DE FORMULARIO
        st.subheader("📝 Paso 2: Datos del bar")
        
        with st.form("formulario_registro", clear_on_submit=True):
            nombre = st.text_input("Nombre del Bar")
            marca = st.text_input("Marca de Sidra")
            formato = st.radio("Formato", ["Vaso (Pote)", "Botella entera"])
            observaciones = st.text_area("Observaciones")
            
            col1, col2 = st.columns(2)
            
            if col1.form_submit_button("✅ Guardar Bar"):
                if nombre:
                    nueva_fila = pd.DataFrame([{
                        "Nombre": str(nombre),
                        "LAT": float(st.session_state.temp_coords[0]),
                        "LON": float(st.session_state.temp_coords[1]),
                        "Marca": str(marca),
                        "Formato": str(formato),
                        "Fecha_registro": datetime.now().strftime("%d/%m/%Y"),
                        "Observaciones": str(observaciones)
                    }])
                    
                    df_final = pd.concat([df_raw, nueva_fila], ignore_index=True)
                    conn.update(worksheet="Ruta de sidreria colaborativa", data=df_final)
                    
                    st.session_state.temp_coords = None
                    st.balloons()
                    st.rerun()
                else:
                    st.error("El nombre es obligatorio.")
            
            if col2.form_submit_button("❌ Cancelar"):
                st.session_state.temp_coords = None
                st.rerun()
