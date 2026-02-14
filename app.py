import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Ruta Sidrera", layout="wide", page_icon="🍎")

# --- MEMORIA DE LA APP (Session State) ---
# Coordenadas por defecto (Barakaldo)
CENTER_START = [43.2960, -2.9975]

if 'map_center' not in st.session_state:
    st.session_state.map_center = CENTER_START
if 'temp_coords' not in st.session_state:
    st.session_state.temp_coords = None
if 'menu_option' not in st.session_state:
    st.session_state.menu_option = "🗺️ Ver Mapa"

# CONEXIÓN
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    NOMBRE_HOJA = "Bares_con_Sidra"
    df_raw = conn.read(ttl="0") 
    df_mapa = df_raw.copy()
except Exception as e:
    st.error("⚠️ Error de conexión.")
    st.stop()

# LIMPIEZA DE COORDENADAS
if not df_mapa.empty:
    df_mapa['LAT'] = pd.to_numeric(df_mapa['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
    df_mapa['LON'] = pd.to_numeric(df_mapa['LON'].astype(str).str.replace(',', '.'), errors='coerce')
    df_mapa = df_mapa.dropna(subset=['LAT', 'LON'])

# CONTROL DE MENÚ (Usamos session_state para poder saltar de pestaña por código)
menu = st.radio("Menú", ["🗺️ Ver Mapa", "➕ Añadir Nuevo"], 
                horizontal=True, 
                label_visibility="collapsed",
                key="menu_radio",
                index=0 if st.session_state.menu_option == "🗺️ Ver Mapa" else 1)

# --- PANTALLAS ---

if menu == "🗺️ Ver Mapa":
    st.subheader("Mapa de Bares")
    
    # El mapa ahora se centra donde diga st.session_state.map_center
    m = folium.Map(location=st.session_state.map_center, zoom_start=18, tiles=None)
    folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                     attr='Google', name='Satélite').add_to(m)
    
    for _, row in df_mapa.iterrows():
        folium.Marker(
            [row['LAT'], row['LON']], 
            popup=f"<b>{row['Nombre']}</b><br>Sidra: {row.get('Marca', 'S/D')}", 
            icon=folium.Icon(color="green", icon="glass-whiskey", prefix="fa")
        ).add_to(m)
    st_folium(m, width="100%", height=550, key="mapa_v1")

elif menu == "➕ Añadir Nuevo":
    if st.session_state.temp_coords is None:
        st.info("📍 Paso 1: Haz clic en el mapa para situar el nuevo bar.")
        m_sel = folium.Map(location=CENTER_START, zoom_start=19, tiles=None)
        folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                         attr='Google', name='Satélite').add_to(m_sel)
        click = st_folium(m_sel, width="100%", height=500, key="mapa_v2")
        if click and click.get("last_clicked"):
            st.session_state.temp_coords = (click["last_clicked"]["lat"], click["last_clicked"]["lng"])
            st.rerun()
    else:
        st.subheader("📝 Paso 2: Datos del bar")
        with st.form("registro"):
            nombre = st.text_input("Nombre del Bar")
            marca = st.text_input("Marca de sidra")
            
            if st.form_submit_button("✅ Guardar Bar", type="primary"):
                if nombre:
                    try:
                        # Guardamos las coordenadas para el mapa antes de limpiar el estado
                        lat_nuevo = float(st.session_state.temp_coords[0])
                        lon_nuevo = float(st.session_state.temp_coords[1])
                        
                        nueva = pd.DataFrame([{
                            "Nombre": str(nombre), 
                            "LAT": lat_nuevo, 
                            "LON": lon_nuevo, 
                            "Marca": str(marca),
                            "Fecha_registro": datetime.now().strftime("%d/%m/%Y")
                        }])
                        
                        df_final = pd.concat([df_raw, nueva], ignore_index=True)
                        conn.update(worksheet=NOMBRE_HOJA, data=df_final)
                        
                        # --- LA MAGIA ESTÁ AQUÍ ---
                        st.session_state.map_center = [lat_nuevo, lon_nuevo] # Centrar mapa en el nuevo bar
                        st.session_state.menu_option = "🗺️ Ver Mapa"         # Cambiar pestaña
                        st.session_state.temp_coords = None                 # Limpiar selección
                        
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error("Error al guardar.")
                        st.write(e)
                else:
                    st.error("El nombre es obligatorio")
            
            if st.form_submit_button("❌ Cancelar"):
                st.session_state.temp_coords = None
                st.session_state.menu_option = "🗺️ Ver Mapa"
                st.rerun()
