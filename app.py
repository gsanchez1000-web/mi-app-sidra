import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

# Configuración inicial
st.set_page_config(page_title="Ruta Sidrera Barakaldo", layout="wide", page_icon="🍎")
st.title("🍎 Nuestra Ruta de la Sidra")

# 1. CONEXIÓN A GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)
df_raw = conn.read(ttl="0")

df = df_raw.copy()
df['LAT'] = pd.to_numeric(df['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
df['LON'] = pd.to_numeric(df['LON'].astype(str).str.replace(',', '.'), errors='coerce')
df_mapa = df.dropna(subset=['LAT', 'LON'])

# 2. FUNCIÓN PARA ADIVINAR EL NOMBRE (Con "escudo" para evitar errores)
def obtener_nombre_google(lat, lon):
    try:
        geolocator = Nominatim(user_agent="sidra_app_v2")
        location = geolocator.reverse((lat, lon), timeout=3)
        if location:
            address = location.raw.get('address', {})
            # Buscamos el nombre del local o la calle
            return address.get('amenity') or address.get('shop') or f"{address.get('road', '')} {address.get('house_number', '')}".strip()
    except:
        return ""
    return ""

# 3. ICONOS (VASO SIDRA VS BOTELLA)
def obtener_icono(formato_texto):
    formato_texto = str(formato_texto)
    if "Botella" in formato_texto and "Vasos" not in formato_texto:
        return folium.Icon(color="green", icon="wine-bottle", prefix="fa", icon_color="white")
    else:
        # Icono de vaso ancho y limpio
        return folium.Icon(color="blue", icon="glass-whiskey", prefix="fa", icon_color="white")

# 4. MAPA SATÉLITE
centro = [43.2960, -2.9975]
m = folium.Map(location=centro, zoom_start=18, tiles=None)
folium.TileLayer(
    tiles = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr = 'Google',
    max_zoom = 20,
    control = False
).add_to(m)

# 5. DIBUJAR MARCADORES EXISTENTES (Con Fecha)
for i, row in df_mapa.iterrows():
    fecha = row.get('Fecha_registro', '---')
    popup_text = f"""
    <div style='font-family: sans-serif; min-width: 140px;'>
        <h4 style='margin:0; color:#d35400;'>{row['Nombre']}</h4>
        <b>Sidra:</b> {row['Marca']}<br>
        <small>Registrado el: {fecha}</small><br>
        <p style='margin-top:5px;'><i>{row['Observaciones']}</i></p>
    </div>
    """
    folium.Marker(
        [row['LAT'], row['LON']],
        popup=folium.Popup(popup_text, max_width=250),
        tooltip=row['Nombre'],
        icon=obtener_icono(row.get('Formato', 'Vaso'))
    ).add_to(m)

# 6. LÓGICA DE CLIC Y FORMULARIO
if 'nombre_detectado' not in st.session_state:
    st.session_state.nombre_detectado = ""

mapa_clic = st_folium(m, width="100%", height=500)

lat_c, lon_c = None, None
if mapa_clic and mapa_clic["last_clicked"]:
    lat_c = mapa_clic["last_clicked"]["lat"]
    lon_c = mapa_clic["last_clicked"]["lng"]
    # Llamamos a la función para autocompletar el nombre
    with st.spinner('Identificando local...'):
        st.session_state.nombre_detectado = obtener_nombre_google(lat_c, lon_c)

st.divider()
with st.form("registro_rapido", clear_on_submit=True):
    st.subheader("➕ Nueva Parada")
    col1, col2 = st.columns(2)
    with col1:
        # El nombre se autocompleta aquí
        nombre_input = st.text_input("Nombre del Bar / Dirección", value=st.session_state.nombre_detectado)
        marca_input = st.text_input("Marca de Sidra")
    with col2:
        formato_input = st.radio("¿Cómo se sirve?", ["Se puede pedir por Vasos (Pote)", "Solo venden la Botella entera"])
    
    obs_input = st.text_area("Observaciones")
    
    if st.form_submit_button("Guardar Parada"):
        if nombre_input and lat_c:
            nueva_fila = pd.DataFrame([{
                "Nombre": nombre_input, "LAT": lat_c, "LON": lon_c,
                "Marca": marca_input, "Formato": formato_input,
                "Fecha_registro": datetime.now().strftime("%d/%m/%Y"),
                "Observaciones": obs_input
            }])
            df_final = pd.concat([df_raw, nueva_fila], ignore_index=True)
            conn.update(data=df_final)
            st.session_state.nombre_detectado = ""
            st.success("¡Guardado con éxito!")
            st.rerun()

# 7. TABLA DE HISTORIAL
st.write("### 📜 Historial de Registros")
st.dataframe(df_mapa[['Nombre', 'Marca', 'Formato', 'Fecha_registro', 'Observaciones']], use_container_width=True)
