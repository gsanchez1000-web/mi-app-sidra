import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Ruta Sidrera", layout="wide", page_icon="🍎")

# 2. CONEXIÓN (Modo automático)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # LEER: Sin especificar nombre de hoja para evitar el error 400
    # Abrirá la primera pestaña que encuentre (la tuya)
    df_raw = conn.read(ttl="0") 
    df_mapa = df_raw.copy()
    
    # Este nombre lo usaremos solo para el botón de GUARDAR
    NOMBRE_HOJA_GUARDAR = "Bares_con_Sidra"

except Exception as e:
    st.error("⚠️ Error crítico de conexión.")
    st.write(e)
    st.stop()

# Limpieza de datos
if not df_mapa.empty:
    df_mapa['LAT'] = pd.to_numeric(df_mapa['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
    df_mapa['LON'] = pd.to_numeric(df_mapa['LON'].astype(str).str.replace(',', '.'), errors='coerce')
    df_mapa = df_mapa.dropna(subset=['LAT', 'LON'])

if 'temp_coords' not in st.session_state:
    st.session_state.temp_coords = None

menu = st.radio("Menú", ["🗺️ Ver Mapa", "➕ Añadir Nuevo"], horizontal=True, label_visibility="collapsed")

if menu == "🗺️ Ver Mapa":
    st.subheader("Mapa de Bares")
    m = folium.Map(location=[43.2960, -2.9975], zoom_start=16, tiles=None)
    folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Satélite').add_to(m)
    
    for _, row in df_mapa.iterrows():
        folium.Marker(
            [row['LAT'], row['LON']], 
            popup=f"<b>{row['Nombre']}</b>", 
            icon=folium.Icon(color="green", icon="glass-whiskey", prefix="fa")
        ).add_to(m)
    st_folium(m, width="100%", height=550, key="mapa_v1")

elif menu == "➕ Añadir Nuevo":
    if st.session_state.temp_coords is None:
        st.info("📍 Paso 1: Toca el mapa en el lugar del nuevo bar.")
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
            if st.form_submit_button("✅ Guardar"):
                if nombre:
                    try:
                        nueva = pd.DataFrame([{
                            "Nombre": str(nombre), 
                            "LAT": float(st.session_state.temp_coords[0]), 
                            "LON": float(st.session_state.temp_coords[1]), 
                            "Marca": str(marca),
                            "Fecha_registro": datetime.now().strftime("%d/%m/%Y")
                        }])
                        df_final = pd.concat([df_raw, nueva], ignore_index=True)
                        
                        # GUARDAR: Aquí sí usamos el nombre de la pestaña
                        conn.update(worksheet=NOMBRE_HOJA_GUARDAR, data=df_final)
                        
                        st.session_state.temp_coords = None
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error("Error al guardar. Verifica que el Excel esté como EDITOR.")
                        st.write(e)
                else:
                    st.error("El nombre es obligatorio")
            if st.form_submit_button("❌ Cancelar"):
                st.session_state.temp_coords = None
                st.rerun()
