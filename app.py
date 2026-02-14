import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

# 1. CONFIGURACIÓN Y CONEXIÓN
st.set_page_config(page_title="Ruta Sidrera Barakaldo", layout="wide", page_icon="🍎")
st.title("🍎 Nuestra Ruta de la Sidra")

conn = st.connection("gsheets", type=GSheetsConnection)
df_raw = conn.read(ttl="0")

df = df_raw.copy()
df['LAT'] = pd.to_numeric(df['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
df['LON'] = pd.to_numeric(df['LON'].astype(str).str.replace(',', '.'), errors='coerce')
df_mapa = df.dropna(subset=['LAT', 'LON'])

# 2. FUNCIÓN DE AUTOCOMPLETADO (GEOPY)
def obtener_nombre_punto(lat, lon):
    try:
        geolocator = Nominatim(user_agent="sidra_app_barakaldo")
        location = geolocator.reverse((lat, lon), timeout=3)
        if location:
            address = location.raw.get('address', {})
            # Prioridad: Nombre del local > Calle y número
            return address.get('amenity') or address.get('shop') or f"{address.get('road', '')} {address.get('house_number', '')}".strip()
    except:
        return ""
    return ""

# 3. LÓGICA DE ICONOS (VASO DE SIDRA Y BOTELLA)
def obtener_icono(formato_texto):
    formato_texto = str(formato_texto)
    if "Botella" in formato_texto and "Vasos" not in formato_texto:
        return folium.Icon(color="green", icon="wine-bottle", prefix="fa", icon_color="white")
    else:
        # Usamos glass-whiskey que es el vaso de sidra más limpio
        return folium.Icon(color="blue", icon="glass-whiskey", prefix="fa", icon_color="white")

# 4. MAPA
centro = [43.2960, -2.9975]
m = folium.Map(location=centro, zoom_start=18, tiles=None)
folium.TileLayer(
    tiles = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr = 'Google Maps',
    max_zoom = 20,
    control = False
).add_to(m)

# 5. DIBUJAR PUNTOS EXISTENTES (CON FECHA)
for i, row in df_mapa.iterrows():
    fecha = row.get('Fecha_registro', '---')
    popup_text = f"""
    <div style='font-family: sans-serif;'>
        <b>{row['Nombre']}</b><br>
        Sidra: {row['Marca']}<br>
        Formato: {row['Formato']}<br>
        <small style='color:gray'>Registrado: {fecha}</small>
    </div>
    """
    folium.Marker(
        [row['LAT'], row['LON']],
        popup=folium.Popup(popup_text, max_width=200),
        tooltip=row['Nombre'],
        icon=obtener_icono(row.get('Formato', 'Vaso'))
    ).add_to(m)

# 6. CAPTURA DE CLIC Y FORMULARIO
if 'nombre_sugerido' not in st.session_state:
    st.session_state.nombre_sugerido = ""

mapa_render = st_folium(m, width="100%", height=500)

lat_clic, lon_clic = None, None
if mapa_render and mapa_render["last_clicked"]:
    lat_clic = mapa_render["last_clicked"]["lat"]
    lon_clic = mapa_render["last_clicked"]["lng"]
    # Intentamos adivinar el nombre
    with st.spinner('Adivinando nombre del sitio...'):
        st.session_state.nombre_sugerido = obtener_nombre_punto(lat_clic, lon_clic)

st.divider()
with st.form("nuevo_registro", clear_on_submit=True):
    st.subheader("➕ Añadir Parada")
    col1, col2 = st.columns(2)
    with col1:
        # Aquí aparece el nombre automático si hemos pinchado en el mapa
        nombre_final = st.text_input("Nombre del Bar/Calle", value=st.session_state.nombre_sugerido)
        marca_sidra = st.text_input("Marca de Sidra")
    with col2:
        formato_sidra = st.radio("¿Cómo se sirve?", ["Se puede pedir por Vasos (Pote)", "Solo venden la Botella entera"])
    
    notas = st.text_area("Observaciones")
    
    if st.form_submit_button("Guardar"):
        if nombre_final and lat_clic:
            nueva_fila = pd.DataFrame([{
                "Nombre": nombre_final, "LAT": lat_clic, "LON": lon_clic,
                "Marca": marca_sidra, "Formato": formato_sidra,
                "Fecha_registro": datetime.now().strftime("%d/%m/%Y"),
                "Observaciones": notas
            }])
            df_final = pd.concat([df_raw, nueva_fila], ignore_index=True)
            conn.update(data=df_final)
            st.session_state.nombre_sugerido = "" # Limpiar
            st.success("¡Guardado!")
            st.rerun()

# 7. TABLA CON FECHAS
st.write("### Historial de la Ruta")
st.dataframe(df_mapa[['Nombre', 'Marca', 'Formato', 'Fecha_registro', 'Observaciones']], use_container_width=True)
