import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Ruta Sidrera", layout="wide")

# CONEXIÓN
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    NOMBRE_HOJA = "Ruta de sidreria colaborativa"
    df_raw = conn.read(worksheet=NOMBRE_HOJA, ttl="0")
    df_mapa = df_raw.copy()
except Exception as e:
    st.error("⚠️ Error al conectar con el Excel.")
    st.write(e) # Nos dirá si es culpa de la URL o del nombre de la hoja
    st.stop()

# LIMPIEZA
if not df_mapa.empty:
    df_mapa['LAT'] = pd.to_numeric(df_mapa['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
    df_mapa['LON'] = pd.to_numeric(df_mapa['LON'].astype(str).str.replace(',', '.'), errors='coerce')
    df_mapa = df_mapa.dropna(subset=['LAT', 'LON'])

if 'temp_coords' not in st.session_state:
    st.session_state.temp_coords = None

menu = st.radio("Menú", ["🗺️ Ver Mapa", "➕ Añadir Nuevo"], horizontal=True)

if menu == "🗺️ Ver Mapa":
    m = folium.Map(location=[43.2960, -2.9975], zoom_start=16)
    for _, row in df_mapa.iterrows():
        folium.Marker(
            [row['LAT'], row['LON']], 
            popup=row['Nombre'],
            icon=folium.Icon(color="green", icon="glass-whiskey", prefix="fa")
        ).add_to(m)
    st_folium(m, width="100%", height=500)

elif menu == "➕ Añadir Nuevo":
    if st.session_state.temp_coords is None:
        st.info("Pulsa en el mapa para situar el bar")
        m_sel = folium.Map(location=[43.2960, -2.9975], zoom_start=18)
        click = st_folium(m_sel, width="100%", height=500)
        if click and click.get("last_clicked"):
            st.session_state.temp_coords = (click["last_clicked"]["lat"], click["last_clicked"]["lng"])
            st.rerun()
    else:
        with st.form("registro"):
            nombre = st.text_input("Nombre del Bar")
            if st.form_submit_button("Guardar"):
                nueva = pd.DataFrame([{"Nombre": nombre, "LAT": st.session_state.temp_coords[0], "LON": st.session_state.temp_coords[1]}])
                df_final = pd.concat([df_raw, nueva], ignore_index=True)
                conn.update(worksheet=NOMBRE_HOJA, data=df_final)
                st.session_state.temp_coords = None
                st.success("¡Guardado!")
                st.rerun()
