import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Ruta Sidrera", layout="wide", page_icon="🍎")

# --- MEMORIA DE LA APP (Session State) ---
CENTER_START = [43.2960, -2.9975]

if 'map_center' not in st.session_state:
    st.session_state.map_center = CENTER_START
if 'temp_coords' not in st.session_state:
    st.session_state.temp_coords = None
if 'last_menu' not in st.session_state:
    st.session_state.last_menu = "🗺️ Ver Mapa"

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

# --- LÓGICA DE NAVEGACIÓN ---
menu = st.radio("Menú", ["🗺️ Ver Mapa", "➕ Añadir Nuevo"], 
                horizontal=True, 
                label_visibility="collapsed")

# Si el usuario cambia manualmente a "Añadir Nuevo", reseteamos las coordenadas temporales
if menu == "➕ Añadir Nuevo" and st.session_state.last_menu != "➕ Añadir Nuevo":
    st.session_state.temp_coords = None
st.session_state.last_menu = menu

# --- PANTALLAS ---

if menu == "🗺️ Ver Mapa":
    st.subheader("Mapa de Bares")
    m = folium.Map(location=st.session_state.map_center, zoom_start=18, tiles=None)
    folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                     attr='Google', name='Satélite').add_to(m)
    
    for _, row in df_mapa.iterrows():
        folium.Marker(
            [row['LAT'], row['LON']], 
            popup=f"<b>{row['Nombre']}</b><br>Sidra: {row.get('Marca', 'S/D')}", 
            icon=folium.Icon(color="green", icon="glass-whiskey", prefix="fa")
        ).add_to(m)
    st_folium(m, width="100%", height=550, key="mapa_v_visual")

elif menu == "➕ Añadir Nuevo":
    if st.session_state.temp_coords is None:
        st.info("📍 **Paso 1:** Haz clic en el mapa exactamente donde está el bar.")
        # Usamos el centro actual para que no se pierda si estamos navegando
        m_sel = folium.Map(location=st.session_state.map_center, zoom_start=19, tiles=None)
        folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                         attr='Google', name='Satélite').add_to(m_sel)
        
        click = st_folium(m_sel, width="100%", height=500, key="mapa_v_registro")
        
        if click and click.get("last_clicked"):
            st.session_state.temp_coords = (click["last_clicked"]["lat"], click["last_clicked"]["lng"])
            st.rerun()
    else:
        st.subheader("📝 Paso 2: Datos del bar")
        st.write(f"Coordenadas seleccionadas: `{st.session_state.temp_coords}`")
        
        with st.form("registro_form"):
            nombre = st.text_input("Nombre del Bar")
            marca = st.text_input("Marca de sidra")
            
            col1, col2 = st.columns(2)
            
            if col1.form_submit_button("✅ Guardar y ver en mapa", type="primary"):
                if nombre:
                    try:
                        lat_n = float(st.session_state.temp_coords[0])
                        lon_n = float(st.session_state.temp_coords[1])
                        
                        nueva_fila = pd.DataFrame([{
                            "Nombre": str(nombre), 
                            "LAT": lat_n, 
                            "LON": lon_n, 
                            "Marca": str(marca),
                            "Fecha_registro": datetime.now().strftime("%d/%m/%Y")
                        }])
                        
                        df_final = pd.concat([df_raw, nueva_fila], ignore_index=True)
                        conn.update(worksheet=NOMBRE_HOJA, data=df_final)
                        
                        # Actualizamos estado para la redirección
                        st.session_state.map_center = [lat_n, lon_n]
                        st.session_state.temp_coords = None
                        # Forzamos que la próxima carga sea en el mapa
                        st.session_state.last_menu = "🗺️ Ver Mapa" 
                        
                        st.balloons()
                        # Nota: st.rerun() nos llevará al estado inicial del radio (índice 0)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")
                else:
                    st.error("El nombre es obligatorio")
            
            if col2.form_submit_button("❌ Cancelar"):
                st.session_state.temp_coords = None
                st.rerun()
