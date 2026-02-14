import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# CONFIGURACIÓN INICIAL
st.set_page_config(page_title="Ruta Sidrera", layout="wide")

# CONEXIÓN
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Nombre de la pestaña en tu Excel
    NOMBRE_HOJA = "Bares_con_Sidra"
    
    # Leemos la hoja
    df_raw = conn.read(worksheet=NOMBRE_HOJA, ttl="0")
    df_mapa = df_raw.copy()
except Exception as e:
    st.error("⚠️ Error al conectar con el Excel.")
    st.info(f"Asegúrate de que la pestaña del Excel se llame exactamente: {NOMBRE_HOJA}")
    st.write(f"Detalle técnico: {e}")
    st.stop()

# LIMPIEZA DE DATOS
if not df_mapa.empty:
    df_mapa['LAT'] = pd.to_numeric(df_mapa['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
    df_mapa['LON'] = pd.to_numeric(df_mapa['LON'].astype(str).str.replace(',', '.'), errors='coerce')
    df_mapa = df_mapa.dropna(subset=['LAT', 'LON'])

if 'temp_coords' not in st.session_state:
    st.session_state.temp_coords = None

menu = st.radio("Menú", ["🗺️ Ver Mapa", "➕ Añadir Nuevo"], horizontal=True)

if menu == "🗺️ Ver Mapa":
    st.subheader("Mapa de la Ruta")
    # Centrado en la zona de interés
    m = folium.Map(location=[43.2960, -2.9975], zoom_start=16)
    folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Satélite').add_to(m)
    
    for _, row in df_mapa.iterrows():
        folium.Marker(
            [row['LAT'], row['LON']], 
            popup=f"<b>{row['Nombre']}</b>", 
            icon=folium.Icon(color="green", icon="glass-whiskey", prefix="fa")
        ).add_to(m)
    st_folium(m, width="100%", height=550)

elif menu == "➕ Añadir Nuevo":
    if st.session_state.temp_coords is None:
        st.info("📍 Paso 1: Toca el mapa en el lugar del nuevo bar.")
        m_sel = folium.Map(location=[43.2960, -2.9975], zoom_start=19)
        folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Satélite').add_to(m_sel)
        click = st_folium(m_sel, width="100%", height=500)
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
                        conn.update(worksheet=NOMBRE_HOJA, data=df_final)
                        st.session_state.temp_coords = None
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error("Error al guardar. Revisa los permisos de 'Editor' en el Excel.")
                        st.write(e)
                else:
                    st.error("El nombre es obligatorio")
            if st.form_submit_button("❌ Cancelar"):
                st.session_state.temp_coords = None
                st.rerun()
