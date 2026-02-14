import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Ruta Sidrera", layout="wide", page_icon="🍎")

# Estilos visuales
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
    # Nombre de la hoja que debes poner en tu Excel
    NOMBRE_HOJA = "Bares_con_Sidra"
    
    # Lectura de datos
    df_raw = conn.read(worksheet=NOMBRE_HOJA, ttl="0")
    df_mapa = df_raw.copy()
except Exception as e:
    st.error("⚠️ Error al conectar con el Excel.")
    st.info(f"Asegúrate de que la pestaña del Excel se llame exactamente: {NOMBRE_HOJA}")
    st.write(f"Detalle técnico: {e}")
    st.stop()

# Limpieza de datos
if not df_mapa.empty:
    df_mapa['LAT'] = pd.to_numeric(df_mapa['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
    df_mapa['LON'] = pd.to_numeric(df_mapa['LON'].astype(str).str.replace(',', '.'), errors='coerce')
    df_mapa = df_mapa.dropna(subset=['LAT', 'LON'])

if 'temp_coords' not in st.session_state:
    st.session_state.temp_coords = None

menu = st.radio("Menú", ["🗺️ Ver Mapa", "📜 Listado", "➕ Añadir Nuevo"], horizontal=True, label_visibility="collapsed")

# --- PANTALLAS ---

if menu == "🗺️ Ver Mapa":
    st.subheader("Mapa de la Ruta")
    m = folium.Map(location=[43.2960, -2.9975], zoom_start=16, tiles=None)
    folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Satélite').add_to(m)
    
    for _, row in df_mapa.iterrows():
        color_pin = "green" if "Botella" in str(row['Formato']) else "blue"
        folium.Marker(
            [row['LAT'], row['LON']], 
            popup=f"<b>{row['Nombre']}</b><br>{row.get('Marca', '')}", 
            icon=folium.Icon(color=color_pin, icon="glass-whiskey", prefix="fa")
        ).add_to(m)
    st_folium(m, width="100%", height=550, key="mapa_v1")

elif menu == "📜 Listado":
    st.subheader("Bares Registrados")
    st.dataframe(df_mapa[['Nombre', 'Marca', 'Formato', 'Fecha_registro']], use_container_width=True, hide_index=True)

elif menu == "➕ Añadir Nuevo":
    if st.session_state.temp_coords is None:
        st.info("📍 **Paso 1:** Toca en el mapa el lugar del nuevo bar.")
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
            marca = st.text_input("Marca de Sidra")
            formato = st.radio("Formato", ["Vaso (Pote)", "Botella entera"])
            
            col1, col2 = st.columns(2)
            if col1.form_submit_button("✅ Guardar", type="primary"):
                if nombre:
                    try:
                        nueva = pd.DataFrame([{
                            "Nombre": str(nombre), 
                            "LAT": float(st.session_state.temp_coords[0]), 
                            "LON": float(st.session_state.temp_coords[1]), 
                            "Marca": str(marca), 
                            "Formato": str(formato), 
                            "Fecha_registro": datetime.now().strftime("%d/%m/%Y")
                        }])
                        df_final = pd.concat([df_raw, nueva], ignore_index=True)
                        conn.update(worksheet=NOMBRE_HOJA, data=df_final)
                        st.session_state.temp_coords = None
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error("Error de permisos. ¿Está el Excel compartido como EDITOR?")
                        st.write(e)
                else:
                    st.error("El nombre es obligatorio")
            if col2.form_submit_button("❌ Cancelar"):
                st.session_state.temp_coords = None
                st.rerun()
