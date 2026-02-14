import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

# Configuración de página
st.set_page_config(page_title="Ruta Sidrera Barakaldo", layout="wide", page_icon="🍎")
st.title("🍎 Nuestra Ruta de la Sidra")

# 1. CONEXIÓN A DATOS
conn = st.connection("gsheets", type=GSheetsConnection)
df_raw = conn.read(ttl="0")

df = df_raw.copy()
df['LAT'] = pd.to_numeric(df['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
df['LON'] = pd.to_numeric(df['LON'].astype(str).str.replace(',', '.'), errors='coerce')
df_mapa = df.dropna(subset=['LAT', 'LON'])

# 2. FUNCIÓN PARA ADIVINAR NOMBRE (AUTOCOMPLETADO)
def obtener_nombre_google(lat, lon):
    try:
        # Usamos un agente único para evitar bloqueos
        geolocator = Nominatim(user_agent="sidra_app_barakaldo_v3")
        location = geolocator.reverse((lat, lon), timeout=3)
        if location:
            address = location.raw.get('address', {})
            # Intentamos: Nombre negocio > Calle y número
            return address.get('amenity') or address.get('shop') or f"{address.get('road', '')} {address.get('house_number', '')}".strip()
    except:
        return "Nuevo Bar"
    return "Nuevo Bar"

# 3. ICONOS (VASO SIDRA VS BOTELLA)
def obtener_icono(formato_texto):
    formato_texto = str(formato_texto)
    if "Botella" in formato_texto and "Vasos" not in formato_texto:
        return folium.Icon(color="green", icon="wine-bottle", prefix="fa", icon_color="white")
    else:
        # Usamos 'glass-whiskey': es un vaso ancho, sólido y sin dibujos raros
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

# 5. DIBUJAR MARCADORES EXISTENTES (CON FECHA)
for i, row in df_mapa.iterrows():
    fecha_reg = row.get('Fecha_registro', '---')
    popup_text = f"""
    <div style='font-family: sans-serif; min-width: 140px;'>
        <h4 style='margin:0; color:#d35400;'>{row['Nombre']}</h4>
        <b>Sidra:</b> {row['Marca']}<br>
        <small style='color:gray;'>Registrado el: {fecha_reg}</small>
        <p style='margin-top:5px; border-top:1px solid #eee; padding-top:5px;'><i>{row['Observaciones']}</i></p>
    </div>
    """
    folium.Marker(
        [row['LAT'], row['LON']],
        popup=folium.Popup(popup_text, max_width=250),
        tooltip=row['Nombre'],
        icon=obtener_icono(row.get('Formato', 'Vaso'))
    ).add_to(m)

# 6. CAPTURA DE CLIC Y FORMULARIO
if 'nombre_input' not in st.session_state:
    st.session_state.nombre_input = ""

mapa_clic = st_folium(m, width="100%", height=500)

lat_c, lon_c = None, None
if mapa_clic and mapa_clic["last_clicked"]:
    lat_c = mapa_clic["last_clicked"]["lat"]
    lon_c = mapa_clic["last_clicked"]["lng"]
    # Rellenamos el nombre automáticamente al pinchar
    with st.spinner('Adivinando nombre del sitio...'):
        st.session_state.nombre_input = obtener_nombre_google(lat_c, lon_c)

st.divider()
with st.form("registro", clear_on_submit=True):
    st.subheader("➕ Añadir bar a la ruta")
    col1, col2 = st.columns(2)
    with col1:
        nombre_final = st.text_input("Nombre (se rellena al tocar el mapa)", value=st.session_state.nombre_input)
        marca_final = st.text_input("Marca de Sidra")
    with col2:
        formato_final = st.radio("¿Qué tienen?", ["Se puede pedir por Vasos (Pote)", "Solo venden la Botella entera"])
    
    obs_final = st.text_area("Observaciones")
    
    if st.form_submit_button("Guardar en mi Excel"):
        if nombre_final and lat_c:
            nueva_fila = pd.DataFrame([{
                "Nombre": nombre_final, "LAT": lat_c, "LON": lon_c,
                "Marca": marca_final, "Formato": formato_final,
                "Fecha_registro": datetime.now().strftime("%d/%m/%Y"),
                "Observaciones": obs_final
            }])
            df_final = pd.concat([df_raw, nueva_fila], ignore_index=True)
            conn.update(data=df_final)
            st.session_state.nombre_input = "" # Limpiar
            st.success("¡Bar guardado!")
            st.rerun()

# 7. TABLA DE HISTORIAL CON FECHAS
st.write("### 📜 Listado de Bares")
st.dataframe(df_mapa[['Nombre', 'Marca', 'Formato', 'Fecha_registro', 'Observaciones']], use_container_width=True)
