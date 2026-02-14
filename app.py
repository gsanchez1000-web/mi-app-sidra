import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# 1. CONFIGURACIÓN E INTERFAZ LIMPIA
st.set_page_config(page_title="Ruta Sidrera", layout="wide", page_icon="🍎")

# Estilo para el botón flotante y botones de navegación
st.markdown("""
    <style>
    .stRadio [role=tablist] { gap: 20px; }
    div.stButton > button {
        background-color: #d35400; color: white; border-radius: 15px;
        height: 3em; width: 100%; font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# 2. CONEXIÓN A DATOS
conn = st.connection("gsheets", type=GSheetsConnection)
df_raw = conn.read(ttl="0")
df_mapa = df_raw.copy()
df_mapa['LAT'] = pd.to_numeric(df_mapa['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
df_mapa['LON'] = pd.to_numeric(df_mapa['LON'].astype(str).str.replace(',', '.'), errors='coerce')
df_mapa = df_mapa.dropna(subset=['LAT', 'LON'])

# 3. CONTROL DE NAVEGACIÓN (Evita el refresco infinito)
if 'pantalla' not in st.session_state:
    st.session_state.pantalla = "Inicio"
if 'temp_coords' not in st.session_state:
    st.session_state.temp_coords = None

# --- BARRA SUPERIOR DE NAVEGACIÓN ---
menu = st.radio("Menú", ["🗺️ Mapa", "📜 Listado", "➕ Añadir Nuevo"], 
                horizontal=True, label_visibility="collapsed")

# --- LÓGICA DE PANTALLAS ---

# PANTALLA 1: MAPA
if menu == "🗺️ Mapa":
    st.subheader("Nuestra Ruta")
    m = folium.Map(location=[43.2960, -2.9975], zoom_start=18, tiles=None)
    folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                     attr='Google', name='Satélite').add_to(m)
    
    for _, row in df_mapa.iterrows():
        color = "green" if "Botella" in str(row['Formato']) else "blue"
        folium.Marker(
            [row['LAT'], row['LON']],
            popup=f"<b>{row['Nombre']}</b><br>{row['Marca']}",
            icon=folium.Icon(color=color, icon="glass-whiskey", prefix="fa")
        ).add_to(m)
    
    # El mapa solo devuelve datos si se interactúa, reduciendo refrescos
    salida = st_folium(m, width="100%", height=500, key="mapa_principal")

# PANTALLA 2: LISTADO
elif menu == "📜 Listado":
    st.subheader("Listado de Bares")
    st.dataframe(df_mapa[['Nombre', 'Marca', 'Formato', 'Fecha_registro', 'Observaciones']], 
                 use_container_width=True, hide_index=True)

# PANTALLA 3: PROCESO DE ALTA (Simbolo +)
elif menu == "➕ Añadir Nuevo":
    if st.session_state.temp_coords is None:
        st.subheader("Paso 1: Selecciona la ubicación")
        st.write("Toca el mapa exactamente sobre el nuevo bar.")
        
        m_sel = folium.Map(location=[43.2960, -2.9975], zoom_start=19, tiles=None)
        folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                         attr='Google', name='Satélite').add_to(m_sel)
        
        salida_sel = st_folium(m_sel, width="100%", height=400, key="mapa_seleccion")
        
        if salida_sel and salida_sel["last_clicked"]:
            coords = (salida_sel["last_clicked"]["lat"], salida_sel["last_clicked"]["lng"])
            st.session_state.temp_coords = coords
            st.rerun()
    else:
        st.subheader("Paso 2: Datos del Bar")
        st.success(f"📍 Ubicación fijada: {st.session_state.temp_coords}")
        
        with st.form("registro_final", clear_on_submit=True):
            nombre = st.text_input("Nombre del Bar")
            marca = st.text_input("Marca de Sidra")
            formato = st.radio("¿Qué sirven?", ["Vaso (Pote)", "Botella entera"])
            obs = st.text_area("Observaciones")
            
            c1, c2 = st.columns(2)
            if c1.form_submit_button("✅ Registrar Bar"):
                if nombre:
                    nueva_fila = pd.DataFrame([{
                        "Nombre": nombre,
                        "LAT": st.session_state.temp_coords[0],
                        "LON": st.session_state.temp_coords[1],
                        "Marca": marca, "Formato": formato,
                        "Fecha_registro": datetime.now().strftime("%d/%m/%Y"),
                        "Observaciones": obs
                    }])
                    df_final = pd.concat([df_raw, nueva_fila], ignore_index=True)
                    conn.update(data=df_final)
                    st.session_state.temp_coords = None
                    st.success("¡Bar guardado!")
                    # Volver al mapa automáticamente
                    st.info("Cargando el mapa de nuevo...")
                    st.rerun()
            
            if c2.form_submit_button("❌ Cancelar"):
                st.session_state.temp_coords = None
                st.rerun()
